from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    id: str
    email: str
    hashed_password: str
    role: str  # "admin", "developer", "user"
    is_active: bool
    created_at: datetime
    updated_at: datetime

    def update_password(self, new_hashed_password: str) -> None:
        self.hashed_password = new_hashed_password
        self.updated_at = datetime.utcnow()
