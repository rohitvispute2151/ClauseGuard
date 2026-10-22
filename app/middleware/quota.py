import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.core.redis import get_redis_client
from app.core.security import client_ip

logger = logging.getLogger(__name__)

# In-process fallback counters: key -> (count, reset_at). Used only when Redis is unreachable.
_memory: dict[str, tuple[int, float]] = {}


def _quota_rules() -> dict[tuple[str, str], tuple[str, int]]:
    """(method, path) -> (bucket name, max requests per window)."""
    return {
        ("POST", "/api/v1/documents"): ("uploads", settings.QUOTA_UPLOADS),
        ("POST", "/api/v1/extract"): ("extractions", settings.QUOTA_EXTRACTIONS),
        ("POST", "/api/v1/ask"): ("questions", settings.QUOTA_QUESTIONS),
    }


class QuotaMiddleware(BaseHTTPMiddleware):
    """Per-IP fixed-window quotas on endpoints that spend LLM tokens.

    Protects a public deployment's free-tier LLM budget. Uses Redis so limits hold across
    instances, with an in-process fallback if Redis is unavailable.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        rule = _quota_rules().get((request.method, request.url.path.rstrip("/")))
        if not settings.QUOTA_ENABLED or rule is None:
            return await call_next(request)

        bucket, limit = rule
        count, retry_after = await self._hit(f"quota:{bucket}:{client_ip(request)}")
        if count > limit:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Demo quota reached for {bucket} ({limit} per "
                    f"{settings.QUOTA_WINDOW_S // 60} min). Try again in {retry_after // 60 + 1} min."
                },
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)

    async def _hit(self, key: str) -> tuple[int, int]:
        """Increment the window counter. Returns (count, seconds until the window resets)."""
        window = settings.QUOTA_WINDOW_S
        try:
            redis = get_redis_client()
            pipe = redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, window, nx=True)
            pipe.ttl(key)
            count, _, ttl = await pipe.execute()
            return int(count), max(int(ttl), 1)
        except Exception as exc:
            logger.debug("Redis quota fallback to in-memory: %s", exc)
            now = time.monotonic()
            count, reset_at = _memory.get(key, (0, now + window))
            if now >= reset_at:
                count, reset_at = 0, now + window
            _memory[key] = (count + 1, reset_at)
            return count + 1, max(int(reset_at - now), 1)
