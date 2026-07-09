from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Float, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.infrastructure.database.session import Base

class UserDB(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="user", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    projects = relationship("ProjectDB", back_populates="owner", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLogDB", back_populates="user")

class ProjectDB(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    owner = relationship("UserDB", back_populates="projects")
    api_keys = relationship("APIKeyDB", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("DocumentDB", back_populates="project", cascade="all, delete-orphan")
    ocr_jobs = relationship("OCRJobDB", back_populates="project", cascade="all, delete-orphan")

class APIKeyDB(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    key_hash = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)

    project = relationship("ProjectDB", back_populates="api_keys")
    audit_logs = relationship("AuditLogDB", back_populates="api_key")

class DocumentDB(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_path = Column(String(1024), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    status = Column(String(50), default="uploaded", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    project = relationship("ProjectDB", back_populates="documents")
    ocr_jobs = relationship("OCRJobDB", back_populates="document", cascade="all, delete-orphan")

class UploadDB(Base):
    __tablename__ = "uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    total_chunks = Column(Integer, nullable=False)
    completed_chunks = Column(Integer, default=0, nullable=False)
    upload_id = Column(String(255), nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class OCRJobDB(Base):
    __tablename__ = "ocr_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    progress = Column(Float, default=0.0, nullable=False)
    current_stage = Column(String(100), default="PENDING", nullable=False)
    error_message = Column(String, nullable=True)
    engine_config = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    project = relationship("ProjectDB", back_populates="ocr_jobs")
    document = relationship("DocumentDB", back_populates="ocr_jobs")
    ocr_result = relationship("OCRResultDB", uselist=False, back_populates="ocr_job", cascade="all, delete-orphan")
    exports = relationship("ExportDB", back_populates="ocr_job", cascade="all, delete-orphan")

class OCRResultDB(Base):
    __tablename__ = "ocr_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("ocr_jobs.id", ondelete="CASCADE"), unique=True, nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    raw_text = Column(String, nullable=False)
    structured_json = Column(JSONB, nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    ocr_job = relationship("OCRJobDB", back_populates="ocr_result")

class ExportDB(Base):
    __tablename__ = "exports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("ocr_jobs.id", ondelete="CASCADE"), nullable=False)
    format = Column(String(50), nullable=False)
    file_path = Column(String(1024), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    ocr_job = relationship("OCRJobDB", back_populates="exports")

class AuditLogDB(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(255), nullable=False)
    resource_id = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(512), nullable=False)
    details = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("UserDB", back_populates="audit_logs")
    api_key = relationship("APIKeyDB", back_populates="audit_logs")
