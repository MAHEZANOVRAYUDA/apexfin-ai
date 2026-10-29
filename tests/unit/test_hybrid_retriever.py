"""
Unit tests for end-to-end HybridRetriever pipeline.
"""

from src.domain.entities import ChunkMetadata, DocumentChunk
from src.retrieval.embedder import MockEmbedder
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.qdrant_client import QdrantVectorStore
from src.retrieval.reranker import MockReranker
from src.retrieval.sparse_bm25 import BM25SearchIndex


def test_hybrid_retriever_indexing_and_retrieval():
    """Verify end-to-end multi-arm indexing and hybrid retrieval."""
    vector_store = QdrantVectorStore(url=":memory:", collection_name="hybrid_test_col")
    embedder = MockEmbedder(vector_dim=384)
    bm25 = BM25SearchIndex()
    reranker = MockReranker(default_limit=2)

    retriever = HybridRetriever(
        vector_store=vector_store,
        embedder=embedder,
        bm25_index=bm25,
        reranker=reranker,
    )

    meta1 = ChunkMetadata(
        document_id="doc-nvda-2024",
        document_name="nvidia_10k.pdf",
        page_number=12,
        chunk_index=0,
    )
    chunk1 = DocumentChunk(
        chunk_id="550e8400-e29b-41d4-a716-446655440101",
        content="NVIDIA Data Center revenue was $18,400 million, up 217% year-on-year.",
        metadata=meta1,
    )

    meta2 = ChunkMetadata(
        document_id="doc-nvda-2024",
        document_name="nvidia_10k.pdf",
        page_number=14,
        chunk_index=1,
    )
    chunk2 = DocumentChunk(
        chunk_id="550e8400-e29b-41d4-a716-446655440102",
        content="Gaming revenue was $2,856 million, up 81% year-on-year.",
        metadata=meta2,
    )

    # 1. Index chunks
    indexed_count = retriever.index_document_chunks([chunk1, chunk2])
    assert indexed_count == 2
    assert vector_store.count() == 2
    assert bm25.count() == 2

    # 2. Retrieve with financial query
    results = retriever.retrieve("What was NVIDIA Data Center revenue $18,400 million?", limit=1)
    assert len(results) == 1
    assert results[0].metadata.chunk_index == 0
    assert "Data Center" in results[0].content
    assert results[0].rerank_score is not None
