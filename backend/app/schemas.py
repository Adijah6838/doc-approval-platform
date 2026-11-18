from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from app.models import UserRole, DocumentStatus


# ==========================================
# 1. Auth & User Schemas
# ==========================================

class UserCreate(BaseModel):
    """What we expect when a user registers."""
    email: EmailStr
    password: str
    org_name: str

class UserLogin(BaseModel):
    """What we expect when a user logs in."""
    email: EmailStr
    password: str

class Token(BaseModel):
    """What we send back when a user logs in successfully."""
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    """What we send back when someone asks for user info."""
    id: int
    email: EmailStr
    role: UserRole
    org_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 2. Organization Schemas
# ==========================================

class OrganizationResponse(BaseModel):
    """What we send back for org info."""
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. Document Schemas
# ==========================================

class DocumentVersionResponse(BaseModel):
    id: int
    version_number: int
    file_name: str
    created_at: datetime
    uploaded_by_id: int

    model_config = ConfigDict(from_attributes=True)

class DocumentResponse(BaseModel):
    id: int
    title: str
    status: DocumentStatus
    org_id: int
    owner_id: int
    created_at: datetime
    versions: list[DocumentVersionResponse] = []

    model_config = ConfigDict(from_attributes=True)

class DocumentListResponse(BaseModel):
    total: int
    items: list[DocumentResponse]

class DocumentListResponse(BaseModel):
    total: int
    items: list[DocumentResponse]

class DocumentListResponse(BaseModel):
    total: int
    items: list[DocumentResponse]
