import asyncio
import logging
import time
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import ClauseType, ExtractionStatus
from app.core.exceptions import DocumentNotFoundError
from app.llm import get_llm_client
from app.llm.client import LLMClient
from app.models.document import Chunk
from app.models.extraction import ClauseResult, Extraction
from app.pipeline.citation_verifier import CitationVerifier
from app.pipeline.repair_loop import RepairLoop
from app.prompts.registry import PromptRegistry
from app.repositories.document_repository import ChunkRepository, DocumentRepository
from app.repositories.extraction_repository import ExtractionRepository
from app.observability.langfuse_client import LangfuseTracker
from app.repositories.ledger_repository import RunLedgerRepository
from app.retrieval.hybrid_search import HybridSearch
from app.schemas.extraction import (
    ClauseResultDetailSchema,
    ClauseResultSchema,
    ExtractionRequest,
    ExtractionResponse,
)

logger = logging.getLogger(__name__)


class ExtractionService:
    """Service orchestrating hybrid retrieval, structured LLM extraction, repair loops, and citations."""

    def __init__(
        self,
        session: AsyncSession,
        llm_client: LLMClient | None = None,
        prompt_registry: PromptRegistry | None = None,
        citation_verifier: CitationVerifier | None = None,
        repair_loop: RepairLoop | None = None,
        tracker: LangfuseTracker | None = None,
    ):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.chunk_repo = ChunkRepository(session)
        self.extraction_repo = ExtractionRepository(session)
        self.ledger_repo = RunLedgerRepository(session)
        self.hybrid_search = HybridSearch(self.chunk_repo)
        self.llm_client = llm_client or get_llm_client()
        self.prompt_registry = prompt_registry or PromptRegistry()
        self.citation_verifier = citation_verifier or CitationVerifier()
        self.repair_loop = repair_loop or RepairLoop()
        self.tracker = tracker or LangfuseTracker()

    async def extract(
        self, request: ExtractionRequest, request_id: str
    ) -> ExtractionResponse:
        start_time = time.monotonic()

        # 1. Validate document exists
        doc = await self.doc_repo.get_by_id(request.document_id)
        if not doc:
            raise DocumentNotFoundError(f"Document {request.document_id} not found")

        # 2. Load prompt template and compute hash
        prompt_template = self.prompt_registry.load("extraction", request.prompt_version)
        prompt_hash = self.prompt_registry.hash(prompt_template)

        # 3. Check extraction cache
        cached = await self.extraction_repo.get_cached(request.document_id, prompt_hash)
        if cached:
            logger.info(f"Returning cached extraction for document {request.document_id}")
            detail_schemas = [
                ClauseResultDetailSchema(
                    id=cr.id,
                    clause_type=ClauseType(cr.clause_type),
                    is_present=cr.is_present,
                    verbatim_quote=cr.verbatim_quote,
                    summary=cr.summary,
                    page_number=cr.page_number,
                    confidence=float(cr.confidence) if cr.confidence is not None else 1.0,
                    citation_verified=cr.citation_verified,
                    source_chunk_id=cr.source_chunk_id,
                    repair_attempts=cr.repair_attempts,
                    used_fallback=cr.used_fallback,
                )
                for cr in cached.clause_results
            ]
            return ExtractionResponse(
                extraction_id=cached.id,
                document_id=cached.document_id,
                status=cached.status,  # type: ignore[arg-type]
                model_id=cached.model_id,
                prompt_version=cached.prompt_version,
                clause_results=detail_schemas,
                cost_usd=float(cached.total_cost_usd or 0.0),
                input_tokens=cached.total_input_tokens or 0,
                output_tokens=cached.total_output_tokens or 0,
                latency_ms=float(cached.latency_ms or 0.0),
                cache_hit=True,
            )

        # 4. Extract clauses in parallel with concurrency semaphore
        semaphore = asyncio.Semaphore(settings.EXTRACTION_CONCURRENCY_CAP)

        async def _extract_single(ct: ClauseType) -> tuple[ClauseResultDetailSchema, int, int, float]:
            async with semaphore:
                return await self._extract_clause(
                    ct, request.document_id, prompt_template
                )

        tasks = [_extract_single(ct) for ct in request.clause_types]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = 0.0
        clause_details: list[ClauseResultDetailSchema] = []

        for detail, in_tok, out_tok, cost in results:
            clause_details.append(detail)
            total_input_tokens += in_tok
            total_output_tokens += out_tok
            total_cost += cost

        latency_ms = (time.monotonic() - start_time) * 1000

        # 5. Persist Extraction record
        model_name = getattr(self.llm_client, "primary", self.llm_client)
        model_id = getattr(model_name, "model_id", "gemini-2.5-flash")

        extraction = Extraction(
            document_id=request.document_id,
            prompt_version=request.prompt_version,
            prompt_hash=prompt_hash,
            model_id=model_id,
            status=ExtractionStatus.COMPLETED,
            total_cost_usd=Decimal(str(round(total_cost, 6))),
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            latency_ms=Decimal(str(round(latency_ms, 2))),
        )
        saved_extraction = await self.extraction_repo.create(extraction)

        # 6. Persist ClauseResults
        orm_results: list[ClauseResult] = []
        for cd in clause_details:
            orm_results.append(
                ClauseResult(
                    extraction_id=saved_extraction.id,
                    clause_type=cd.clause_type.value,
                    is_present=cd.is_present,
                    verbatim_quote=cd.verbatim_quote,
                    summary=cd.summary,
                    page_number=cd.page_number,
                    confidence=Decimal(str(round(cd.confidence, 3))),
                    citation_verified=cd.citation_verified,
                    source_chunk_id=cd.source_chunk_id,
                    repair_attempts=cd.repair_attempts,
                    used_fallback=cd.used_fallback,
                )
            )
        await self.extraction_repo.add_clause_results(orm_results)

        # Set DB IDs on response schemas
        for schema_item, orm_item in zip(clause_details, orm_results):
            schema_item.id = orm_item.id

        # 7. Log run to Ledger
        await self.ledger_repo.log_run(
            request_id=request_id,
            endpoint="/extract",
            model_id=model_id,
            provider="gemini",
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            cost_usd=total_cost,
            latency_ms=latency_ms,
            document_id=request.document_id,
            cache_hit=False,
            prompt_version=request.prompt_version,
            prompt_hash=prompt_hash,
            metadata={"clause_count": len(request.clause_types)},
        )

        # Flush Langfuse telemetry
        self.tracker.flush()

        return ExtractionResponse(
            extraction_id=saved_extraction.id,
            document_id=request.document_id,
            status=ExtractionStatus.COMPLETED,
            model_id=model_id,
            prompt_version=request.prompt_version,
            clause_results=clause_details,
            cost_usd=round(total_cost, 6),
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            latency_ms=round(latency_ms, 2),
            cache_hit=False,
        )

    async def _extract_clause(
        self,
        clause_type: ClauseType,
        document_id: uuid.UUID,
        prompt_template: str,
    ) -> tuple[ClauseResultDetailSchema, int, int, float]:
        # 1. Hybrid retrieval for candidate chunks
        async with self.tracker.trace_span(
            name=f"retrieval:{clause_type.value}",
            input={"query": clause_type.value, "document_id": str(document_id)},
            metadata={"strategy": "hybrid"},
        ) as ret_span:
            candidate_chunks: list[Chunk] = await self.hybrid_search.search(
                query=clause_type.value.replace("_", " "),
                document_id=document_id,
                clause_filter=clause_type.value,
                limit=settings.RETRIEVAL_TOP_K,
            )
            if ret_span and hasattr(ret_span, "update"):
                ret_span.update(output={"chunk_count": len(candidate_chunks)})

        # 2. Build context
        if candidate_chunks:
            context_str = "\n\n---\n\n".join(
                f"[Chunk #{c.chunk_index} | Page {c.page_number}]\n{c.content}"
                for c in candidate_chunks
            )
        else:
            context_str = "No specific sections found matching this clause."

        prompt = prompt_template.format(
            clause_type=clause_type.value,
            context=context_str,
        )

        # 3. Call RepairLoop with LLMClient
        model_name = getattr(self.llm_client, "primary", self.llm_client)
        model_id = getattr(model_name, "model_id", "gemini-flash-lite-latest")

        async with self.tracker.trace_generation(
            name=f"llm_extraction:{clause_type.value}",
            model=model_id,
            input=prompt,
        ) as gen_span:
            parsed, response, repair_attempts, used_fallback = await self.repair_loop.execute(
                llm_client=self.llm_client,
                prompt=prompt,
                schema=ClauseResultSchema,
            )
            if gen_span and hasattr(gen_span, "update"):
                gen_span.update(
                    output=response.content,
                    usage_details={"input": response.input_tokens, "output": response.output_tokens},
                    metadata={"cost_usd": response.cost_usd, "repair_attempts": repair_attempts},
                )

        # 4. Programmatic citation verification
        verified = False
        source_chunk_id: uuid.UUID | None = None
        if parsed.is_present and parsed.verbatim_quote:
            async with self.tracker.trace_span(
                name=f"citation_verification:{clause_type.value}",
                input={"quote": parsed.verbatim_quote},
            ) as cit_span:
                verified, source_chunk_id = self.citation_verifier.verify(
                    parsed.verbatim_quote, candidate_chunks
                )
                if cit_span and hasattr(cit_span, "update"):
                    cit_span.update(output={"verified": verified, "chunk_id": str(source_chunk_id) if source_chunk_id else None})

        detail = ClauseResultDetailSchema(
            clause_type=clause_type,
            is_present=parsed.is_present,
            verbatim_quote=parsed.verbatim_quote,
            summary=parsed.summary,
            page_number=parsed.page_number,
            confidence=parsed.confidence,
            citation_verified=verified,
            source_chunk_id=source_chunk_id,
            repair_attempts=repair_attempts,
            used_fallback=used_fallback,
        )
        return detail, response.input_tokens, response.output_tokens, response.cost_usd
