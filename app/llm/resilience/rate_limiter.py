import time
import logging
from app.core.config import settings
from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token-bucket rate limiter backed by Redis with in-memory fallback."""

    def __init__(
        self,
        max_tokens: int | None = None,
        refill_rate: float | None = None,
    ):
        self.max_tokens = max_tokens or settings.RATE_LIMIT_TOKENS
        self.refill_rate = refill_rate or settings.RATE_LIMIT_REFILL_RATE
        # In-memory fallback tracking: {key: (tokens, last_time)}
        self._memory_buckets: dict[str, tuple[float, float]] = {}

    async def acquire(self, key: str, tokens: int = 1) -> tuple[bool, float]:
        """
        Attempt to acquire tokens.
        Returns (acquired: bool, retry_after: float).
        """
        try:
            redis = get_redis_client()
            now = time.time()
            bucket_key = f"rate_limit:{key}"

            # Simple token bucket in Redis via pipeline
            pipe = redis.pipeline()
            pipe.get(f"{bucket_key}:tokens")
            pipe.get(f"{bucket_key}:ts")
            res = await pipe.execute()

            current_tokens = float(res[0]) if res[0] is not None else float(self.max_tokens)
            last_ts = float(res[1]) if res[1] is not None else now

            # Refill
            elapsed = max(0.0, now - last_ts)
            current_tokens = min(float(self.max_tokens), current_tokens + elapsed * self.refill_rate)

            if current_tokens >= tokens:
                current_tokens -= tokens
                pipe = redis.pipeline()
                pipe.set(f"{bucket_key}:tokens", current_tokens, ex=3600)
                pipe.set(f"{bucket_key}:ts", now, ex=3600)
                await pipe.execute()
                return True, 0.0
            else:
                retry_after = (tokens - current_tokens) / self.refill_rate
                return False, round(retry_after, 2)

        except Exception as exc:
            logger.debug(f"Redis rate limiter fallback to in-memory: {exc}")
            return self._acquire_in_memory(key, tokens)

    def _acquire_in_memory(self, key: str, tokens: int) -> tuple[bool, float]:
        now = time.monotonic()
        if key not in self._memory_buckets:
            self._memory_buckets[key] = (float(self.max_tokens), now)

        current_tokens, last_time = self._memory_buckets[key]
        elapsed = max(0.0, now - last_time)
        current_tokens = min(float(self.max_tokens), current_tokens + elapsed * self.refill_rate)

        if current_tokens >= tokens:
            self._memory_buckets[key] = (current_tokens - tokens, now)
            return True, 0.0
        else:
            retry_after = (tokens - current_tokens) / self.refill_rate
            self._memory_buckets[key] = (current_tokens, now)
            return False, round(retry_after, 2)
