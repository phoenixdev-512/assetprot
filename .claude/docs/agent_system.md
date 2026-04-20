# Agent System

## Overview

Built with LangGraph 0.2. The graph is a directed pipeline (not cyclic in MVP) compiled once at
startup in `ml/agents/graph.py`. Runs are dispatched as Celery tasks — one run per asset per
scheduled scan cycle (default: every 6 hours per asset).

---

## Agent Graph

```
PlannerNode → CrawlerNode → MatcherNode → WatermarkDecoderNode → ReporterNode
```

All nodes share `AgentState` (see `architectural_patterns.md` §5).
The graph is invoked via: `compiled_graph.invoke(initial_state)` inside the Celery task.

---

## Node Responsibilities

### PlannerNode (`ml/agents/planner_agent.py`)
- Input: `asset_id`
- Reads asset metadata from DB (title, sport, teams, tags, known entity names)
- Decomposes into `SearchTask` list: text queries + reverse-image seeds + known piracy domains
- Output: `state.search_tasks` populated

### CrawlerNode (`ml/agents/crawler_agent.py`)
- Input: `state.search_tasks`
- Uses `httpx` for static pages, Playwright for JS-rendered (social embeds, streaming sites)
- Targets: Google reverse image search API, Twitter/X search API, known piracy aggregator list
  (configured in `config/crawl_targets.py` — update this file to add new scan targets)
- Rate-limits itself per domain using Redis-backed token bucket
- Output: `state.discovered_urls` populated

### MatcherNode (`ml/agents/matcher_agent.py`)
- Input: `state.discovered_urls`
- For each URL: fetches media, generates CLIP embedding + pHash on the fly
- Runs ANN query against Qdrant; Hamming distance check for pHash
- Candidates above threshold added to `state.candidate_matches`
- Skips URLs already processed in last 24h (Redis dedup cache keyed by URL hash)

### WatermarkDecoderNode (`ml/agents/watermark_decoder_node.py`)
- Input: `state.candidate_matches`
- Runs `invisible-watermark` decoder on each candidate's video frames
- If extracted payload matches a registered asset: escalates to `confirmed_violation`
- If no payload found: candidate remains as `suspected_violation` for human review

### ReporterNode (`ml/agents/reporter_node.py`)
- Input: `state.confirmed_violations` + `state.candidate_matches`
- Calls Claude for structured triage on each item (see `architectural_patterns.md` §4)
- Writes violations to PostgreSQL via `detection_repo`
- Dispatches WebSocket push notification to connected dashboard clients
- Enqueues DMCA generation task for confirmed violations (separate Celery task)

---

## Crawl Targets Config (`config/crawl_targets.py`)

Piracy site list and social platform search endpoints are externalized here.
Do not hardcode domains in agent code. Adding a new scan target = one line in this file.

---

## Failure Handling

- Each node wraps its work in try/except; errors appended to `state.errors`
- Graph continues on node failure (other nodes degrade gracefully)
- On completion, if `state.errors` is non-empty, the run is marked `partial` in the DB
- Full failures (graph crash) are caught in the Celery task and marked `failed` with retry
