from dataclasses import dataclass, field
from app.core.config import settings
from app.core.constants import ClauseType
from app.pipeline.section_detector import Section


@dataclass
class ChunkData:
    chunk_index: int
    content: str
    page_number: int
    section_name: str
    clause_hint: str | None
    token_count: int
    metadata: dict = field(default_factory=dict)


class Chunker:
    """Section-aware chunker that divides sections into size-bounded overlapping chunks."""

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    def chunk(self, sections: list[Section]) -> list[ChunkData]:
        chunks: list[ChunkData] = []
        global_index = 0

        for section in sections:
            words = section.content.split()
            if not words:
                continue

            # Estimate ~1.3 tokens per word, or roughly words // 1.3
            words_per_chunk = max(50, int(self.chunk_size * 0.75))
            words_overlap = max(10, int(self.chunk_overlap * 0.75))

            if len(words) <= words_per_chunk:
                content = " ".join(words)
                chunks.append(
                    ChunkData(
                        chunk_index=global_index,
                        content=content,
                        page_number=section.page_number,
                        section_name=section.name,
                        clause_hint=section.clause_hint.value if section.clause_hint else None,
                        token_count=len(words),
                        metadata={"words": len(words)},
                    )
                )
                global_index += 1
            else:
                step = words_per_chunk - words_overlap
                for i in range(0, len(words), step):
                    chunk_words = words[i : i + words_per_chunk]
                    if not chunk_words:
                        break
                    content = " ".join(chunk_words)
                    chunks.append(
                        ChunkData(
                            chunk_index=global_index,
                            content=content,
                            page_number=section.page_number,
                            section_name=section.name,
                            clause_hint=section.clause_hint.value if section.clause_hint else None,
                            token_count=len(chunk_words),
                            metadata={"words": len(chunk_words), "start_offset": i},
                        )
                    )
                    global_index += 1

        return chunks
