import json
import logging
from typing import TypeVar
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.core.exceptions import ExtractionValidationError
from app.llm.client import LLMClient, LLMResponse

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class RepairLoop:
    """
    Orchestrates structured output validation and automatic repair loop.
    Malformed JSON -> re-prompt with error message -> fallback model -> typed error.
    """

    def __init__(self, max_repairs: int | None = None):
        self.max_repairs = max_repairs or settings.MAX_REPAIR_ATTEMPTS

    async def execute(
        self,
        llm_client: LLMClient,
        prompt: str,
        schema: type[T],
        system: str | None = None,
    ) -> tuple[T, LLMResponse, int, bool]:
        """
        Executes structured generation with repair loop.
        Returns (parsed_schema, last_response, repair_attempts, used_fallback).
        """
        current_prompt = prompt
        attempts = 0
        used_fallback = False

        for attempt in range(self.max_repairs + 1):
            try:
                validated_model, response = await llm_client.generate_structured(
                    prompt=current_prompt,
                    schema=schema,
                    system=system,
                )
                return validated_model, response, attempts, used_fallback

            except (ValidationError, json.JSONDecodeError, Exception) as exc:
                attempts += 1
                logger.warning(
                    f"Structured validation attempt {attempt + 1} failed: {exc}"
                )

                if attempt < self.max_repairs:
                    # Construct repair prompt showing the error
                    current_prompt = (
                        f"{prompt}\n\n"
                        f"IMPORTANT: Your previous output failed schema validation with error:\n"
                        f"{str(exc)}\n\n"
                        f"Please rectify the mistake and output ONLY the valid JSON object."
                    )
                else:
                    # Final attempt: trigger fallback if resilient client has one
                    if hasattr(llm_client, "fallback"):
                        logger.info("Attempting fallback provider for repair loop...")
                        try:
                            validated_model, response = await llm_client.fallback.generate_structured(
                                prompt=current_prompt,
                                schema=schema,
                                system=system,
                            )
                            used_fallback = True
                            return validated_model, response, attempts, used_fallback
                        except Exception as fallback_exc:
                            logger.error(f"Fallback repair also failed: {fallback_exc}")

        raise ExtractionValidationError(
            f"Failed to extract structured data conforming to {schema.__name__} after {attempts} attempts."
        )
