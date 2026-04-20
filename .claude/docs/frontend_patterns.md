# Frontend Patterns

## App Router Structure (`apps/web/src/app/`)

```
app/
├── (auth)/
│   └── login/page.tsx
├── (dashboard)/
│   ├── layout.tsx           ← Dashboard shell (sidebar, nav, AlertContext provider)
│   ├── page.tsx             ← Threat overview (globe + alert feed)
│   ├── assets/
│   │   ├── page.tsx         ← Asset list (Server Component)
│   │   └── [id]/page.tsx    ← Asset detail
│   ├── violations/
│   │   ├── page.tsx         ← Violations feed
│   │   └── [id]/page.tsx    ← Violation detail + DMCA flow
│   └── settings/page.tsx
└── api/                     ← Next.js API routes (thin proxies only — no business logic)
```

---

## Data Fetching Rules

**Server Components** — use for initial page data. Fetch directly from the FastAPI backend using
`lib/api-client.ts` server-side functions. No loading skeletons needed; data arrives with the page.

**Client Components + SWR** — use for data that updates after load: violations feed, task status
polling, asset list after upload. SWR config in `lib/swr-config.ts` sets global dedupe interval.

**Never** use `useEffect` for fetching. Never fetch in layout components.

Polling pattern for task status:
```typescript
// lib/hooks/useTaskStatus.ts
const { data } = useSWR(`/tasks/${taskId}`, fetcher, {
  refreshInterval: (data) => data?.status === 'complete' ? 0 : 2000,
})
```

---

## Real-Time Alerts (WebSocket)

Single WebSocket connection managed in `lib/ws-client.ts`.
Wrapped in `AlertContext` (`components/providers/AlertContext.tsx`) and provided at dashboard layout level.
Components subscribe via `useAlerts()` hook — never open a WebSocket directly in a component.

On new violation event received, SWR cache for `/violations` is mutated optimistically.

---

## Component Structure

`components/ui/` — shadcn/ui primitives (do not edit these directly; re-export and extend)
`components/shared/` — app-wide shared components (PageHeader, DataTable, StatusBadge)
`components/features/` — domain-specific components organized by feature:

```
features/
├── assets/         (UploadZone, FingerprintProgress, AssetCard)
├── violations/     (ViolationDetail, SideBySideComparison, ModalityBreakdown)
├── dmca/           (DMCAGenerator, DMCAPreview)
└── map/            (ThreatGlobe, PropagationArc)  — Mapbox GL
```

---

## API Client (`lib/api-client.ts`)

All API calls go through this module. It unwraps the response envelope (see `architectural_patterns.md` §6),
handles auth token injection, and throws typed errors.
Components and hooks never use `fetch` directly.

---

## TypeScript Conventions

- All API response types are generated from the OpenAPI spec: `npm run generate-types`
  (runs `openapi-typescript` against the FastAPI `/openapi.json` endpoint)
- Do not hand-write API response types — regenerate them
- All component props interfaces are co-located in the same file as the component
