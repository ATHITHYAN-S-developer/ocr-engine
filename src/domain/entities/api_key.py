from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class APIKey:
    id: str
    project_id: str
    key_hash: str
    name: str
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None

    def deactivate(self) -> None:
        self.is_active = False

    def use(self) -> None:
        self.last_used_at = datetime.utcnow()
