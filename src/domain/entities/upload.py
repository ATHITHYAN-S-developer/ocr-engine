from dataclasses import dataclass
from datetime import datetime

@dataclass
class Upload:
    id: str
    project_id: str
    filename: str
    total_chunks: int
    completed_chunks: int
    upload_id: str
    status: str  # "pending", "completed", "expired"
    created_at: datetime

    def increment_chunks(self) -> None:
        if self.completed_chunks < self.total_chunks:
            self.completed_chunks += 1
        if self.completed_chunks == self.total_chunks:
            self.status = "completed"
