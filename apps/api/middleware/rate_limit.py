import redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from config.redis_keys import rate_limit_key
from core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_window: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self._redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)

    async def dispatch(self, request: Request, call_next):
        org_id = request.headers.get("X-Org-Id", "anonymous")
        key = rate_limit_key(org_id, request.url.path)
        count = self._redis.incr(key)
        if count == 1:
            self._redis.expire(key, self.window_seconds)
        if count > self.requests_per_window:
            return JSONResponse(
                {"success": False, "error": {"code": "RATE_LIMITED", "message": "Too many requests"}, "meta": {}},
                status_code=429,
            )
        return await call_next(request)
