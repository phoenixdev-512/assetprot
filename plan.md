# GUARDIAN — Prototype Build & Deploy Plan

> **Target**: Working demo-ready prototype in ≤1 hour  
> **Last Updated**: 2026-04-28 22:30 IST  
> **Status**: 🟢 All code fixes applied. Frontend running on localhost:3000. Docker infra pending restart.

---

## 1. Current State Summary

### What Exists (90% code-complete)

| Layer | Files | Status |
|-------|-------|--------|
| **Backend (FastAPI)** | 40+ Python files | ✅ Code complete — routers, services, models, repos, tasks, agents |
| **Frontend (Next.js 14)** | 18+ TSX files | ✅ Code complete — `tsc --noEmit` passes with 0 errors |
| **Infrastructure** | docker-compose.yml, 2 Dockerfiles | ✅ Config present |
| **Database** | Models, seed data, Alembic migrations | ✅ 8 models, 5 demo assets + 5 violations |
| **Documentation** | IMPLEMENTATION.md, ARCHITECTURE.md, DEPLOYMENT_GUIDE.md | ✅ Comprehensive |
| **Design System** | globals.css, 5 UI components | ✅ Premium dark theme with animations |
| **SOLID Refactoring** | Protocols, strategy pattern, DIP | ✅ Applied across backend |

### What Was Broken (fixed ✅ / remaining 🔲)

| Issue | Severity | Status | Fix Applied |
|-------|----------|--------|-------------|
| `create_tables()` never called on startup | 🔴 CRITICAL | ✅ Fixed | Added to `main.py` lifespan before seed |
| `config.py` requires all env vars, crashes on missing | 🔴 CRITICAL | ✅ Fixed | Made optional with defaults |
| Root `.env` uses wrong DB hostname (`db` → `postgres`) | 🔴 CRITICAL | ✅ Fixed | Corrected to `postgres` |
| Rate limiter crashes if Redis unavailable | 🔴 CRITICAL | ✅ Fixed | Made lazy + graceful fallthrough |
| ML model loading crashes app if torch fails | 🟡 HIGH | ✅ Fixed | Wrapped in try/except |
| Missing `email-validator` dependency | 🟡 HIGH | ✅ Fixed | Added to requirements.txt |
| `torch` downloads 2GB GPU version | 🟡 HIGH | ✅ Fixed | CPU-only in Dockerfile, removed from requirements |
| docker-compose missing env vars (QDRANT_API_KEY, etc.) | 🟡 HIGH | ✅ Fixed | Added defaults with `${VAR:-default}` |
| Deprecated `version: '3.9'` warning | 🟠 LOW | ✅ Fixed | Removed |
| Frontend `.env.local` missing | 🟡 MEDIUM | ✅ Fixed | Created with `NEXT_PUBLIC_API_URL` |
| No `README.md` | 🟡 MEDIUM | ✅ Fixed | Created |
| Docker Desktop not running | 🔴 BLOCKING | 🔲 Pending | User needs to ensure Docker Desktop is running |
| End-to-end integration never tested | 🔴 CRITICAL | 🔲 Pending | Needs Docker up → browser test |

---

## 2. Files Modified in This Sprint

### Bug Fixes (7 files)

| File | Change |
|------|--------|
| `apps/api/main.py` | Added `create_tables()` to lifespan, wrapped ML loading in try/except |
| `apps/api/core/config.py` | Made all env vars optional with sensible defaults |
| `apps/api/middleware/rate_limit.py` | Lazy Redis init, graceful fallthrough on failure |
| `apps/api/requirements.txt` | Added `email-validator`, removed `torch` (moved to Dockerfile) |
| `.env` | Fixed `DATABASE_URL` hostname from `db` → `postgres` |
| `docker-compose.yml` | Added missing env vars, removed deprecated `version` key |
| `infrastructure/docker/api.Dockerfile` | CPU-only torch, upload dir creation, layer caching |

### New Files (3 files)

| File | Purpose |
|------|---------|
| `apps/web/.env.local` | Frontend API URL config |
| `README.md` | Quick-start + architecture overview |
| `plan.md` | This file |

