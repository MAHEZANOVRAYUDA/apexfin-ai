"""
Pure Domain Entities for ApexFin AI.
Free from ORMs, web frameworks, or third-party storage dependencies.
"""

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """Metadata attached to an individual content chunk."""

    document_id: str = Field(description="Unique identifier of parent document")
    document_name: str = Field(description="Original filename of the document")
    page_number: int = Field(ge=1, description="1-indexed PDF page number")
    chunk_index: int = Field(ge=0, description="Sequential index within document")
    is_table: bool = Field(
        default=False, description="Whether this chunk represents a financial table"
    )
    table_id: str | None = Field(
        default=None, description="Identifier of table if chunk is a table"
    )
    section_header: str | None = Field(default=None, description="Closest preceding section title")


class DocumentChunk(BaseModel):
    """Atomic unit of retrieved financial text or structured Markdown table."""

    chunk_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique chunk UUID",
    )
    content: str = Field(min_length=1, description="Raw textual or Markdown table content")
    metadata: ChunkMetadata
    dense_score: float | None = Field(default=None, description="Cosine similarity score")
    sparse_score: float | None = Field(default=None, description="BM25 lexical relevance score")
    rrf_score: float | None = Field(
        default=None, description="Reciprocal Rank Fusion combined score"
    )
    rerank_score: float | None = Field(default=None, description="Cross-encoder relevance score")


class FinancialMetric(BaseModel):
    """Structured financial data point extracted from document."""

    name: str = Field(description="Name of financial metric, e.g. 'Operating Cash Flow'")
    value: float | str = Field(description="Numerical or quantified financial value")
    unit: str = Field(default="USD Millions", description="Unit of measurement or currency")
    period: str = Field(description="Fiscal period, e.g. 'FY2023', 'Q3 2024'")
    context_sentence: str = Field(
        description="Verbatim sentence from source establishing the metric"
    )


class CitationSource(BaseModel):
    """Traceable, audit-ready source citation from verified documents."""

    document_name: str = Field(description="Source document filename")
    page_number: int = Field(ge=1, description="1-indexed page number of the finding")
    is_table: bool = Field(default=False, description="Whether citation originates from a table")
    excerpt: str = Field(description="Verbatim text excerpt containing the evidence")
    relevance_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score of this citation's relevance",
    )


class AnalysisReport(BaseModel):
    """Guaranteed structured output contract returned to user and API clients."""

    query: str = Field(description="The user's original financial query")
    executive_summary: str = Field(
        min_length=10,
        description="Concise, audit-grade financial summary directly answering query",
    )
    extracted_metrics: list[FinancialMetric] = Field(
        default_factory=list,
        description="List of quantitative financial figures extracted from verified sources",
    )
    citations: list[CitationSource] = Field(
        min_length=1,
        description="Verifiable citations grounding every claim made in the summary",
    )
    audit_warnings: list[str] = Field(
        default_factory=list,
        description="Notices regarding discrepancies, missing quarters, or potential ambiguities",
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Calculated overall confidence based on retrieval and fact-check scores",
    )
    model_used: str = Field(default="", description="The specific LLM that generated this analysis")
    processing_time_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Total roundtrip processing time in milliseconds",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp of report generation",
    )


class DocumentIngestionResult(BaseModel):
    """Result summary emitted after ingesting a PDF document."""

    document_id: str
    document_name: str
    total_pages: int
    total_chunks: int
    tables_extracted: int
    ingestion_duration_seconds: float
    status: str = "indexed"
