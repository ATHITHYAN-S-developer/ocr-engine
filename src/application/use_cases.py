import secrets
import hashlib
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from src.domain.entities.user import User
from src.domain.entities.project import Project
from src.domain.entities.api_key import APIKey
from src.domain.entities.document import Document
from src.domain.entities.ocr_job import OCRJob
from src.domain.entities.ocr_result import OCRResult
from src.domain.entities.export import Export
from src.domain.repository_interfaces import (
    IUserRepository, IProjectRepository, IAPIKeyRepository,
    IDocumentRepository, IOCRJobRepository, IOCRResultRepository, IExportRepository
)
from src.application.interfaces.security_interfaces import IPasswordHasher, ITokenService
from src.application.interfaces.storage_interface import IStorageService
from src.domain.exceptions import EntityNotFoundException, InvalidCredentialsException, UnauthorizedException
from src.infrastructure.queue.tasks import process_ocr_job

class RegisterUserUseCase:
    def __init__(self, user_repo: IUserRepository, password_hasher: IPasswordHasher):
        self.user_repo = user_repo
        self.password_hasher = password_hasher

    def execute(self, email: str, password: str, role: str = "user") -> User:
        if self.user_repo.get_by_email(email):
            raise ValueError(f"Email {email} already registered.")
        
        hashed = self.password_hasher.hash_password(password)
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            hashed_password=hashed,
            role=role,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.user_repo.add(user)
        return user

class AuthenticateUserUseCase:
    def __init__(self, user_repo: IUserRepository, password_hasher: IPasswordHasher, token_service: ITokenService):
        self.user_repo = user_repo
        self.password_hasher = password_hasher
        self.token_service = token_service

    def execute(self, email: str, password: str) -> Tuple[str, str]:
        user = self.user_repo.get_by_email(email)
        if not user or not self.password_hasher.verify_password(password, user.hashed_password):
            raise InvalidCredentialsException("Invalid email or password.")
        
        access_token = self.token_service.create_access_token({"sub": user.id, "role": user.role})
        # Generate 7-day refresh token
        refresh_token = self.token_service.create_access_token({"sub": user.id, "type": "refresh"}, expires_delta_minutes=10080)
        return access_token, refresh_token

class CreateProjectUseCase:
    def __init__(self, project_repo: IProjectRepository):
        self.project_repo = project_repo

    def execute(self, name: str, description: str, owner_id: str) -> Project:
        project = Project(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            owner_id=owner_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.project_repo.add(project)
        return project

class CreateAPIKeyUseCase:
    def __init__(self, api_key_repo: IAPIKeyRepository, project_repo: IProjectRepository):
        self.api_key_repo = api_key_repo
        self.project_repo = project_repo

    def execute(self, project_id: str, name: str, user_id: str) -> Tuple[APIKey, str]:
        # Validate project belongs to user
        project = self.project_repo.get_by_id(project_id)
        if not project or project.owner_id != user_id:
            raise UnauthorizedException("Project not owned by user.")
            
        # Secure key generation: 'ocr_sk_' + 32 random bytes (hex)
        raw_key = "ocr_sk_" + secrets.token_hex(32)
        hashed_key = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        
        api_key = APIKey(
            id=str(uuid.uuid4()),
            project_id=project_id,
            key_hash=hashed_key,
            name=name,
            is_active=True,
            created_at=datetime.utcnow()
        )
        self.api_key_repo.add(api_key)
        return api_key, raw_key

class UploadDocumentUseCase:
    def __init__(self, doc_repo: IDocumentRepository, project_repo: IProjectRepository, storage: IStorageService):
        self.doc_repo = doc_repo
        self.project_repo = project_repo
        self.storage = storage

    def execute(self, project_id: str, filename: str, file_type: str, file_data: bytes) -> Document:
        # Validate format
        allowed_types = ["PDF", "DOCX", "PNG", "JPEG", "JPG", "TIFF", "BMP", "WEBP"]
        ext = file_type.upper().strip(".")
        if ext not in allowed_types:
            raise ValueError(f"Unsupported file format: {file_type}. Supported: {allowed_types}")

        # Construct safe upload destination
        doc_id = str(uuid.uuid4())
        dest_path = f"projects/{project_id}/documents/{doc_id}/{filename}"
        
        # Save to S3 or local storage
        self.storage.upload_file(file_data, dest_path)
        
        # Save Document entity to DB
        document = Document(
            id=doc_id,
            project_id=project_id,
            name=filename,
            file_type=ext,
            file_path=dest_path,
            file_size=len(file_data),
            status="uploaded",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.doc_repo.add(document)
        return document

class StartOCRJobUseCase:
    def __init__(self, job_repo: IOCRJobRepository, doc_repo: IDocumentRepository):
        self.job_repo = job_repo
        self.doc_repo = doc_repo

    def execute(self, project_id: str, document_id: str, engine_config: Dict[str, Any]) -> OCRJob:
        document = self.doc_repo.get_by_id(document_id)
        if not document or document.project_id != project_id:
            raise EntityNotFoundException("Document", document_id)
            
        job_id = str(uuid.uuid4())
        job = OCRJob(
            id=job_id,
            project_id=project_id,
            document_id=document_id,
            status="pending",
            progress=0.0,
            current_stage="PENDING",
            engine_config=engine_config,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.job_repo.add(job)
        
        # Trigger async worker queue process
        process_ocr_job.delay(job_id)
        return job
