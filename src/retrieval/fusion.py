"""
Reciprocal Rank Fusion (RRF) algorithm for ApexFin AI.
Fuses heterogeneous ranking lists from dense vector search and BM25 lexical search.
"""

from collections import defaultdict

from src.domain.entities import DocumentChunk


def reciprocal_rank_fusion(
    dense_results: list[DocumentChunk],
    sparse_results: list[DocumentChunk],
    k: int = 60,
    limit: int = 50,
) -> list[DocumentChunk]:
    """
    Fuses two ranked result lists into a single consensus ranking using Reciprocal Rank Fusion.

    RRF Score formula for document d:
        RRF(d) = sum_{m in {dense, sparse}} (1 / (k + rank_m(d)))

    Args:
        dense_results: Ranked candidates from semantic vector search (0-indexed).
        sparse_results: Ranked candidates from BM25 lexical search (0-indexed).
        k: Smoothing constant preventing high-rank domination (default 60).
        limit: Maximum number of fused candidate chunks to return.

    Returns:
        List of merged DocumentChunk objects ordered by rrf_score descending.
    """
    rrf_scores: dict[str, float] = defaultdict(float)
    chunk_store: dict[str, DocumentChunk] = {}

    # 1. Process Dense Vector Rankings
    for rank, chunk in enumerate(dense_results):
        cid = chunk.chunk_id
        rrf_scores[cid] += 1.0 / (k + rank + 1)
        if cid not in chunk_store:
            chunk_store[cid] = chunk.model_copy(deep=True)
        else:
            chunk_store[cid].dense_score = chunk.dense_score

    # 2. Process Sparse BM25 Rankings
    for rank, chunk in enumerate(sparse_results):
        cid = chunk.chunk_id
        rrf_scores[cid] += 1.0 / (k + rank + 1)
        if cid not in chunk_store:
            chunk_store[cid] = chunk.model_copy(deep=True)
        else:
            chunk_store[cid].sparse_score = chunk.sparse_score

    # 3. Assign final RRF score and sort
    fused_candidates: list[DocumentChunk] = []
    for cid, combined_score in rrf_scores.items():
        chunk = chunk_store[cid]
        chunk.rrf_score = round(combined_score, 6)
        fused_candidates.append(chunk)

    fused_candidates.sort(key=lambda c: c.rrf_score or 0.0, reverse=True)
    return fused_candidates[:limit]
