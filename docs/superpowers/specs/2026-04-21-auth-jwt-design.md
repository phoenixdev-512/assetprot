# Auth / JWT Layer — Design Spec

**Date:** 2026-04-21
**Status:** Approved
**Scope:** MVP — Task 2 Phase 2 Backend

---

## Overview

JWT-based authentication for GUARDIAN. Access tokens (15 min) and refresh tokens (7 days) returned
as JSON in the response body. Frontend stores tokens in memory and silently refreshes. No cookies
in MVP — simpler to test and wire up; httpOnly cookie migration is Phase 2.

---

## Endpoints

| Method | Path | Auth required | Purpose |
|---|---|---|---|
| `POST` | `/auth/register` | No | Create org + user; return token pair |
| `POST` | `/auth/login` | No | Verify credentials; return token pair |
| `POST` | `/auth/refresh` | Refresh token in body | Return new access token |
| `GET` | `/auth/me` | Access token (Bearer) | Return current user profile |

---

## File Layout

```
apps/api/
├── schemas/auth.py           # Pydantic request/response schemas
├── services/auth_service.py  # Business logic: hashing, token creation, user lookup
├── core/security.py          # JWT encode/decode utilities (no business logic)
├── routers/auth.py           # Thin route handlers; delegate to auth_service
└── dependencies/auth.py      # get_current_user — Depends() for protected routes
```

---

## Schemas (`schemas/auth.py`)

```python
# Requests
class RegisterRequest(BaseModel):
    org_name: str           # max 255 chars
    email: EmailStr
    password: str           # min 8 chars, validated here

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

# Responses
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str
    org_id: str
    email: str
    is_active: bool
    created_at: str         # ISO 8601
```

All wrapped in the standard API envelope `{ "success": true, "data": {...}, "meta": {} }`.

---

## Token Payload

```json
{
  "sub": "<user_uuid>",
  "org_id": "<org_uuid>",
  "type": "access" | "refresh",
  "exp": <unix_timestamp>
}
```

Signing: HS256 via `python-jose[cryptography]`. Key: `settings.jwt_secret_key` (already in `Settings`).

---

## Core Security Utilities (`core/security.py`)

Four pure functions — no DB access, no FastAPI dependencies:

- `hash_password(plain: str) -> str` — bcrypt via `passlib[bcrypt]`
- `verify_password(plain: str, hashed: str) -> bool`
- `create_access_token(user_id: str, org_id: str) -> str` — 15-min expiry
- `create_refresh_token(user_id: str, org_id: str) -> str` — 7-day expiry
- `decode_token(token: str) -> dict` — raises `HTTPException 401` on invalid/expired

---

## Service (`services/auth_service.py`)

`AuthService` receives an `AsyncSession` in its constructor (injected by FastAPI `Depends`).

- `register(req: RegisterRequest) -> TokenResponse`
  - Check email not already taken (raise 409 if so)
  - Create `Organization` + `User` in a single transaction
  - Return `TokenResponse`

- `login(req: LoginRequest) -> TokenResponse`
  - Fetch user by email (raise 401 if not found or inactive)
  - Verify password (raise 401 on mismatch — same error, no user enumeration)
  - Return `TokenResponse`

- `refresh(req: RefreshRequest) -> TokenResponse`
  - Decode token, assert `type == "refresh"` (raise 401 otherwise)
  - Fetch user, assert still active (raise 401 if not)
  - Return new `TokenResponse` (new access token; refresh token reused, not rotated in MVP)

- `get_me(user_id: str) -> UserResponse`
  - Fetch user by id, return `UserResponse`

---

## Dependency (`dependencies/auth.py`)

```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_session),
) -> User:
```

- Decodes Bearer token from `Authorization` header
- Asserts `type == "access"`
- Fetches and returns the `User` ORM object
- Raises `HTTP 401` on any failure

`scheme = HTTPBearer()` — extracts Bearer token from `Authorization` header. We use `HTTPBearer` rather than `OAuth2PasswordBearer` because our login endpoint accepts JSON, not OAuth2 form data; using `OAuth2PasswordBearer` would mislead the Swagger UI.

---

## Router (`routers/auth.py`)

Thin handlers only. Each calls the service and wraps the result in the standard envelope:

```python
@router.post("/register")
async def register(req: RegisterRequest, service: AuthService = Depends(get_auth_service)):
    data = await service.register(req)
    return {"success": True, "data": data.model_dump(), "meta": {}}
```

Same pattern for `/login`, `/refresh`, `/me`.

Registered in `main.py` with `app.include_router(auth_router, prefix="/auth", tags=["auth"])`.

---

## Error Handling

| Scenario | HTTP status | Error code |
|---|---|---|
| Email already registered | 409 | `EMAIL_TAKEN` |
| Invalid credentials (login) | 401 | `INVALID_CREDENTIALS` |
| Token expired or invalid | 401 | `TOKEN_INVALID` |
| Token is wrong type | 401 | `TOKEN_INVALID` |
| User inactive | 401 | `ACCOUNT_INACTIVE` |

Errors use the standard envelope: `{ "success": false, "error": { "code": "...", "message": "..." } }`.

---

## Testing

New test file: `tests/test_auth.py`

- `test_register_success` — creates org + user, returns valid token pair
- `test_register_duplicate_email` — second register with same email → 409
- `test_login_success` — valid credentials → tokens
- `test_login_wrong_password` — → 401
- `test_login_unknown_email` — → 401 (same message as wrong password)
- `test_refresh_success` — valid refresh token → new access token
- `test_refresh_with_access_token` — wrong token type → 401
- `test_me_authenticated` — valid Bearer → user profile
- `test_me_unauthenticated` — no token → 401

All tests use the existing `db_session` fixture. Route tests will use `httpx.AsyncClient` against the FastAPI app.

---

## Dependencies to Add

```
passlib[bcrypt]
python-jose[cryptography]
```

Add to `apps/api/requirements.txt`.

---

## What's Explicitly Out of Scope (MVP)

- Email verification
- Password reset flow
- Refresh token rotation
- Token revocation / blocklist
- httpOnly cookie transport
- SSO / OAuth2 social login