---

## 3. Deployment Plan

### Option A: Docker Compose (Recommended) — ~15 min

**Prerequisites**: Docker Desktop running

```bash
# 1. Start all 6 services
docker compose up --build -d

# 2. Wait for health (30–60 seconds first time)
#    Watch logs:
docker compose logs -f api

# 3. Verify
curl http://localhost:8000/health

# 4. Open browser
#    http://localhost:3000 → Login → Dashboard
```

**Services launched**:
| Service | Port | Purpose |
|---------|------|---------|
| postgres | 5433 | Database |
| redis | 6381 | Cache + Celery broker |
| qdrant | 6333 | Vector DB |
| api | 8000 | FastAPI backend |
| celery_worker | — | Background task worker |
| web | 3000 | Next.js frontend |

---

### Option B: Local Dev (No Docker) — ~25 min

**Prerequisites**: PostgreSQL 16, Redis 7, Python 3.11, Node 20

```bash
# 1. Start Postgres + Redis (if not already running)
#    Ensure PostgreSQL is on port 5432 with user/pass: guardian/changeme_dev

# 2. Backend
cd apps/api
python -m venv venv && .\venv\Scripts\activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
python -c "import asyncio; from db.seed import main; asyncio.run(main())"
uvicorn main:app --reload --port 8000

# 3. Frontend (new terminal)
cd apps/web
npm install
npm run dev

# 4. Open http://localhost:3000
```

---

### Option C: Hybrid (Docker infra + Local code) — ~10 min

```bash
# 1. Start only infrastructure services
docker compose up -d postgres redis qdrant

# 2. Update apps/api/.env to point to Docker ports:
#    DATABASE_URL=postgresql+asyncpg://guardian:changeme_dev@localhost:5433/guardian
#    REDIS_URL=redis://localhost:6381/0
#    QDRANT_URL=http://localhost:6333

# 3. Run backend locally
cd apps/api
pip install -r requirements.txt  # (if not already)
uvicorn main:app --reload --port 8000

# 4. Run frontend locally  
cd apps/web
npm run dev
```

---

## 4. Demo Flow (5-minute script)

### Segment 1: Login → Dashboard (1 min)
1. Open `http://localhost:3000`
2. Enter credentials: `admin@demo.com` / `demo123!`
3. Dashboard loads with:
   - 4 stat cards (Total Assets: 5, Violations: 5, Reach: ~228K, Protection: 100%)
   - Global Threat Map with animated arcs
   - Recent Assets list
   - Live Alert Feed

### Segment 2: Asset Upload (2 min)
1. Click **Upload** in sidebar
2. Drag any image onto the drop zone
3. Show auto-detection (file name → title, MIME → content type)
4. Click **Upload & Protect**
5. Watch 4-step progress bar animate

### Segment 3: Violations (1.5 min)
1. Navigate to **Violations** page
2. Show violation cards:
   - Platform badges (YouTube, Reddit, Instagram, TikTok)
   - Confidence meters with color coding
   - Estimated reach numbers

### Segment 4: API Health (0.5 min)
```bash
curl http://localhost:8000/health | python -m json.tool
```

---

## 5. Architecture for Presentation

