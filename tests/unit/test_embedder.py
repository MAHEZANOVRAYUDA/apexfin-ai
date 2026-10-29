"""
Unit tests for dense vector embedder implementations in ApexFin AI.
"""

from src.retrieval.embedder import MockEmbedder


def test_mock_embedder_dimensions_and_normalization():
    """Verify MockEmbedder outputs normalized 384-dimensional vectors."""
    embedder = MockEmbedder(vector_dim=384)
    docs = [
        "Apple Inc reported quarterly revenue of $89.5 billion.",
        "NVIDIA gross margin expanded to 75.0% in Q3.",
    ]
    vectors = embedder.embed_documents(docs)

    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    assert len(vectors[1]) == 384

    # Verify L2 unit length (norm ~ 1.0)
    norm0 = sum(x * x for x in vectors[0]) ** 0.5
    assert abs(norm0 - 1.0) < 1e-4


def test_mock_embedder_query():
    """Verify single query vector generation."""
    embedder = MockEmbedder(vector_dim=384)
    q_vec = embedder.embed_query("What was total net sales?")
    assert len(q_vec) == 384
    assert abs(sum(x * x for x in q_vec) ** 0.5 - 1.0) < 1e-4
