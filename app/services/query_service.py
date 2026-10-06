import json
import logging
import re
import time
import uuid
from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DocumentNotFoundError
from app.core.messages import MSG_NOT_FOUND_IN_DOCUMENT
from app.llm import get_llm_client
from app.llm.client import LLMClient
from app.pipeline.citation_verifier import CitationVerifier
from app.prompts.registry import PromptRegistry
from app.repositories.document_repository import ChunkRepository, DocumentRepository
from app.repositories.ledger_repository import RunLedgerRepository
from app.retrieval.context_assembler import ContextAssembler
from app.retrieval.hybrid_search import HybridSearch
from app.schemas.question import AskRequest, CitationSchema

logger = logging.getLogger(__name__)


class QueryService:
    """Service handling grounded contract Q&A with SSE streaming and citation verification."""

    def __init__(
        self,
        session: AsyncSession,
        llm_client: LLMClient | None = None,
        prompt_registry: PromptRegistry | None = None,
        citation_verifier: CitationVerifier | None = None,
        context_assembler: ContextAssembler | None = None,
    ):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.chunk_repo = ChunkRepository(session)
        self.ledger_repo = RunLedgerRepository(session)
        self.hybrid_search = HybridSearch(self.chunk_repo)
        self.llm_client = llm_client or get_llm_client()
        self.prompt_registry = prompt_registry or PromptRegistry()
        self.citation_verifier = citation_verifier or CitationVerifier()
        self.context_assembler = context_assembler or ContextAssembler()

    async def ask_stream(
        self, request: AskRequest, request_id: str
    ) -> AsyncIterator[dict[str, str]]:
        start_time = time.monotonic()

        # 1. Verify document exists
        doc = await self.doc_repo.get_by_id(request.document_id)
        if not doc:
            raise DocumentNotFoundError(f"Document {request.document_id} not found")

        # 2. Hybrid retrieval
        chunks = await self.hybrid_search.search(
            query=request.question,
            document_id=request.document_id,
            limit=8,
        )

        if not chunks:
            yield {
                "event": "token",
                "data": json.dumps({"data": MSG_NOT_FOUND_IN_DOCUMENT}),
            }
            yield {
                "event": "done",
                "data": json.dumps({
                    "cost_usd": 0.0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "latency_ms": round((time.monotonic() - start_time) * 1000, 2),
                }),
            }
            return

        # 3. Assemble context
        context_str = self.context_assembler.assemble(chunks)

        # 4. Load and format prompt
        prompt_template = self.prompt_registry.load("qa", "v1")
        prompt = prompt_template.format(
            context=context_str,
            question=request.question,
        )

        # 5. Stream LLM tokens
        full_response = ""
        output_tokens = 0

        async for token in self.llm_client.stream(prompt):
            full_response += token
            output_tokens += 1
            yield {
                "event": "token",
                "data": json.dumps({"data": token}),
            }

        # 6. Extract quotes and verify citations
        citations = self._extract_citations(full_response, chunks)
        yield {
            "event": "citations",
            "data": json.dumps(
                {"citations": [c.model_dump(mode="json") for c in citations]},
                default=str,
            ),
        }

        # 7. Complete telemetry & ledger
        latency_ms = (time.monotonic() - start_time) * 1000
        input_tokens = len(prompt) // 4

        model_name = getattr(self.llm_client, "primary", self.llm_client)
        model_id = getattr(model_name, "model_id", "gemini-flash-lite-latest")

        await self.ledger_repo.log_run(
            request_id=request_id,
            endpoint="/ask",
            model_id=model_id,
            provider="gemini",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=0.0,
            latency_ms=latency_ms,
            document_id=request.document_id,
        )

        yield {
            "event": "done",
            "data": json.dumps({
                "cost_usd": 0.0,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_ms": round(latency_ms, 2),
            }),
        }

    def _extract_citations(
        self, text: str, candidate_chunks: list
    ) -> list[CitationSchema]:
        """Extracts quoted text in the generated answer and verifies against retrieved chunks."""
        citations: list[CitationSchema] = []
        quotes = re.findall(r'"([^"]{15,})"', text)

        for quote in set(quotes):
            verified, chunk_id = self.citation_verifier.verify(quote, candidate_chunks)
            matching_chunk = next((c for c in candidate_chunks if c.id == chunk_id), None)
            page_number = matching_chunk.page_number if matching_chunk else None

            citations.append(
                CitationSchema(
                    quote=quote,
                    page_number=page_number,
                    chunk_id=chunk_id,
                    verified=verified,
                )
            )

        return citations
