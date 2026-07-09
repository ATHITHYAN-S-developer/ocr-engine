from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any

@dataclass
class OCRResult:
    id: str
    job_id: str
    document_id: str
    raw_text: str
    structured_json: Dict[str, Any]  # Matches structured JSON schema
    confidence: float
    created_at: datetime
