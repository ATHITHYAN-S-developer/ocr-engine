from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.entities.user import User
from src.domain.entities.project import Project
from src.domain.entities.api_key import APIKey
from src.domain.entities.document import Document
from src.domain.entities.upload import Upload
from src.domain.entities.ocr_job import OCRJob
from src.domain.entities.ocr_result import OCRResult
from src.domain.entities.export import Export
from src.domain.entities.audit_log import AuditLog

class IUserRepository(ABC):
    @abstractmethod
    def add(self, user: User) -> None: pass
    
    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[User]: pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]: pass

class IProjectRepository(ABC):
    @abstractmethod
    def add(self, project: Project) -> None: pass
    
    @abstractmethod
    def get_by_id(self, project_id: str) -> Optional[Project]: pass
    
    @abstractmethod
    def list_by_owner(self, owner_id: str) -> List[Project]: pass

class IAPIKeyRepository(ABC):
    @abstractmethod
    def add(self, api_key: APIKey) -> None: pass
    
    @abstractmethod
    def get_by_id(self, key_id: str) -> Optional[APIKey]: pass
    
    @abstractmethod
    def get_by_hash(self, key_hash: str) -> Optional[APIKey]: pass
    
    @abstractmethod
    def list_by_project(self, project_id: str) -> List[APIKey]: pass

class IDocumentRepository(ABC):
    @abstractmethod
    def add(self, document: Document) -> None: pass
    
    @abstractmethod
    def get_by_id(self, document_id: str) -> Optional[Document]: pass
    
    @abstractmethod
    def list_by_project(self, project_id: str) -> List[Document]: pass
    
    @abstractmethod
    def update(self, document: Document) -> None: pass
    
    @abstractmethod
    def delete(self, document_id: str) -> None: pass

class IUploadRepository(ABC):
    @abstractmethod
    def add(self, upload: Upload) -> None: pass
    
    @abstractmethod
    def get_by_id(self, upload_id: str) -> Optional[Upload]: pass
    
    @abstractmethod
    def update(self, upload: Upload) -> None: pass

class IOCRJobRepository(ABC):
    @abstractmethod
    def add(self, job: OCRJob) -> None: pass
    
    @abstractmethod
    def get_by_id(self, job_id: str) -> Optional[OCRJob]: pass
    
    @abstractmethod
    def update(self, job: OCRJob) -> None: pass
    
    @abstractmethod
    def list_by_project(self, project_id: str) -> List[OCRJob]: pass

class IOCRResultRepository(ABC):
    @abstractmethod
    def add(self, result: OCRResult) -> None: pass
    
    @abstractmethod
    def get_by_job_id(self, job_id: str) -> Optional[OCRResult]: pass
    
    @abstractmethod
    def get_by_document_id(self, document_id: str) -> Optional[OCRResult]: pass

class IExportRepository(ABC):
    @abstractmethod
    def add(self, export: Export) -> None: pass
    
    @abstractmethod
    def get_by_id(self, export_id: str) -> Optional[Export]: pass
    
    @abstractmethod
    def get_by_job_and_format(self, job_id: str, format_name: str) -> Optional[Export]: pass

class IAuditLogRepository(ABC):
    @abstractmethod
    def add(self, log: AuditLog) -> None: pass
    
    @abstractmethod
    def list_by_project(self, project_id: str) -> List[AuditLog]: pass
