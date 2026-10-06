from app.core.config import settings
from app.models.document import Chunk


class ContextAssembler:
    """Assembles retrieved chunks into context string within a token budget."""

    def __init__(self, max_tokens: int | None = None):
        self.max_tokens = max_tokens or settings.CONTEXT_TOKEN_BUDGET

    def assemble(self, chunks: list[Chunk]) -> str:
        selected_sections: list[str] = []
        accumulated_tokens = 0

        for chunk in chunks:
            # Approximate token count if not saved
            tokens = chunk.token_count or (len(chunk.content.split()) * 4 // 3)
            if accumulated_tokens + tokens > self.max_tokens:
                break

            header = f"[Page {chunk.page_number or '?'}"
            if chunk.section_name:
                header += f" | Section: {chunk.section_name}"
            header += f" | Chunk #{chunk.chunk_index}]"

            selected_sections.append(f"{header}\n{chunk.content}")
            accumulated_tokens += tokens

        return "\n\n---\n\n".join(selected_sections)
