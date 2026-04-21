# GUARDIAN Phase 2: Backend Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire up JWT auth, org-scoped dependency injection, base Pydantic schemas, rate limiting middleware, and skeleton routers for assets/violations/scan-runs — giving every future phase a complete HTTP layer to build on.

**Architecture:** Six-layer addition on top of Phase 1's ORM foundation: schemas → security utilities → dependency injection → middleware → repositories → routers. Each layer tested independently before the next is built. A new `users` table is added (Alembic migration 0002) since JWT auth requires user records. All routers mount under `/api/v1` and return the standard envelope `{"success": bool, "data": ..., "meta": {...}}`.

**Tech Stack:** FastAPI 0.115, python-jose 3.3 (JWT), passlib+bcrypt (passwords), redis-py 5.1 (rate limiter), SQLAlchemy 2.0 async, Pydantic v2, Alembic

---

## File Map

```
apps/api/
├── requirements.txt                    ← add python-jose, passlib
├── main.py                             ← include routers, rate limit middleware, extended health
├── config/
│   ├── __init__.py                     ← new
│   ├── redis_keys.py                   ← new — Redis key constants
│   └── rate_limits.py                  ← new — rate limit constants
├── core/
│   ├── config.py                       ← add jwt_algorithm, access_token_expire_minutes
│   ├── security.py                     ← new — create_access_token, decode_token, hash/verify password
│   └── dependencies.py                 ← new — get_db, get_current_user, get_current_org
├── middleware/
│   ├── __init__.py                     ← new
│   └── rate_limit.py                   ← new — Redis token bucket middleware
├── models/
│   ├── __init__.py                     ← add User
│   └── user.py                         ← new — User ORM model
├── schemas/
│   ├── __init__.py                     ← new
│   ├── base.py                         ← new — APIResponse[T], PaginatedResponse[T], ErrorDetail
│   ├── auth.py                         ← new — LoginRequest, TokenResponse
│   ├── asset.py                        ← new — AssetCreate, AssetResponse
│   ├── violation.py                    ← new — ViolationResponse, ViolationVerdict
│   └── scan_run.py                     ← new — ScanRunResponse
├── db/
│   ├── repositories/
│   │   ├── __init__.py                 ← new
│   │   ├── user_repo.py                ← new — get_by_email, create
│   │   ├── asset_repo.py               ← new — list_by_org, get_by_id
│   │   ├── violation_repo.py           ← new — list_by_org
│   │   └── scan_run_repo.py            ← new — list_by_asset
│   └── migrations/versions/
│       └── 0002_add_users.py           ← new
├── services/
│   ├── __init__.py                     ← new
│   ├── auth_service.py                 ← new — authenticate_user, create_tokens
│   ├── asset_service.py                ← new — list_assets, get_asset
│   ├── violation_service.py            ← new — list_violations
│   └── scan_run_service.py             ← new — list_scan_runs
├── routers/
│   ├── __init__.py                     ← new
│   ├── auth.py                         ← new — POST /api/v1/auth/login, /refresh
│   ├── assets.py                       ← new — GET /api/v1/assets, /assets/{id}
│   ├── violations.py                   ← new — GET /api/v1/violations
│   ├── scan_runs.py                    ← new — GET /api/v1/scan-runs
│   └── tasks.py                        ← new — GET /api/v1/tasks/{task_id}
└── tests/
    ├── conftest.py                     ← extend with auth fixtures (test user, token)
    ├── test_schemas.py                 ← new
    ├── test_security.py                ← new
    ├── test_auth_router.py             ← new
    ├── test_assets_router.py           ← new
    ├── test_violations_router.py       ← new
    └── test_health.py                  ← extend — verify DB+Redis checks
```

---

## Task 1: User ORM model + migration 0002

**Files:**
- Create: `apps/api/models/user.py`
- Modify: `apps/api/models/__init__.py`
- Create: `apps/api/db/migrations/versions/0002_add_users.py`
- Modify: `apps/api/tests/test_db_models.py`

- [ ] **Step 1: Write the failing test**

Append to `apps/api/tests/test_db_models.py`:

```python
from models.user import User

@pytest.mark.asyncio
async def test_create_user(db_session):
    org = Organization(name="Auth Org", plan="pro")
    db_session.add(org)
    await db_session.flush()
    user = User(
        org_id=org.id,
        email="admin@sportsco.com",
        hashed_password="$2b$12$placeholder",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    assert user.id is not None
    assert user.is_active is True
```

- [ ] **Step 2: Run — expect ImportError**

```bash
cd apps/api && pytest tests/test_db_models.py::test_create_user -v
```

Expected: `ModuleNotFoundError: No module named 'models.user'`

- [ ] **Step 3: Write models/user.py**

