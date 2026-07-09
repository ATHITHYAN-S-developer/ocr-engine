from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class OCRJob:
    id: str
    project_id: str
    document_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: float  # 0.0 to 1.0
    current_stage: str  # "PREPROCESSING", "DETECTION", "RECOGNITION", etc.
    engine_config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None

    def update_progress(self, progress: float, stage: str) -> None:
        self.progress = progress
        self.current_stage = stage
        self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        self.status = "completed"
        self.progress = 1.0
        self.current_stage = "COMPLETED"
        self.updated_at = datetime.utcnow()

    def fail(self, error_message: str) -> None:
        self.status = "failed"
        self.error_message = error_message
        self.current_stage = "FAILED"
        self.updated_at = datetime.utcnow()
