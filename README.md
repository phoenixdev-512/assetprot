# GUARDIAN — AI-Native Digital Asset Protection Platform

> Protecting sports media rights with multimodal AI fingerprinting, autonomous detection agents, and automated DMCA enforcement.

![Python](https://img.shields.io/badge/Python-3.11-blue) ![Next.js](https://img.shields.io/badge/Next.js-14-black) ![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green) ![Docker](https://img.shields.io/badge/Docker-Compose-blue)

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local frontend dev)
- Python 3.11+ (for local backend dev)

### 1. Start with Docker (Recommended)

```bash
# Clone and configure
cp .env.example .env
# Edit .env if needed (defaults work for demo)

# Start all services
docker compose up --build

# Wait ~60 seconds for first-time setup
# Frontend:  http://localhost:3000
# API:       http://localhost:8000
# API Docs:  http://localhost:8000/docs
# Health:    http://localhost:8000/health
```

### 2. Demo Credentials

| Field    | Value           |
|----------|-----------------|
| Email    | admin@demo.com  |
| Password | demo123!        |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GUARDIAN PLATFORM                        │
├──────────────────┬──────────────────────────────────────────┤
│   Next.js 14     │           FastAPI Backend                │
│   React Frontend │                                          │
│                  │  Routers → Services → Repositories       │
│  • Login/Dash    │  • Auth (JWT)    • Asset CRUD            │
│  • Asset Mgmt    │  • Fingerprint   • Violation Detection   │
│  • Violations    │  • DMCA Notice   • Scan Orchestration    │
│  • Upload        │  • Threat Map    • WebSocket Alerts      │
│  • Threat Map    │  • Agent Trace   • Structured Logging    │
├──────────────────┴──────────────────────────────────────────┤
│                    Infrastructure                           │
│  PostgreSQL │ Redis │ Qdrant Vector DB │ Celery Workers     │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React 18, TailwindCSS, Radix UI |
| Backend | FastAPI, SQLAlchemy 2.0 (async), Pydantic v2 |
| Auth | JWT (access + refresh tokens), bcrypt |
| Task Queue | Celery 5.4 + Redis |
| Vector DB | Qdrant (CLIP embeddings, cosine similarity) |
| ML Models | CLIP ViT-B/32, imagehash, invisible-watermark |
| Agent Framework | LangGraph (5-node pipeline) |
| Real-time | WebSocket with ConnectionManager |
| Database | PostgreSQL + asyncpg |
| Containers | Docker Compose (6 services) |

## Key Features

- **Multimodal Fingerprinting**: CLIP embeddings + perceptual hashing + steganographic watermarking
- **Autonomous Detection**: LangGraph agent pipeline (Planner → Crawler → Matcher → Reporter)
- **Real-time Alerts**: WebSocket-powered live violation notifications
- **Global Threat Map**: Interactive SVG visualization with animated threat arcs
- **DMCA Automation**: One-click notice generation for rights enforcement
- **SOLID Architecture**: Protocol-based dependency injection, strategy pattern

## API Endpoints

```
POST   /auth/register         Register user
POST   /auth/login            Login (returns JWT)
POST   /auth/refresh          Refresh token
GET    /auth/me               Current user

GET    /api/v1/assets         List assets
POST   /api/v1/assets         Upload asset
GET    /api/v1/assets/:id     Get asset

GET    /api/v1/violations     List violations
POST   /api/v1/violations     Create violation

GET    /api/v1/scan-runs      List scan runs
POST   /api/v1/scan-runs      Trigger scan

GET    /api/v1/threats        Threat map data
POST   /api/v1/dmca           Generate DMCA notice

GET    /health                System health check

WS     /ws/alerts/:user_id    User alerts
WS     /ws/org/:org_id        Org alerts
```

## Documentation

- [IMPLEMENTATION.md](IMPLEMENTATION.md) — Detailed sprint report
- [ARCHITECTURE.md](ARCHITECTURE.md) — System architecture
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) — Full deployment instructions

---

*Built for Hackathon Sprint — April 2026*