```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, func, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    organization: Mapped["Organization"] = relationship("Organization")
```

Save to: `apps/api/models/user.py`

- [ ] **Step 4: Update models/__init__.py**

```python
from models.organization import Organization
from models.asset import Asset
from models.asset_fingerprint import AssetFingerprint
from models.violation import Violation
from models.dmca_notice import DMCANotice
from models.task import Task
from models.scan_run import ScanRun
from models.user import User

__all__ = ["Organization", "Asset", "AssetFingerprint", "Violation", "DMCANotice", "Task", "ScanRun", "User"]
```

- [ ] **Step 5: Run — expect PASS**

```bash
cd apps/api && pytest tests/test_db_models.py::test_create_user -v
```

Expected: `PASSED` (conftest creates tables from Base.metadata, which now includes users)

- [ ] **Step 6: Write migration 0002**

```python
"""add users table

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-20
"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
```

Save to: `apps/api/db/migrations/versions/0002_add_users.py`

- [ ] **Step 7: Apply migration**

```bash
cd apps/api && alembic upgrade head
```

Expected: `Running upgrade 0001 -> 0002, add users table`

- [ ] **Step 8: Run full test suite — expect 11 PASS**

```bash
cd apps/api && pytest tests/ -v
```

Expected: all 11 tests PASS

- [ ] **Step 9: Commit**

```bash
git add apps/api/models/user.py apps/api/models/__init__.py apps/api/db/migrations/versions/0002_add_users.py apps/api/tests/test_db_models.py
git commit -m "feat: add User ORM model and migration 0002"
```

---

## Task 2: Redis key constants + rate limit config

**Files:**
- Create: `apps/api/config/__init__.py`
- Create: `apps/api/config/redis_keys.py`
- Create: `apps/api/config/rate_limits.py`

- [ ] **Step 1: Write config/__init__.py**

```python
```

(empty — marks it as a package)

Save to: `apps/api/config/__init__.py`

- [ ] **Step 2: Write config/redis_keys.py**

```python
def task_key(task_id: str) -> str:
    return f"guardian:task:{task_id}"

def url_cache_key(url_hash: str) -> str:
    return f"guardian:cache:url:{url_hash}"

def rate_limit_key(org_id: str, endpoint: str) -> str:
    return f"guardian:rl:{org_id}:{endpoint}"

def session_key(session_id: str) -> str:
    return f"guardian:session:{session_id}"
```

Save to: `apps/api/config/redis_keys.py`

- [ ] **Step 3: Write config/rate_limits.py**

```python
# Requests per window per org per endpoint
RATE_LIMIT_REQUESTS: int = 100
RATE_LIMIT_WINDOW_SECONDS: int = 60

# Crawler: requests per domain per minute (prevents GUARDIAN becoming a DDoS tool)
CRAWLER_RATE_LIMIT_REQUESTS: int = 10
CRAWLER_RATE_LIMIT_WINDOW_SECONDS: int = 60
```

Save to: `apps/api/config/rate_limits.py`

- [ ] **Step 4: Commit**

```bash
git add apps/api/config/
git commit -m "feat: add Redis key helpers and rate limit constants"
```

---

## Task 3: Base Pydantic schemas

**Files:**
- Create: `apps/api/schemas/__init__.py`
- Create: `apps/api/schemas/base.py`
- Create: `apps/api/schemas/auth.py`
- Create: `apps/api/schemas/asset.py`
- Create: `apps/api/schemas/violation.py`
- Create: `apps/api/schemas/scan_run.py`
- Create: `apps/api/tests/test_schemas.py`

- [ ] **Step 1: Write failing tests**

```python
# apps/api/tests/test_schemas.py
import pytest
from datetime import datetime, timezone
from uuid import uuid4
from schemas.base import APIResponse, PaginatedResponse
from schemas.auth import LoginRequest, TokenResponse
from schemas.asset import AssetResponse
from schemas.violation import ViolationResponse


def test_api_response_success():
    r = APIResponse[dict](success=True, data={"foo": "bar"})
    assert r.success is True
    assert r.data == {"foo": "bar"}
    assert r.meta == {}


def test_api_response_error():
    r = APIResponse[None](success=False, data=None, error={"code": "NOT_FOUND", "message": "x"})
    assert r.success is False
    assert r.error["code"] == "NOT_FOUND"


def test_paginated_response():
    r = PaginatedResponse[dict](
        success=True,
        data=[{"id": "1"}],
        meta={"total": 1, "page": 1, "page_size": 20},
    )
    assert r.meta["total"] == 1


def test_login_request_validation():
    req = LoginRequest(email="user@example.com", password="secret")
    assert req.email == "user@example.com"


def test_token_response():
    t = TokenResponse(access_token="abc.def.ghi", token_type="bearer")
    assert t.token_type == "bearer"


def test_asset_response_id_is_str():
    asset_id = uuid4()
    r = AssetResponse(
        id=asset_id,
        org_id=uuid4(),
        title="Match Clip",
        content_type="video",
        status="pending",
        territories=["US"],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    assert isinstance(r.model_dump()["id"], str)
```

