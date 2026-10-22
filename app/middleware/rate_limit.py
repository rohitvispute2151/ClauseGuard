from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.security import client_ip
from app.core.messages import MSG_RATE_LIMIT_EXCEEDED
from app.llm.resilience.rate_limiter import RateLimiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforces token-bucket rate limiting per client IP."""

    def __init__(self, app, rate_limiter: RateLimiter | None = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limit on health check
        if request.url.path.endswith("/health"):
            return await call_next(request)

        # Keyed on IP, never on a client-supplied header (which could be rotated to dodge the limit).
        acquired, retry_after = await self.rate_limiter.acquire(f"client:{client_ip(request)}")

        if not acquired:
            # Middleware sits outside FastAPI's exception handlers, so return the response directly.
            return JSONResponse(
                status_code=429,
                content={"detail": MSG_RATE_LIMIT_EXCEEDED.format(retry_after=retry_after)},
                headers={"Retry-After": str(max(int(retry_after), 1))},
            )

        return await call_next(request)
