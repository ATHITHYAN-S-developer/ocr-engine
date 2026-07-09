from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# AUTH SCHEMAS
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    role: Optional[str] = "user"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str

class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# PROJECT SCHEMAS
class ProjectCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: Optional[str] = ""

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    owner_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# API KEY SCHEMAS
class APIKeyCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100)

class APIKeyResponse(BaseModel):
    id: str
    project_id: str
    name: str
    key: Optional[str] = None # Plain key value returned only once on creation
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None

# DOCUMENT SCHEMAS
class DocumentUploadInit(BaseModel):
    name: str
    file_type: str  # PDF, PNG, JPEG, etc.
    file_size: int
    project_id: str

class DocumentResponse(BaseModel):
    id: str
    project_id: str
    name: str
    file_type: str
    file_path: str
    file_size: int
    status: str
    created_at: datetime

# UPLOAD SCHEMAS
class ChunkUploadResponse(BaseModel):
    upload_id: str
    chunk_index: int
    completed_chunks: int
    total_chunks: int
    status: str

# JOB SCHEMAS
class JobCreate(BaseModel):
    document_id: str
    engine_config: Optional[Dict[str, Any]] = {}

class JobResponse(BaseModel):
    id: str
    project_id: str
    document_id: str
    status: str
    progress: float
    current_stage: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# RESULT SCHEMAS
class OCRResultResponse(BaseModel):
    id: str
    job_id: str
    document_id: str
    raw_text: str
    structured_json: Dict[str, Any]
    confidence: float
    created_at: datetime

# HEALTH SCHEMAS
class HealthResponse(BaseModel):
    status: str
    database: str
    redis: str
    timestamp: datetime
