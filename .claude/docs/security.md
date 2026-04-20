# Security

## Auth Flow

JWT-based auth. Short-lived access tokens (15 min) + refresh tokens (7 days) stored in httpOnly cookies.
Token signing key loaded from environment — never hardcoded.
All protected routes use `Depends(get_current_user)` in FastAPI.
Next.js middleware (`middleware.ts`) validates session on every request to `(dashboard)` routes.

---

## Zero-Trust Service-to-Service

All internal service calls (API → Celery task results, API → Qdrant, API → PG) use:
- Separate credentials per service (no shared root credentials)
- Connections authenticated via environment-injected secrets
- Qdrant: API key auth enabled even in local Docker Compose (habit formation)

mTLS between services is Phase 2. In MVP, services communicate only within the Docker network
(not exposed externally except the API and web ports).

---

## Rate Limiting

Redis token bucket, applied at two levels:
1. **Per-org, per-endpoint** — prevents API abuse by tenants
2. **Per-domain, in the crawler** — prevents GUARDIAN from being used as a DDoS tool against scan targets

Constants in `config/rate_limits.py`. Middleware in `api/middleware/rate_limit.py`.

---

## Request Signing (Upload API)

Upload requests are signed with HMAC-SHA256 using the org's API key.
Prevents replay attacks on the ingest endpoint.
Verification in `api/middleware/request_signing.py`.

---

## Secrets Management

All secrets via environment variables. In production: AWS Secrets Manager or HashiCorp Vault.
`.env.example` documents every variable with description and example format.
`python-dotenv` loads `.env` in local dev only — never in production containers.

Never log secrets, tokens, or API keys. The `api/core/logging.py` config scrubs known secret
field names from structured log output.

---

## GDPR / CCPA Hooks

`assets.territories` field drives data residency logic.
EU-originating content (`territories` includes EU codes) is flagged in asset metadata.
Data deletion: `DELETE /assets/{id}` triggers cascade that removes fingerprints, Qdrant vectors,
and all derivatives. Raw media is never stored — only fingerprints.

---

## What's Intentionally Not in MVP

- mTLS between internal services (Phase 2)
- SOC 2 audit logging (Phase 2)
- SSO / SAML (Phase 2)
