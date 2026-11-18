import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app import models, schemas
from app.api import deps
router = APIRouter(prefix="/documents", tags=["Documents"])

# Where we will store uploaded files locally
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=schemas.DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    Upload a new document. 
    The document is automatically tied to the current user's organization.
    """
    # 1. Create the Document record
    new_doc = models.Document(
        title=title,
        owner_id=current_user.id,
        org_id=current_user.org_id,
        status=models.DocumentStatus.DRAFT
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    # 2. Save the file physically to the disk
    file_extension = os.path.splitext(file.filename)[1]
    safe_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as buffer:
        while chunk := file.file.read(1024 * 1024):
            buffer.write(chunk)

    # 3. Create the Version record
    new_version = models.DocumentVersion(
        document_id=new_doc.id,
        version_number=1,
        file_name=file.filename,
        file_path=file_path,
        uploaded_by_id=current_user.id
    )
    db.add(new_version)
    db.commit()
    
    db.refresh(new_doc)
    return new_doc
@router.get("/", response_model=schemas.DocumentListResponse)
def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = None,
    doc_status: models.DocumentStatus | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    List documents for the current user's organization.
    Supports pagination (skip, limit), search by title, and filter by status.
    """
    # 1. Start the query, enforcing Multi-Tenancy!
    query = db.query(models.Document).filter(models.Document.org_id == current_user.org_id)

    # 2. Apply search filter (if provided)
    if search:
        query = query.filter(models.Document.title.ilike(f"%{search}%"))

    # 3. Apply status filter (if provided)
    if doc_status:
        query = query.filter(models.Document.status == doc_status)

    # 4. Get total count BEFORE pagination
    total = query.count()

    # 5. Apply pagination and order by newest first
    documents = query.order_by(models.Document.created_at.desc()).offset(skip).limit(limit).all()

    return {"total": total, "items": documents}


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """Download the latest version of a document."""
    # 1. Find the document, ensuring it belongs to the user's organization
    doc = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.org_id == current_user.org_id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 2. Find the latest version
    if not doc.versions:
        raise HTTPException(status_code=404, detail="No versions found for this document")
    
    latest_version = max(doc.versions, key=lambda v: v.version_number)

    # 3. Check if the file exists on disk
    if not os.path.exists(latest_version.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    # 4. Return the file
    return FileResponse(
        path=latest_version.file_path, 
        filename=latest_version.file_name,
        media_type='application/octet-stream'
    )
@router.get("/", response_model=schemas.DocumentListResponse)
def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = None,
    doc_status: models.DocumentStatus | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """
    List documents for the current user's organization.
    Supports pagination (skip, limit), search by title, and filter by status.
    """
    query = db.query(models.Document).filter(models.Document.org_id == current_user.org_id)

    if search:
        query = query.filter(models.Document.title.ilike(f"%{search}%"))

    if doc_status:
        query = query.filter(models.Document.status == doc_status)

    total = query.count()

    documents = query.order_by(models.Document.created_at.desc()).offset(skip).limit(limit).all()

    return {"total": total, "items": documents}


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    """Download the latest version of a document."""
    doc = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.org_id == current_user.org_id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not doc.versions:
        raise HTTPException(status_code=404, detail="No versions found for this document")

    latest_version = max(doc.versions, key=lambda v: v.version_number)

    if not os.path.exists(latest_version.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        path=latest_version.file_path,
        filename=latest_version.file_name,
        media_type="application/octet-stream"
    )

@router.patch("/{document_id}/status", response_model=schemas.DocumentResponse)
def update_document_status(
    document_id: int,
    new_status: models.DocumentStatus,
    db: Session = Depends(get_db),
    # The bouncer! Only OWNER or REVIEWER can use this route
    current_user: models.User = Depends(deps.require_role([models.UserRole.OWNER, models.UserRole.REVIEWER]))
):
    """
    Update the status of a document (Approve/Reject).
    Only accessible by OWNER or REVIEWER roles.
    """
    # 1. Find the document, enforcing multi-tenancy
    doc = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.org_id == current_user.org_id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 2. Update the status
    doc.status = new_status
    db.commit()
    db.refresh(doc)

    return doc
