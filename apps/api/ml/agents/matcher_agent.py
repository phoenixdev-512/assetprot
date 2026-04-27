import hashlib
import logging
from io import BytesIO
from typing import Any

import httpx
import imagehash
from PIL import Image

from config.thresholds import CLIP_SIMILARITY_MIN, PHASH_MATCH_BITS
from ml.agents.state import AgentState
from ml.fingerprinting.clip_embed import compute_clip_embedding
from ml.fingerprinting.perceptual_hash import compute_phash
from ml.qdrant_store import search_similar

logger = logging.getLogger(__name__)


async def fetch_image(url: str) -> Image.Image | None:
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                if "image" in content_type:
                    return Image.open(BytesIO(response.content))
    except Exception as e:
        logger.debug(f"Failed to fetch image from {url}: {e}")
    return None


async def matcher_node(state: AgentState) -> dict[str, Any]:
    discovered_urls = state.get("discovered_urls", [])
    candidate_matches: list[dict] = []
    errors = state.get("errors", [])

    for url in discovered_urls[:50]:
        try:
            img = await fetch_image(url)
            if img is None:
                continue

            try:
                phash = compute_phash(img)
            except Exception as e:
                logger.debug(f"pHash failed for {url}: {e}")
                phash = None

            try:
                embedding = compute_clip_embedding(img)
            except Exception as e:
                logger.debug(f"CLIP embedding failed for {url}: {e}")
                continue

            try:
                matches = await search_similar(
                    embedding,
                    score_threshold=CLIP_SIMILARITY_MIN,
                    limit=5,
                )
            except Exception as e:
                logger.debug(f"Qdrant search failed for {url}: {e}")
                continue

            for match in matches:
                candidate_matches.append({
                    "url": url,
                    "asset_id": match["payload"]["asset_id"],
                    "similarity": match["score"],
                    "phash": phash,
                    "platform": extract_platform(url),
                })

        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            errors.append({
                "node": "matcher",
                "error": str(e),
                "url": url,
            })

    return {"candidate_matches": candidate_matches, "errors": errors}


def extract_platform(url: str) -> str:
    domain = url.split("/")[2] if "/" in url else ""
    platform_map = {
        "twitter.com": "twitter",
        "x.com": "twitter",
        "instagram.com": "instagram",
        "tiktok.com": "tiktok",
        "youtube.com": "youtube",
        "reddit.com": "reddit",
        "imgur.com": "imgur",
        "flickr.com": "flickr",
    }
    for domain_key, platform in platform_map.items():
        if domain_key in domain:
            return platform
    return "unknown"