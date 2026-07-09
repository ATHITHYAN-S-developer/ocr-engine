import hashlib
from typing import Generator, Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.infrastructure.database.session import SessionLocal
from src.infrastructure.database.repositories import (
    SQLUserRepository, SQLProjectRepository, SQLAPIKeyRepository,
    SQLDocumentRepository, SQLOCRJobRepository, SQLOCRResultRepository, SQLExportRepository
)
from src.infrastructure.security.service import BCryptPasswordHasher, JWTTokenService
from src.infrastructure.storage.service import get_storage_service
from src.application.use_cases import (
    RegisterUserUseCase, AuthenticateUserUseCase, CreateProjectUseCase,
    CreateAPIKeyUseCase, UploadDocumentUseCase, StartOCRJobUseCase
)
from src.domain.entities.user import User
from src.domain.entities.project import Project

# Security headers
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Injected Use Cases
def get_user_use_cases(db: Session = Depends(get_db)):
    user_repo = SQLUserRepository(db)
    pwd_hasher = BCryptPasswordHasher()
    token_service = JWTTokenService()
    return (
        RegisterUserUseCase(user_repo, pwd_hasher),
        AuthenticateUserUseCase(user_repo, pwd_hasher, token_service)
    )

def get_project_use_cases(db: Session = Depends(get_db)):
    project_repo = SQLProjectRepository(db)
    api_key_repo = SQLAPIKeyRepository(db)
    return (
        CreateProjectUseCase(project_repo),
        CreateAPIKeyUseCase(api_key_repo, project_repo)
    )

def get_document_use_cases(db: Session = Depends(get_db)):
    doc_repo = SQLDocumentRepository(db)
    project_repo = SQLProjectRepository(db)
    storage = get_storage_service()
    return UploadDocumentUseCase(doc_repo, project_repo, storage)

def get_job_use_cases(db: Session = Depends(get_db)):
    job_repo = SQLOCRJobRepository(db)
    doc_repo = SQLDocumentRepository(db)
    return StartOCRJobUseCase(job_repo, doc_repo)

# Authentication resolvers
def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated with JWT token"
        )
    token_service = JWTTokenService()
    user_repo = SQLUserRepository(db)
    
    try:
        payload = token_service.decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
            
        user = user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive or deleted")
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}"
        )

def get_authenticated_project_id(
    db: Session = Depends(get_db),
    api_key: Optional[str] = Depends(api_key_header),
    current_user: Optional[User] = Depends(get_current_user)
) -> str:
    """
    Validates either standard header x-api-key or current user context.
    Returns target project UUID.
    """
    if api_key:
        # Programmatic Access via API Key hash comparison
        hashed = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
        key_repo = SQLAPIKeyRepository(db)
        key_record = key_repo.get_by_hash(hashed)
        if not key_record or not key_record.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or deactivated API Key"
            )
        return key_record.project_id

    if current_user:
        # Interactive access: return owner's first project (or raise error if they haven't created one)
        proj_repo = SQLProjectRepository(db)
        projects = proj_repo.list_by_owner(current_user.id)
        if not projects:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has no projects created. Please create a project first."
            )
        return projects[0].id

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication credentials (JWT token or x-api-key header required)"
    )
