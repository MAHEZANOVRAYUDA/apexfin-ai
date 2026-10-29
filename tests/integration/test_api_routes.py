"""
Integration tests for ApexFin AI FastAPI REST & SSE endpoints.
Verifies RFC 7807 error envelopes and end-to-end pipeline execution.
"""

import io

import fitz
import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import (
    get_hybrid_retriever,
    get_llm_client,
    get_structured_engine,
    get_vector_store,
)
from src.api.main import app
from src.generation.llm_client import MockLLMClient
from src.generation.structured_engine import StructuredGenerationEngine
from src.retrieval.embedder import MockEmbedder
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.qdrant_client import QdrantVectorStore
from src.retrieval.reranker import MockReranker
from src.retrieval.sparse_bm25 import BM25SearchIndex


def create_sample_pdf_bytes() -> bytes:
    """Generates valid in-memory financial PDF with a table."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 40), "ITEM 7. MANAGEMENT'S DISCUSSION")
    page.insert_text((50, 70), "Apple net sales in fiscal 2023 were $383,285 million.")
    page.draw_rect(fitz.Rect(50, 100, 300, 200))
    page.draw_line(fitz.Point(50, 130), fitz.Point(300, 130))
    page.insert_text((60, 120), "Line Item")
    page.insert_text((180, 120), "FY2023")
    page.insert_text((60, 160), "Net Sales")
    page.insert_text((180, 160), "$383,285M")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture
def client():
    """TestClient fixture with mocked LLM and fast mock embedders."""
    vector_store = QdrantVectorStore(url=":memory:", collection_name="test_integration_col")
    vector_store.ensure_collection(vector_size=384)

    mock_retriever = HybridRetriever(
        vector_store=vector_store,
        embedder=MockEmbedder(vector_dim=384),
        bm25_index=BM25SearchIndex(),
        reranker=MockReranker(default_limit=3),
    )
    mock_llm = MockLLMClient()
    mock_engine = StructuredGenerationEngine(llm_client=mock_llm)

    app.dependency_overrides[get_llm_client] = lambda: mock_llm
    app.dependency_overrides[get_structured_engine] = lambda: mock_engine
    app.dependency_overrides[get_hybrid_retriever] = lambda: mock_retriever
    app.dependency_overrides[get_vector_store] = lambda: mock_retriever.vector_store

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_health_check(client: TestClient):
    """Verify health endpoint."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_serve_html_index(client: TestClient):
    """Verify root path serves craftsman web UI."""
    res = client.get("/")
    assert res.status_code == 200
    assert "ApexFin AI" in res.text
    assert "text/html" in res.headers["content-type"]


def test_upload_document_success(client: TestClient):
    """Verify PDF upload parses tables and indexes chunks."""
    pdf_bytes = create_sample_pdf_bytes()
    files = {"file": ("apple_10k_sample.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

    res = client.post("/api/v1/documents/upload", files=files)
    assert res.status_code == 201
    data = res.json()
    assert data["document_name"] == "apple_10k_sample.pdf"
    assert data["total_chunks"] >= 1
    assert data["status"] == "indexed"


def test_upload_document_invalid_extension(client: TestClient):
    """Verify uploading non-pdf yields RFC 7807 ProblemDetails."""
    files = {"file": ("malicious.txt", io.BytesIO(b"Hello"), "text/plain")}
    res = client.post("/api/v1/documents/upload", files=files)

    assert res.status_code == 422
    assert res.headers["content-type"] == "application/problem+json"
    data = res.json()
    assert data["type"] == "https://apexfin.ai/errors/document-parsing"
    assert "Document Parsing Failed" in data["title"]


def test_query_financial_report(client: TestClient):
    """Verify end-to-end query returns AnalysisReport."""
    # 1. First upload document
    pdf_bytes = create_sample_pdf_bytes()
    files = {"file": ("apple_10k.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    upload_res = client.post("/api/v1/documents/upload", files=files)
    doc_id = upload_res.json()["document_id"]

    # 2. Execute analysis query
    payload = {
        "query": "What was Apple's net sales in fiscal 2023?",
        "document_id": doc_id,
        "top_k": 3,
        "strict_fact_check": False,
    }
    res = client.post("/api/v1/analysis/query", json=payload)
    assert res.status_code == 200
    report = res.json()
    assert report["query"] == "What was Apple's net sales in fiscal 2023?"
    assert "Net sales and revenue reached" in report["executive_summary"]
    assert len(report["citations"]) >= 1


def test_query_validation_error_rfc_7807(client: TestClient):
    """Verify invalid query payload produces RFC 7807 validation envelope."""
    payload = {"query": "ab"}  # Min length is 3
    res = client.post("/api/v1/analysis/query", json=payload)

    assert res.status_code == 422
    assert res.headers["content-type"] == "application/problem+json"
    data = res.json()
    assert data["title"] == "Request Validation Failed"
    assert data["invalid_params"] is not None


def test_stream_financial_analysis(client: TestClient):
    """Verify SSE stream returns status and result events."""
    res = client.get("/api/v1/analysis/stream?q=What was net sales?")
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]
    body = res.text
    assert "event: status" in body
    assert "event: result" in body
    assert "event: done" in body