```
┌─────────────────────────────────────────────────────────────────┐
│                        GUARDIAN PLATFORM                         │
├────────────────────┬────────────────────────────────────────────┤
│  Next.js 14        │              FastAPI Backend               │
│  React 18 + TS     │                                            │
│                    │   ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  • Login / Auth    │   │ Routers  │→ │ Services │→ │ Repos  │  │
│  • Dashboard       │   │ (HTTP)   │  │ (Logic)  │  │ (DB)   │  │
│  • Assets          │   ├──────────┤  ├──────────┤  ├────────┤  │
│  • Violations      │   │ Auth     │  │ Auth     │  │ Asset  │  │
│  • Upload          │   │ Assets   │  │ Asset    │  │ Violat.│  │
│  • ThreatMap (SVG) │   │ Violat.  │  │ Violat.  │  │ ScanRun│  │
│  • AlertFeed       │   │ Threats  │  │ FPrint   │  └────────┘  │
│                    │   │ ScanRuns │  │ DMCA     │              │
│                    │   │ DMCA     │  │ Threat   │  ┌────────┐  │
│                    │   │ WebSock  │  │ Notif.   │  │ Qdrant │  │
│                    │   │ Tasks    │  └──────────┘  │ Vector │  │
│                    │   └──────────┘                 │  DB    │  │
│                    │                                └────────┘  │
│                    │   ┌────────────────────────────────────┐   │
│                    │   │  ML / Agent Pipeline (LangGraph)   │   │
│                    │   │  Planner → Crawler → Matcher →     │   │
│                    │   │  WatermarkDecoder → Reporter       │   │
│                    │   │                                    │   │
│                    │   │  CLIP ViT-B/32 | pHash | wHash    │   │
│                    │   │  Chromaprint | DWT Watermarking    │   │
│                    │   └────────────────────────────────────┘   │
├────────────────────┴────────────────────────────────────────────┤
│                       Infrastructure                            │
│  PostgreSQL 16 │ Redis 7 │ Qdrant 1.11 │ Celery 5.4 Workers   │
└─────────────────────────────────────────────────────────────────┘
```

### SOLID Principles Applied

| Principle | Implementation |
|-----------|----------------|
| **SRP** | Routers handle HTTP only, services handle logic, repos handle DB |
| **OCP** | FingerprintService uses Strategy pattern — add new media types without modifying existing code |
| **LSP** | All strategies/repos implement protocols — any impl can substitute another |
| **ISP** | Focused protocols: `VectorStore`, `NotificationService`, `DMCAGenerator`, `FingerprintStrategy` |
| **DIP** | Services depend on protocol abstractions, not concrete implementations |

---

## 6. Tech Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Next.js 14, React 18, TypeScript, TailwindCSS, Radix UI | Premium dark-themed SPA |
| Backend | FastAPI, Python 3.11, Pydantic v2 | Async REST API |
| ORM | SQLAlchemy 2.0 (async) + Alembic | DB schema & migrations |
| Auth | JWT (access + refresh), bcrypt, python-jose | Stateless auth |
| Task Queue | Celery 5.4 + Redis | Background fingerprinting |
| Vector DB | Qdrant 1.11 | CLIP embeddings, ANN search |
| ML | CLIP ViT-B/32, imagehash, invisible-watermark | Fingerprinting |
| Agents | LangGraph 0.2 | Autonomous detection pipeline |
| Real-time | FastAPI WebSocket | Live violation alerts |
| Database | PostgreSQL 16 + asyncpg | Primary data store |
| Containers | Docker Compose (6 services) | Local dev & deployment |

---

## 7. API Endpoints

```
Authentication:
  POST   /auth/register          Register new user + org
  POST   /auth/login             Login → JWT tokens
  POST   /auth/refresh           Refresh access token
  GET    /auth/me                Current user profile

Assets:
  GET    /api/v1/assets          List assets (paginated)
  POST   /api/v1/assets          Upload + ingest asset
  GET    /api/v1/assets/:id      Get single asset

Violations:
  GET    /api/v1/violations      List violations (paginated, filterable)
  GET    /api/v1/violations/:id  Get single violation
  POST   /api/v1/violations      Create violation (triggers WS alert)

Scans:
  GET    /api/v1/scan-runs       List scan runs
  POST   /api/v1/scan-runs       Trigger detection scan
  GET    /api/v1/scan-runs/:id   Get scan run + agent trace

Threats:
  GET    /api/v1/threats         GeoJSON-ready threat map data

DMCA:
  POST   /api/v1/dmca            Generate DMCA notice

System:
  GET    /health                 System health (DB, Redis, Qdrant, ML, uploads)

WebSocket:
  WS     /ws/alerts/:user_id    Per-user real-time alerts
  WS     /ws/org/:org_id        Per-org real-time alerts
```

---

## 8. Database Schema (8 tables)

