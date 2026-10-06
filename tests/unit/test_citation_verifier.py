import uuid
import pytest
from app.models.document import Chunk
from app.pipeline.citation_verifier import CitationVerifier


def test_citation_verifier_exact_match():
    verifier = CitationVerifier(similarity_threshold=0.80)
    chunk_id = uuid.uuid4()
    chunks = [
        Chunk(
            id=chunk_id,
            document_id=uuid.uuid4(),
            chunk_index=0,
            content="Either party may terminate this Agreement upon thirty (30) days prior written notice to the other party.",
        )
    ]

    quote = "Either party may terminate this Agreement upon thirty (30) days prior written notice"
    verified, matched_id = verifier.verify(quote, chunks)

    assert verified is True
    assert matched_id == chunk_id


def test_citation_verifier_fuzzy_match():
    verifier = CitationVerifier(similarity_threshold=0.80)
    chunk_id = uuid.uuid4()
    chunks = [
        Chunk(
            id=chunk_id,
            document_id=uuid.uuid4(),
            chunk_index=0,
            content="In no event shall either party's aggregate liability exceed the total fees paid under this Agreement in the preceding 12 months.",
        )
    ]

    # Slight whitespace / minor typo variant
    quote = "in no event shall either party's aggregate liability exceed total fees paid under this agreement in preceding 12 months"
    verified, matched_id = verifier.verify(quote, chunks)

    assert verified is True
    assert matched_id == chunk_id


def test_citation_verifier_rejects_hallucination():
    verifier = CitationVerifier(similarity_threshold=0.80)
    chunks = [
        Chunk(
            id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            chunk_index=0,
            content="This Agreement shall be governed by and construed in accordance with the laws of the State of California.",
        )
    ]

    # Completely fabricated quote
    fake_quote = "The Vendor shall indemnify and hold harmless the Customer against all damages up to $10,000,000."
    verified, matched_id = verifier.verify(fake_quote, chunks)

    assert verified is False
    assert matched_id is None


def test_citation_verifier_handles_empty_quote():
    verifier = CitationVerifier()
    verified, matched_id = verifier.verify("", [])
    assert verified is False
    assert matched_id is None