Save to: `apps/api/tests/test_schemas.py`

- [ ] **Step 2: Run — expect ImportError**

```bash
cd apps/api && pytest tests/test_schemas.py -v
```

Expected: `ModuleNotFoundError: No module named 'schemas'`

- [ ] **Step 3: Write schemas/__init__.py**

```python
```

(empty)

Save to: `apps/api/schemas/__init__.py`

- [ ] **Step 4: Write schemas/base.py**

```python
from typing import Generic, TypeVar, Any
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: T
    meta: dict[str, Any] = {}
    error: dict[str, Any] | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool
    data: list[T]
    meta: dict[str, Any] = {}
```

Save to: `apps/api/schemas/base.py`

- [ ] **Step 5: Write schemas/auth.py**

```python
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
```

Save to: `apps/api/schemas/auth.py`

- [ ] **Step 6: Write schemas/asset.py**

```python
import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, field_serializer


class AssetCreate(BaseModel):
    title: str
    content_type: str  # video | image | audio
    territories: list[str] = []
    rights_metadata: dict[str, Any] | None = None


class AssetResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    title: str
    content_type: str
    status: str
    territories: list[str]
    rights_metadata: dict[str, Any] | None = None
    blockchain_tx_hash: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id", "org_id")
    def serialize_uuid(self, v: uuid.UUID) -> str:
        return str(v)
```

Save to: `apps/api/schemas/asset.py`

- [ ] **Step 7: Write schemas/violation.py**

```python
import uuid
from datetime import datetime
from typing import Literal, Any
from pydantic import BaseModel, field_serializer


class ViolationVerdict(BaseModel):
    infringement_type: Literal["exact_copy", "re_encoded", "partial_clip", "audio_only", "false_positive"]
    confidence: float
    transformation_type: list[str]
    platform: str
    estimated_reach: int | None = None
    rights_territory_violation: bool
    reasoning: str


class ViolationResponse(BaseModel):
    id: uuid.UUID
    asset_id: uuid.UUID
    discovered_url: str
    platform: str
    status: str
    confidence: float
    infringement_type: str | None = None
    transformation_types: list[str]
    estimated_reach: int | None = None
    triage_verdict: dict[str, Any] | None = None
    detected_at: datetime
    resolved_at: datetime | None = None

    model_config = {"from_attributes": True}

    @field_serializer("id", "asset_id")
    def serialize_uuid(self, v: uuid.UUID) -> str:
        return str(v)
```

Save to: `apps/api/schemas/violation.py`

- [ ] **Step 8: Write schemas/scan_run.py**

```python
import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, field_serializer


class ScanRunResponse(BaseModel):
    id: uuid.UUID
    asset_id: uuid.UUID
    status: str
    violations_found: int
    errors: dict[str, Any] | None = None
    run_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id", "asset_id")
    def serialize_uuid(self, v: uuid.UUID) -> str:
        return str(v)
```

Save to: `apps/api/schemas/scan_run.py`

- [ ] **Step 9: Install email-validator (needed by EmailStr)**

```bash
cd apps/api && pip install "pydantic[email]"
```

Also add to requirements.txt — replace the pydantic line:

```
pydantic[email]==2.9.2
```

- [ ] **Step 10: Run — expect all schema tests PASS**

```bash
cd apps/api && pytest tests/test_schemas.py -v
```

Expected: 6 tests PASSED

- [ ] **Step 11: Commit**

```bash
git add apps/api/schemas/ apps/api/tests/test_schemas.py apps/api/requirements.txt
git commit -m "feat: add base Pydantic schemas — APIResponse, auth, asset, violation, scan_run"
```

---

## Task 4: JWT security utilities

**Files:**
- Create: `apps/api/core/security.py`
- Modify: `apps/api/core/config.py`
- Modify: `apps/api/requirements.txt`
- Create: `apps/api/tests/test_security.py`

- [ ] **Step 1: Add dependencies to requirements.txt**

Append to `apps/api/requirements.txt`:

```
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

Install:

```bash
cd apps/api && pip install "python-jose[cryptography]==3.3.0" "passlib[bcrypt]==1.7.4"
```

- [ ] **Step 2: Write failing tests**

```python
# apps/api/tests/test_security.py
import pytest
from datetime import timedelta
from core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify():
    hashed = hash_password("mysecret")
    assert hashed != "mysecret"
    assert verify_password("mysecret", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_access_token():
    token = create_access_token({"sub": "user-uuid-123", "org_id": "org-uuid-456"})
    payload = decode_access_token(token)
    assert payload["sub"] == "user-uuid-123"
    assert payload["org_id"] == "org-uuid-456"


def test_expired_token_returns_none():
    token = create_access_token({"sub": "u"}, expires_delta=timedelta(seconds=-1))
    result = decode_access_token(token)
    assert result is None


def test_invalid_token_returns_none():
    result = decode_access_token("not.a.token")
    assert result is None
```

Save to: `apps/api/tests/test_security.py`

- [ ] **Step 3: Run — expect ImportError**

```bash
cd apps/api && pytest tests/test_security.py -v
```

Expected: `ModuleNotFoundError: No module named 'core.security'`

- [ ] **Step 4: Extend core/config.py**

Replace the full content of `apps/api/core/config.py`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    redis_url: str
    qdrant_url: str
    qdrant_api_key: str
    anthropic_api_key: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    celery_broker_url: str
    celery_result_backend: str
    app_env: str = "development"


settings = Settings()
```

- [ ] **Step 5: Write core/security.py**

```python
from datetime import datetime, timedelta, timezone
from typing import Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from core.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {**data, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
```

Save to: `apps/api/core/security.py`

- [ ] **Step 6: Run — expect all PASS**

```bash
cd apps/api && pytest tests/test_security.py -v
```

Expected: 4 tests PASSED

- [ ] **Step 7: Commit**

```bash
git add apps/api/core/security.py apps/api/core/config.py apps/api/requirements.txt apps/api/tests/test_security.py
git commit -m "feat: add JWT security utilities and password hashing"
```

---

## Task 5: Repositories + dependency injection

**Files:**
- Create: `apps/api/db/repositories/__init__.py`
- Create: `apps/api/db/repositories/user_repo.py`
- Create: `apps/api/db/repositories/asset_repo.py`
- Create: `apps/api/db/repositories/violation_repo.py`
- Create: `apps/api/db/repositories/scan_run_repo.py`
- Create: `apps/api/core/dependencies.py`

- [ ] **Step 1: Write db/repositories/__init__.py**

```python
```

(empty)

Save to: `apps/api/db/repositories/__init__.py`

- [ ] **Step 2: Write db/repositories/user_repo.py**

```python
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, org_id: uuid.UUID, email: str, hashed_password: str) -> User:
    user = User(org_id=org_id, email=email, hashed_password=hashed_password)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user
```

Save to: `apps/api/db/repositories/user_repo.py`

- [ ] **Step 3: Write db/repositories/asset_repo.py**

```python
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.asset import Asset


async def list_by_org(
    db: AsyncSession, org_id: uuid.UUID, offset: int = 0, limit: int = 20
) -> tuple[list[Asset], int]:
    from sqlalchemy import func
    count_q = await db.execute(select(func.count()).select_from(Asset).where(Asset.org_id == org_id))
    total = count_q.scalar_one()
    q = await db.execute(
        select(Asset).where(Asset.org_id == org_id).offset(offset).limit(limit)
    )
    return q.scalars().all(), total


async def get_by_id(db: AsyncSession, asset_id: uuid.UUID, org_id: uuid.UUID) -> Asset | None:
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.org_id == org_id)
    )
    return result.scalar_one_or_none()
```

Save to: `apps/api/db/repositories/asset_repo.py`

- [ ] **Step 4: Write db/repositories/violation_repo.py**

```python
import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models.violation import Violation
from models.asset import Asset


async def list_by_org(
    db: AsyncSession, org_id: uuid.UUID, offset: int = 0, limit: int = 20
) -> tuple[list[Violation], int]:
    base = select(Violation).join(Asset, Violation.asset_id == Asset.id).where(Asset.org_id == org_id)
    count_q = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_q.scalar_one()
    q = await db.execute(base.offset(offset).limit(limit))
    return q.scalars().all(), total
```

Save to: `apps/api/db/repositories/violation_repo.py`

- [ ] **Step 5: Write db/repositories/scan_run_repo.py**

```python
import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models.scan_run import ScanRun
from models.asset import Asset


async def list_by_org(
    db: AsyncSession, org_id: uuid.UUID, offset: int = 0, limit: int = 20
) -> tuple[list[ScanRun], int]:
    base = select(ScanRun).join(Asset, ScanRun.asset_id == Asset.id).where(Asset.org_id == org_id)
    count_q = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_q.scalar_one()
    q = await db.execute(base.offset(offset).limit(limit))
    return q.scalars().all(), total
```

Save to: `apps/api/db/repositories/scan_run_repo.py`

- [ ] **Step 6: Write core/dependencies.py**

```python
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_async_session
from core.security import decode_access_token
import db.repositories.user_repo as user_repo
from models.user import User

_bearer = HTTPBearer()


async def get_db() -> AsyncSession:
    async for session in get_async_session():
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = await user_repo.get_by_id(db, uuid.UUID(user_id_str))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_current_org_id(current_user: User = Depends(get_current_user)) -> uuid.UUID:
    return current_user.org_id
```

Save to: `apps/api/core/dependencies.py`

- [ ] **Step 7: Commit**

```bash
git add apps/api/db/repositories/ apps/api/core/dependencies.py
git commit -m "feat: add repositories and dependency injection (get_db, get_current_user, get_current_org_id)"
```

---

## Task 6: Rate limiting middleware

**Files:**
- Create: `apps/api/middleware/__init__.py`
- Create: `apps/api/middleware/rate_limit.py`
- Create: `apps/api/tests/test_rate_limit.py`

- [ ] **Step 1: Write failing tests**

```python
# apps/api/tests/test_rate_limit.py
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.requests import Request
from middleware.rate_limit import RateLimitMiddleware


def _make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, requests_per_window=3, window_seconds=60)

    @app.get("/test")
    async def test_route(request: Request):
        return JSONResponse({"ok": True})

    return app


@pytest.mark.asyncio
async def test_rate_limit_allows_within_limit():
    app = _make_app()
    with patch("middleware.rate_limit.redis.Redis") as mock_redis_cls:
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock()
        mock_redis_cls.from_url.return_value = mock_redis
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get("/test", headers={"X-Org-Id": "org-123"})
        assert r.status_code == 200


@pytest.mark.asyncio
async def test_rate_limit_blocks_over_limit():
    app = _make_app()
    with patch("middleware.rate_limit.redis.Redis") as mock_redis_cls:
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=4)  # over limit of 3
        mock_redis.expire = AsyncMock()
        mock_redis_cls.from_url.return_value = mock_redis
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get("/test", headers={"X-Org-Id": "org-123"})
        assert r.status_code == 429
```

Save to: `apps/api/tests/test_rate_limit.py`

- [ ] **Step 2: Run — expect ImportError**

```bash
cd apps/api && pytest tests/test_rate_limit.py -v
```

Expected: `ModuleNotFoundError: No module named 'middleware'`

- [ ] **Step 3: Write middleware/__init__.py**

```python
```

(empty)

Save to: `apps/api/middleware/__init__.py`

- [ ] **Step 4: Write middleware/rate_limit.py**

```python
import redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from config.redis_keys import rate_limit_key
from core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_window: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self._redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)

    async def dispatch(self, request: Request, call_next):
        org_id = request.headers.get("X-Org-Id", "anonymous")
        endpoint = request.url.path
        key = rate_limit_key(org_id, endpoint)
        count = self._redis.incr(key)
        if count == 1:
            self._redis.expire(key, self.window_seconds)
        if count > self.requests_per_window:
            return JSONResponse(
                {"success": False, "error": {"code": "RATE_LIMITED", "message": "Too many requests"}, "meta": {}},
                status_code=429,
            )
        return await call_next(request)
```

Save to: `apps/api/middleware/rate_limit.py`

- [ ] **Step 5: Run — expect PASS**

```bash
cd apps/api && pytest tests/test_rate_limit.py -v
```

Expected: 2 tests PASSED

- [ ] **Step 6: Commit**

```bash
git add apps/api/middleware/ apps/api/tests/test_rate_limit.py
git commit -m "feat: add Redis token-bucket rate limiting middleware"
```

---

## Task 7: Services + Auth router

**Files:**
- Create: `apps/api/services/__init__.py`
- Create: `apps/api/services/auth_service.py`
- Create: `apps/api/services/asset_service.py`
- Create: `apps/api/services/violation_service.py`
- Create: `apps/api/services/scan_run_service.py`
- Create: `apps/api/routers/__init__.py`
- Create: `apps/api/routers/auth.py`
- Create: `apps/api/tests/test_auth_router.py`

- [ ] **Step 1: Write failing tests**

```python
# apps/api/tests/test_auth_router.py
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_login_returns_token(db_session):
    from models.organization import Organization
    from models.user import User
    from core.security import hash_password

    org = Organization(name="Test Org", plan="pro")
    db_session.add(org)
    await db_session.flush()
    user = User(org_id=org.id, email="test@guardian.io", hashed_password=hash_password("password123"))
    db_session.add(user)
    await db_session.commit()

    with patch("routers.auth.get_db", return_value=_yield(db_session)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post("/api/v1/auth/login", json={"email": "test@guardian.io", "password": "password123"})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert "access_token" in body["data"]


@pytest.mark.asyncio
async def test_login_bad_credentials(db_session):
    with patch("routers.auth.get_db", return_value=_yield(db_session)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post("/api/v1/auth/login", json={"email": "nobody@x.com", "password": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_without_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/assets")
    assert r.status_code == 403  # HTTPBearer returns 403 when no credentials provided


async def _yield(value):
    yield value
```

Save to: `apps/api/tests/test_auth_router.py`

- [ ] **Step 2: Run — expect import errors (routers not yet created)**

```bash
cd apps/api && pytest tests/test_auth_router.py::test_protected_route_without_token -v
```

Expected: `ImportError` or route not found (404) — either is acceptable at this stage

- [ ] **Step 3: Write services/__init__.py**

```python
```

(empty). Save to: `apps/api/services/__init__.py`

- [ ] **Step 4: Write services/auth_service.py**

```python
from sqlalchemy.ext.asyncio import AsyncSession
from core.security import verify_password, create_access_token, hash_password
import db.repositories.user_repo as user_repo
from models.user import User


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await user_repo.get_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user


def build_token_payload(user: User) -> dict:
    return create_access_token({"sub": str(user.id), "org_id": str(user.org_id)})
```

Save to: `apps/api/services/auth_service.py`

- [ ] **Step 5: Write services/asset_service.py**

```python
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
import db.repositories.asset_repo as asset_repo
from models.asset import Asset


async def list_assets(db: AsyncSession, org_id: uuid.UUID, offset: int, limit: int):
    return await asset_repo.list_by_org(db, org_id, offset, limit)


async def get_asset(db: AsyncSession, asset_id: uuid.UUID, org_id: uuid.UUID) -> Asset | None:
    return await asset_repo.get_by_id(db, asset_id, org_id)
```

Save to: `apps/api/services/asset_service.py`

- [ ] **Step 6: Write services/violation_service.py**

```python
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
import db.repositories.violation_repo as violation_repo


async def list_violations(db: AsyncSession, org_id: uuid.UUID, offset: int, limit: int):
    return await violation_repo.list_by_org(db, org_id, offset, limit)
```

Save to: `apps/api/services/violation_service.py`

- [ ] **Step 7: Write services/scan_run_service.py**

```python
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
import db.repositories.scan_run_repo as scan_run_repo


async def list_scan_runs(db: AsyncSession, org_id: uuid.UUID, offset: int, limit: int):
    return await scan_run_repo.list_by_org(db, org_id, offset, limit)
```

Save to: `apps/api/services/scan_run_service.py`

- [ ] **Step 8: Write routers/__init__.py**

```python
```

(empty). Save to: `apps/api/routers/__init__.py`

- [ ] **Step 9: Write routers/auth.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.auth import LoginRequest, TokenResponse
from schemas.base import APIResponse
from core.dependencies import get_db
from services.auth_service import authenticate_user, build_token_payload

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=APIResponse[TokenResponse])
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, body.email, body.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = build_token_payload(user)
    return APIResponse(success=True, data=TokenResponse(access_token=token))
