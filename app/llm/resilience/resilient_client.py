import logging
from collections.abc import AsyncIterator
from typing import TypeVar
from pydantic import BaseModel

from app.core.exceptions import CircuitOpenError, LLMProviderError
from app.core.messages import MSG_PROVIDER_FAILURE
from app.llm.client import LLMClient, LLMResponse
from app.llm.resilience.circuit_breaker import CircuitBreaker
from app.llm.resilience.rate_limiter import RateLimiter
from app.llm.resilience.retry import RetryPolicy

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class ResilientLLMClient(LLMClient):
    """
    Coordinates primary (Google Gemini) and fallback (Groq) providers
    with circuit breakers, retry with exponential backoff & jitter, and rate limiting.
    """

    def __init__(
        self,
        primary: LLMClient,
        fallback: LLMClient,
        retry_policy: RetryPolicy | None = None,
        primary_circuit: CircuitBreaker | None = None,
        fallback_circuit: CircuitBreaker | None = None,
        rate_limiter: RateLimiter | None = None,
    ):
        self.primary = primary
        self.fallback = fallback
        self.retry_policy = retry_policy or RetryPolicy()
        self.primary_circuit = primary_circuit or CircuitBreaker(name="gemini_primary")
        self.fallback_circuit = fallback_circuit or CircuitBreaker(name="groq_fallback")
        self.rate_limiter = rate_limiter or RateLimiter()

    async def generate(
        self, prompt: str, system: str | None = None, max_tokens: int = 4096
    ) -> LLMResponse:
        # Check rate limit
        await self.rate_limiter.acquire(key="global_llm")

        # Attempt primary with retry and circuit breaker
        try:
            return await self.retry_policy.execute(
                self.primary_circuit.call,
                self.primary.generate,
                prompt=prompt,
                system=system,
                max_tokens=max_tokens,
            )
        except (CircuitOpenError, LLMProviderError, Exception) as primary_exc:
            logger.warning(
                f"Primary provider (Gemini) failed: {primary_exc}. Failing over to Groq..."
            )

        # Attempt fallback with circuit breaker
        try:
            return await self.retry_policy.execute(
                self.fallback_circuit.call,
                self.fallback.generate,
                prompt=prompt,
                system=system,
                max_tokens=max_tokens,
            )
        except Exception as fallback_exc:
            logger.error(f"Fallback provider (Groq) also failed: {fallback_exc}")
            raise LLMProviderError(MSG_PROVIDER_FAILURE) from fallback_exc

    async def generate_structured(
        self, prompt: str, schema: type[T], system: str | None = None
    ) -> tuple[T, LLMResponse]:
        await self.rate_limiter.acquire(key="global_llm")

        try:
            return await self.retry_policy.execute(
                self.primary_circuit.call,
                self.primary.generate_structured,
                prompt=prompt,
                schema=schema,
                system=system,
            )
        except (CircuitOpenError, LLMProviderError, Exception) as primary_exc:
            logger.warning(
                f"Primary structured generation failed ({primary_exc}). Failing over to Groq..."
            )

        try:
            return await self.retry_policy.execute(
                self.fallback_circuit.call,
                self.fallback.generate_structured,
                prompt=prompt,
                schema=schema,
                system=system,
            )
        except Exception as fallback_exc:
            logger.error(f"Fallback structured generation also failed: {fallback_exc}")
            raise LLMProviderError(MSG_PROVIDER_FAILURE) from fallback_exc

    async def stream(
        self, prompt: str, system: str | None = None
    ) -> AsyncIterator[str]:
        await self.rate_limiter.acquire(key="global_llm")

        # Try primary stream
        if not self.primary_circuit.is_open():
            try:
                async for token in self.primary.stream(prompt=prompt, system=system):
                    yield token
                self.primary_circuit._on_success()
                return
            except Exception as exc:
                self.primary_circuit._on_failure()
                logger.warning(f"Primary stream failed ({exc}), falling over to Groq...")

        # Fallback stream
        if not self.fallback_circuit.is_open():
            try:
                async for token in self.fallback.stream(prompt=prompt, system=system):
                    yield token
                self.fallback_circuit._on_success()
                return
            except Exception as exc:
                self.fallback_circuit._on_failure()
                logger.error(f"Fallback stream also failed: {exc}")
                raise LLMProviderError(MSG_PROVIDER_FAILURE) from exc

        raise LLMProviderError(MSG_PROVIDER_FAILURE)
