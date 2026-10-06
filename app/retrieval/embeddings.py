import hashlib
import math
from app.core.config import settings


class EmbeddingClient:
    """
    Embedding generator.
    Produces dense embedding vectors normalized to unit length.
    Uses deterministic feature projection for reliable local operation and zero API cost.
    """

    def __init__(self, dimension: int | None = None):
        self.dimension = dimension or settings.EMBEDDING_DIMENSION

    async def embed_single(self, text: str) -> list[float]:
        return self._compute_embedding(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self._compute_embedding(t) for t in texts]

    def _compute_embedding(self, text: str) -> list[float]:
        """
        Computes a deterministic dense float vector of specified dimension
        by hash-n-gram projection with L2 normalization.
        """
        vec = [0.0] * self.dimension
        words = text.lower().split()
        if not words:
            return vec

        for word in words:
            # Hash word into dimension index and sign
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if (h >> 32) % 2 == 0 else -1.0
            vec[idx] += sign

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [round(x / norm, 6) for x in vec]

        return vec
