# Data Models

## PostgreSQL — Core Tables

### `organizations`
Tenant root. Every asset, user, and violation belongs to an org.
`id, name, plan, created_at`

### `assets`
Protected media assets registered by an org.
`id, org_id, title, content_type (video|image|audio), status (pending|fingerprinting|protected|failed),`
`rights_metadata (JSONB), territories (text[]), created_at, updated_at`

### `asset_fingerprints`
One row per asset. All fingerprint derivatives stored here (never the raw media).
`asset_id (FK), phash, whash, chromaprint, watermark_payload, embedding_vector_hash, fingerprinted_at`

### `violations`
Each detected infringement event.
`id, asset_id, discovered_url, platform, status (suspected|confirmed|dismissed|dmca_sent),`
`confidence, infringement_type, transformation_types (text[]), estimated_reach,`
`triage_verdict (JSONB), detected_at, resolved_at`

### `dmca_notices`
Generated takedown notices.
`id, violation_id, notice_text, status (draft|sent|acknowledged|rejected), sent_at`

### `tasks`
Celery task tracking for frontend polling.
`id (= Celery task_id), type, status (queued|running|complete|failed), result (JSONB), created_at`

### `scan_runs`
Records of each agent graph execution.
`id, asset_id, status (running|complete|partial|failed), violations_found, errors (JSONB), run_at`

---

## Qdrant

Single collection: `asset_embeddings` — see `ml_pipeline.md` for schema.
Payload fields are indexed for filtered ANN search by `org_id` and `content_type`.

---

## Pydantic Schema Conventions (`apps/api/schemas/`)

- Request schemas: `{Resource}Create`, `{Resource}Update`
- Response schemas: `{Resource}Response` (never expose raw ORM models to API layer)
- All datetimes: ISO 8601 strings in responses (`model_config = {"json_encoders": {datetime: ...}}`)
- IDs: always `str` in schemas (UUID stored as UUID in PG, serialized to string)
- Nullable fields use `X | None` syntax, not `Optional[X]`

---

## Redis Key Conventions

```
guardian:task:{task_id}          → task result (TTL 24h)
guardian:cache:url:{url_hash}    → dedup cache for crawler (TTL 24h)
guardian:rl:{org_id}:{endpoint}  → rate limit bucket
guardian:session:{session_id}    → user session
```

All Redis keys are defined as constants in `config/redis_keys.py`.
