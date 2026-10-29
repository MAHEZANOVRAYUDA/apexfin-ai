"""
Unified Hybrid Retriever orchestrator for ApexFin AI.
Coordinates Dense Vector Search, BM25 Lexical Inverted Index, RRF, and Cross-Encoder Re-Ranking.
"""

from src.config.settings import get_settings
from src.domain.entities import DocumentChunk
from src.retrieval.embedder import BaseEmbedder, FastEmbedder
from src.retrieval.fusion import reciprocal_rank_fusion
from src.retrieval.qdrant_client import QdrantVectorStore
from src.retrieval.reranker import BaseReranker, CrossEncoderReranker
from src.retrieval.sparse_bm25 import BM25SearchIndex


class HybridRetriever:
    """
    Two-stage hybrid retrieval engine:
    Stage 1: Multi-arm candidate retrieval (Dense Vector + BM25 Lexical) -> Reciprocal Rank Fusion (RRF).
    Stage 2: Cross-Encoder joint scoring -> Top-K context for LLM synthesis.
    """

    def __init__(
        self,
        vector_store: QdrantVectorStore | None = None,
        embedder: BaseEmbedder | None = None,
        bm25_index: BM25SearchIndex | None = None,
        reranker: BaseReranker | None = None,
    ):
        settings = get_settings()
        self.vector_store = vector_store or QdrantVectorStore()
        self.embedder = embedder or FastEmbedder()
        self.bm25_index = bm25_index or BM25SearchIndex()
        self.reranker = reranker or CrossEncoderReranker()

        self.candidate_limit = settings.MAX_RETRIEVAL_CANDIDATES
        self.top_k_limit = settings.TOP_RERANK_LIMIT

    def index_document_chunks(self, chunks: list[DocumentChunk]) -> int:
        """
        Indexes a collection of DocumentChunks simultaneously into Qdrant and the BM25 index.
        Returns total chunks indexed.
        """
        if not chunks:
            return 0

        # 1. Generate dense vectors
        contents = [chunk.content for chunk in chunks]
        embeddings = self.embedder.embed_documents(contents)

        # 2. Upsert into Qdrant Vector Store
        self.vector_store.upsert_chunks(chunks, embeddings)

        # 3. Add to BM25 Inverted Index
        self.bm25_index.add_chunks(chunks)

        return len(chunks)

    def retrieve(
        self,
        query: str,
        document_id: str | None = None,
        limit: int | None = None,
    ) -> list[DocumentChunk]:
        """
        Executes end-to-end hybrid retrieval:
        1. Dense retrieval via Qdrant
        2. Sparse retrieval via BM25
        3. Reciprocal Rank Fusion (RRF)
        4. Cross-Encoder Re-Ranking
        """
        if not query.strip():
            return []

        final_limit = limit or self.top_k_limit

        # Step 1: Dense Vector arm
        query_vector = self.embedder.embed_query(query)
        dense_candidates = self.vector_store.search(
            query_vector=query_vector,
            limit=self.candidate_limit,
            document_id=document_id,
        )

        # Step 2: Sparse BM25 arm
        sparse_candidates = self.bm25_index.search(
            query=query,
            limit=self.candidate_limit,
            document_id=document_id,
        )

        # Step 3: Reciprocal Rank Fusion (RRF)
        fused_candidates = reciprocal_rank_fusion(
            dense_results=dense_candidates,
            sparse_results=sparse_candidates,
            k=60,
            limit=self.candidate_limit * 2,
        )

        if not fused_candidates:
            return []

        # Step 4: Cross-Encoder Re-ranking
        return self.reranker.rerank(
            query=query,
            candidates=fused_candidates,
            limit=final_limit,
        )
