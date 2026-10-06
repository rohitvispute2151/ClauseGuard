import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.extraction import Extraction, ClauseResult
from app.repositories.base import BaseRepository


class ExtractionRepository(BaseRepository[Extraction]):
    """SQLAlchemy 2.0 repository for Extraction entities."""

    def __init__(self, session: AsyncSession):
        super().__init__(Extraction, session)

    async def get_with_clauses(self, extraction_id: uuid.UUID) -> Extraction | None:
        stmt = (
            select(Extraction)
            .where(Extraction.id == extraction_id)
            .options(selectinload(Extraction.clause_results))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_cached(
        self, document_id: uuid.UUID, prompt_hash: str
    ) -> Extraction | None:
        """Find recent completed extraction matching (document_id, prompt_hash)."""
        stmt = (
            select(Extraction)
            .where(Extraction.document_id == document_id)
            .where(Extraction.prompt_hash == prompt_hash)
            .where(Extraction.status == "COMPLETED")
            .options(selectinload(Extraction.clause_results))
            .order_by(Extraction.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_clause_results(
        self, clause_results: list[ClauseResult]
    ) -> list[ClauseResult]:
        self.session.add_all(clause_results)
        await self.session.commit()
        return clause_results
