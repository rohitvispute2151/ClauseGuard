import hashlib
import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DocumentStatus
from app.core.exceptions import DocumentNotFoundError, DocumentProcessingError
from app.models.document import Chunk, Document
from app.pipeline.chunker import Chunker
from app.pipeline.pdf_parser import PDFParser
from app.pipeline.section_detector import SectionDetector
from app.repositories.document_repository import ChunkRepository, DocumentRepository
from app.retrieval.embeddings import EmbeddingClient

logger = logging.getLogger(__name__)


class IngestService:
    """Service for contract PDF parsing, section detection, chunking, and embedding."""

    def __init__(
        self,
        session: AsyncSession,
        pdf_parser: PDFParser | None = None,
        section_detector: SectionDetector | None = None,
        chunker: Chunker | None = None,
        embedding_client: EmbeddingClient | None = None,
    ):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.chunk_repo = ChunkRepository(session)
        self.pdf_parser = pdf_parser or PDFParser()
        self.section_detector = section_detector or SectionDetector()
        self.chunker = chunker or Chunker()
        self.embedding_client = embedding_client or EmbeddingClient()

    async def ingest(
        self, file_bytes: bytes, filename: str
    ) -> tuple[Document, bool, str | None]:
        """
        Idempotent ingest: hashes content, checks DB, creates record.
        Returns (document, already_exists, job_id).
        """
        content_hash = hashlib.sha256(file_bytes).hexdigest()

        # Check idempotency
        existing = await self.doc_repo.get_by_hash(content_hash)
        if existing:
            logger.info(f"Document with hash {content_hash} already exists: {existing.id}")
            return existing, True, None

        # Create new document record
        document = Document(
            filename=filename,
            content_hash=content_hash,
            status=DocumentStatus.PENDING,
            metadata_={"file_size_bytes": len(file_bytes)},
        )
        created_doc = await self.doc_repo.create(document)

        # Dispatch async task or execute locally if celery is not running
        job_id = f"job-{uuid.uuid4()}"
        try:
            from app.workers.tasks.ingest import ingest_document_task
            ingest_document_task.delay(str(created_doc.id), file_bytes.hex())
        except Exception as exc:
            logger.warning(f"Could not dispatch Celery task ({exc}). Running inline processing...")
            await self.process_document(created_doc.id, file_bytes)

        return created_doc, False, job_id

    async def process_document(
        self, document_id: uuid.UUID, file_bytes: bytes
    ) -> Document:
        """
        Core ingestion pipeline: PDF parse -> sections -> chunking -> embeddings -> DB store.
        """
        doc = await self.doc_repo.get_by_id(document_id)
        if not doc:
            raise DocumentNotFoundError(f"Document {document_id} not found")

        await self.doc_repo.update_status(document_id, DocumentStatus.PROCESSING)

        try:
            # 1. Parse PDF
            pages = self.pdf_parser.parse(file_bytes)
            raw_text = "\n\n".join(p.content for p in pages)

            # 2. Detect Sections
            sections = self.section_detector.detect(pages)

            # 3. Chunk
            chunk_data_list = self.chunker.chunk(sections)

            # 4. Generate Embeddings (batch)
            contents = [c.content for c in chunk_data_list]
            embeddings = await self.embedding_client.embed_batch(contents)

            # 5. Build Chunk ORM records
            chunks: list[Chunk] = []
            for cd, emb in zip(chunk_data_list, embeddings):
                chunks.append(
                    Chunk(
                        document_id=document_id,
                        chunk_index=cd.chunk_index,
                        content=cd.content,
                        embedding=emb,
                        page_number=cd.page_number,
                        section_name=cd.section_name,
                        clause_hint=cd.clause_hint,
                        token_count=cd.token_count,
                        metadata_=cd.metadata,
                    )
                )

            # 6. Bulk persist chunks
            await self.chunk_repo.bulk_create(chunks)

            # 7. Update document status
            updated_doc = await self.doc_repo.update_status(
                document_id,
                DocumentStatus.COMPLETED,
                total_pages=len(pages),
                total_chunks=len(chunks),
                raw_text=raw_text,
            )
            logger.info(
                f"Successfully ingested document {document_id}: {len(pages)} pages, {len(chunks)} chunks"
            )
            return updated_doc or doc

        except Exception as exc:
            logger.error(f"Failed to process document {document_id}: {exc}", exc_info=True)
            await self.doc_repo.update_status(
                document_id, DocumentStatus.FAILED, error_message=str(exc)
            )
            raise DocumentProcessingError(f"Document processing failed: {exc}") from exc
