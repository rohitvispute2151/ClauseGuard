from fastapi import HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.messages import MSG_RATE_LIMIT_EXCEEDED
from app.llm.resilience.rate_limiter import RateLimiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforces token-bucket rate limiting per client API key or client host."""

    def __init__(self, app, rate_limiter: RateLimiter | None = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limit on health check
        if request.url.path.endswith("/health"):
            return await call_next(request)

        client_key = (
            request.headers.get("X-API-Key")
            or request.client.host
            if request.client
            else "anonymous"
        )
        acquired, retry_after = await self.rate_limiter.acquire(f"client:{client_key}")

        if not acquired:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=MSG_RATE_LIMIT_EXCEEDED.format(retry_after=retry_after),
                headers={"Retry-After": str(int(retry_after))},
            )

        return await call_next(request)
