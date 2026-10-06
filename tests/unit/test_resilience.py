import pytest
import asyncio
from app.core.constants import CircuitState
from app.core.exceptions import CircuitOpenError
from app.llm.resilience.circuit_breaker import CircuitBreaker
from app.llm.resilience.rate_limiter import RateLimiter
from app.llm.resilience.retry import RetryPolicy


@pytest.mark.asyncio
async def test_circuit_breaker_trips_to_open():
    cb = CircuitBreaker(name="test", failure_threshold=3, recovery_timeout_s=1.0)
    assert cb.state == CircuitState.CLOSED

    async def failing_func():
        raise ValueError("Simulated network error")

    for _ in range(3):
        with pytest.raises(ValueError):
            await cb.call(failing_func)

    # Now circuit breaker must be open
    assert cb.state == CircuitState.OPEN
    assert cb.is_open() is True

    # Calling it raises CircuitOpenError immediately without invoking func
    with pytest.raises(CircuitOpenError):
        await cb.call(failing_func)


@pytest.mark.asyncio
async def test_retry_policy_eventual_success():
    attempts = 0
    policy = RetryPolicy(max_retries=3, base_delay_s=0.01, max_delay_s=0.05, jitter=False)

    async def flaky_func():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ConnectionError("Temporary connection drop")
        return "SUCCESS"

    result = await policy.execute(flaky_func)
    assert result == "SUCCESS"
    assert attempts == 3


@pytest.mark.asyncio
async def test_rate_limiter_in_memory_bucket():
    limiter = RateLimiter(max_tokens=3, refill_rate=1.0)

    # Acquire 3 tokens
    ok1, _ = await limiter.acquire("test-client", 1)
    ok2, _ = await limiter.acquire("test-client", 1)
    ok3, _ = await limiter.acquire("test-client", 1)
    assert ok1 and ok2 and ok3

    # 4th acquisition must be rejected
    ok4, retry_after = await limiter.acquire("test-client", 1)
    assert ok4 is False
    assert retry_after > 0.0
