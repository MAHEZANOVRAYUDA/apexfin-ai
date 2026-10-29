"""
Sparse lexical search engine for ApexFin AI using BM25Plus.
Specialized for exact matching of financial metrics, regulatory items, and ticker codes.
"""

import re

from rank_bm25 import BM25Plus

from src.domain.entities import DocumentChunk


class FinancialTokenizer:
    """
    Financial-aware lexical tokenizer.
    Preserves currency figures ($10,000), percentages (12.5%), acronyms (EBITDA),
    negative accounting figures, and SEC regulatory tags (Item 8).
    """

    TOKEN_REGEX = re.compile(
        r"[$€£¥]?\d+(?:[,\.]\d+)*%?|\b[A-Za-z]+-[0-9A-Za-z]+\b|\b[A-Za-z0-9_]+\b",
        re.UNICODE,
    )

    @classmethod
    def tokenize(cls, text: str) -> list[str]:
        """Tokenizes text while preserving financial syntax."""
        if not text:
            return []
        matches = [m.group(0) for m in cls.TOKEN_REGEX.finditer(text)]
        return [m.lower().strip() for m in matches if m.strip()]


class BM25SearchIndex:
    """
    Inverted index using BM25Plus for exact keyword retrieval on financial chunks.
    BM25Plus prevents the negative/zero IDF issue present in Okapi on small collections.
    Complements dense vector embeddings in the hybrid retrieval pipeline.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunks: list[DocumentChunk] = []
        self.tokenized_corpus: list[list[str]] = []
        self.bm25: BM25Plus | None = None

    def build_index(self, chunks: list[DocumentChunk]) -> None:
        """Indexes an array of DocumentChunks into the BM25Plus model."""
        self.chunks = list(chunks)
        self.tokenized_corpus = [
            FinancialTokenizer.tokenize(chunk.content) for chunk in self.chunks
        ]

        if self.tokenized_corpus and any(len(doc) > 0 for doc in self.tokenized_corpus):
            self.bm25 = BM25Plus(self.tokenized_corpus, k1=self.k1, b=self.b)
        else:
            self.bm25 = None

    def add_chunks(self, new_chunks: list[DocumentChunk]) -> None:
        """
        Appends new chunks and rebuilds the BM25 index incrementally.
        Tokenizes ONLY incoming chunks to avoid O(N) re-tokenization bottlenecks.
        """
        if not new_chunks:
            return

        new_tokens = [FinancialTokenizer.tokenize(chunk.content) for chunk in new_chunks]
        self.chunks.extend(new_chunks)
        self.tokenized_corpus.extend(new_tokens)

        if self.tokenized_corpus and any(len(doc) > 0 for doc in self.tokenized_corpus):
            self.bm25 = BM25Plus(self.tokenized_corpus, k1=self.k1, b=self.b)
        else:
            self.bm25 = None

    def search(
        self,
        query: str,
        limit: int = 25,
        document_id: str | None = None,
    ) -> list[DocumentChunk]:
        """
        Executes BM25Plus query and returns top matching chunks with sparse_score populated.
        Optionally filters results by document_id.
        """
        if not self.bm25 or not self.chunks or not query.strip():
            return []

        tokenized_query = FinancialTokenizer.tokenize(query)
        if not tokenized_query:
            return []

        doc_scores = self.bm25.get_scores(tokenized_query)

        # Pair chunks with scores
        scored_pairs: list[tuple[float, DocumentChunk]] = []
        for score, chunk in zip(doc_scores, self.chunks, strict=False):
            if score <= 0.0:
                continue
            if document_id and chunk.metadata.document_id != document_id:
                continue

            # Clone chunk to avoid modifying original instance
            cloned = chunk.model_copy(deep=True)
            cloned.sparse_score = float(score)
            scored_pairs.append((score, cloned))

        # Sort descending by BM25 score
        scored_pairs.sort(key=lambda x: x[0], reverse=True)
        return [pair[1] for pair in scored_pairs[:limit]]

    def count(self) -> int:
        """Returns total number of chunks currently in the index."""
        return len(self.chunks)
