import uuid
from typing import Literal
from pydantic import BaseModel, Field

from app.core.constants import MAX_QUESTION_LENGTH, MIN_QUESTION_LENGTH


class AskRequest(BaseModel):
    """Request payload for POST /ask."""
    document_id: uuid.UUID
    question: str = Field(
        ...,
        min_length=MIN_QUESTION_LENGTH,
        max_length=MAX_QUESTION_LENGTH,
        description="Legal or procurement question regarding the contract.",
    )


class CitationSchema(BaseModel):
    """Verified citation extracted from answer context."""
    quote: str
    page_number: int | None = None
    chunk_id: uuid.UUID | None = None
    verified: bool = False


class SSETokenEvent(BaseModel):
    """Token chunk streamed over Server-Sent Events."""
    data: str


class SSECitationEvent(BaseModel):
    """Citations event sent when streaming finishes."""
    citations: list[CitationSchema]


class SSEDoneEvent(BaseModel):
    """Final telemetry event indicating completion of stream."""
    cost_usd: float
    input_tokens: int
    output_tokens: int
    latency_ms: float


class SSEErrorEvent(BaseModel):
    """Error event sent over stream if an error occurs."""
    message: str
