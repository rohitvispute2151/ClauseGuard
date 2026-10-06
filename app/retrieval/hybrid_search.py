import uuid
from collections import defaultdict
from app.core.config import settings
from app.core.constants import RRF_K
from app.models.document import Chunk
from app.repositories.document_repository import ChunkRepository
from app.retrieval.embeddings import EmbeddingClient


class HybridSearch:
    """
    Hybrid retrieval engine combining pgvector vector search and PostgreSQL FTS
    via Reciprocal Rank Fusion (RRF).
    """

    def __init__(
        self,
        chunk_repo: ChunkRepository,
        embedding_client: EmbeddingClient | None = None,
        rrf_k: int = RRF_K,
    ):
        self.chunk_repo = chunk_repo
        self.embedding_client = embedding_client or EmbeddingClient()
        self.rrf_k = rrf_k

    async def search(
        self,
        query: str,
        document_id: uuid.UUID,
        clause_filter: str | None = None,
        limit: int | None = None,
    ) -> list[Chunk]:
        search_limit = limit or settings.RETRIEVAL_TOP_K

        # 1. Vector Search
        query_embedding = await self.embedding_client.embed_single(query)
        vector_chunks = await self.chunk_repo.vector_search(
            embedding=query_embedding,
            document_id=document_id,
            clause_filter=clause_filter,
            limit=search_limit * 2,
        )

        # 2. Full-Text Search
        fts_chunks = await self.chunk_repo.fts_search(
            query=query,
            document_id=document_id,
            clause_filter=clause_filter,
            limit=search_limit * 2,
        )

        # 3. Reciprocal Rank Fusion
        fused_chunks = self._rrf_fuse(vector_chunks, fts_chunks)

        return fused_chunks[:search_limit]

    def _rrf_fuse(
        self, vector_chunks: list[Chunk], fts_chunks: list[Chunk]
    ) -> list[Chunk]:
        """
        RRF algorithm: score = sum(1.0 / (k + rank)) across ranking channels.
        """
        scores: dict[uuid.UUID, float] = defaultdict(float)
        chunk_map: dict[uuid.UUID, Chunk] = {}

        for rank, chunk in enumerate(vector_chunks):
            scores[chunk.id] += 1.0 / (self.rrf_k + rank + 1)
            chunk_map[chunk.id] = chunk

        for rank, chunk in enumerate(fts_chunks):
            scores[chunk.id] += 1.0 / (self.rrf_k + rank + 1)
            chunk_map[chunk.id] = chunk

        sorted_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)
        return [chunk_map[cid] for cid in sorted_ids]
