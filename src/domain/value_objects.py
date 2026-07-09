import re
from dataclasses import dataclass
from typing import Optional, Dict, Any
from src.domain.exceptions import InvalidEntityException

@dataclass(frozen=True)
class BoundingBox:
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    def __post_init__(self) -> None:
        if self.x_min < 0 or self.y_min < 0:
            raise InvalidEntityException("BoundingBox coordinates cannot be negative")
        if self.x_max < self.x_min or self.y_max < self.y_min:
            raise InvalidEntityException("Invalid BoundingBox dimensions (max must be >= min)")

@dataclass(frozen=True)
class TextSegment:
    text: str
    confidence: float
    bbox: BoundingBox

@dataclass(frozen=True)
class Email:
    address: str

    def __post_init__(self) -> None:
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, self.address):
            raise InvalidEntityException(f"Invalid email address format: {self.address}")

@dataclass(frozen=True)
class OcrEngineConfig:
    recognition_engine: str = "mock"
    detect_tables: bool = True
    detect_forms: bool = True
    language: str = "en"
    preprocessing_steps: Optional[Dict[str, Any]] = None
