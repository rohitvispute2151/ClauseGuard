from app.llm.client import LLMClient, LLMResponse
from app.llm.providers.gemini import GeminiProvider
from app.llm.providers.groq import GroqProvider
from app.llm.resilience.resilient_client import ResilientLLMClient

_default_client: ResilientLLMClient | None = None


def get_llm_client() -> ResilientLLMClient:
    """Singleton factory for resilient LLM client with Gemini primary and Groq fallback."""
    global _default_client
    if _default_client is None:
        primary = GeminiProvider()
        fallback = GroqProvider()
        _default_client = ResilientLLMClient(primary=primary, fallback=fallback)
    return _default_client


__all__ = [
    "LLMClient",
    "LLMResponse",
    "GeminiProvider",
    "GroqProvider",
    "ResilientLLMClient",
    "get_llm_client",
]
