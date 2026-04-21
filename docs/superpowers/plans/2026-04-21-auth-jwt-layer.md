# Auth/JWT Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement JWT authentication (register, login, refresh, /me) for the GUARDIAN FastAPI backend.

**Architecture:** Security utilities live in `core/security.py` (pure functions, no DB), business logic in `services/auth_service.py` (receives AsyncSession), a `get_current_user` Depends in `dependencies/auth.py`, and thin HTTP handlers in `routers/auth.py`. Tokens are returned as JSON body (not cookies). HTTPBearer scheme — not OAuth2PasswordBearer.

**Tech Stack:** FastAPI, SQLAlchemy async, PostgreSQL, passlib[bcrypt], python-jose[cryptography], httpx AsyncClient for integration tests.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `apps/api/requirements.txt` | Modify | Add passlib[bcrypt], python-jose[cryptography] |
| `apps/api/schemas/__init__.py` | Create | Package init |
| `apps/api/schemas/auth.py` | Create | Pydantic request/response schemas |
| `apps/api/core/security.py` | Create | Pure JWT/bcrypt functions (no DB access) |
| `apps/api/services/__init__.py` | Create | Package init |
| `apps/api/services/auth_service.py` | Create | AuthService: register, login, refresh, get_me |
| `apps/api/dependencies/__init__.py` | Create | Package init |
| `apps/api/dependencies/auth.py` | Create | get_current_user + get_auth_service FastAPI Depends |
| `apps/api/routers/__init__.py` | Create | Package init |
| `apps/api/routers/auth.py` | Create | 4 thin HTTP route handlers |
| `apps/api/main.py` | Modify | Include auth router at /auth prefix |
| `apps/api/tests/conftest.py` | Modify | Add `client` fixture (httpx AsyncClient with DB override) |
| `apps/api/tests/test_security.py` | Create | 6 unit tests for core/security.py pure functions |
| `apps/api/tests/test_auth.py` | Create | 9 integration tests via HTTP |

---

### Task 1: Add Dependencies

**Files:**
- Modify: `apps/api/requirements.txt`

- [ ] **Step 1: Add packages to requirements.txt**

Add these two lines at the bottom of `apps/api/requirements.txt`:
```
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
```

- [ ] **Step 2: Install the new packages**

```bash
cd apps/api && pip install passlib[bcrypt]==1.7.4 "python-jose[cryptography]==3.3.0"
```

Expected: both packages install successfully with no errors.

- [ ] **Step 3: Verify install**

```bash
cd apps/api && python -c "from passlib.context import CryptContext; from jose import jwt; print('OK')"
```

Expected output: `OK`

- [ ] **Step 4: Commit**

```bash
git add apps/api/requirements.txt
git commit -m "chore: add passlib[bcrypt] and python-jose[cryptography] for JWT auth"
```

---

### Task 2: Create Schemas

**Files:**
- Create: `apps/api/schemas/__init__.py`
- Create: `apps/api/schemas/auth.py`

- [ ] **Step 1: Create the schemas package init**

Create `apps/api/schemas/__init__.py` with empty content (just a newline).

- [ ] **Step 2: Create schemas/auth.py**

Create `apps/api/schemas/auth.py`:
```python
from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    org_name: str
    email: EmailStr
    password: str

    @field_validator("org_name")
    @classmethod
    def org_name_max_length(cls, v: str) -> str:
        if len(v) > 255:
            raise ValueError("org_name must be 255 characters or fewer")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    org_id: str
    email: str
    is_active: bool
    created_at: str
```

- [ ] **Step 3: Verify schemas import cleanly**

```bash
cd apps/api && python -c "from schemas.auth import RegisterRequest, TokenResponse, UserResponse; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add apps/api/schemas/
git commit -m "feat: add Pydantic auth schemas (RegisterRequest, LoginRequest, TokenResponse, UserResponse)"
```

---

### Task 3: TDD — core/security.py

**Files:**
- Create: `apps/api/tests/test_security.py`
- Create: `apps/api/core/security.py`

- [ ] **Step 1: Write failing tests**

Create `apps/api/tests/test_security.py`:
```python
import pytest
from fastapi import HTTPException


def test_hash_password_returns_bcrypt_hash():
    from core.security import hash_password
    hashed = hash_password("mysecretpassword")
    assert hashed.startswith("$2b$")
    assert hashed != "mysecretpassword"


def test_verify_password_correct():
    from core.security import hash_password, verify_password
    hashed = hash_password("mysecretpassword")
    assert verify_password("mysecretpassword", hashed) is True


def test_verify_password_wrong():
    from core.security import hash_password, verify_password
    hashed = hash_password("mysecretpassword")
    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token_decodes():
    from core.security import create_access_token, decode_token
    token = create_access_token("user-id-123", "org-id-456")
    payload = decode_token(token)
    assert payload["sub"] == "user-id-123"
    assert payload["org_id"] == "org-id-456"
    assert payload["type"] == "access"


def test_create_refresh_token_decodes():
    from core.security import create_refresh_token, decode_token
    token = create_refresh_token("user-id-123", "org-id-456")
    payload = decode_token(token)
    assert payload["sub"] == "user-id-123"
    assert payload["org_id"] == "org-id-456"
    assert payload["type"] == "refresh"


def test_decode_token_invalid_raises_401():
    from core.security import decode_token
    with pytest.raises(HTTPException) as exc_info:
        decode_token("not.a.valid.token")
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "TOKEN_INVALID"
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd apps/api && DATABASE_URL="postgresql+asyncpg://guardian:changeme_dev@localhost:5432/guardian" pytest tests/test_security.py -v
```

