"""
Unit tests for QdrantVectorStore in-memory integration.
"""

from src.domain.entities import ChunkMetadata, DocumentChunk
from src.retrieval.embedder import MockEmbedder
from src.retrieval.qdrant_client import QdrantVectorStore


def test_qdrant_in_memory_upsert_and_search():
    """Verify QdrantVectorStore indexes and retrieves chunks with cosine score."""
    store = QdrantVectorStore(url=":memory:", collection_name="test_collection")
    embedder = MockEmbedder(vector_dim=384)

    meta1 = ChunkMetadata(
        document_id="doc-apple",
        document_name="apple_10k.pdf",
        page_number=5,
        chunk_index=0,
    )
    chunk1 = DocumentChunk(
        chunk_id="550e8400-e29b-41d4-a716-446655440000",
        content="Apple gross margin increased due to services growth.",
        metadata=meta1,
    )

    meta2 = ChunkMetadata(
        document_id="doc-tesla",
        document_name="tesla_10k.pdf",
        page_number=10,
        chunk_index=1,
    )
    chunk2 = DocumentChunk(
        chunk_id="550e8400-e29b-41d4-a716-446655440001",
        content="Tesla automotive regulatory credits revenue.",
        metadata=meta2,
    )

    chunks = [chunk1, chunk2]
    embeddings = embedder.embed_documents([c.content for c in chunks])

    store.upsert_chunks(chunks, embeddings)
    assert store.count() == 2

    # Query for Apple
    query_vec = embedder.embed_query("Apple gross margin")
    results = store.search(query_vec, limit=2)

    assert len(results) == 2
    assert results[0].metadata.document_id == "doc-apple"
    assert results[0].dense_score is not None

    # Filtered search
    tesla_only = store.search(query_vec, limit=2, document_id="doc-tesla")
    assert len(tesla_only) == 1
    assert tesla_only[0].metadata.document_id == "doc-tesla"

    # Delete Apple
    store.delete_document("doc-apple")
    assert store.count() == 1

    # Verify get_all_chunks returns remaining chunks
    remaining = store.get_all_chunks()
    assert len(remaining) == 1
    assert remaining[0].metadata.document_id == "doc-tesla"
