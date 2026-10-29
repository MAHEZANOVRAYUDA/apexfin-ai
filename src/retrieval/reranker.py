"""
Cross-Encoder Re-Ranking module for ApexFin AI.
Scores query-chunk text pairs jointly to eliminate false positive candidates.
"""

from abc import ABC, abstractmethod
from typing import Any

from src.config.settings import get_settings
from src.domain.entities import DocumentChunk


class BaseReranker(ABC):
    """Abstract interface for re-ranking retrieved candidate chunks."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: list[DocumentChunk],
        limit: int | None = None,
    ) -> list[DocumentChunk]:
        """Reranks candidate chunks with respect to query."""


class CrossEncoderReranker(BaseReranker):
    """
    Joint cross-encoder scoring using ms-marco-MiniLM-L-6-v2.
    Evaluates full cross-attention between query tokens and chunk content.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model: Any = None
        settings = get_settings()
        self.default_limit = settings.TOP_RERANK_LIMIT

    def _init_model(self) -> None:
        if self._model is not None:
            return
        try:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name, device="cpu")
        except Exception as exc:
            raise RuntimeError(
                f"Failed to initialize CrossEncoder with model '{self.model_name}': {exc}"
            ) from exc

    def rerank(
        self,
        query: str,
        candidates: list[DocumentChunk],
        limit: int | None = None,
    ) -> list[DocumentChunk]:
        """Re-ranks candidate chunks and assigns rerank_score."""
        if not candidates or not query.strip():
            return []

        top_limit = limit or self.default_limit
        if len(candidates) <= 1:
            candidates[0].rerank_score = 1.0
            return candidates[:top_limit]

        self._init_model()
        pairs = [(query, chunk.content) for chunk in candidates]
        scores = self._model.predict(pairs)

        reranked_chunks: list[DocumentChunk] = []
        for chunk, score in zip(candidates, scores, strict=False):
            # Clone and assign rerank score
            cloned = chunk.model_copy(deep=True)
            # Sigmoid or normalized score if negative logits
            cloned.rerank_score = round(float(score), 4)
            reranked_chunks.append(cloned)

        reranked_chunks.sort(key=lambda c: c.rerank_score or 0.0, reverse=True)
        return reranked_chunks[:top_limit]


class MockReranker(BaseReranker):
    """
    Deterministic reranker for offline unit tests.
    Calculates overlap and preserves test determinism.
    """

    def __init__(self, default_limit: int = 5):
        self.default_limit = default_limit

    def rerank(
        self,
        query: str,
        candidates: list[DocumentChunk],
        limit: int | None = None,
    ) -> list[DocumentChunk]:
        if not candidates:
            return []

        top_limit = limit or self.default_limit
        query_words = set(query.lower().split())

        scored: list[DocumentChunk] = []
        for chunk in candidates:
            cloned = chunk.model_copy(deep=True)
            chunk_words = set(cloned.content.lower().split())
            overlap = len(query_words.intersection(chunk_words))
            base_score = cloned.rrf_score or 0.5
            cloned.rerank_score = round(base_score + (overlap * 0.1), 4)
            scored.append(cloned)

        scored.sort(key=lambda c: c.rerank_score or 0.0, reverse=True)
        return scored[:top_limit]
