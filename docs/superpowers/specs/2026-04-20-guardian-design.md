# GUARDIAN MVP — Design Spec
**Date:** 2026-04-20
**Approach:** Vertical slices (Option B) — build one complete user journey first, then layer in agents, violations, and DMCA.

---

## 1. Architecture & Build Order

Six sequential phases, each delivering a testable increment:

| Phase | Deliverable | Key files |
|---|---|---|
| 1 | Infrastructure | `docker-compose.yml`, all Dockerfiles, `.env.example`, Alembic models + migrations |
| 2 | Backend core | FastAPI app, auth (JWT), middleware (rate limit, request signing), base schemas, DI wiring |
| 3 | Fingerprinting pipeline | 4 ML stages as Celery tasks, Qdrant writes, `/assets` ingest endpoint |
| 4 | Frontend slice 1 | Next.js shell, login, asset list + upload, task-status polling — first demoable end-to-end path |
| 5 | Agent system | LangGraph graph + 5 nodes, Playwright/httpx crawler, scan scheduler (Celery beat) |
| 6 | Triage + DMCA | Claude classification, anomaly detector, DMCA generation, violation feed, WebSocket alerts, Frontend slice 2 |

Phase 2 stubs (blockchain attestation, HiDDeN neural watermarking, Tor/dark-web scanning) are wired as Protocol + null-implementation no-ops and never implemented in MVP.

---

## 2. Data Flow

### Ingest path
```
Upload → POST /assets → immediate 200 with task_id
  → Celery: fingerprint_task (async)
      ├── Stage 1: pHash + wHash (imagehash) → PostgreSQL asset_fingerprints
      ├── Stage 2: CLIP embed (openai/clip-vit-base-patch32) → Qdrant asset_embeddings
      ├── Stage 3: Chromaprint (fpcalc subprocess) → PostgreSQL asset_fingerprints.chromaprint
      └── Stage 4: invisible-watermark embed (DwtDctSvd) → asset_fingerprints.watermark_payload
           → asset.status = "protected"
```

### Scan path (every 6 hours per asset via Celery beat)
```
Celery beat → scan_task → LangGraph graph.invoke(AgentState)
  PlannerNode     → generates SearchTask list from asset metadata
  CrawlerNode     → httpx (static) + Playwright (JS-rendered); Redis token-bucket rate limit per domain
  MatcherNode     → CLIP embed + pHash on each URL; ANN query Qdrant; Hamming check pHash
  WatermarkDecoder→ invisible-watermark decode on candidate frames
  ReporterNode    → Claude triage (structured JSON) → violations table
                  → WebSocket push to dashboard clients
                  → Celery: dmca_generation_task (confirmed violations only)
```

### Frontend real-time
- Task status: SWR polls `GET /tasks/{id}` every 2s until `status=complete`
- Violations: single shared WebSocket (`AlertContext`) pushes new events; SWR cache mutated optimistically

---

## 3. Key Technical Decisions

- **No raw media stored.** Only fingerprints and embeddings persisted. GDPR/CCPA delete = cascade wipe of `asset_fingerprints`, Qdrant vector, and all `violations` rows.
- **Models loaded once** at FastAPI lifespan startup into `app.state`; injected via `Depends()`. Never loaded inside a request handler or Celery task body.
- **All similarity thresholds** in `config/thresholds.py` (`PHASH_MATCH_BITS`, `CLIP_SIMILARITY_MIN`, `AUDIO_FP_MATCH_SCORE`, `WATERMARK_CONFIDENCE_MIN`). Never hardcoded in ML or service code.
- **LangGraph graph compiled once** at startup in `ml/agents/graph.py`. Never rebuilt per-request.
- **Phase 2 stubs** use Protocol + null implementation (`null_attestation.py`). Injected via `Depends()` — swappable without touching callers.
- **OpenAPI types auto-generated** for frontend: `npm run generate-types` targets FastAPI's `/openapi.json`. Hand-written API response types are forbidden.
- **Three-layer backend**: Router (thin, validates input) → Service (business logic) → Repository (all DB/Qdrant queries). ML calls never in routers.
- **All API responses** use the standard envelope: `{ success, data, meta: { request_id } }` for success; `{ success, error: { code, message }, meta }` for errors. Frontend `lib/api-client.ts` unwraps before components see data.

---

## 4. Error Handling & Failure Modes

| Scenario | Behaviour |
|---|---|
| Fingerprint stage failure | Failed stages retried independently; asset marked `fingerprint_partial` |
| Agent node failure | Error appended to `state.errors`; graph continues; run marked `partial` in `scan_runs` |
| Agent graph crash | Caught in Celery task; run marked `failed`; retried 3× with exponential backoff |
| Claude output invalid JSON | Re-prompt once; on second failure mark violation `requires_human_review` |
| Rate limit exceeded | 429 + `Retry-After` header; crawler self-throttles via Redis token bucket per domain |
| Celery task crash (general) | Marked `failed`; automatic retry 3× exponential backoff |

---

## 5. Security Constraints

- JWT: 15-min access tokens + 7-day refresh tokens in httpOnly cookies
- All protected API routes: `Depends(get_current_user)`
- Next.js middleware validates session on every `(dashboard)` route request
- Upload endpoint: HMAC-SHA256 request signing (org API key) to prevent replay attacks
- Rate limiting at two levels: per-org/per-endpoint (abuse prevention) + per-domain in crawler (DDoS prevention)
- Internal services communicate only within Docker network; no external exposure except API + web ports
- Secrets via environment variables only; `python-dotenv` in local dev only; `api/core/logging.py` scrubs known secret field names

---

## 6. Testing Targets

- Backend: ≥60% coverage via pytest (`--cov=. --cov-report=term-missing`)
- Frontend: `tsc --noEmit` passes; `npm test` passes
- Integration: Docker Compose `up --build` succeeds; seed script produces a working dev dataset

---

## 7. Out of Scope (Phase 2+)

- Blockchain attestation (EAS + Polygon) — stub only
- HiDDeN neural watermarking — stub only
- Dark-web / Tor scanning — stub only (`DARK_WEB_TARGETS` empty list)
- mTLS between internal services
- SOC 2 audit logging
- SSO / SAML
- Live broadcast watermarking
- NFT-gated content authentication
