import asyncio
import logging
import random
from collections.abc import Callable
from typing import Any, TypeVar

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryPolicy:
    """Executes callables with exponential backoff and randomized jitter."""

    def __init__(
        self,
        max_retries: int | None = None,
        base_delay_s: float | None = None,
        max_delay_s: float | None = None,
        jitter: bool = True,
    ):
        self.max_retries = max_retries or settings.LLM_MAX_RETRIES
        self.base_delay_s = base_delay_s or settings.LLM_BASE_DELAY_S
        self.max_delay_s = max_delay_s or settings.LLM_MAX_DELAY_S
        self.jitter = jitter

    def _calculate_delay(self, attempt: int) -> float:
        delay = self.base_delay_s * (2 ** attempt)
        if self.jitter:
            delay = delay * (0.5 + random.random() * 0.5)
        return min(delay, self.max_delay_s)

    async def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        last_exception: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                last_exception = exc
                if attempt >= self.max_retries:
                    logger.error(
                        f"RetryPolicy exhausted after {self.max_retries} retries: {exc}"
                    )
                    break

                delay = self._calculate_delay(attempt)
                logger.warning(
                    f"Attempt {attempt + 1} failed ({exc}). Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)

        if last_exception:
            raise last_exception
        raise RuntimeError("RetryPolicy failed unexpectedly")
