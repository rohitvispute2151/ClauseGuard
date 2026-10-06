import uuid
from typing import Any
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.document import Document, Chunk
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """SQLAlchemy 2.0 repository for Document entities."""

    def __init__(self, session: AsyncSession):
        super().__init__(Document, session)

    async def get_by_hash(self, content_hash: str) -> Document | None:
        stmt = select(Document).where(Document.content_hash == content_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_chunks(self, document_id: uuid.UUID) -> Document | None:
        stmt = (
            select(Document)
            .where(Document.id == document_id)
            .options(selectinload(Document.chunks))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(
        self, document_id: uuid.UUID, status: str, **kwargs: Any
    ) -> Document | None:
        values = {"status": status, **kwargs}
        stmt = (
            update(Document)
            .where(Document.id == document_id)
            .values(**values)
            .returning(Document)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one_or_none()


class ChunkRepository(BaseRepository[Chunk]):
    """SQLAlchemy 2.0 repository for Chunk entities, supporting vector & FTS retrieval."""

    def __init__(self, session: AsyncSession):
        super().__init__(Chunk, session)

    async def bulk_create(self, chunks: list[Chunk]) -> list[Chunk]:
        self.session.add_all(chunks)
        await self.session.commit()
        return chunks

    async def get_by_document(self, document_id: uuid.UUID) -> list[Chunk]:
        stmt = (
            select(Chunk)
            .where(Chunk.document_id == document_id)
            .order_by(Chunk.chunk_index)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def vector_search(
        self,
        embedding: list[float],
        document_id: uuid.UUID,
        clause_filter: str | None = None,
        limit: int = 10,
    ) -> list[Chunk]:
        """Cosine distance vector search using pgvector."""
        stmt = select(Chunk).where(Chunk.document_id == document_id)
        if clause_filter:
            stmt = stmt.where(Chunk.clause_hint == clause_filter)

        # Distance operator <=> for cosine distance
        if hasattr(Chunk.embedding, "cosine_distance"):
            stmt = stmt.order_by(Chunk.embedding.cosine_distance(embedding)).limit(limit)
        else:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def fts_search(
        self,
        query: str,
        document_id: uuid.UUID,
        clause_filter: str | None = None,
        limit: int = 10,
    ) -> list[Chunk]:
        """PostgreSQL Full-Text Search using plainto_tsquery and ts_rank."""
        stmt = select(Chunk).where(Chunk.document_id == document_id)
        if clause_filter:
            stmt = stmt.where(Chunk.clause_hint == clause_filter)

        # Fallback ILIKE / tsquery match
        try:
            tsquery = func.plainto_tsquery("english", query)
            stmt = (
                stmt.where(Chunk.fts_vector.op("@@")(tsquery))
                .order_by(func.ts_rank(Chunk.fts_vector, tsquery).desc())
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            chunks = list(result.scalars().all())
            if chunks:
                return chunks
        except Exception:
            pass

        # Fallback ILIKE search if FTS has no matches or before indexing
        fallback_stmt = (
            select(Chunk)
            .where(Chunk.document_id == document_id)
            .where(Chunk.content.ilike(f"%{query[:50]}%"))
            .limit(limit)
        )
        fallback_res = await self.session.execute(fallback_stmt)
        return list(fallback_res.scalars().all())
