# GUARDIAN Progress

---

## Phase 2 Backend

### Task 1: User ORM Model + Migration ✅ COMPLETE (2026-04-21)

- `apps/api/models/user.py` — User ORM model (id, org_id FK, email, hashed_password, is_active, created_at)
- `apps/api/models/__init__.py` — User registered in __all__
- `apps/api/db/migrations/versions/0002_add_users.py` — Alembic migration (revision 0002, down_revision b47f479c9504)
- `apps/api/tests/test_db_models.py` — test_create_user added
- All 8 tables live in PostgreSQL; 11/11 tests passing
- Commit: `5fd6330`

---

### Task 2: Auth / JWT Layer ✅ COMPLETE (2026-04-21)

- Spec: `docs/superpowers/specs/2026-04-21-auth-jwt-design.md`
- JSON body tokens (access 15 min + refresh 7 days); HTTPBearer scheme
- `apps/api/schemas/auth.py` — RegisterRequest, LoginRequest, RefreshRequest, TokenResponse, UserResponse
- `apps/api/core/security.py` — hash_password, verify_password, create_access_token, create_refresh_token, decode_token
- `apps/api/services/auth_service.py` — AuthService (register, login, refresh, get_me)
- `apps/api/dependencies/auth.py` — get_current_user + get_auth_service Depends
- `apps/api/routers/auth.py` — 4 route handlers at /auth/{register,login,refresh,me}
- `apps/api/tests/test_security.py` — 6 unit tests; `apps/api/tests/test_auth.py` — 9 integration tests
- Commits: `afc01ba`→`29b5af5`

---

### Task 3: HTTP Layer (schemas, repos, middleware, routers) ✅ COMPLETE (2026-04-21)

- `apps/api/config/redis_keys.py`, `rate_limits.py` — Redis key helpers + rate limit constants
- `apps/api/schemas/base.py` — APIResponse[T], PaginatedResponse[T]
- `apps/api/schemas/asset.py`, `violation.py`, `scan_run.py` — ORM-serializing response schemas
- `apps/api/db/repositories/` — asset_repo, violation_repo, scan_run_repo, user_repo
- `apps/api/core/dependencies.py` — get_db, get_current_org_id (wraps existing get_current_user)
- `apps/api/middleware/rate_limit.py` — Redis token-bucket RateLimitMiddleware
- `apps/api/services/` — asset_service, violation_service, scan_run_service
- `apps/api/routers/assets.py` — GET /api/v1/assets, /api/v1/assets/{id}
- `apps/api/routers/violations.py` — GET /api/v1/violations
- `apps/api/routers/scan_runs.py` — GET /api/v1/scan-runs
- `apps/api/routers/tasks.py` — GET /api/v1/tasks/{task_id}
- Updated `apps/api/main.py` — all routers mounted, rate limit middleware, extended /health
- Tests: test_schemas.py (6), test_rate_limit.py (2), test_assets_router.py (3)
- **38/38 tests passing, 90% coverage**
- Commits: `204fe77`→`1e88688`

---

## Phase 3: ML Fingerprinting Pipeline ✅ COMPLETE (2026-04-21)

### Files Created

| File | Responsibility |
|---|---|
| `apps/api/config/thresholds.py` | PHASH_MATCH_BITS=10, CLIP_SIMILARITY_MIN=0.85, AUDIO_FP_MATCH_SCORE=0.80, WATERMARK_CONFIDENCE_MIN=0.90 |
| `apps/api/ml/__init__.py` | Package init |
| `apps/api/ml/fingerprinting/__init__.py` | Package init |
| `apps/api/ml/fingerprinting/perceptual_hash.py` | compute_phash, compute_whash (imagehash) |
| `apps/api/ml/fingerprinting/clip_embed.py` | compute_clip_embedding — injected model/processor |
| `apps/api/ml/fingerprinting/audio_fingerprint.py` | compute_chromaprint — fpcalc subprocess |
| `apps/api/ml/fingerprinting/watermark.py` | embed_watermark, decode_watermark (imwatermark DwtDctSvd) |
| `apps/api/ml/qdrant_store.py` | init_collection, upsert_embedding, search_similar |
| `apps/api/ml/model_loader.py` | load_models(app) — CLIP into app.state at startup, skip in APP_ENV=test |
| `apps/api/blockchain/__init__.py` | Package init |
| `apps/api/blockchain/protocol.py` | Attestation Protocol ABC |
| `apps/api/blockchain/null_attestation.py` | NullAttestation — no-op Phase 2 stub |
| `apps/api/services/fingerprint_service.py` | FingerprintService — orchestrates 4 stages, writes DB + Qdrant |
| `apps/api/tasks/__init__.py` | Package init |
| `apps/api/tasks/fingerprint_task.py` | fingerprint_task Celery task wrapping FingerprintService |

