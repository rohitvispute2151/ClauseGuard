import logging
import time
from collections.abc import Callable
from typing import Any

from app.core.config import settings
from app.core.constants import CircuitState
from app.core.exceptions import CircuitOpenError

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Three-state circuit breaker: CLOSED -> OPEN -> HALF_OPEN."""

    def __init__(
        self,
        name: str,
        failure_threshold: int | None = None,
        recovery_timeout_s: float | None = None,
    ):
        self.name = name
        self.failure_threshold = (
            failure_threshold or settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD
        )
        self.recovery_timeout_s = (
            recovery_timeout_s or settings.CIRCUIT_BREAKER_RECOVERY_S
        )
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0

    def is_open(self) -> bool:
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            if (time.monotonic() - self.last_failure_time) > self.recovery_timeout_s:
                logger.info(
                    f"CircuitBreaker [{self.name}] transition: OPEN -> HALF_OPEN"
                )
                self.state = CircuitState.HALF_OPEN
                return False
            return True
        return False

    async def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        if self.is_open():
            raise CircuitOpenError(f"CircuitBreaker [{self.name}] is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as exc:
            self._on_failure()
            raise exc

    def _on_success(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"CircuitBreaker [{self.name}] recovered: HALF_OPEN -> CLOSED")
            self.state = CircuitState.CLOSED
        self.failure_count = 0

    def _on_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if (
            self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)
            and self.failure_count >= self.failure_threshold
        ):
            logger.warning(
                f"CircuitBreaker [{self.name}] tripped: -> OPEN (failures: {self.failure_count})"
            )
            self.state = CircuitState.OPEN