```

Save to: `apps/api/routers/auth.py`

- [ ] **Step 10: Commit**

```bash
git add apps/api/services/ apps/api/routers/__init__.py apps/api/routers/auth.py apps/api/tests/test_auth_router.py
git commit -m "feat: add auth service and login router"
```

---

## Task 8: Assets, Violations, ScanRuns, Tasks routers

**Files:**
- Create: `apps/api/routers/assets.py`
- Create: `apps/api/routers/violations.py`
- Create: `apps/api/routers/scan_runs.py`
- Create: `apps/api/routers/tasks.py`
- Create: `apps/api/tests/test_assets_router.py`

- [ ] **Step 1: Write failing asset router test**

```python
# apps/api/tests/test_assets_router.py
import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from core.security import create_access_token
import uuid


def _make_token(user_id: str, org_id: str) -> str:
    return create_access_token({"sub": user_id, "org_id": org_id})


@pytest.mark.asyncio
async def test_list_assets_returns_empty_for_new_org(db_session):
    org_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    token = _make_token(user_id, org_id)

    async def _fake_db():
        yield db_session

    from core import dependencies
    app.dependency_overrides[dependencies.get_db] = _fake_db

    # Also need a user in DB for get_current_user
    from models.organization import Organization
    from models.user import User
    from core.security import hash_password
    import uuid as _uuid

    real_org_id = _uuid.UUID(org_id)
    real_user_id = _uuid.UUID(user_id)
    org = Organization(id=real_org_id, name="Org", plan="free")
    db_session.add(org)
    await db_session.flush()
    user = User(id=real_user_id, org_id=real_org_id, email="u@test.com", hashed_password=hash_password("x"))
    db_session.add(user)
    await db_session.commit()

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get("/api/v1/assets", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["data"] == []
        assert body["meta"]["total"] == 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_asset_not_found(db_session):
    org_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    token = _make_token(user_id, org_id)

    from models.organization import Organization
    from models.user import User
    from core.security import hash_password
    import uuid as _uuid

    real_org_id = _uuid.UUID(org_id)
    real_user_id = _uuid.UUID(user_id)
    org = Organization(id=real_org_id, name="Org2", plan="free")
    db_session.add(org)
    await db_session.flush()
    user = User(id=real_user_id, org_id=real_org_id, email="u2@test.com", hashed_password=hash_password("x"))
    db_session.add(user)
    await db_session.commit()

    async def _fake_db():
        yield db_session

    from core import dependencies
    app.dependency_overrides[dependencies.get_db] = _fake_db
    try:
        random_id = str(uuid.uuid4())
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get(f"/api/v1/assets/{random_id}", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()
```

Save to: `apps/api/tests/test_assets_router.py`

- [ ] **Step 2: Write routers/assets.py**

```python
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.asset import AssetResponse
from schemas.base import APIResponse, PaginatedResponse
from core.dependencies import get_db, get_current_org_id
from services.asset_service import list_assets, get_asset

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])


