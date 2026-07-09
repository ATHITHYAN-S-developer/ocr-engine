from dataclasses import dataclass
from datetime import datetime

@dataclass
class Document:
    id: str
    project_id: str
    name: str
    file_type: str
    file_path: str
    file_size: int
    status: str  # "uploaded", "processing", "completed", "failed"
    created_at: datetime
    updated_at: datetime

    def update_status(self, new_status: str) -> None:
        self.status = new_status
        self.updated_at = datetime.utcnow()
