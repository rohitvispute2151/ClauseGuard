import logging
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: aioredis.Redis | None = None


def get_redis_client() -> aioredis.Redis:
    """Get or create singleton async Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_timeout=5.0,
        )
    return _redis_client


async def close_redis_client() -> None:
    """Close Redis client on application shutdown."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