Expected: all 6 tests FAIL with `ModuleNotFoundError` or `ImportError` — `core/security.py` does not exist yet.

- [ ] **Step 3: Implement core/security.py**

Create `apps/api/core/security.py`:
```python
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
```

- [ ] **Step 4: Run to verify they pass**

```bash
cd apps/api && DATABASE_URL="postgresql+asyncpg://guardian:changeme_dev@localhost:5432/guardian" pytest tests/test_security.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/api/core/security.py apps/api/tests/test_security.py
git commit -m "feat: add core/security.py — bcrypt hashing and JWT encode/decode utilities (TDD)"
```

---

### Task 4: Write Integration Tests + Add Client Fixture

**Files:**
- Modify: `apps/api/tests/conftest.py`
- Create: `apps/api/tests/test_auth.py`

- [ ] **Step 1: Add `client` fixture to conftest.py**

Append these lines to the bottom of `apps/api/tests/conftest.py`:
```python
from httpx import AsyncClient, ASGITransport
import pytest_asyncio


@pytest_asyncio.fixture
async def client(db_session):
    from main import app
    from db.session import get_async_session

    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

- [ ] **Step 2: Write all 9 integration tests**

Create `apps/api/tests/test_auth.py`:
```python
import pytest

REGISTER_PAYLOAD = {
    "org_name": "Sports Network",
    "email": "admin@sportsnet.com",
    "password": "securepass123",
}


