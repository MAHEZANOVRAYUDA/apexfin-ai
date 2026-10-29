"""
Unit tests for Reciprocal Rank Fusion (RRF).
"""

from src.domain.entities import ChunkMetadata, DocumentChunk
from src.retrieval.fusion import reciprocal_rank_fusion


def test_reciprocal_rank_fusion_consensus_boost():
    """Verify chunk present in both dense and sparse arms gets highest RRF boost."""
    meta = ChunkMetadata(
        document_id="doc-1",
        document_name="test.pdf",
        page_number=1,
        chunk_index=0,
    )

    c_consensus = DocumentChunk(chunk_id="chunk-shared", content="Consensus chunk", metadata=meta)
    c_dense_only = DocumentChunk(chunk_id="chunk-dense", content="Dense only", metadata=meta)
    c_sparse_only = DocumentChunk(chunk_id="chunk-sparse", content="Sparse only", metadata=meta)

    # Rank lists:
    # Dense: [c_consensus (rank 0), c_dense_only (rank 1)]
    # Sparse: [c_consensus (rank 0), c_sparse_only (rank 1)]
    dense_list = [c_consensus, c_dense_only]
    sparse_list = [c_consensus, c_sparse_only]

    fused = reciprocal_rank_fusion(dense_list, sparse_list, k=60, limit=10)

    assert len(fused) == 3
    # Consensus chunk should rank first because it accumulated reciprocal scores from both
    assert fused[0].chunk_id == "chunk-shared"
    # RRF score for rank 0 on both: (1/61) + (1/61) ~ 0.032787
    expected_score = round((1.0 / 61.0) + (1.0 / 61.0), 6)
    assert fused[0].rrf_score == expected_score


def test_reciprocal_rank_fusion_empty_inputs():
    """Verify RRF handles empty candidate lists gracefully."""
    assert reciprocal_rank_fusion([], [], k=60) == []
