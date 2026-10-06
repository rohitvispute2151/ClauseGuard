import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ledger import RunLedger
from app.repositories.base import BaseRepository


class RunLedgerRepository(BaseRepository[RunLedger]):
    """SQLAlchemy 2.0 repository for RunLedger cost and token tracking."""

    def __init__(self, session: AsyncSession):
        super().__init__(RunLedger, session)

    async def log_run(
        self,
        request_id: str,
        endpoint: str,
        model_id: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float | Decimal,
        latency_ms: float | Decimal,
        document_id: uuid.UUID | None = None,
        cache_hit: bool = False,
        prompt_version: str | None = None,
        prompt_hash: str | None = None,
        metadata: dict | None = None,
    ) -> RunLedger:
        ledger_entry = RunLedger(
            document_id=document_id,
            request_id=request_id,
            endpoint=endpoint,
            model_id=model_id,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=Decimal(str(cost_usd)),
            latency_ms=Decimal(str(latency_ms)),
            cache_hit=cache_hit,
            prompt_version=prompt_version,
            prompt_hash=prompt_hash,
            metadata_=metadata or {},
        )
        return await self.create(ledger_entry)
