# Phase 2 Stubs

These features have interface definitions in the codebase but are **not wired up** in the MVP.
Do not implement them during Phase 1. Extend the existing stubs only.

---

## Blockchain / Content Attestation (`apps/api/blockchain/`)

### What's stubbed
`blockchain/attestation_service.py` defines the `AttestationService` interface:
```python
class AttestationService(Protocol):
    async def anchor_asset(self, asset_id: str, fingerprint_hash: str) -> str: ...
    async def verify_attestation(self, tx_hash: str) -> AttestationRecord: ...
```

`blockchain/null_attestation.py` — the no-op implementation used in MVP.
It logs the call and returns a fake transaction hash. This is what's injected via `Depends()`.

### Phase 2 plan
Replace `null_attestation.py` with `eas_attestation.py` (Ethereum Attestation Service on Polygon Amoy testnet).
The `AttestationService` interface does not change — only the injected implementation does.
The asset model already has `blockchain_tx_hash` and `attested_at` columns (nullable in MVP).

---

## HiDDeN Neural Watermarking

`ml/fingerprinting/watermark_embed.py` uses `invisible-watermark` in MVP.
The encoder/decoder interface is designed to be swappable:
```python
class WatermarkBackend(Protocol):
    def embed(self, frame: np.ndarray, payload: bytes) -> np.ndarray: ...
    def decode(self, frame: np.ndarray) -> bytes | None: ...
```

Phase 2: implement `HiDDeNBackend` using the trained HiDDeN encoder/decoder checkpoints.
Current: `InvisibleWatermarkBackend` wraps the `invisible-watermark` library.

---

## Dark Web / Aggregator Scanning

`config/crawl_targets.py` has a `DARK_WEB_TARGETS` list that is currently empty.
The `CrawlerNode` skips entries in this list if Tor proxy is not configured.
`GUARDIAN_TOR_PROXY_URL` env var controls this — unset in MVP.

---

## Live Broadcast Watermarking

Not stubbed in MVP. Placeholder ticket only. Would require integration with broadcast encoder APIs
(AWS MediaLive or similar). Out of scope for Phase 1.

---

## NFT-Gated Content Authentication

Not stubbed. Phase 3 concept. No code exists for this yet.
