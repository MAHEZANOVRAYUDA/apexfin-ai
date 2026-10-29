"""
Unit tests for Reranker components.
"""

from src.domain.entities import ChunkMetadata, DocumentChunk
from src.retrieval.reranker import MockReranker


def test_mock_reranker_scoring():
    """Verify MockReranker assigns rerank_score based on query text relevance."""
    meta = ChunkMetadata(
        document_id="doc-1",
        document_name="test.pdf",
        page_number=1,
        chunk_index=0,
    )
    c1 = DocumentChunk(
        chunk_id="c1",
        content="Capital expenditures for fiscal 2023 were $10 billion.",
        metadata=meta,
    )
    c2 = DocumentChunk(
        chunk_id="c2",
        content="General corporate governance and board elections.",
        metadata=meta,
    )

    reranker = MockReranker(default_limit=2)
    reranked = reranker.rerank(
        query="What were capital expenditures?",
        candidates=[c2, c1],
    )

    assert len(reranked) == 2
    # c1 has higher lexical query overlap so it should rank first
    assert reranked[0].chunk_id == "c1"
    assert reranked[0].rerank_score is not None
    assert reranked[0].rerank_score > reranked[1].rerank_score
