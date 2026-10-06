from app.models import Document
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Extraction(Base):
    __tablename__ = "extractions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    total_cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    total_input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    document: Mapped["Document"] = relationship("Document", back_populates="extractions")
    clause_results: Mapped[list["ClauseResult"]] = relationship(
        back_populates="extraction", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_extractions_cache", "document_id", "prompt_hash"),
    )


class ClauseResult(Base):
    __tablename__ = "clause_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    extraction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("extractions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clause_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    is_present: Mapped[bool] = mapped_column(Boolean, nullable=False)
    verbatim_quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    citation_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false"), default=False
    )
    source_chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chunks.id", ondelete="SET NULL"), nullable=True
    )
    repair_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), default=0
    )
    used_fallback: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false"), default=False
    )
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, server_default=text("'{}'::jsonb"), nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    extraction: Mapped["Extraction"] = relationship(back_populates="clause_results")
