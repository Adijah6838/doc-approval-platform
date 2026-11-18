import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app import models, schemas
from app.api import deps

router = APIRouter(prefix="/documents", tags=["Documents"])
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=schemas.DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user)
):
    new_doc = models.Document(title=title, owner_id=current_user.id, org_id=current_user.org_id, status=models.DocumentStatus.DRAFT)
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    file_extension = os.path.splitext(file.filename)[1]
    safe_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as buffer:
        while chunk := file.file.read(1024 * 1024):
            buffer.write(chunk)

    new_version = models.DocumentVersion(
        document_id=new_doc.id, version_number=1, file_name=file.filename, 
        file_path=file_path, uploaded_by_id=current_user.id
    )
    db.add(new_version)
    db.commit()
    db.refresh(new_doc)
    return new_doc

@router.get("/", response_model=schemas.DocumentListResponse)
def list_documents(
    skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100),
    search: str | None = None, doc_status: models.DocumentStatus | None = None,
    db: Session = Depends(get_db), current_user: models.User = Depends(deps.get_current_user)
):
    query = db.query(models.Document).filter(models.Document.org_id == current_user.org_id)
    if search:
        query = query.filter(models.Document.title.ilike(f"%{search}%"))
    if doc_status:
        query = query.filter(models.Document.status == doc_status)
    
    total = query.count()
    documents = query.order_by(models.Document.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": documents}

@router.get("/{document_id}/download")
def download_document(document_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(deps.get_current_user)):
    doc = db.query(models.Document).filter(models.Document.id == document_id, models.Document.org_id == current_user.org_id).first()
    if not doc or not doc.versions:
        raise HTTPException(status_code=404, detail="Document not found")
    
    latest_version = max(doc.versions, key=lambda v: v.version_number)
    if not os.path.exists(latest_version.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
        
    return FileResponse(path=latest_version.file_path, filename=latest_version.file_name, media_type='application/octet-stream')

@router.post("/{document_id}/submit", response_model=schemas.DocumentResponse)
def submit_for_review(document_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(deps.get_current_user)):
    doc = db.query(models.Document).filter(models.Document.id == document_id, models.Document.org_id == current_user.org_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != models.DocumentStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only DRAFT documents can be submitted")
    
    doc.status = models.DocumentStatus.PENDING
    log = models.AuditLog(org_id=current_user.org_id, user_id=current_user.id, document_id=doc.id, action="Submitted for review")
    db.add(log)
    db.commit()
    db.refresh(doc)
    return doc

@router.post("/{document_id}/review", response_model=schemas.DocumentResponse)
def review_document(
    document_id: int, review: schemas.ReviewRequest, 
    db: Session = Depends(get_db), current_user: models.User = Depends(deps.require_role([models.UserRole.REVIEWER, models.UserRole.OWNER]))
):
    doc = db.query(models.Document).filter(models.Document.id == document_id, models.Document.org_id == current_user.org_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != models.DocumentStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only PENDING documents can be reviewed")
    
    if review.action.lower() == "approve":
        doc.status = models.DocumentStatus.APPROVED
        action_text = "Approved"
    elif review.action.lower() == "reject":
        doc.status = models.DocumentStatus.REJECTED
        action_text = "Rejected"
    else:
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")
        
    log = models.AuditLog(org_id=current_user.org_id, user_id=current_user.id, document_id=doc.id, action=action_text)
    db.add(log)
    db.commit()
    db.refresh(doc)
    return doc
