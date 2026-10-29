"""
Financial analysis and SSE streaming endpoints for ApexFin AI.
"""

import asyncio
import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from src.api.dependencies import (
    get_fact_checker,
    get_hybrid_retriever,
    get_structured_engine,
)
from src.domain.entities import AnalysisReport, CitationSource
from src.domain.exceptions import DocumentNotFoundError
from src.generation.fact_checker import DeterministicFactChecker
from src.generation.structured_engine import StructuredGenerationEngine
from src.retrieval.hybrid_retriever import HybridRetriever

router = APIRouter(prefix="/analysis", tags=["Financial Intelligence"])


class QueryRequest(BaseModel):
    """Payload contract for financial query requests."""

    query: str = Field(
        min_length=3,
        max_length=500,
        description="Natural language financial inquiry, e.g. 'What was Apple's total net sales in FY2023?'",
        examples=["What was Apple's total net sales in FY2023?"],
    )
    document_id: str | None = Field(
        default=None,
        description="Optional filter targeting a specific indexed document",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of context chunks forwarded to LLM synthesis",
    )
    strict_fact_check: bool = Field(
        default=False,
        description="Whether to fail fast with HTTP 422 if hallucinated numbers are detected",
    )


@router.post(
    "/query",
    response_model=AnalysisReport,
    status_code=status.HTTP_200_OK,
    summary="Execute Financial Analysis",
    description="Performs Two-Stage Hybrid Retrieval, XML-guarded synthesis, and deterministic fact verification.",
)
async def query_financial_report(
    payload: QueryRequest,
    retriever: HybridRetriever = Depends(get_hybrid_retriever),
    engine: StructuredGenerationEngine = Depends(get_structured_engine),
    fact_checker: DeterministicFactChecker = Depends(get_fact_checker),
) -> AnalysisReport:
    # 1. Retrieve candidates
    candidates = retriever.retrieve(
        query=payload.query,
        document_id=payload.document_id,
        limit=payload.top_k,
    )

    if not candidates:
        if payload.document_id:
            raise DocumentNotFoundError(payload.document_id)
        # Empty fallback report if no indexed data exists
        return AnalysisReport(
            query=payload.query,
            executive_summary="No indexed financial filings matching the query were found in the database.",
            extracted_metrics=[],
            citations=[
                CitationSource(
                    document_name="System",
                    page_number=1,
                    excerpt="No matching documents found in index.",
                    relevance_score=0.0,
                )
            ],
            audit_warnings=["Notice: Index contains no matching data for this search."],
            confidence_score=0.0,
            model_used="none",
        )

    # 2. Structured LLM Generation
    raw_report = await engine.generate_analysis(
        query=payload.query,
        retrieved_chunks=candidates,
    )

    # 3. Deterministic Numerical Fact-Check
    return fact_checker.verify_report(
        report=raw_report,
        retrieved_chunks=candidates,
        strict=payload.strict_fact_check,
    )


@router.get(
    "/stream",
    summary="Stream Financial Analysis via Server-Sent Events (SSE)",
    description="Streams granular status progression (retrieval, reranking, synthesis, fact-checking) followed by final AnalysisReport JSON.",
)
async def stream_financial_analysis(
    q: str = Query(..., min_length=3, max_length=500, description="Financial query"),
    document_id: str | None = Query(None, description="Optional target document ID"),
    top_k: int = Query(5, ge=1, le=20),
    strict: bool = Query(False),
    retriever: HybridRetriever = Depends(get_hybrid_retriever),
    engine: StructuredGenerationEngine = Depends(get_structured_engine),
    fact_checker: DeterministicFactChecker = Depends(get_fact_checker),
) -> EventSourceResponse:
    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        # Step 1: Retrieval
        yield {
            "event": "status",
            "data": json.dumps(
                {
                    "step": "retrieval",
                    "message": "Executing dense vector + BM25 lexical hybrid search...",
                }
            ),
        }
        await asyncio.sleep(0.05)

        candidates = retriever.retrieve(query=q, document_id=document_id, limit=top_k)

        # Step 2: Reranking
        yield {
            "event": "status",
            "data": json.dumps(
                {
                    "step": "reranking",
                    "message": f"Cross-Encoder filtered {len(candidates)} high-relevance chunks.",
                }
            ),
        }
        await asyncio.sleep(0.05)

        if not candidates:
            report = AnalysisReport(
                query=q,
                executive_summary="No indexed financial filings matching the query were found in the database.",
                extracted_metrics=[],
                citations=[
                    CitationSource(
                        document_name="System",
                        page_number=1,
                        excerpt="No matching documents found in index.",
                        relevance_score=0.0,
                    )
                ],
                audit_warnings=["Notice: Index contains no matching data for this search."],
                confidence_score=0.0,
                model_used="none",
            )
            yield {"event": "result", "data": report.model_dump_json()}
            yield {"event": "done", "data": json.dumps({"status": "complete"})}
            return

        try:
            # Step 3: Synthesis
            yield {
                "event": "status",
                "data": json.dumps(
                    {
                        "step": "synthesis",
                        "message": "Groq LPU / Gemini Flash synthesizing structured report...",
                    }
                ),
            }
            raw_report = await engine.generate_analysis(query=q, retrieved_chunks=candidates)

            # Step 4: Fact checking
            yield {
                "event": "status",
                "data": json.dumps(
                    {
                        "step": "fact_checking",
                        "message": "Deterministic verbatim fact-checker scanning numbers...",
                    }
                ),
            }
            verified_report = fact_checker.verify_report(
                report=raw_report,
                retrieved_chunks=candidates,
                strict=strict,
            )

            # Step 5: Final Result
            yield {"event": "result", "data": verified_report.model_dump_json()}
            yield {"event": "done", "data": json.dumps({"status": "complete"})}
        except Exception as exc:
            yield {
                "event": "problem",
                "data": json.dumps(
                    {
                        "type": "https://apexfin.ai/errors/model-inference",
                        "title": "Model Inference Failed",
                        "detail": str(exc),
                        "status": 502,
                    }
                ),
            }
            yield {"event": "done", "data": json.dumps({"status": "error"})}

    return EventSourceResponse(event_generator())
