import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from src.domain.entities.user import User
from src.domain.entities.project import Project
from src.domain.entities.api_key import APIKey
from src.domain.entities.document import Document
from src.domain.entities.upload import Upload
from src.domain.entities.ocr_job import OCRJob
from src.domain.entities.ocr_result import OCRResult
from src.domain.entities.export import Export
from src.domain.entities.audit_log import AuditLog
from src.domain.repository_interfaces import (
    IUserRepository, IProjectRepository, IAPIKeyRepository,
    IDocumentRepository, IUploadRepository, IOCRJobRepository,
    IOCRResultRepository, IExportRepository, IAuditLogRepository
)
from src.infrastructure.database.models import (
    UserDB, ProjectDB, APIKeyDB, DocumentDB, UploadDB,
    OCRJobDB, OCRResultDB, ExportDB, AuditLogDB
)

# MAPPERS
def map_user_to_domain(u: UserDB) -> User:
    return User(
        id=str(u.id), email=u.email, hashed_password=u.hashed_password,
        role=u.role, is_active=u.is_active, created_at=u.created_at, updated_at=u.updated_at
    )

def map_project_to_domain(p: ProjectDB) -> Project:
    return Project(
        id=str(p.id), name=p.name, description=p.description or "",
        owner_id=str(p.owner_id), created_at=p.created_at, updated_at=p.updated_at
    )

def map_api_key_to_domain(k: APIKeyDB) -> APIKey:
    return APIKey(
        id=str(k.id), project_id=str(k.project_id), key_hash=k.key_hash,
        name=k.name, is_active=k.is_active, created_at=k.created_at, last_used_at=k.last_used_at
    )

def map_document_to_domain(d: DocumentDB) -> Document:
    return Document(
        id=str(d.id), project_id=str(d.project_id), name=d.name,
        file_type=d.file_type, file_path=d.file_path, file_size=d.file_size,
        status=d.status, created_at=d.created_at, updated_at=d.updated_at
    )

def map_upload_to_domain(up: UploadDB) -> Upload:
    return Upload(
        id=str(up.id), project_id=str(up.project_id), filename=up.filename,
        total_chunks=up.total_chunks, completed_chunks=up.completed_chunks,
        upload_id=up.upload_id, status=up.status, created_at=up.created_at
    )

def map_ocr_job_to_domain(j: OCRJobDB) -> OCRJob:
    return OCRJob(
        id=str(j.id), project_id=str(j.project_id), document_id=str(j.document_id),
        status=j.status, progress=j.progress, current_stage=j.current_stage,
        engine_config=j.engine_config, created_at=j.created_at, updated_at=j.updated_at,
        error_message=j.error_message
    )

def map_ocr_result_to_domain(r: OCRResultDB) -> OCRResult:
    return OCRResult(
        id=str(r.id), job_id=str(r.job_id), document_id=str(r.document_id),
        raw_text=r.raw_text, structured_json=r.structured_json,
        confidence=r.confidence, created_at=r.created_at
    )

def map_export_to_domain(e: ExportDB) -> Export:
    return Export(
        id=str(e.id), job_id=str(e.job_id), format=e.format,
        file_path=e.file_path, created_at=e.created_at
    )

def map_audit_log_to_domain(a: AuditLogDB) -> AuditLog:
    return AuditLog(
        id=str(a.id), user_id=str(a.user_id) if a.user_id else None,
        api_key_id=str(a.api_key_id) if a.api_key_id else None,
        action=a.action, resource_id=a.resource_id, ip_address=a.ip_address,
        user_agent=a.user_agent, details=a.details, created_at=a.created_at
    )


# REPOSITORIES
class SQLUserRepository(IUserRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, user: User) -> None:
        user_db = UserDB(
            id=uuid.UUID(user.id), email=user.email, hashed_password=user.hashed_password,
            role=user.role, is_active=user.is_active, created_at=user.created_at, updated_at=user.updated_at
        )
        self.session.add(user_db)
        self.session.commit()

    def get_by_id(self, user_id: str) -> Optional[User]:
        db_user = self.session.query(UserDB).filter(UserDB.id == uuid.UUID(user_id)).first()
        return map_user_to_domain(db_user) if db_user else None

    def get_by_email(self, email: str) -> Optional[User]:
        db_user = self.session.query(UserDB).filter(UserDB.email == email).first()
        return map_user_to_domain(db_user) if db_user else None


