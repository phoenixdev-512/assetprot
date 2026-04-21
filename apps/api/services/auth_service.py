from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from models.organization import Organization
from models.user import User
from schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def register(self, req: RegisterRequest) -> TokenResponse:
        existing = await self._db.scalar(select(User).where(User.email == req.email))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "EMAIL_TAKEN", "message": "Email is already registered"},
            )
        org = Organization(name=req.org_name)
        self._db.add(org)
        await self._db.flush()
        user = User(
            org_id=org.id,
            email=req.email,
            hashed_password=hash_password(req.password),
        )
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)
        return TokenResponse(
            access_token=create_access_token(str(user.id), str(user.org_id)),
            refresh_token=create_refresh_token(str(user.id), str(user.org_id)),
        )

    async def login(self, req: LoginRequest) -> TokenResponse:
        user = await self._db.scalar(select(User).where(User.email == req.email))
        _invalid = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"},
        )
        if not user or not user.is_active:
            raise _invalid
        if not verify_password(req.password, user.hashed_password):
            raise _invalid
        return TokenResponse(
            access_token=create_access_token(str(user.id), str(user.org_id)),
            refresh_token=create_refresh_token(str(user.id), str(user.org_id)),
        )

    async def refresh(self, req: RefreshRequest) -> TokenResponse:
        payload = decode_token(req.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "TOKEN_INVALID", "message": "Token is not a refresh token"},
            )
        user = await self._db.get(User, payload["sub"])
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "ACCOUNT_INACTIVE", "message": "Account is inactive"},
            )
        return TokenResponse(
            access_token=create_access_token(str(user.id), str(user.org_id)),
            refresh_token=req.refresh_token,
        )

    async def get_me(self, user_id: str) -> UserResponse:
        user = await self._db.get(User, user_id)
        return UserResponse(
            id=str(user.id),
            org_id=str(user.org_id),
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
        )
