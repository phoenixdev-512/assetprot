import redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_window: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self._redis = None

    def _get_redis(self):
        if self._redis is None:
            try:
                from config.redis_keys import rate_limit_key  # noqa: F401
                self._redis = redis.Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=1)
            except Exception:
                return None
        return self._redis

    async def dispatch(self, request: Request, call_next):
        r = self._get_redis()
        if r is None:
            return await call_next(request)
        try:
            from config.redis_keys import rate_limit_key
            org_id = request.headers.get("X-Org-Id", "anonymous")
            key = rate_limit_key(org_id, request.url.path)
            count = r.incr(key)
            if count == 1:
                r.expire(key, self.window_seconds)
            if count > self.requests_per_window:
                return JSONResponse(
                    {"success": False, "error": {"code": "RATE_LIMITED", "message": "Too many requests"}, "meta": {}},
                    status_code=429,
                )
        except Exception:
            pass  # Rate limiting is non-critical — let request through
        return await call_next(request)

