import asyncio
import logging
import uuid
from app.core.database import bypass_session_factory
from app.services.ingest_service import IngestService
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="clauseguard.ingest_document",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def ingest_document_task(self, document_id_str: str, file_hex: str) -> dict:
    """Celery background task for asynchronous PDF ingestion."""
    doc_id = uuid.UUID(document_id_str)
    file_bytes = bytes.fromhex(file_hex)

    async def _run():
        async with bypass_session_factory() as session:
            service = IngestService(session)
            await service.process_document(document_id=doc_id, file_bytes=file_bytes)

    try:
        asyncio.run(_run())
        return {"status": "COMPLETED", "document_id": document_id_str}
    except Exception as exc:
        logger.error(f"Celery task ingest_document failed: {exc}", exc_info=True)
        raise self.retry(exc=exc)
