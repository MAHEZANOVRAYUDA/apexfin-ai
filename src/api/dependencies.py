"""
Dependency injection container for ApexFin AI FastAPI application.
Provides cached singletons and swappable service components.
"""

from functools import lru_cache

from src.config.settings import Settings, get_settings
from src.generation.fact_checker import DeterministicFactChecker
from src.generation.llm_client import BaseLLMClient, DualLLMClient
from src.generation.prompts import FinancialPromptBuilder
from src.generation.structured_engine import StructuredGenerationEngine
from src.ingestion.chunker import HierarchicalChunker
from src.ingestion.pdf_parser import PDFParser
from src.retrieval.embedder import BaseEmbedder, FastEmbedder
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.qdrant_client import QdrantVectorStore
from src.retrieval.reranker import BaseReranker, CrossEncoderReranker
from src.retrieval.sparse_bm25 import BM25SearchIndex


@lru_cache
def get_app_settings() -> Settings:
    """Returns singleton settings."""
    return get_settings()


@lru_cache
def get_pdf_parser() -> PDFParser:
    """Returns coordinate-aware PDF parser."""
    return PDFParser()


@lru_cache
def get_chunker() -> HierarchicalChunker:
    """Returns context-aware hierarchical chunker."""
    return HierarchicalChunker()


@lru_cache
def get_vector_store() -> QdrantVectorStore:
    """Returns Qdrant vector store connection."""
    return QdrantVectorStore()


@lru_cache
def get_embedder() -> BaseEmbedder:
    """Returns dense vector embedding model."""
    return FastEmbedder()


@lru_cache
def get_bm25_index() -> BM25SearchIndex:
    """Returns sparse lexical BM25 index."""
    return BM25SearchIndex()


@lru_cache
def get_reranker() -> BaseReranker:
    """Returns cross-encoder reranker."""
    return CrossEncoderReranker()


@lru_cache
def get_hybrid_retriever() -> HybridRetriever:
    """Returns unified hybrid retrieval coordinator."""
    return HybridRetriever(
        vector_store=get_vector_store(),
        embedder=get_embedder(),
        bm25_index=get_bm25_index(),
        reranker=get_reranker(),
    )


@lru_cache
def get_llm_client() -> BaseLLMClient:
    """Returns dual-provider asynchronous LLM client."""
    return DualLLMClient()


@lru_cache
def get_prompt_builder() -> FinancialPromptBuilder:
    """Returns financial prompt builder with canary nonce."""
    return FinancialPromptBuilder()


@lru_cache
def get_structured_engine() -> StructuredGenerationEngine:
    """Returns structured extraction engine."""
    return StructuredGenerationEngine(
        llm_client=get_llm_client(),
        prompt_builder=get_prompt_builder(),
    )


@lru_cache
def get_fact_checker() -> DeterministicFactChecker:
    """Returns deterministic verbatim fact checker."""
    return DeterministicFactChecker()
