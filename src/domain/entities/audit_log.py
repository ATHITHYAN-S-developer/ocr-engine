from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class AuditLog:
    id: str
    action: str
    resource_id: str
    ip_address: str
    user_agent: str
    details: Dict[str, Any]
    created_at: datetime
    user_id: Optional[str] = None
    api_key_id: Optional[str] = None
