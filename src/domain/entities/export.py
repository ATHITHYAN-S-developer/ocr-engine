from dataclasses import dataclass
from datetime import datetime

@dataclass
class Export:
    id: str
    job_id: str
    format: str  # "TXT", "JSON", "CSV", "DOCX", "PDF", "XML", "MD"
    file_path: str
    created_at: datetime
