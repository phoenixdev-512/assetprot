# GUARDIAN — Claude Context

## What This Is
AI-native digital asset protection platform for sports media. Ingests video/audio/image assets,
generates multi-layer perceptual fingerprints + steganographic watermarks, then runs autonomous
agents that scan the web for unauthorized copies. Violations trigger auto-generated DMCA notices.

MVP scope: ingest → fingerprint → store → agent scan → match → alert. Blockchain and dark-web
scanning are Phase 2 stubs only.

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui | Type-safe, component library saves UI time |
| Backend | FastAPI (Python 3.11) | Async-native, ideal for ML integration |
| Task Queue | Celery + Redis | Replaces Kafka — sufficient throughput for MVP |
| Primary DB | PostgreSQL 16 (via SQLAlchemy + Alembic) | Relational core: assets, violations, orgs |
| Vector DB | Qdrant | ANN search for embedding similarity at ms latency |
| Cache / Broker | Redis 7 | Celery broker + hot cache + rate limiting |
| AI — Embeddings | CLIP (openai/clip-vit-base-patch32) | Replaces ImageBind — production-ready, local |
| AI — Audio | Chromaprint / fpcalc | Broadcast audio fingerprinting |
| AI — Watermark | invisible-watermark (rikeijin) | Production-ready; HiDDeN deferred to Phase 2 |
| AI — Classification | Claude claude-sonnet-4-20250514 via Anthropic SDK | Violation triage with structured JSON output |
| AI — Agents | LangGraph 0.2 | PlannerAgent → CrawlerAgent → MatcherAgent → ReporterAgent |
| Crawler | Playwright (dynamic) + httpx (static) | Replaces Scrapy — lighter, async-native |
| Blockchain | Stubbed (Phase 2) | EAS + Polygon planned; hooks present, not wired |
| Local Infra | Docker Compose | One-command spin-up; no k8s in MVP |

---

## Project Structure

```
guardian/
├── CLAUDE.md
├── docker-compose.yml
├── .env.example
├── apps/
│   ├── web/                  # Next.js 14 frontend
│   │   └── src/
│   │       ├── app/          # App Router pages + layouts
│   │       ├── components/   # Reusable UI (shadcn base + custom)
│   │       └── lib/          # API client, type definitions, utils
│   └── api/                  # FastAPI backend (Python)
│       ├── routers/          # HTTP route definitions (thin — delegate to services)
│       ├── services/         # Business logic; one service per domain
│       ├── ml/               # All ML model code
│       │   ├── fingerprinting/   # perceptual_hash, audio_fingerprint, watermark
│       │   ├── agents/           # LangGraph agent definitions
│       │   └── triage/           # violation_classifier, anomaly_detector
│       ├── models/           # SQLAlchemy ORM models
│       ├── schemas/          # Pydantic request/response schemas
│       ├── db/               # Alembic migrations + session factory
│       ├── blockchain/       # Phase 2 stubs (interfaces defined, not wired)
│       └── tests/            # pytest; target ≥60% coverage
├── infrastructure/
│   └── docker/               # Per-service Dockerfiles
└── .claude/
    └── docs/                 # Extended documentation (see below)
```

---

## Essential Commands

```bash
# Start all services (postgres, redis, qdrant, api, web, celery worker)
docker compose up --build

# Run backend tests
cd apps/api && pytest --cov=. --cov-report=term-missing

# Run frontend type-check
cd apps/web && npx tsc --noEmit

# Run frontend tests
cd apps/web && npm test

# Apply DB migrations
cd apps/api && alembic upgrade head

# Generate new migration
cd apps/api && alembic revision --autogenerate -m "description"

# Seed development data
cd apps/api && python scripts/seed_dev_data.py
```

---

## Environment Variables
See `.env.example` — all variables documented with descriptions. Never hardcode secrets.
Key groups: `DATABASE_URL`, `REDIS_URL`, `QDRANT_*`, `ANTHROPIC_API_KEY`, `CELERY_*`.

---

## Additional Documentation

Check these files when working on the relevant area:

| File | When to read |
|---|---|
| `.claude/docs/architectural_patterns.md` | Service boundaries, dependency injection, API design, agent orchestration patterns |
| `.claude/docs/ml_pipeline.md` | Fingerprinting pipeline stages, model details, embedding storage conventions |
| `.claude/docs/agent_system.md` | LangGraph agent graph, node contracts, crawl targets, similarity thresholds |
| `.claude/docs/data_models.md` | DB schema, Qdrant collection layout, Pydantic schema conventions |
| `.claude/docs/frontend_patterns.md` | App Router conventions, data fetching, component structure, real-time updates |
| `.claude/docs/security.md` | Auth flow, rate limiting, zero-trust service calls, GDPR hooks |
| `.claude/docs/phase2_stubs.md` | Blockchain interfaces, dark-web scanning hooks — do not implement, only extend stubs |
