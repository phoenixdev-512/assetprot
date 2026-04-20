# GUARDIAN Build Progress

## Status: Phase 1 — Infrastructure (Tasks 1–6 of 11 complete)

Last commit: `9532a10` — feat: add Task and ScanRun ORM models — all 7 models complete

---

## How to Resume

When starting a new session, tell Claude:

> "Resume the GUARDIAN build from progress.md. We are in Phase 1 infrastructure, starting at Task 7 (Alembic migrations). Use the subagent-driven-development skill to continue dispatching implementer + reviewer subagents per the plan at `docs/superpowers/plans/2026-04-20-phase1-infrastructure.md`."

Then Claude should:
1. Read this file + the plan file
2. Apply the outstanding minor fix from Task 6 review (see below)
3. Continue with Task 7

---

## Completed Tasks

| # | Task | Status | Key Commits |
|---|---|---|---|
| 1 | Project scaffolding + .gitignore + pytest.ini | ✅ | 981de30, 7d41714 |
| 2 | Environment configuration | ✅ | 27ba3e4, 62e3ca8 |
| 3 | SQLAlchemy base + session factory | ✅ | 83e0245, ed9c868 |
| 4 | ORM models — Organization + Asset | ✅ | 8b21f5c, 3e73d4a |
| 5 | ORM models — AssetFingerprint + Violation + DMCANotice | ✅ | a73f35d, 0ea3a64 |
| 6 | ORM models — Task + ScanRun | ✅ | 9532a10 |

## Remaining Tasks

| # | Task | Status |
|---|---|---|
| 7 | Alembic setup + initial migration | ⬜ |
| 8 | FastAPI app skeleton + /health endpoint | ⬜ |
| 9 | Docker Compose + Dockerfiles | ⬜ |
| 10 | Next.js web scaffold | ⬜ |
| 11 | Integration test — docker compose up | ⬜ |

---

## Outstanding Fix Before Task 7

The Task 6 code reviewer flagged two minor issues (non-blocking, but tidy up before Task 7):

**Fix A — `task.py` created_at missing explicit nullable=False**

In `apps/api/models/task.py`, `created_at` column should have `nullable=False` added for consistency with the rest of the codebase:
```python
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), nullable=False
)
```

**Fix B — Two test assertions to add in test_db_models.py**

In `test_create_task`: add `assert t.type == "fingerprint"`
In `test_create_scan_run`: add `assert run.run_at is not None`

Apply these as a single commit: `fix: explicit nullable on task.created_at, complete test assertions`

---

## What Has Been Built

### Directory structure
```
guardian/
├── .gitignore
├── .env.example
├── .env  (local only, gitignored)
├── CLAUDE.md
├── apps/
│   └── api/
│       ├── requirements.txt
│       ├── requirements-dev.txt
│       ├── pytest.ini
│       ├── core/
│       │   ├── __init__.py
│       │   └── config.py          ← pydantic-settings Settings class
│       ├── db/
│       │   ├── __init__.py
│       │   ├── base.py            ← DeclarativeBase
│       │   ├── session.py         ← async engine + get_async_session
│       │   └── migrations/
│       │       └── versions/
│       │           └── .gitkeep
│       ├── models/
│       │   ├── __init__.py        ← exports all 7 models
│       │   ├── organization.py
│       │   ├── asset.py
│       │   ├── asset_fingerprint.py
│       │   ├── violation.py
│       │   ├── dmca_notice.py
│       │   ├── task.py
│       │   └── scan_run.py
│       └── tests/
│           ├── __init__.py
│           ├── conftest.py        ← db_session fixture
│           └── test_db_models.py  ← 8 tests, all passing
├── .claude/
│   └── docs/                      ← all reference docs moved here
│       ├── architectural_patterns.md
│       ├── ml_pipeline.md
│       ├── agent_system.md
│       ├── data_models.md
│       ├── frontend_patterns.md
│       ├── security.md
│       └── phase2_stubs.md
└── docs/
    └── superpowers/
        ├── specs/
        │   └── 2026-04-20-guardian-design.md
        └── plans/
            └── 2026-04-20-phase1-infrastructure.md
```

### Test status
```
8 tests PASSED (all in apps/api/tests/test_db_models.py)
- test_db_session_connects
- test_create_organization
- test_create_asset
- test_create_asset_fingerprint
- test_create_violation
- test_create_dmca_notice
- test_create_task
- test_create_scan_run
```

### Key decisions made during build
- `org_id` on Asset has `index=True` (added proactively — primary multi-tenant filter)
- `asset_id` on Violation and ScanRun have `index=True`
- `violation_id` on DMCANotice has `index=True`
- `TEST_DATABASE_URL` in conftest.py reads from env var with localhost fallback
- conftest `db_session` fixture uses `try/finally` for safe teardown
- pytest.ini has `pythonpath = .` and `asyncio_default_fixture_loop_scope = function`
- `.env.example` Celery Redis URLs use `localhost` (not `redis` Docker hostname)

---

## Phase 1 Plan Reference

Full plan: `docs/superpowers/plans/2026-04-20-phase1-infrastructure.md`

**Task 7 summary (Alembic):** Create `alembic.ini`, `db/migrations/env.py` (async), `db/migrations/script.py.mako`, then run `alembic revision --autogenerate -m "initial_schema"` to generate `0001_initial_schema.py`. Apply with `alembic upgrade head`. Add test `test_all_seven_tables_exist`.

**Task 8 summary (FastAPI):** Create `main.py` (FastAPI app + lifespan + /health + CORS), `celery_app.py` (Celery stub). Test with httpx AsyncClient. 9 tests total.

**Task 9 summary (Docker):** Create `docker-compose.yml` (6 services: postgres, redis, qdrant, api, celery_worker, web), `infrastructure/docker/api.Dockerfile`, `infrastructure/docker/web.Dockerfile`.

**Task 10 summary (Next.js):** Create `apps/web/package.json`, `next.config.ts`, `tsconfig.json`, `tailwind.config.ts`, `postcss.config.mjs`, `src/app/layout.tsx`, `src/app/globals.css`, `src/app/page.tsx`. Run `npm install && tsc --noEmit`.

**Task 11 summary (Integration):** Copy `.env.example` → `.env`, `docker compose up --build -d`, `alembic upgrade head` inside container, verify `/health` + web + qdrant, `docker compose down`.

---

## After Phase 1

Phases 2–6 each get their own plan. The order:
- Phase 2: Backend core (auth, middleware, base schemas, routers, DI)
- Phase 3: Fingerprinting pipeline (CLIP, pHash, Chromaprint, watermark, Celery tasks)
- Phase 4: Frontend slice 1 (login, asset upload, task polling)
- Phase 5: Agent system (LangGraph, 5 nodes, Playwright crawler)
- Phase 6: Triage + DMCA (Claude classification, DMCA generation, WebSocket)
