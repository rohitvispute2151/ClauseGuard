import json
import logging
import time
from collections.abc import AsyncIterator
from typing import TypeVar
import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import LLMProviderError
from app.llm.client import LLMClient, LLMResponse
from app.llm.cost import calculate_cost

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class GroqProvider(LLMClient):
    """
    Fallback LLM provider using Groq (FreeLLM.net).
    Provides ultra-low latency LPU inference with Llama 3.3 70B and standard OpenAI compatibility.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_id: str | None = None,
        base_url: str | None = None,
    ):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model_id = model_id or settings.GROQ_MODEL_ID
        self.base_url = (base_url or settings.GROQ_BASE_URL).rstrip("/")
        self.provider_name = "groq"

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def generate(
        self, prompt: str, system: str | None = None, max_tokens: int = 4096
    ) -> LLMResponse:
        start_time = time.monotonic()
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.1,
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
            except Exception as exc:
                raise LLMProviderError(f"Groq API error: {exc}") from exc

        latency_ms = (time.monotonic() - start_time) * 1000
        choice = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        in_tokens = usage.get("prompt_tokens", len(prompt) // 4)
        out_tokens = usage.get("completion_tokens", len(choice) // 4)

        return LLMResponse(
            content=choice,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            model_id=self.model_id,
            provider=self.provider_name,
            latency_ms=round(latency_ms, 2),
            cost_usd=calculate_cost(self.model_id, in_tokens, out_tokens),
        )

    async def generate_structured(
        self, prompt: str, schema: type[T], system: str | None = None
    ) -> tuple[T, LLMResponse]:
        schema_json = json.dumps(schema.model_json_schema())
        schema_instruction = (
            f"\nYou MUST respond with valid JSON adhering strictly to this schema:\n{schema_json}"
        )
        augmented_prompt = prompt + schema_instruction

        start_time = time.monotonic()
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": augmented_prompt})

        payload = {
            "model": self.model_id,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
            except Exception as exc:
                raise LLMProviderError(f"Groq structured generation failed: {exc}") from exc

        latency_ms = (time.monotonic() - start_time) * 1000
        content_str = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        in_tokens = usage.get("prompt_tokens", len(augmented_prompt) // 4)
        out_tokens = usage.get("completion_tokens", len(content_str) // 4)

        parsed_data = json.loads(content_str)
        validated_model = schema.model_validate(parsed_data)

        llm_response = LLMResponse(
            content=content_str,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            model_id=self.model_id,
            provider=self.provider_name,
            latency_ms=round(latency_ms, 2),
            cost_usd=calculate_cost(self.model_id, in_tokens, out_tokens),
        )
        return validated_model, llm_response

    async def stream(
        self, prompt: str, system: str | None = None
    ) -> AsyncIterator[str]:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_id,
            "messages": messages,
            "stream": True,
            "temperature": 0.2,
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise LLMProviderError(f"Groq stream error ({response.status_code}): {error_text.decode()}")

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk["choices"][0].get("delta", {})
                            token = delta.get("content", "")
                            if token:
                                yield token
                        except Exception:
                            continue