```
organizations (id, name, plan, created_at)
    ├── users (id, org_id, email, hashed_password, is_active, created_at)
    ├── assets (id, org_id, title, content_type, status, territories, rights_metadata, ...)
    │     ├── asset_fingerprints (id, asset_id, phash, whash, watermark_payload, clip_vector_id)
    │     ├── violations (id, org_id, asset_id, discovered_url, platform, status, confidence, ...)
    │     │     └── dmca_notices (id, violation_id, notice_text, status, sent_at)
    │     └── scan_runs (id, org_id, asset_id, status, violations_found, agent_trace_log)
    └── tasks (id, name, status, result, error)
```

---

## 9. Remaining TODO

### Must-Do (for demo)
- [x] Fix `create_tables()` not called on startup
- [x] Fix config requiring all env vars
- [x] Fix `.env` DB hostname mismatch
- [x] Fix rate limiter crashing without Redis
- [x] Fix ML model loading crash
- [x] Add missing `email-validator` dep
- [x] Optimize Docker build (CPU-only torch)
- [x] Create `README.md`
- [x] Create `plan.md`
- [ ] **Start Docker Desktop & `docker compose up --build`**
- [ ] **Verify health endpoint returns green**
- [ ] **Walk through demo flow in browser**
- [ ] **Git commit all changes**

### Nice-to-Have (post-demo)
- [ ] Run backend pytest suite
- [ ] Add frontend unit tests
- [ ] Implement actual CLIP fingerprinting on upload
- [ ] Connect LangGraph agent pipeline end-to-end
- [ ] Add Alembic migration for schema changes
- [ ] Deploy to cloud (AWS/GCP/Azure)
- [ ] Add blockchain attestation (Phase 2 stub)
- [ ] Add dark web scanning (Phase 2 stub)

---

## 10. Quick Commands Reference

```bash
# Start everything
docker compose up --build -d

# View logs
docker compose logs -f api        # API logs
docker compose logs -f web        # Frontend logs
docker compose logs -f postgres   # DB logs

# Health check
curl http://localhost:8000/health | python -m json.tool

# Login test
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@demo.com","password":"demo123!"}'

# Stop everything
docker compose down

# Full reset (wipes DB)
docker compose down -v && docker compose up --build -d

# TypeScript check
cd apps/web && npx tsc --noEmit

# Python syntax check
cd apps/api && python -c "import py_compile, glob; [py_compile.compile(f, doraise=True) for f in glob.glob('**/*.py', recursive=True)]"
```

---

## 11. Docker Troubleshooting

### BuildKit I/O Error
If you see `input/output error` during `docker compose build`:
```bash
# 1. Restart Docker Desktop
# Close Docker Desktop completely, then reopen it

# 2. Prune all build cache
docker system prune -af
docker builder prune -af

# 3. Rebuild with clean cache
docker compose build --no-cache
docker compose up -d
```

### Docker Desktop Won't Start
```bash
# Reset Docker Desktop data (CAUTION: destroys all containers/images)
# Settings → Troubleshoot → Reset to factory defaults

# Or reinstall Docker Desktop from:
# https://www.docker.com/products/docker-desktop
```

### Alternative: Run Without Docker
```bash
# 1. Install PostgreSQL 16 locally
# 2. Install Redis locally
# 3. Use Option B or Option C from section 3
```

---

## 12. What Happens on First Startup

```mermaid
sequenceDiagram
    participant D as Docker Compose
    participant P as PostgreSQL
    participant R as Redis
    participant Q as Qdrant
    participant A as FastAPI API
    participant W as Next.js Web

    D->>P: Start postgres:16
    D->>R: Start redis:7-alpine
    D->>Q: Start qdrant:v1.11.3
    P-->>D: Healthy (pg_isready)
    R-->>D: Healthy (redis-cli ping)
    D->>A: Start API (depends_on: postgres, redis)
    A->>A: ensure_upload_dir()
    A->>P: create_tables() (CREATE TABLE IF NOT EXISTS)
    A->>A: load_models() (CLIP, Qdrant collection)
    A->>P: seed_demo_data() (5 assets, 5 violations)
    D->>W: Start frontend
    W-->>D: Ready on :3000
    A-->>D: Ready on :8000
```

---

*Generated: April 28, 2026 — Hackathon Sprint*