@router.get("", response_model=PaginatedResponse[AssetResponse])
async def list_assets_route(
    offset: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    assets, total = await list_assets(db, org_id, offset, limit)
    return PaginatedResponse(
        success=True,
        data=[AssetResponse.model_validate(a) for a in assets],
        meta={"total": total, "offset": offset, "limit": limit},
    )


@router.get("/{asset_id}", response_model=APIResponse[AssetResponse])
async def get_asset_route(
    asset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    asset = await get_asset(db, asset_id, org_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return APIResponse(success=True, data=AssetResponse.model_validate(asset))
```

Save to: `apps/api/routers/assets.py`

- [ ] **Step 3: Write routers/violations.py**

```python
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.violation import ViolationResponse
from schemas.base import PaginatedResponse
from core.dependencies import get_db, get_current_org_id
from services.violation_service import list_violations

router = APIRouter(prefix="/api/v1/violations", tags=["violations"])


@router.get("", response_model=PaginatedResponse[ViolationResponse])
async def list_violations_route(
    offset: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    violations, total = await list_violations(db, org_id, offset, limit)
    return PaginatedResponse(
        success=True,
        data=[ViolationResponse.model_validate(v) for v in violations],
        meta={"total": total, "offset": offset, "limit": limit},
    )
```

Save to: `apps/api/routers/violations.py`

- [ ] **Step 4: Write routers/scan_runs.py**

```python
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.scan_run import ScanRunResponse
from schemas.base import PaginatedResponse
from core.dependencies import get_db, get_current_org_id
from services.scan_run_service import list_scan_runs

router = APIRouter(prefix="/api/v1/scan-runs", tags=["scan-runs"])


@router.get("", response_model=PaginatedResponse[ScanRunResponse])
async def list_scan_runs_route(
    offset: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    runs, total = await list_scan_runs(db, org_id, offset, limit)
    return PaginatedResponse(
        success=True,
        data=[ScanRunResponse.model_validate(r) for r in runs],
        meta={"total": total, "offset": offset, "limit": limit},
    )
```

Save to: `apps/api/routers/scan_runs.py`

- [ ] **Step 5: Write routers/tasks.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from schemas.base import APIResponse
from core.dependencies import get_db, get_current_user
from models.task import Task
from models.user import User

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.get("/{task_id}", response_model=APIResponse[dict])
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return APIResponse(
        success=True,
        data={"id": task.id, "type": task.type, "status": task.status, "result": task.result},
    )
```

Save to: `apps/api/routers/tasks.py`

- [ ] **Step 6: Run asset router tests — expect PASS**

```bash
cd apps/api && pytest tests/test_assets_router.py -v
```

Expected: 2 tests PASSED (after main.py is updated in next task)

Note: These tests will fail until main.py includes the routers — that happens in Task 9. Run the tests after Task 9.

- [ ] **Step 7: Commit**

```bash
git add apps/api/routers/assets.py apps/api/routers/violations.py apps/api/routers/scan_runs.py apps/api/routers/tasks.py apps/api/tests/test_assets_router.py
git commit -m "feat: add assets, violations, scan-runs, and tasks routers"
```

---

## Task 9: Wire everything into main.py + extended health

**Files:**
- Modify: `apps/api/main.py`
- Modify: `apps/api/tests/test_health.py`

- [ ] **Step 1: Update test_health.py with extended checks**

Replace full content of `apps/api/tests/test_health.py`:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_health_returns_ok():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "ok"
    assert "db" in data["data"]
    assert "redis" in data["data"]


@pytest.mark.asyncio
async def test_api_v1_prefix_exists():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/assets")
    assert r.status_code in (401, 403)  # protected — not 404
```

- [ ] **Step 2: Run — expect test_api_v1_prefix_exists to fail (404 before routers mounted)**

```bash
cd apps/api && pytest tests/test_health.py::test_api_v1_prefix_exists -v
```

Expected: FAIL (404)

- [ ] **Step 3: Rewrite main.py**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import redis as redis_lib

from core.config import settings
from db.session import AsyncSessionLocal
from middleware.rate_limit import RateLimitMiddleware
from routers.auth import router as auth_router
from routers.assets import router as assets_router
from routers.violations import router as violations_router
from routers.scan_runs import router as scan_runs_router
from routers.tasks import router as tasks_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Phase 3: load ML models into app.state here
    yield


app = FastAPI(title="GUARDIAN API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)

app.include_router(auth_router)
app.include_router(assets_router)
app.include_router(violations_router)
app.include_router(scan_runs_router)
app.include_router(tasks_router)


@app.get("/health")
async def health():
    db_ok = False
    redis_ok = False

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    try:
        r = redis_lib.Redis.from_url(settings.redis_url, socket_connect_timeout=1)
        r.ping()
        redis_ok = True
    except Exception:
        pass

    status_str = "ok" if (db_ok and redis_ok) else "degraded"
    return {
        "success": True,
        "data": {"status": status_str, "db": "ok" if db_ok else "error", "redis": "ok" if redis_ok else "error"},
        "meta": {},
    }
```

Save to: `apps/api/main.py`

- [ ] **Step 4: Run full test suite**

```bash
cd apps/api && pytest tests/ -v --cov=. --cov-report=term-missing
```

Expected: all tests PASS. Health tests pass (db/redis may show "error" in unit test environment — that's fine, `success: true` is still returned). `test_api_v1_prefix_exists` returns 403 (bearer not provided).

Note: If `test_health_returns_ok` fails because `db` key is missing when DB is unreachable, the test still passes since we only assert `success: True` and presence of `db`/`redis` keys — not their values.

- [ ] **Step 5: Run asset router tests**

```bash
cd apps/api && pytest tests/test_assets_router.py -v
```

Expected: 2 tests PASSED

- [ ] **Step 6: Commit**

```bash
git add apps/api/main.py apps/api/tests/test_health.py
git commit -m "feat: wire all routers into main.py, add rate limit middleware, extend health endpoint"
```

---

## Task 10: Final verification

- [ ] **Step 1: Run full test suite with coverage**

```bash
cd apps/api && pytest tests/ -v --cov=. --cov-report=term-missing
```

Expected: all tests PASS, coverage ≥ 40% (Phase 3 will bring it higher with ML layer tests)

- [ ] **Step 2: Verify docker compose still starts**

```bash
docker compose up --build -d
sleep 10
curl http://localhost:8000/health
```

Expected:
```json
{"success": true, "data": {"status": "ok", "db": "ok", "redis": "ok"}, "meta": {}}
```

- [ ] **Step 3: Apply migration 0002 in container**

```bash
docker compose exec api alembic upgrade head
```

Expected: `Running upgrade 0001 -> 0002, add users table`

- [ ] **Step 4: Smoke test auth endpoint**

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"nobody@test.com","password":"x"}' | python -m json.tool
```

Expected: `{"success": false, ...}` with 401 (user doesn't exist yet — that's correct)

- [ ] **Step 5: Verify protected routes reject unauthenticated**

```bash
curl -s http://localhost:8000/api/v1/assets | python -m json.tool
```

Expected: 403 (no Bearer token)

- [ ] **Step 6: Shut down**

```bash
docker compose down
```

- [ ] **Step 7: Update progress.md**

Replace the Phase 2 section in `progress.md`:

```markdown
## Status: Phase 2 — COMPLETE ✅ | Phase 3 — Not started
```

Add Phase 2 completed tasks table and verification results (mirror the Phase 1 section style).

- [ ] **Step 8: Final commit**

```bash
git add progress.md
git commit -m "chore: Phase 2 backend core complete — auth, routers, rate limiting verified"
```

---

## Verification Checklist

Before calling Phase 2 done, confirm all of the following:

- [ ] `pytest tests/ -v` — all tests PASS (target: 20+ tests)
- [ ] `GET /health` returns `{"status": "ok", "db": "ok", "redis": "ok"}` when stack is up
- [ ] `POST /api/v1/auth/login` with bad credentials → 401
- [ ] `GET /api/v1/assets` without token → 403
- [ ] `GET /api/v1/violations` without token → 403
- [ ] `alembic upgrade head` applies migration 0002 (users table)
- [ ] `docker compose up --build` — all 6 services healthy
- [ ] Coverage ≥ 40%
