from dataclasses import dataclass
from datetime import datetime

@dataclass
class Project:
    id: str
    name: str
    description: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
