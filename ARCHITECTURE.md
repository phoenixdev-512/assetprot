# GUARDIAN — Architecture

Last updated: 2026-04-28

## Overview

GUARDIAN is an AI-native digital-asset protection platform built to ingest video/audio/image assets, generate multi-layer fingerprints and steganographic watermarks, run autonomous agents to scan the web for unauthorized copies, and trigger DMCA workflows when matches are found. The MVP covers: ingest → fingerprint → store → agent scan → match → alert. Blockchain and dark-web scanning are Phase 2 stubs.

See the high-level design notes in [CLAUDE.md](CLAUDE.md#L1-L200).

## Tech stack (summary)
- Frontend: Next.js 14 (App Router), TypeScript, Tailwind, shadcn/ui.
- Backend: FastAPI (Python 3.11).
- Task queue: Celery with Redis (broker + result backend).
- Primary DB: PostgreSQL (SQLAlchemy + Alembic).
- Vector DB: Qdrant (ANN for embeddings).
- Cache / broker: Redis (also used for rate-limiting middleware).
- Embeddings / ML: CLIP (`openai/clip-vit-base-patch32`) loaded via Transformers; Chromaprint for audio; invisible-watermark for steganographic watermarking.
- Agents: LangGraph orchestrating Planner → Crawler → Matcher → Reporter.
- Crawler: Playwright for dynamic content + `httpx` for static fetches.
- Local dev infra: Docker Compose.

## High-level components

- Web UI (`apps/web`): SPA/SSR UI that calls the API (`NEXT_PUBLIC_API_URL`).
- API service (`apps/api`): FastAPI app exposing routers for `assets`, `auth`, `tasks`, `scan_runs`, `violations`, `dmca`.
  - Entrypoint & model loading: [apps/api/main.py](apps/api/main.py#L1-L200).
  - Celery configuration: [apps/api/celery_app.py](apps/api/celery_app.py#L1-L200).
  - ML loader & Qdrant init: [apps/api/ml/model_loader.py](apps/api/ml/model_loader.py#L1-L200).
- Workers (Celery): processes tasks defined under `apps/api/tasks/` and `apps/api/services/`.
- Datastores: Postgres (relational), Qdrant (vector) and local filesystem for uploaded files.
- External AI: Anthropic Claude for structured triage (via `ANTHROPIC_API_KEY`), used by triage services.

## Runtime sequence (detailed)

1. Ingest
   - The user (or ingestion pipeline) uploads an asset via the UI or direct API call.
   - API creates an `asset` record in Postgres and persists the binary to `upload_dir` (created at startup in `main.py`).

2. Fingerprinting (async)
   - API enqueues a fingerprinting task (Celery) with metadata and file path.
   - Celery worker executes tasks under `apps/api/tasks/` (e.g., `fingerprint_task.py`):
     - Compute perceptual embeddings (images/videos) via CLIP.
     - Compute audio fingerprint via Chromaprint (`fpcalc`).
     - Create steganographic watermark payloads using the invisible-watermark tooling.
     - Store vectors into Qdrant and fingerprint metadata into Postgres (`asset_fingerprint` or similar model).

3. Indexing & storage
   - Vectors: persisted to Qdrant with collection initialized in `ml.model_loader.load_models()`.
   - Metadata: persisted to Postgres via SQLAlchemy models under `apps/api/models/`.

4. Detection & agents
   - LangGraph-based agents orchestrate scanning flows (PlannerAgent produces tasks; CrawlerAgent fetches candidate pages/assets; MatcherAgent computes embeddings and queries Qdrant; ReporterAgent writes `violation` records and triggers DMCA flows).
   - Crawlers use Playwright for dynamic sites and `httpx` for static fetches.

5. DMCA & reporting
   - When matches surpass configured thresholds, `violation` records are created and DMCA generation code in `services/dmca_service.py` produces structured notices. Blockchain attestation remains a Phase 2 stub under `apps/api/blockchain/`.

## Key files and where to look

- Application startup and API routes: [apps/api/main.py](apps/api/main.py#L1-L200)
- Celery app config: [apps/api/celery_app.py](apps/api/celery_app.py#L1-L200)
- Model and Qdrant initialization: [apps/api/ml/model_loader.py](apps/api/ml/model_loader.py#L1-L200)
- Docker orchestration (local dev): [docker-compose.yml](docker-compose.yml#L1-L200)
- Project overview and design notes: [CLAUDE.md](CLAUDE.md#L1-L200)
- Routers: [apps/api/routers/](apps/api/routers/) — endpoints for assets, auth, violations, scan runs, DMCA, tasks.
- ML code: [apps/api/ml/](apps/api/ml/) — fingerprinting, agents, triage components.
- Tasks: [apps/api/tasks/](apps/api/tasks/) — Celery tasks definitions (fingerprint/detection jobs).
- DB models: [apps/api/models/](apps/api/models/) — SQLAlchemy models used across services.

> Note: directory links above point to existing folders in the repository root; open the folders in your editor to inspect individual files.

## Configuration & environment

- `.env` / `.env.example` drive runtime settings. Key variables:
  - `DATABASE_URL` (Postgres asyncpg URL)
  - `REDIS_URL` (Redis for cache and non-broker usage)
  - `QDRANT_URL`, `QDRANT_API_KEY`
  - `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
  - `ANTHROPIC_API_KEY` (Claude)
  - `POSTGRES_PASSWORD`

- `docker-compose.yml` configures services and maps internal URLs for local development (see [docker-compose.yml](docker-compose.yml#L1-L200)).

## Data model & storage conventions (summary)

- Postgres holds canonical relational state:
  - `asset` — metadata and ingestion status
  - `asset_fingerprint` — computed fingerprints and references
  - `violation` — detected matches and investigation state
  - `dmca_notice` — generated notices and status
  - `scan_run` — agent-run metadata

- Qdrant holds vector embeddings (512-dim by default from CLIP) and is used for ANN lookups. Collections are initialized in `ml.model_loader.init_collection`.

- Filesystem: uploaded binaries are stored under the `upload_dir` (created at startup in `main.py`) and served/processed locally inside the container volumes.

## ML & inference details

- CLIP is loaded into `FastAPI.app.state` on startup by `ml.model_loader.load_models()` to enable low-latency in-process inference for synchronous requests and agent pipelines. See [apps/api/ml/model_loader.py](apps/api/ml/model_loader.py#L1-L200).
- Audio fingerprinting uses Chromaprint (`fpcalc`) executed by tasks when audio tracks are present.
- Watermarking is implemented using the `invisible-watermark` tooling (see `apps/api/ml/fingerprinting/` for implementation files).
- All model artifacts are currently pulled from transformers hub and run in CPU mode by default; GPU support requires container and orchestration changes.

## Agents and detection thresholds

- Agents are defined under `apps/api/ml/agents/` and operate in a chain: Planner → Crawler → Matcher → Reporter.
- Matching uses a similarity threshold defined in `apps/api/config/thresholds.py`; tune thresholds to balance recall vs precision.

## Observability & health

- API health endpoint: `/health` implemented in `apps/api/main.py` performs DB and Redis checks.
- Logs: FastAPI and Celery log to stdout; Docker Compose captures logs for each service.

## Tests & CI

- Backend tests live under `apps/api/tests/` and run via `pytest` (see `pytest.ini`). Aim for >=60% coverage for the backend.
- Frontend type-checks via `npx tsc --noEmit` and tests via `npm test` in `apps/web`.

## How to run locally (developer flow)

1. Build and run all services (Postgres, Redis, Qdrant, API, Celery, Web):

```bash
docker compose up --build
```

2. Run backend tests:

```bash
cd apps/api && pytest --cov=. --cov-report=term-missing
```

3. Apply DB migrations:

```bash
cd apps/api && alembic upgrade head
```

4. Type-check frontend:

```bash
cd apps/web && npx tsc --noEmit
```

## Deployment & scaling notes

- The Docker Compose setup is for local development. Production should run services under an orchestrator (Kubernetes, ECS, or managed services).
- Recommendations:
  - Use managed Postgres and managed Qdrant (or secure internal cluster).
  - Use Redis as a managed cache with ACLs and persistence configuration.
  - Run Celery workers autoscaled by queue length; separate worker pools for CPU-bound (fingerprinting) vs IO-bound tasks.
  - Serve ML inference from GPU-enabled nodes or a separate inference cluster if using larger models.

## Security & secrets

- Never check `.env` or secrets into source control. Use environment-specific secret stores.
- Secure Qdrant with API keys and network controls in production.
- Rate limiting middleware (`middleware/rate_limit.py`) uses Redis; tune limits per API key/organization.

## Future roadmap (Phase 2+)

- Blockchain attestation: implement EAS + Polygon attestation flows under `apps/api/blockchain/` for tamper-evident proofs of ownership.
- Dark-web scanning: integrate additional crawler endpoints / third-party feeds and more robust evasion-resistant crawling.
- GPU acceleration: build GPU-enabled Docker images and switch CLIP & other heavy models to GPU runtimes.
- Distributed agent orchestration: move LangGraph agent execution to dedicated agent runners with queue-backed task dispatch and retry policies.
- Rate-limited public API & authentication tiers: add API keys, usage quotas, and per-organization billing.
- Observability: integrate tracing (OpenTelemetry), metrics (Prometheus), and structured logging (JSON).

## Operational runbook (short)

- Start stack (dev): `docker compose up --build`.
- Troubleshooting tips:
  - If API cannot connect to Postgres, check `POSTGRES_PASSWORD` and `DATABASE_URL` mapping in `.env` vs `docker-compose.yml`.
  - If Qdrant is unreachable, confirm `QDRANT_URL` and container health.
  - Check Celery logs for task failures; common issues are missing native dependencies for `fpcalc`.

## Next steps I can take for you

- Generate diagrams (sequence diagram, component diagram, ERD) from this architecture.
- Produce a concise `README.md` or `DEPLOY.md` for ops.
- Expand `ARCHITECTURE.md` with per-endpoint API reference and example payloads.

---

If you want, I will commit this file to the repo and update the todo list to mark the documentation steps complete. Which follow-up should I do next? (diagrams, ERD, commit, or expand specific sections)
