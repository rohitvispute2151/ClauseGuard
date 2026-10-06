import re
import uuid
from rapidfuzz import fuzz
from app.core.config import settings
from app.models.document import Chunk


class CitationVerifier:
    """
    Programmatic citation verifier.
    Checks whether a verbatim quote from LLM extraction or Q&A exists in candidate source chunks.
    """

    def __init__(self, similarity_threshold: float | None = None):
        self.threshold = (
            similarity_threshold or settings.CITATION_SIMILARITY_THRESHOLD
        ) * 100.0

    def verify(
        self, quote: str | None, chunks: list[Chunk]
    ) -> tuple[bool, uuid.UUID | None]:
        """
        Verifies if quote exists in candidate chunks.
        Returns (is_verified: bool, source_chunk_id: uuid.UUID | None).
        """
        if not quote or not quote.strip() or not chunks:
            return False, None

        normalized_quote = self._normalize(quote)
        if len(normalized_quote) < 5:
            return False, None

        best_score = 0.0
        best_chunk_id: uuid.UUID | None = None

        for chunk in chunks:
            normalized_chunk = self._normalize(chunk.content)

            # Fast path: exact substring
            if normalized_quote in normalized_chunk:
                return True, chunk.id

            # Slow path: RapidFuzz partial ratio
            score = fuzz.partial_ratio(normalized_quote, normalized_chunk)
            if score > best_score:
                best_score = score
                best_chunk_id = chunk.id

        is_verified = best_score >= self.threshold
        return is_verified, best_chunk_id if is_verified else None

    def _normalize(self, text: str) -> str:
        """Collapse whitespace, lowercase, and normalize punctuation quotes."""
        text = text.lower()
        text = re.sub(r'[""\'`]', '"', text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
