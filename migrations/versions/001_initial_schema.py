"""Initial ClauseGuard schema with pgvector and FTS

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-10-06 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 1. documents table
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("total_pages", sa.Integer(), nullable=True),
        sa.Column("total_chunks", sa.Integer(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_documents_content_hash", "documents", ["content_hash"], unique=True)
    op.create_index("ix_documents_status", "documents", ["status"])

    # 2. chunks table
    op.create_table(
        "chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(384), nullable=True),
        sa.Column("fts_vector", postgresql.TSVECTOR(), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section_name", sa.String(256), nullable=True),
        sa.Column("clause_hint", sa.String(128), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk_index"),
    )
    op.create_index("ix_chunks_document_id", "chunks", ["document_id"])
    op.create_index("ix_chunks_section_name", "chunks", ["section_name"])
    op.create_index("ix_chunks_clause_hint", "chunks", ["clause_hint"])

    # 3. extractions table
    op.create_table(
        "extractions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prompt_version", sa.String(32), nullable=False),
        sa.Column("prompt_hash", sa.String(64), nullable=False),
        sa.Column("model_id", sa.String(128), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("total_cost_usd", sa.Numeric(10, 6), nullable=True),
        sa.Column("total_input_tokens", sa.Integer(), nullable=True),
        sa.Column("total_output_tokens", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Numeric(10, 2), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_extractions_document_id", "extractions", ["document_id"])
    op.create_index("ix_extractions_cache", "extractions", ["document_id", "prompt_hash"])

    # 4. clause_results table
    op.create_table(
        "clause_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("extraction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("extractions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clause_type", sa.String(64), nullable=False),
        sa.Column("is_present", sa.Boolean(), nullable=False),
        sa.Column("verbatim_quote", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("citation_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("source_chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chunks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("repair_attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("used_fallback", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_clause_results_extraction_id", "clause_results", ["extraction_id"])
    op.create_index("ix_clause_results_clause_type", "clause_results", ["clause_type"])

    # 5. run_ledger table
    op.create_table(
        "run_ledger",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("endpoint", sa.String(64), nullable=False),
        sa.Column("model_id", sa.String(128), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=False, server_default="0.0"),
        sa.Column("latency_ms", sa.Numeric(10, 2), nullable=False, server_default="0.0"),
        sa.Column("cache_hit", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("prompt_version", sa.String(32), nullable=True),
        sa.Column("prompt_hash", sa.String(64), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_run_ledger_request_id", "run_ledger", ["request_id"])
    op.create_index("ix_run_ledger_created_at", "run_ledger", ["created_at"])


def downgrade() -> None:
    op.drop_table("run_ledger")
    op.drop_table("clause_results")
    op.drop_table("extractions")
    op.drop_table("chunks")
    op.drop_table("documents")
