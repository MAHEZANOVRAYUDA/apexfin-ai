"""
Document ingestion and indexing API routes for ApexFin AI.
"""

import asyncio
import time
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from src.api.dependencies import (
    get_chunker,
    get_hybrid_retriever,
    get_pdf_parser,
    get_vector_store,
)
from src.domain.entities import DocumentIngestionResult
from src.domain.exceptions import DocumentParsingError
from src.ingestion.chunker import HierarchicalChunker
from src.ingestion.pdf_parser import PDFParser
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.qdrant_client import QdrantVectorStore

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentIngestionResult,
    status_code=status.HTTP_201_CREATED,
    summary="Upload & Index Financial PDF",
    description="Parses coordinate-aware narrative text and isolates tables into atomic Markdown chunks.",
)
async def upload_document(
    file: UploadFile = File(..., description="SEC Form 10-K, 10-Q, or Annual Report PDF"),
    parser: PDFParser = Depends(get_pdf_parser),
    chunker: HierarchicalChunker = Depends(get_chunker),
    retriever: HybridRetriever = Depends(get_hybrid_retriever),
) -> DocumentIngestionResult:
    start_time = time.perf_counter()

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise DocumentParsingError("Uploaded file must have a valid .pdf extension.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise DocumentParsingError("Uploaded file is empty (0 bytes).")

    # 1. Parse coordinate layout and extract Markdown tables in non-blocking thread
    parsed_doc = await asyncio.to_thread(parser.parse_bytes, pdf_bytes, file.filename)

    # 2. Chunk hierarchically with table preservation in non-blocking thread
    chunks = await asyncio.to_thread(chunker.chunk_document, parsed_doc)
    if not chunks:
        raise DocumentParsingError("Failed to extract any readable content or tables from PDF.")

    # 3. Dual Index into Qdrant & BM25 in non-blocking thread
    await asyncio.to_thread(retriever.index_document_chunks, chunks)

    elapsed_seconds = round(time.perf_counter() - start_time, 2)
    tables_count = sum(len(page.tables) for page in parsed_doc.pages)

    return DocumentIngestionResult(
        document_id=parsed_doc.document_id,
        document_name=parsed_doc.document_name,
        total_pages=parsed_doc.total_pages,
        total_chunks=len(chunks),
        tables_extracted=tables_count,
        ingestion_duration_seconds=elapsed_seconds,
        status="indexed",
    )


@router.get(
    "/stats",
    summary="Vector Store Statistics",
    description="Returns total number of chunks currently indexed in Qdrant.",
)
def get_storage_stats(
    vector_store: QdrantVectorStore = Depends(get_vector_store),
) -> dict[str, int]:
    total_chunks = vector_store.count()
    return {"total_indexed_chunks": total_chunks}


@router.get(
    "/list",
    summary="List Indexed Documents",
    description="Returns metadata for all documents currently indexed in vector storage.",
)
def list_indexed_documents(
    vector_store: QdrantVectorStore = Depends(get_vector_store),
) -> list[dict[str, Any]]:
    return vector_store.list_documents()


@router.post(
    "/load-samples",
    summary="Preload Benchmark Sample Filings",
    description="Indexes Apple FY2023 and NVIDIA FY2024 Form 10-K filings for interactive evaluation.",
)
def load_sample_filings(
    retriever: HybridRetriever = Depends(get_hybrid_retriever),
) -> dict[str, Any]:
    from src.ingestion.sample_loader import load_benchmark_samples

    total = load_benchmark_samples(retriever)
    return {"message": "Sample filings indexed successfully", "chunks_indexed": total}


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Document",
    description="Purges all indexed vectors and metadata for a specific document ID.",
)
def delete_document(
    document_id: str,
    vector_store: QdrantVectorStore = Depends(get_vector_store),
) -> None:
    current_count = vector_store.count(document_id=document_id)
    if current_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found in index.",
        )
    vector_store.delete_document(document_id)