class SQLProjectRepository(IProjectRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, project: Project) -> None:
        proj_db = ProjectDB(
            id=uuid.UUID(project.id), name=project.name, description=project.description,
            owner_id=uuid.UUID(project.owner_id), created_at=project.created_at, updated_at=project.updated_at
        )
        self.session.add(proj_db)
        self.session.commit()

    def get_by_id(self, project_id: str) -> Optional[Project]:
        proj = self.session.query(ProjectDB).filter(ProjectDB.id == uuid.UUID(project_id)).first()
        return map_project_to_domain(proj) if proj else None

    def list_by_owner(self, owner_id: str) -> List[Project]:
        projs = self.session.query(ProjectDB).filter(ProjectDB.owner_id == uuid.UUID(owner_id)).all()
        return [map_project_to_domain(p) for p in projs]


class SQLAPIKeyRepository(IAPIKeyRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, api_key: APIKey) -> None:
        key_db = APIKeyDB(
            id=uuid.UUID(api_key.id), project_id=uuid.UUID(api_key.project_id),
            key_hash=api_key.key_hash, name=api_key.name, is_active=api_key.is_active,
            created_at=api_key.created_at, last_used_at=api_key.last_used_at
        )
        self.session.add(key_db)
        self.session.commit()

    def get_by_id(self, key_id: str) -> Optional[APIKey]:
        k = self.session.query(APIKeyDB).filter(APIKeyDB.id == uuid.UUID(key_id)).first()
        return map_api_key_to_domain(k) if k else None

    def get_by_hash(self, key_hash: str) -> Optional[APIKey]:
        k = self.session.query(APIKeyDB).filter(APIKeyDB.key_hash == key_hash, APIKeyDB.is_active == True).first()
        if k:
            k.last_used_at = datetime.utcnow()
            self.session.commit()
            return map_api_key_to_domain(k)
        return None

    def list_by_project(self, project_id: str) -> List[APIKey]:
        keys = self.session.query(APIKeyDB).filter(APIKeyDB.project_id == uuid.UUID(project_id)).all()
        return [map_api_key_to_domain(k) for k in keys]


class SQLDocumentRepository(IDocumentRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, document: Document) -> None:
        doc_db = DocumentDB(
            id=uuid.UUID(document.id), project_id=uuid.UUID(document.project_id),
            name=document.name, file_type=document.file_type, file_path=document.file_path,
            file_size=document.file_size, status=document.status,
            created_at=document.created_at, updated_at=document.updated_at
        )
        self.session.add(doc_db)
        self.session.commit()

    def get_by_id(self, document_id: str) -> Optional[Document]:
        d = self.session.query(DocumentDB).filter(DocumentDB.id == uuid.UUID(document_id)).first()
        return map_document_to_domain(d) if d else None

    def list_by_project(self, project_id: str) -> List[Document]:
        docs = self.session.query(DocumentDB).filter(DocumentDB.project_id == uuid.UUID(project_id)).all()
        return [map_document_to_domain(d) for d in docs]

    def update(self, document: Document) -> None:
        d = self.session.query(DocumentDB).filter(DocumentDB.id == uuid.UUID(document.id)).first()
        if d:
            d.status = document.status
            d.updated_at = document.updated_at
            self.session.commit()

    def delete(self, document_id: str) -> None:
        d = self.session.query(DocumentDB).filter(DocumentDB.id == uuid.UUID(document_id)).first()
        if d:
            self.session.delete(d)
            self.session.commit()


class SQLUploadRepository(IUploadRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, upload: Upload) -> None:
        up_db = UploadDB(
            id=uuid.UUID(upload.id), project_id=uuid.UUID(upload.project_id),
            filename=upload.filename, total_chunks=upload.total_chunks,
            completed_chunks=upload.completed_chunks, upload_id=upload.upload_id,
            status=upload.status, created_at=upload.created_at
        )
        self.session.add(up_db)
        self.session.commit()

    def get_by_id(self, upload_id: str) -> Optional[Upload]:
        up = self.session.query(UploadDB).filter(UploadDB.id == uuid.UUID(upload_id)).first()
        return map_upload_to_domain(up) if up else None

    def update(self, upload: Upload) -> None:
        up = self.session.query(UploadDB).filter(UploadDB.id == uuid.UUID(upload.id)).first()
        if up:
            up.completed_chunks = upload.completed_chunks
            up.status = upload.status
            self.session.commit()


