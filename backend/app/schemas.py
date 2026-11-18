from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from app.models import UserRole, DocumentStatus

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    org_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    org_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class OrganizationResponse(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

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

class ReviewRequest(BaseModel):
    action: str
    comment: str | None = None
