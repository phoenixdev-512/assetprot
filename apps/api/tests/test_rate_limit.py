import pytest
from unittest.mock import MagicMock, patch
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.requests import Request
from middleware.rate_limit import RateLimitMiddleware


def _make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, requests_per_window=3, window_seconds=60)

    @app.get("/test")
    async def test_route(request: Request):
        return JSONResponse({"ok": True})

    return app


@pytest.mark.asyncio
async def test_rate_limit_allows_within_limit():
    app = _make_app()
    mock_redis = MagicMock()
    mock_redis.incr.return_value = 1
    with patch("middleware.rate_limit.redis.Redis.from_url", return_value=mock_redis):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get("/test", headers={"X-Org-Id": "org-123"})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_rate_limit_blocks_over_limit():
    app = _make_app()
    mock_redis = MagicMock()
    mock_redis.incr.return_value = 4  # over limit of 3
    with patch("middleware.rate_limit.redis.Redis.from_url", return_value=mock_redis):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get("/test", headers={"X-Org-Id": "org-123"})
    assert r.status_code == 429
