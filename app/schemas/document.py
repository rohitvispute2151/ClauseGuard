import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict


class DocumentUploadResponse(BaseModel):
    """Response returned upon POST /documents upload."""
    document_id: uuid.UUID
    job_id: str | None
    status: Literal["PENDING", "ALREADY_EXISTS"]
    message: str

    model_config = ConfigDict(from_attributes=True)


class DocumentStatusResponse(BaseModel):
    """Response returned upon GET /documents/{id}."""
    id: uuid.UUID
    filename: str
    content_hash: str
    status: Literal["PENDING", "PROCESSING", "COMPLETED", "FAILED", "ALREADY_EXISTS"]
    total_pages: int | None
    total_chunks: int | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
