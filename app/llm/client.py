from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    content: str
    input_tokens: int
    output_tokens: int
    model_id: str
    provider: str
    latency_ms: float
    cost_usd: float = 0.0


class LLMClient(ABC):
    """Abstract Base Class for all LLM providers."""

    @abstractmethod
    async def generate(
        self, prompt: str, system: str | None = None, max_tokens: int = 4096
    ) -> LLMResponse:
        """Generate a standard text completion."""
        pass

    @abstractmethod
    async def generate_structured(
        self, prompt: str, schema: type[T], system: str | None = None
    ) -> tuple[T, LLMResponse]:
        """Generate structured output validated against a Pydantic schema."""
        pass

    @abstractmethod
    async def stream(
        self, prompt: str, system: str | None = None
    ) -> AsyncIterator[str]:
        """Stream response tokens asynchronously."""
        pass