### Files Modified

| File | Change |
|---|---|
| `apps/api/requirements.txt` | Added imagehash, Pillow, transformers, torch, invisible-watermark, opencv-python-headless, python-multipart, pytest-env |
| `apps/api/core/config.py` | Added upload_dir, qdrant_collection settings |
| `apps/api/main.py` | Lifespan: creates upload_dir, loads models if not test env |
| `apps/api/routers/assets.py` | Added POST /api/v1/assets ingest endpoint |
| `apps/api/schemas/asset.py` | Added AssetIngestResponse |
| `apps/api/pytest.ini` | Added APP_ENV=test env var |
| `apps/api/tests/conftest.py` | Added `import models` to register all ORM models before create_all |

### Tests Added

- `apps/api/tests/test_fingerprinting.py` — 10 unit tests (pHash, wHash, CLIP, chromaprint, watermark)
- `apps/api/tests/test_fingerprint_service.py` — 3 integration tests (image, audio, error handling)
- `apps/api/tests/test_assets_ingest.py` — 3 HTTP integration tests (POST /api/v1/assets)

**54/54 tests passing, 87% coverage**

### Key bug fixed
`conftest.py` now imports `models` at module level so all ORM models are registered with `Base.metadata` before `create_all` runs on the first test, preventing "relation does not exist" failures when the ingest test file is collected first alphabetically.

---

## DB State
- PostgreSQL running locally on port 5432
- `DATABASE_URL=postgresql+asyncpg://guardian:changeme_dev@localhost:5432/guardian`
- Run migrations with: `DATABASE_URL="postgresql+asyncpg://guardian:changeme_dev@localhost:5432/guardian" alembic upgrade head`
- Run tests with: `DATABASE_URL="postgresql+asyncpg://guardian:changeme_dev@localhost:5432/guardian" pytest tests/ -v`

---

## API Routes Summary

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | /auth/register | No | Create org + user, return token pair |
| POST | /auth/login | No | Verify credentials, return token pair |
| POST | /auth/refresh | Refresh token | Return new access token |
| GET | /auth/me | Bearer | Current user profile |
| POST | /api/v1/assets | Bearer | Upload asset, dispatch fingerprint task |
| GET | /api/v1/assets | Bearer | List org assets (paginated) |
| GET | /api/v1/assets/{id} | Bearer | Get single asset |
| GET | /api/v1/violations | Bearer | List org violations (paginated) |
| GET | /api/v1/scan-runs | Bearer | List org scan runs (paginated) |
| GET | /api/v1/tasks/{id} | Bearer | Get task status |
| GET | /health | No | DB + Redis health check |

---

## Resumption Prompt (Next Session)

> Continue GUARDIAN — Phase 4: Frontend Slice 1.
>
> Read progress.md before starting. Phase 3 ML fingerprinting pipeline is fully complete:
> 4-stage pipeline (pHash, CLIP, Chromaprint, watermark), Celery task, POST /api/v1/assets ingest,
> 54/54 tests at 87% coverage.
>
> Key context:
> - Stack: FastAPI + SQLAlchemy async + PostgreSQL + Celery/Redis + Qdrant
> - Auth: HTTPBearer at /auth/*; protected routes via get_current_user in dependencies/auth.py
> - POST /api/v1/assets: multipart upload → saves to upload_dir → dispatches fingerprint_task → returns {asset_id, task_id}
> - Celery task polls DB for status updates (pending → fingerprinting → protected | failed)
> - PostgreSQL on localhost:5432; prefix pytest with DATABASE_URL="postgresql+asyncpg://guardian:changeme_dev@localhost:5432/guardian"
> - 54/54 tests currently passing — do not regress
> - Next: Next.js 14 frontend — login page, asset list, asset upload form, task-status polling (GET /api/v1/tasks/{id})
