"""
Domain layer containing pure entities and RFC 7807 problem exceptions.
"""

from src.domain.entities import (
    AnalysisReport,
    ChunkMetadata,
    CitationSource,
    DocumentChunk,
    DocumentIngestionResult,
    FinancialMetric,
)
from src.domain.exceptions import (
    ApexFinException,
    DocumentNotFoundError,
    DocumentParsingError,
    ModelInferenceError,
    ProblemDetails,
    PromptInjectionDetectedError,
    RateLimitExceededError,
    VerificationFactCheckError,
)

__all__ = [
    "AnalysisReport",
    "ApexFinException",
    "ChunkMetadata",
    "CitationSource",
    "DocumentChunk",
    "DocumentIngestionResult",
    "DocumentNotFoundError",
    "DocumentParsingError",
    "FinancialMetric",
    "ModelInferenceError",
    "ProblemDetails",
    "PromptInjectionDetectedError",
    "RateLimitExceededError",
    "VerificationFactCheckError",
]
