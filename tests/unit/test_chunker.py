from app.core.constants import ClauseType
from app.pipeline.chunker import Chunker
from app.pipeline.section_detector import Section


def test_chunker_divides_sections():
    chunker = Chunker(chunk_size=100, chunk_overlap=20)
    sections = [
        Section(
            name="Termination",
            page_number=1,
            clause_hint=ClauseType.TERMINATION,
            content="This is a contract clause regarding termination. " * 30,
        ),
        Section(
            name="Governing Law",
            page_number=2,
            clause_hint=ClauseType.GOVERNING_LAW,
            content="This Agreement is governed by the laws of New York.",
        ),
    ]

    chunks = chunker.chunk(sections)

    assert len(chunks) > 1
    # Check that chunks retain section metadata and clause hints
    term_chunks = [c for c in chunks if c.clause_hint == ClauseType.TERMINATION.value]
    law_chunks = [c for c in chunks if c.clause_hint == ClauseType.GOVERNING_LAW.value]

    assert len(term_chunks) >= 1
    assert len(law_chunks) == 1
    assert law_chunks[0].page_number == 2
    assert "New York" in law_chunks[0].content
