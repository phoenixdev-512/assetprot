from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_ALGORITHM = "HS256"
_ACCESS_TOKEN_EXPIRE_MINUTES = 15
_REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str, org_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "org_id": org_id, "type": "access", "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=_ALGORITHM)


def create_refresh_token(user_id: str, org_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": user_id, "org_id": org_id, "type": "refresh", "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_INVALID", "message": "Token is invalid or expired"},
        )
