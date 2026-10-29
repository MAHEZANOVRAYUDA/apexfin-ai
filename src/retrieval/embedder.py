"""
Embedding generation adapter for ApexFin AI.
Generates 384-dimensional dense vectors for semantic similarity search.
"""

import math
import re
from abc import ABC, abstractmethod
from typing import Any


class BaseEmbedder(ABC):
    """Abstract interface for dense vector embedding models."""

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generates dense embeddings for a batch of text chunks."""

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Generates dense embedding for a single user query."""


class FastEmbedder(BaseEmbedder):
    """
    Lightweight embedding provider using FastEmbed ONNX or SentenceTransformers
    as fallback, defaulting to BAAI/bge-small-en-v1.5 (384 dimensions).
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model_name = model_name
        self._backend: Any = None
        self._backend_type: str = "uninitialized"

    def _init_backend(self) -> None:
        if self._backend is not None:
            return

        # Attempt 1: FastEmbed ONNX
        try:
            from fastembed import TextEmbedding

            self._backend = TextEmbedding(model_name=self.model_name)
            self._backend_type = "fastembed"
            return
        except (ImportError, Exception):
            pass

        # Attempt 2: SentenceTransformer (already installed and verified)
        try:
            from sentence_transformers import SentenceTransformer

            # Use local cache / fast CPU model
            self._backend = SentenceTransformer(self.model_name, device="cpu")
            self._backend_type = "sentence_transformers"
            return
        except Exception as exc:
            raise RuntimeError(
                f"Failed to initialize dense embedder '{self.model_name}'. "
                "Ensure either fastembed or sentence-transformers is installed."
            ) from exc

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embeds a list of document chunks into 384-dim normalized vectors."""
        if not texts:
            return []
        self._init_backend()

        if self._backend_type == "fastembed":
            embeddings = list(self._backend.embed(texts))
            return [e.tolist() if hasattr(e, "tolist") else list(e) for e in embeddings]

        # SentenceTransformers fallback
        embeddings = self._backend.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return [e.tolist() if hasattr(e, "tolist") else list(e) for e in embeddings]

    def embed_query(self, text: str) -> list[float]:
        """Embeds a single query string."""
        return self.embed_documents([text])[0]


class MockEmbedder(BaseEmbedder):
    """
    Deterministic pseudo-embedding generator for fast, 100% offline unit tests.
    Produces fixed 384-dimensional unit vectors based on token hashing.
    """

    def __init__(self, vector_dim: int = 384):
        self.vector_dim = vector_dim

    def _hash_to_vector(self, text: str) -> list[float]:
        words = re.findall(r"\w+", text.lower())
        vec = [0.0] * self.vector_dim
        if not words:
            vec[0] = 1.0
            return vec

        for word in words:
            h = hash(word) % self.vector_dim
            vec[h] += 1.0

        # L2 Normalize
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        else:
            vec[0] = 1.0
        return vec

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._hash_to_vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._hash_to_vector(text)
