"""
Unit tests for financial BM25 lexical search and financial tokenization.
"""

from src.domain.entities import ChunkMetadata, DocumentChunk
from src.retrieval.sparse_bm25 import BM25SearchIndex, FinancialTokenizer


def test_financial_tokenizer_preserves_financial_entities():
    """Verify tokenizer preserves currency, acronyms, and percentages."""
    text = "Apple AAPL reported $383,285M revenue with 2.8% contraction in Item 8."
    tokens = FinancialTokenizer.tokenize(text)

    assert "$383,285" in tokens or "383,285" in tokens or "$383,285m" in tokens
    assert "aapl" in tokens
    assert "2.8%" in tokens
    assert "item" in tokens
    assert "8" in tokens


def test_bm25_search_scoring_and_ranking():
    """Verify BM25 returns exact matching financial chunks with sparse_score."""
    meta1 = ChunkMetadata(
        document_id="doc-apple",
        document_name="apple.pdf",
        page_number=1,
        chunk_index=0,
    )
    c1 = DocumentChunk(
        content="Apple recorded cash from operations of $110,543 million.",
        metadata=meta1,
    )

    meta2 = ChunkMetadata(
        document_id="doc-nvidia",
        document_name="nvidia.pdf",
        page_number=1,
        chunk_index=1,
    )
    c2 = DocumentChunk(
        content="NVIDIA Data Center segment generated $18,400 million in revenue.",
        metadata=meta2,
    )

    index = BM25SearchIndex()
    index.build_index([c1, c2])

    # Search for Apple cash flow
    results = index.search("Apple cash operations $110,543", limit=5)
    assert len(results) >= 1
    assert results[0].metadata.document_id == "doc-apple"
    assert results[0].sparse_score is not None
    assert results[0].sparse_score > 0.0

    # Search with document filter
    filtered = index.search("revenue", document_id="doc-nvidia", limit=5)
    assert len(filtered) == 1
    assert filtered[0].metadata.document_id == "doc-nvidia"

    # Incrementally add new chunk
    meta3 = ChunkMetadata(document_id="doc-meta", document_name="meta.pdf", page_number=2, chunk_index=0)
    c3 = DocumentChunk(content="Meta reality labs revenue was $1,000 million.", metadata=meta3)
    index.add_chunks([c3])
    assert index.count() == 3
    meta_results = index.search("reality labs", limit=1)
    assert len(meta_results) == 1
    assert meta_results[0].metadata.document_id == "doc-meta"
