import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from passlib.context import CryptContext
from src.application.interfaces.security_interfaces import IPasswordHasher, ITokenService
from src.config import settings
from src.domain.exceptions import UnauthorizedException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class BCryptPasswordHasher(IPasswordHasher):
    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, password: str, hashed_password: str) -> bool:
        try:
            return pwd_context.verify(password, hashed_password)
        except Exception:
            return False

class JWTTokenService(ITokenService):
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_expire = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    def create_access_token(self, data: Dict[str, Any], expires_delta_minutes: Optional[int] = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=expires_delta_minutes or self.access_expire)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def decode_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException("Token has expired")
        except jwt.InvalidTokenError:
            raise UnauthorizedException("Invalid token")
