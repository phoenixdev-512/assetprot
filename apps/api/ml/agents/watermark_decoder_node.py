import logging
from typing import Any

import httpx
from PIL import Image

from config.thresholds import WATERMARK_CONFIDENCE_MIN
from ml.agents.state import AgentState
from ml.fingerprinting.watermark import decode_watermark

logger = logging.getLogger(__name__)


async def fetch_image(url: str) -> Image.Image | None:
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                if "image" in content_type:
                    from io import BytesIO
                    return Image.open(BytesIO(response.content))
    except Exception as e:
        logger.debug(f"Failed to fetch image from {url}: {e}")
    return None


def extract_asset_id_from_payload(payload: bytes) -> str | None:
    try:
        decoded = payload.replace(b"\x00", b"").decode("ascii")
        if decoded:
            return decoded
    except Exception:
        pass
    return None


async def watermark_decoder_node(state: AgentState) -> dict[str, Any]:
    candidate_matches = state.get("candidate_matches", [])
    confirmed_violations: list[dict] = []
    errors = state.get("errors", [])

    for candidate in candidate_matches:
        url = candidate.get("url")
        if not url:
            continue

        try:
            img = await fetch_image(url)
            if img is None:
                continue

            payload = decode_watermark(img)
            asset_id = extract_asset_id_from_payload(payload)

            if asset_id and asset_id == candidate.get("asset_id"):
                confirmed_violations.append({
                    "url": url,
                    "asset_id": asset_id,
                    "platform": candidate.get("platform"),
                    "similarity": candidate.get("similarity"),
                    "confidence": 1.0,
                    "detection_type": "watermark",
                })
            else:
                similarity = candidate.get("similarity", 0)
                if similarity >= WATERMARK_CONFIDENCE_MIN:
                    confirmed_violations.append({
                        "url": url,
                        "asset_id": candidate.get("asset_id"),
                        "platform": candidate.get("platform"),
                        "similarity": similarity,
                        "confidence": similarity,
                        "detection_type": "visual_similarity",
                    })

        except Exception as e:
            logger.debug(f"Watermark decode failed for {url}: {e}")

    return {"confirmed_violations": confirmed_violations, "errors": errors}