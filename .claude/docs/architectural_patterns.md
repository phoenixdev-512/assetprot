# Architectural Patterns

## 1. Router → Service → Repository (Three-Layer Backend)

Routers are thin. They validate input via Pydantic schemas and delegate immediately to a service.
Services own all business logic and orchestrate across repositories and ML modules.
Repositories encapsulate all DB/Qdrant queries — services never write raw SQL or ORM queries directly.

```
routers/assets.py        → services/asset_service.py     → db/repositories/asset_repo.py
routers/detections.py    → services/detection_service.py → db/repositories/detection_repo.py
                                                          → ml/fingerprinting/...
```

This means: if you're adding a feature, the router gets at most one new function, the service gets
the logic, and any new query lives in the repo. Never put ML calls in a router.

---

## 2. Dependency Injection via FastAPI `Depends()`

All shared resources (DB session, Qdrant client, Celery app, config) are injected via FastAPI's
dependency system. Never instantiate these inside route handlers or services directly.

Pattern used throughout `routers/`:
```python
# routers/assets.py
async def upload_asset(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    qdrant: QdrantClient = Depends(get_qdrant),
    asset_service: AssetService = Depends(get_asset_service),
):
```

Service constructors accept these as parameters — makes unit testing straightforward (inject mocks).

---

## 3. Celery Tasks for All ML Work

No ML inference runs inside an HTTP request. Every fingerprinting, embedding, watermark, and
classification job is dispatched as a Celery task and returns a task ID immediately.

Pattern:
- Router dispatches task → returns `{"task_id": "...", "status": "queued"}`
- Frontend polls `GET /tasks/{task_id}` or receives a WebSocket push when complete
- Task results stored in Redis (TTL 24h) and persisted to PostgreSQL on completion

This keeps API response times <100ms regardless of ML processing time.

---

## 4. Structured JSON Contracts for AI Classification

All calls to Claude for violation classification use a system prompt that enforces JSON output.
The response is validated against a Pydantic model before being stored or surfaced.

Canonical output schema (see `schemas/violation.py`):
```python
class ViolationVerdict(BaseModel):
    infringement_type: Literal["exact_copy", "re_encoded", "partial_clip", "audio_only", "false_positive"]
    confidence: float          # 0.0–1.0
    transformation_type: list[str]
    platform: str
    estimated_reach: int | None
    rights_territory_violation: bool
    reasoning: str
```

Never parse AI output with regex. Always validate through the schema; catch `ValidationError` and
re-prompt once before marking the triage as `requires_human_review`.

---

## 5. LangGraph Agent Graph — Node Contract

Each agent node in the LangGraph graph follows a strict input/output contract using a shared
`AgentState` TypedDict. Nodes must be pure functions of state — no side effects except writing
back to state. External I/O (DB writes, HTTP calls) happens in tool functions called by nodes.

```python
# ml/agents/state.py
class AgentState(TypedDict):
    asset_id: str
    search_tasks: list[SearchTask]
    discovered_urls: list[str]
    candidate_matches: list[CandidateMatch]
    confirmed_violations: list[Violation]
    errors: list[str]
```

Nodes: `planner_node` → `crawler_node` → `matcher_node` → `watermark_decoder_node` → `reporter_node`

The graph is defined once in `ml/agents/graph.py` and compiled at startup. Never rebuild the graph
per-request.

---

## 6. API Response Envelope

All API responses use a consistent envelope. This is enforced by a base response schema in
`schemas/base.py` and applied in every router.

Success:
```json
{ "success": true, "data": { ... }, "meta": { "request_id": "..." } }
```

Error:
```json
{ "success": false, "error": { "code": "ASSET_NOT_FOUND", "message": "..." }, "meta": { ... } }
```

Frontend `lib/api-client.ts` unwraps this envelope — components never see the raw envelope shape.

---

## 7. Similarity Threshold Constants

All embedding similarity and perceptual hash thresholds are defined as named constants in
`api/config/thresholds.py` — never hardcoded in ML or service code. This makes tuning visible
and centralized.

```python
PHASH_MATCH_BITS: int = 10       # Hamming distance ≤ this = match
CLIP_SIMILARITY_MIN: float = 0.88
AUDIO_FP_MATCH_SCORE: float = 0.75
WATERMARK_CONFIDENCE_MIN: float = 0.90
```

---

## 8. Frontend Data Fetching Pattern

Server Components fetch data directly for initial page load (no loading states, no waterfalls).
Client Components use SWR for polling/real-time updates (violations feed, task status).
Never fetch in a `useEffect` — use SWR or a Server Component.

Real-time alerts use a WebSocket connection managed in `lib/ws-client.ts`, consumed via a
single shared React context (`AlertContext`) so only one socket connection exists per session.