class SQLOCRJobRepository(IOCRJobRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, job: OCRJob) -> None:
        job_db = OCRJobDB(
            id=uuid.UUID(job.id), project_id=uuid.UUID(job.project_id),
            document_id=uuid.UUID(job.document_id), status=job.status,
            progress=job.progress, current_stage=job.current_stage,
            engine_config=job.engine_config, error_message=job.error_message,
            created_at=job.created_at, updated_at=job.updated_at
        )
        self.session.add(job_db)
        self.session.commit()

    def get_by_id(self, job_id: str) -> Optional[OCRJob]:
        j = self.session.query(OCRJobDB).filter(OCRJobDB.id == uuid.UUID(job_id)).first()
        return map_ocr_job_to_domain(j) if j else None

    def update(self, job: OCRJob) -> None:
        j = self.session.query(OCRJobDB).filter(OCRJobDB.id == uuid.UUID(job.id)).first()
        if j:
            j.status = job.status
            j.progress = job.progress
            j.current_stage = job.current_stage
            j.error_message = job.error_message
            j.updated_at = job.updated_at
            self.session.commit()

    def list_by_project(self, project_id: str) -> List[OCRJob]:
        jobs = self.session.query(OCRJobDB).filter(OCRJobDB.project_id == uuid.UUID(project_id)).all()
        return [map_ocr_job_to_domain(j) for j in jobs]


class SQLOCRResultRepository(IOCRResultRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, result: OCRResult) -> None:
        res_db = OCRResultDB(
            id=uuid.UUID(result.id), job_id=uuid.UUID(result.job_id),
            document_id=uuid.UUID(result.document_id), raw_text=result.raw_text,
            structured_json=result.structured_json, confidence=result.confidence,
            created_at=result.created_at
        )
        self.session.add(res_db)
        self.session.commit()

    def get_by_job_id(self, job_id: str) -> Optional[OCRResult]:
        r = self.session.query(OCRResultDB).filter(OCRResultDB.job_id == uuid.UUID(job_id)).first()
        return map_ocr_result_to_domain(r) if r else None

    def get_by_document_id(self, document_id: str) -> Optional[OCRResult]:
        r = self.session.query(OCRResultDB).filter(OCRResultDB.document_id == uuid.UUID(document_id)).first()
        return map_ocr_result_to_domain(r) if r else None


class SQLExportRepository(IExportRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, export: Export) -> None:
        exp_db = ExportDB(
            id=uuid.UUID(export.id), job_id=uuid.UUID(export.job_id),
            format=export.format, file_path=export.file_path,
            created_at=export.created_at
        )
        self.session.add(exp_db)
        self.session.commit()

    def get_by_id(self, export_id: str) -> Optional[Export]:
        e = self.session.query(ExportDB).filter(ExportDB.id == uuid.UUID(export_id)).first()
        return map_export_to_domain(e) if e else None

    def get_by_job_and_format(self, job_id: str, format_name: str) -> Optional[Export]:
        e = self.session.query(ExportDB).filter(
            ExportDB.job_id == uuid.UUID(job_id),
            ExportDB.format == format_name.upper()
        ).first()
        return map_export_to_domain(e) if e else None


class SQLAuditLogRepository(IAuditLogRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, log: AuditLog) -> None:
        log_db = AuditLogDB(
            id=uuid.UUID(log.id),
            user_id=uuid.UUID(log.user_id) if log.user_id else None,
            api_key_id=uuid.UUID(log.api_key_id) if log.api_key_id else None,
            action=log.action, resource_id=log.resource_id, ip_address=log.ip_address,
            user_agent=log.user_agent, details=log.details, created_at=log.created_at
        )
        self.session.add(log_db)
        self.session.commit()

    def list_by_project(self, project_id: str) -> List[AuditLog]:
        # Log entries referencing keys in this project
        # In a real environment we can query through project or key associations.
        # Let's filter logs by api_key belonging to the project.
        logs = self.session.query(AuditLogDB).join(
            APIKeyDB, AuditLogDB.api_key_id == APIKeyDB.id, isouter=True
        ).filter(
            APIKeyDB.project_id == uuid.UUID(project_id)
        ).all()
        return [map_audit_log_to_domain(l) for l in logs]
