# ML Pipeline

## Fingerprinting Pipeline — 4 Parallel Stages

All four run concurrently via `asyncio.gather()` in `services/fingerprint_service.py`.
Results are stored atomically: if any stage fails, the asset is marked `fingerprint_partial`
and the failed stages are retried independently.

### Stage 1 — Perceptual Hash (`ml/fingerprinting/perceptual_hash.py`)
- Computes pHash (DCT-based) + wHash (wavelet) on keyframes
- Output: 256-bit binary string per hash type
- Stored in PostgreSQL `asset_fingerprints.phash` / `.whash`
- Lookup: Hamming distance ≤ `PHASH_MATCH_BITS` (see `config/thresholds.py`)
- Robust to: re-encoding, compression, mild crop, color grade

### Stage 2 — CLIP Multimodal Embedding (`ml/fingerprinting/clip_embedder.py`)
- Model: `openai/clip-vit-base-patch32` loaded once at startup via `@lru_cache`
- Extracts embeddings from video keyframes; averages into a single 512-dim vector
- Stored in Qdrant collection `asset_embeddings`
- Lookup: cosine similarity ≥ `CLIP_SIMILARITY_MIN`
- Catches: audio-stripped clips, partial re-uploads, same content different encoding

### Stage 3 — Audio Fingerprint (`ml/fingerprinting/audio_fingerprint.py`)
- Extracts audio channel via ffmpeg subprocess, generates Chromaprint via `fpcalc`
- Fingerprint stored as compressed bitstring in PostgreSQL
- Matching uses AcoustID-style sliding window correlation
- Catches: screen recordings, radio rebroadcasts, audio-only re-uploads

### Stage 4 — Steganographic Watermark (`ml/fingerprinting/watermark_embed.py`)
- Library: `invisible-watermark` (rikeijin/invisible-watermark)
- Embeds 48-bit payload: `{org_id: 16bit | asset_id: 16bit | timestamp: 12bit | territory: 4bit}`
- Algorithm: DwtDctSvd (most robust to re-encoding among library options)
- Decoder: `watermark_decoder.py` — run on any candidate match; confirmed payload = irrefutable proof
- Note: HiDDeN neural watermarking is Phase 2; current approach survives H.264 re-encode in testing

---

## Qdrant Collection Schema

Collection name: `asset_embeddings`
```python
VectorParams(size=512, distance=Distance.COSINE)

# Payload stored per point:
{
  "asset_id": str,
  "org_id": str,
  "content_type": "video" | "image" | "audio",
  "created_at": int  # unix timestamp
}
```

All Qdrant operations go through `db/repositories/vector_repo.py` — never call the client directly
from service or ML code.

---

## Model Loading

Models are loaded once at worker startup via FastAPI lifespan events (`api/main.py`).
They are stored in `app.state` and injected via `Depends()`.
Never load a model inside a request handler or Celery task — this causes unacceptable latency.

```python
# api/main.py (lifespan)
app.state.clip_model = load_clip_model()
app.state.watermark_encoder = load_watermark_encoder()
```

---

## Anomaly Detection (`ml/triage/anomaly_detector.py`)

Tracks view/share velocity of detected content over time in PostgreSQL (TimescaleDB-compatible
schema, regular PG in MVP). Uses Isolation Forest (sklearn) fit on historical organic share patterns.
Flags content whose velocity Z-score exceeds threshold as "anomalous propagation."
Model is retrained weekly via a scheduled Celery beat task.
