import uuid
from datetime import datetime
from typing import Any
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.core.database import Base
from app.core.config import settings


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="PENDING", index=True
    )
    total_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_chunks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, server_default=text("'{}'::jsonb"), nullable=False, default=dict
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="Chunk.chunk_index"
    )
    extractions: Mapped[list["Extraction"]] = relationship(
        "Extraction", back_populates="document", cascade="all, delete-orphan"
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(settings.EMBEDDING_DIMENSION), nullable=True
    )
    fts_vector: Mapped[Any | None] = mapped_column(TSVECTOR, nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_name: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    clause_hint: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, server_default=text("'{}'::jsonb"), nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    document: Mapped["Document"] = relationship(back_populates="chunks")

    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk_index"),
        Index("ix_chunks_fts_vector", "fts_vector", postgresql_using="gin"),
    )
