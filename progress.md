# GUARDIAN Phase 2 Backend — Progress

---

## Task 1: User ORM Model + Migration ✅ COMPLETE (2026-04-21)

- `apps/api/models/user.py` — User ORM model (id, org_id FK, email, hashed_password, is_active, created_at)
- `apps/api/models/__init__.py` — User registered in __all__
- `apps/api/db/migrations/versions/0002_add_users.py` — Alembic migration (revision 0002, down_revision b47f479c9504)
- `apps/api/tests/test_db_models.py` — test_create_user added
- All 8 tables live in PostgreSQL; 11/11 tests passing
- Commit: `5fd6330`

---

## Task 2: Auth / JWT Layer ✅ COMPLETE (2026-04-21)

### Design ✅ (2026-04-21)
- Spec: `docs/superpowers/specs/2026-04-21-auth-jwt-design.md` (commit `b20429b`)
- Approach: JSON body tokens (access 15 min + refresh 7 days), no cookies in MVP
- `HTTPBearer` scheme (not OAuth2PasswordBearer — login accepts JSON not form data)

### Implementation ✅ (2026-04-21)
Files created:
- `apps/api/schemas/auth.py` — RegisterRequest, LoginRequest, RefreshRequest, TokenResponse, UserResponse
- `apps/api/core/security.py` — hash_password, verify_password, create_access_token, create_refresh_token, decode_token (HS256, bcrypt)
- `apps/api/services/auth_service.py` — AuthService (register, login, refresh, get_me)
- `apps/api/dependencies/auth.py` — get_current_user + get_auth_service Depends
- `apps/api/routers/auth.py` — 4 thin route handlers + standard envelope
- `apps/api/tests/test_security.py` — 6 unit tests (security utilities)
- `apps/api/tests/test_auth.py` — 9 integration tests (register, login, refresh, /me)
- Updated `apps/api/main.py` — include_router(auth_router, prefix="/auth") + HTTPException envelope handler
- Updated `apps/api/requirements.txt` — passlib[bcrypt]==1.7.4, python-jose[cryptography]==3.3.0, bcrypt==4.0.1
- 26/26 tests passing (11 original + 6 security unit + 9 auth integration)
- Commits: `afc01ba`, `4c62dad`, `2f1dcac`, `e5b99b6`, `29b5af5`

---

## DB State
- PostgreSQL running locally on port 5432
- `DATABASE_URL=postgresql+asyncpg://guardian:changeme_dev@localhost:5432/guardian`
- Run migrations with: `DATABASE_URL="postgresql+asyncpg://guardian:changeme_dev@localhost:5432/guardian" alembic upgrade head`
- Run tests with: `DATABASE_URL="postgresql+asyncpg://guardian:changeme_dev@localhost:5432/guardian" pytest tests/ -v`

---

## Resumption Prompt (Next Session)

> Continue GUARDIAN Phase 2 Backend — Task 3: (TBD — define next task).
>
> Read progress.md before starting. All auth endpoints are live at /auth/register, /auth/login, /auth/refresh, /auth/me.
>
> Key context:
> - Stack: FastAPI + SQLAlchemy async + PostgreSQL
> - Auth layer complete: HTTPBearer, JSON tokens, standard envelope
> - `get_current_user` dependency in `dependencies/auth.py` protects routes
> - PostgreSQL on localhost:5432; prefix pytest with `DATABASE_URL="postgresql+asyncpg://guardian:changeme_dev@localhost:5432/guardian"`
> - 26/26 tests currently passing — do not regress
