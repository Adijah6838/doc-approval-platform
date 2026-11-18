import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.db.db import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    users = relationship("User", back_populates="organization")
    documents = relationship("Document", back_populates="organization")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # 'owner', 'reviewer', 'employee'
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    organization = relationship("Organization", back_populates="users")
    documents = relationship("Document", back_populates="owner")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    status = Column(String, default="Draft", nullable=False)  # Draft, Pending Review, Approved, Rejected
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    organization = relationship("Organization", back_populates="documents")
    owner = relationship("User", back_populates="documents")
