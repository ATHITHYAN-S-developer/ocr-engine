from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class IPasswordHasher(ABC):
    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Hash a plain text password."""
        pass

    @abstractmethod
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        pass

class ITokenService(ABC):
    @abstractmethod
    def create_access_token(self, data: Dict[str, Any], expires_delta_minutes: Optional[int] = None) -> str:
        """Create a JWT access token."""
        pass

    @abstractmethod
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode a JWT token and return payload."""
        pass