@pytest.mark.asyncio
async def test_register_success(client):
    resp = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    assert resp.status_code == 409
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "EMAIL_TAKEN"


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(
        "/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["access_token"]
    assert body["data"]["refresh_token"]


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    resp = await client.post(
        "/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "wrongpassword"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_unknown_email(client):
    resp = await client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "somepassword"},
    )
    assert resp.status_code == 401
    body = resp.json()
    assert body["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_refresh_success(client):
    reg = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    refresh_token = reg.json()["data"]["refresh_token"]
    resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["access_token"]


@pytest.mark.asyncio
async def test_refresh_with_access_token(client):
    reg = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    access_token = reg.json()["data"]["access_token"]
    resp = await client.post("/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "TOKEN_INVALID"


@pytest.mark.asyncio
async def test_me_authenticated(client):
    reg = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    access_token = reg.json()["data"]["access_token"]
    resp = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["email"] == REGISTER_PAYLOAD["email"]
    assert data["is_active"] is True
    assert "id" in data
    assert "org_id" in data


@pytest.mark.asyncio
async def test_me_unauthenticated(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 403
```

- [ ] **Step 3: Run to verify tests fail (routes don't exist yet)**

```bash
cd apps/api && DATABASE_URL="postgresql+asyncpg://guardian:changeme_dev@localhost:5432/guardian" pytest tests/test_auth.py -v
```

Expected: all 9 tests FAIL with 404 Not Found (routes not registered yet).

- [ ] **Step 4: Commit**

```bash
git add apps/api/tests/conftest.py apps/api/tests/test_auth.py
git commit -m "test: add auth integration tests and httpx client fixture (red phase)"
```

---

### Task 5: Implement Service, Dependencies, Router, and Wire main.py

**Files:**
- Create: `apps/api/services/__init__.py`
- Create: `apps/api/services/auth_service.py`
- Create: `apps/api/dependencies/__init__.py`
- Create: `apps/api/dependencies/auth.py`
- Create: `apps/api/routers/__init__.py`
- Create: `apps/api/routers/auth.py`
- Modify: `apps/api/main.py`

- [ ] **Step 1: Create package __init__.py files**

Create `apps/api/services/__init__.py` (single newline).

Create `apps/api/dependencies/__init__.py` (single newline).

Create `apps/api/routers/__init__.py` (single newline).

- [ ] **Step 2: Implement services/auth_service.py**

Create `apps/api/services/auth_service.py`:
```python
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
```

- [ ] **Step 3: Implement dependencies/auth.py**

Create `apps/api/dependencies/auth.py`:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import decode_token
from db.session import get_async_session
from models.user import User

_bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_async_session),
) -> User:
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_INVALID", "message": "Token is not an access token"},
        )
    user = await db.get(User, payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "ACCOUNT_INACTIVE", "message": "Account is inactive"},
        )
    return user


async def get_auth_service(db: AsyncSession = Depends(get_async_session)):
    from services.auth_service import AuthService
    return AuthService(db)
```

- [ ] **Step 4: Implement routers/auth.py**

Create `apps/api/routers/auth.py`:
```python
from fastapi import APIRouter, Depends

from dependencies.auth import get_auth_service, get_current_user
from models.user import User
from schemas.auth import LoginRequest, RefreshRequest, RegisterRequest
from services.auth_service import AuthService

router = APIRouter()


@router.post("/register")
async def register(req: RegisterRequest, service: AuthService = Depends(get_auth_service)):
    data = await service.register(req)
    return {"success": True, "data": data.model_dump(), "meta": {}}


@router.post("/login")
async def login(req: LoginRequest, service: AuthService = Depends(get_auth_service)):
    data = await service.login(req)
    return {"success": True, "data": data.model_dump(), "meta": {}}


@router.post("/refresh")
async def refresh(req: RefreshRequest, service: AuthService = Depends(get_auth_service)):
    data = await service.refresh(req)
    return {"success": True, "data": data.model_dump(), "meta": {}}


@router.get("/me")
async def me(
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    data = await service.get_me(str(current_user.id))
    return {"success": True, "data": data.model_dump(), "meta": {}}
```

- [ ] **Step 5: Update main.py to register the auth router**

Replace the entire contents of `apps/api/main.py` with:
```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="GUARDIAN API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])


@app.get("/health")
async def health():
    return {"success": True, "data": {"status": "ok"}, "meta": {}}
```

- [ ] **Step 6: Run all tests to verify everything passes**

```bash
cd apps/api && DATABASE_URL="postgresql+asyncpg://guardian:changeme_dev@localhost:5432/guardian" pytest tests/ -v
```

Expected: all 20 tests PASS (11 original + 6 security + 9 auth integration). 0 failures, 0 regressions.

- [ ] **Step 7: Commit all implementation files**

```bash
git add apps/api/services/ apps/api/dependencies/ apps/api/routers/ apps/api/main.py
git commit -m "feat: implement Auth/JWT layer — register, login, refresh, /me endpoints with TDD (green phase)"
```

---

### Task 6: Update progress.md

**Files:**
- Modify: `progress.md`

- [ ] **Step 1: Run full test suite one final time**

```bash
cd apps/api && DATABASE_URL="postgresql+asyncpg://guardian:changeme_dev@localhost:5432/guardian" pytest tests/ -v --tb=short
```

Expected: 20 tests PASS, 0 failures.

- [ ] **Step 2: Update progress.md — mark Task 2 complete**

In `progress.md`, replace the Task 2 section header and status line:

Change `## Task 2: Auth / JWT Layer 🔄 IN PROGRESS` to `## Task 2: Auth / JWT Layer ✅ COMPLETE (2026-04-21)`

And add under the Implementation section:
```
### Implementation ✅ (2026-04-21)
Files created:
- `apps/api/schemas/auth.py` — RegisterRequest, LoginRequest, RefreshRequest, TokenResponse, UserResponse
- `apps/api/core/security.py` — hash_password, verify_password, create_access_token, create_refresh_token, decode_token
- `apps/api/services/auth_service.py` — AuthService (register, login, refresh, get_me)
- `apps/api/dependencies/auth.py` — get_current_user + get_auth_service Depends
- `apps/api/routers/auth.py` — 4 thin route handlers
- Updated `apps/api/main.py` — include_router(auth_router, prefix="/auth")
- Updated `apps/api/requirements.txt` — passlib[bcrypt], python-jose[cryptography]
- `apps/api/tests/test_security.py` — 6 unit tests (security utilities)
- `apps/api/tests/test_auth.py` — 9 integration tests
- 20/20 tests passing
```

- [ ] **Step 3: Commit progress.md**

```bash
git add progress.md
git commit -m "chore: update progress.md — Task 2 Auth/JWT complete, 20/20 tests passing"
```

---

## Spec Coverage Checklist

| Spec requirement | Covered by |
|---|---|
| POST /auth/register — creates org + user, returns token pair | Task 5: AuthService.register |
| POST /auth/login — verifies creds, returns token pair | Task 5: AuthService.login |
| POST /auth/refresh — returns new access token | Task 5: AuthService.refresh |
| GET /auth/me — returns current user profile | Task 5: AuthService.get_me + router |
| 409 EMAIL_TAKEN on duplicate register | Task 5: register |
| 401 INVALID_CREDENTIALS — no user enumeration | Task 5: login |
| 401 TOKEN_INVALID — wrong token type | Task 5: refresh + dependency |
| 401 ACCOUNT_INACTIVE | Task 5: refresh + dependency |
| 401 TOKEN_INVALID — expired/bad token | Task 3: decode_token |
| HTTPBearer (not OAuth2PasswordBearer) | Task 5: dependencies/auth.py |
| Tokens as JSON body (not cookies) | Task 5: TokenResponse |
| HS256, key = settings.jwt_secret_key | Task 3: core/security.py |
| Standard envelope { success, data/error, meta } | Task 5: routers/auth.py |
| 9 integration test cases | Task 4: test_auth.py |
| 6 security unit tests | Task 3: test_security.py |
| passlib[bcrypt] + python-jose[cryptography] | Task 1: requirements.txt |
| Refresh token NOT rotated (MVP) | Task 5: refresh returns same refresh_token |
