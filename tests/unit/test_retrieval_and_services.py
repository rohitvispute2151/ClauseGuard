import uuid
import pytest
from app.core.constants import ClauseType
from app.llm.client import LLMClient, LLMResponse
from app.models.document import Chunk, Document
from app.prompts.registry import PromptRegistry
from app.retrieval.context_assembler import ContextAssembler
from app.retrieval.embeddings import EmbeddingClient
from app.retrieval.hybrid_search import HybridSearch
from app.schemas.extraction import ClauseResultSchema, ExtractionRequest
from app.schemas.question import AskRequest
from app.services.extraction_service import ExtractionService
from app.services.query_service import QueryService


class MockLLMClient(LLMClient):
    """Mock LLM client returning compliant structured extraction and streaming."""

    async def generate(self, prompt, system=None, max_tokens=4096):
        return LLMResponse(
            content="Mocked answer citing \"Either party may terminate upon 30 days written notice\".",
            input_tokens=100,
            output_tokens=30,
            model_id="gemini-2.5-flash",
            provider="gemini",
            latency_ms=120.0,
        )

    async def generate_structured(self, prompt, schema, system=None):
        instance = ClauseResultSchema(
            clause_type=ClauseType.TERMINATION,
            is_present=True,
            verbatim_quote="Either party may terminate upon 30 days written notice.",
            summary="30 days termination without cause.",
            page_number=1,
            confidence=0.98,
        )
        return instance, LLMResponse(
            content="{}",
            input_tokens=150,
            output_tokens=45,
            model_id="gemini-2.5-flash",
            provider="gemini",
            latency_ms=180.0,
        )

    async def stream(self, prompt, system=None):
        tokens = [
            "Based ", "on ", "Section ", "2, ", "the ", "agreement ", "states: ",
            "\"Either party may terminate upon 30 days written notice\"."
        ]
        for t in tokens:
            yield t


def test_embedding_client_deterministic_and_normalized():
    client = EmbeddingClient(dimension=384)
    v1 = client._compute_embedding("Termination and liability caps")
    v2 = client._compute_embedding("Termination and liability caps")
    v3 = client._compute_embedding("Completely different governing law clause")

    assert len(v1) == 384
    assert v1 == v2  # Deterministic
    assert v1 != v3  # Differentiable


def test_context_assembler_budget_limit():
    assembler = ContextAssembler(max_tokens=50)
    chunks = [
        Chunk(id=uuid.uuid4(), document_id=uuid.uuid4(), chunk_index=0, content="Small first chunk.", page_number=1, token_count=10),
        Chunk(id=uuid.uuid4(), document_id=uuid.uuid4(), chunk_index=1, content="Second chunk.", page_number=1, token_count=20),
        Chunk(id=uuid.uuid4(), document_id=uuid.uuid4(), chunk_index=2, content="This third chunk would exceed fifty token budget." * 10, page_number=2, token_count=100),
    ]

    context = assembler.assemble(chunks)
    assert "Small first chunk." in context
    assert "Second chunk." in context
    assert "exceed fifty token" not in context


def test_prompt_registry_hashing():
    registry = PromptRegistry()
    template = registry.load("extraction", "v2")
    h = registry.hash(template)
    assert len(h) == 16
    assert isinstance(h, str)
