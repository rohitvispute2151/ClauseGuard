import uuid
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import ClauseType


class ExtractionRequest(BaseModel):
    """Request payload for POST /extract."""
    document_id: uuid.UUID
    clause_types: list[ClauseType] = Field(
        default_factory=lambda: list(ClauseType),
        description="List of clause types to extract. Defaults to all 10 standard clauses."
    )
    prompt_version: str = Field(default="v2", description="Prompt template version to use")


class ClauseResultSchema(BaseModel):
    """The structured output schema targeted by the LLM."""
    clause_type: ClauseType
    is_present: bool
    verbatim_quote: str | None = Field(
        default=None,
        description="Exact quote from the contract text. Must be verbatim from source."
    )
    summary: str | None = Field(
        default=None,
        description="Plain-language concise summary of what this clause entails."
    )
    page_number: int | None = Field(
        default=None,
        description="Page number where the clause appears in the contract."
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Model confidence score between 0.0 and 1.0."
    )


class ClauseResultDetailSchema(ClauseResultSchema):
    """Detail schema returned to clients with programmatic verification flags."""
    id: uuid.UUID | None = None
    citation_verified: bool = False
    source_chunk_id: uuid.UUID | None = None
    repair_attempts: int = 0
    used_fallback: bool = False

    model_config = ConfigDict(from_attributes=True)


class ExtractionResponse(BaseModel):
    """Response returned upon POST /extract and GET /extractions/{id}."""
    extraction_id: uuid.UUID
    document_id: uuid.UUID
    status: Literal["COMPLETED", "PARTIAL", "FAILED"]
    model_id: str
    prompt_version: str
    clause_results: list[ClauseResultDetailSchema]
    cost_usd: float
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cache_hit: bool

    model_config = ConfigDict(from_attributes=True)
