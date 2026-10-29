# Graph Report - apexfin-ai  (2026-10-29)

## Corpus Check
- 55 files · ~22,039 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 597 nodes · 1276 edges · 39 communities (34 shown, 5 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 107 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- StructuredGenerationEngine
- PDFParser
- AnalysisReport
- Settings
- exceptions.py
- HybridRetriever
- analysis.py
- ChunkMetadata
- .build_index
- HierarchicalChunker
- test_api_routes.py
- DocumentChunk
- BM25SearchIndex
- MockEmbedder
- ApexFin AI: Production-Grade Financial Intelligence & Audit-Ready Hybrid RAG Engine
- app.js
- test_rag_benchmark.py
- entities.py
- DeterministicFactChecker
- src/__init__.py
- tests/__init__.py
- unit/__init__.py
- apexfin-ai
- Product Requirements Document (PRD) & Technical Specification
- DualLLMClient
- Implementation Plan: ApexFin AI
- MockLLMClient
- get_settings
- documents.py
- structured_engine.py
- dependencies.py
- QdrantVectorStore
- .validate_environment
- get_structured_engine
- FastEmbedder
- .ensure_collection
- test_sparse_bm25.py
- QueryRequest
- todo.md

## God Nodes (most connected - your core abstractions)
1. `DocumentChunk` - 68 edges
2. `ChunkMetadata` - 42 edges
3. `HybridRetriever` - 30 edges
4. `QdrantVectorStore` - 29 edges
5. `get_settings()` - 26 edges
6. `StructuredGenerationEngine` - 24 edges
7. `AnalysisReport` - 23 edges
8. `DeterministicFactChecker` - 22 edges
9. `BM25SearchIndex` - 22 edges
10. `DualLLMClient` - 21 edges

## Surprising Connections (you probably didn't know these)
- `benchmark_retriever()` --uses--> `ChunkMetadata`  [INFERRED]
  tests/evaluation/test_rag_benchmark.py → src/domain/entities.py
- `test_structured_engine_happy_path()` --uses--> `ChunkMetadata`  [INFERRED]
  tests/unit/test_structured_engine.py → src/domain/entities.py
- `benchmark_retriever()` --uses--> `DocumentChunk`  [INFERRED]
  tests/evaluation/test_rag_benchmark.py → src/domain/entities.py
- `test_structured_engine_happy_path()` --uses--> `DocumentChunk`  [INFERRED]
  tests/unit/test_structured_engine.py → src/domain/entities.py
- `test_dual_client_no_keys_raises_error()` --uses--> `ModelInferenceError`  [INFERRED]
  tests/unit/test_llm_client.py → src/domain/exceptions.py

## Import Cycles
- None detected.

## Communities (39 total, 5 thin omitted)

### Community 0 - "StructuredGenerationEngine"
Cohesion: 0.11
Nodes (21): PromptInjectionDetectedError, Raised when canary tokens or adversarial patterns are triggered., FinancialPromptBuilder, Constructs isolated, XML-delimited prompts with canary nonces to prevent…, Injects canary secret nonce into system prompt template., Encapsulates document chunks inside structured XML tags., Constructs safe user message with segregated query and evidence., Coordinates LLM inference, canary security checks, and strict Pydantic v2… (+13 more)

### Community 1 - "PDFParser"
Cohesion: 0.09
Nodes (28): post, upload_document(), DocumentParsingError, Raised when PDF document structure is corrupt or unreadable., PDFParser, Path, Reads a local PDF file from disk and parses it., Coordinate-aware PDF parser designed for SEC 10-K, 10-Q, and annual financial… (+20 more)

### Community 2 - "AnalysisReport"
Cohesion: 0.11
Nodes (25): EventSourceResponse, get, post, query_financial_report(), stream_financial_analysis(), AnalysisReport, CitationSource, FinancialMetric (+17 more)

### Community 3 - "Settings"
Cohesion: 0.12
Nodes (20): BaseSettings, parametrize, Central application settings schema. Reads from environment variables and…, Checks if at least one cloud LLM API key is configured with a real value., Settings, Unit tests for Settings configuration and fail-fast validation in ApexFin AI., Verify numerical boundary checks on operational limits., Verify default development configuration. (+12 more)

### Community 4 - "exceptions.py"
Cohesion: 0.07
Nodes (24): Exception, ApexFinException, DocumentNotFoundError, ProblemDetails, BaseModel, Domain Exceptions & RFC 7807 Problem Details for ApexFin AI. Standardizes…, RFC 7807 Standard Error Envelope. Provides human-readable explanation and…, Base exception for all ApexFin AI domain failures. (+16 more)

### Community 5 - "HybridRetriever"
Cohesion: 0.10
Nodes (20): Pre-packaged SEC 10-K benchmark filings loader for ApexFin AI. Enables…, Reciprocal Rank Fusion (RRF) algorithm for ApexFin AI. Fuses heterogeneous…, Fuses two ranked result lists into a single consensus ranking using Reciprocal…, reciprocal_rank_fusion(), HybridRetriever, Unified Hybrid Retriever orchestrator for ApexFin AI. Coordinates Dense Vector…, Two-stage hybrid retrieval engine: Stage 1: Multi-arm candidate retrieval…, Indexes a collection of DocumentChunks simultaneously into Qdrant and the BM25… (+12 more)

### Community 6 - "analysis.py"
Cohesion: 0.22
Nodes (13): FastAPI, get_hybrid_retriever(), get_vector_store(), Returns Qdrant vector store connection., Returns unified hybrid retrieval coordinator., create_app(), lifespan(), FastAPI application entrypoint for ApexFin AI. Configures CORS, global RFC 7807… (+5 more)

### Community 7 - "ChunkMetadata"
Cohesion: 0.15
Nodes (16): ChunkMetadata, Metadata attached to an individual content chunk., Unit tests for pure domain entities in ApexFin AI. Verifies contract…, Verify ChunkMetadata accepts valid coordinates and defaults., Verify page_number must be >= 1 (1-indexed for financial auditability)., Verify chunk_index must be >= 0., Verify DocumentChunk auto-generates UUID and handles multi-arm scores., Verify chunk rejects empty content. (+8 more)

### Community 8 - ".build_index"
Cohesion: 0.20
Nodes (6): Tokenizes text while preserving financial syntax., Indexes an array of DocumentChunks into the BM25Plus model., Appends new chunks and rebuilds the BM25 index., Executes BM25Plus query and returns top matching chunks with sparse_score…, Verify tokenizer preserves currency, acronyms, and percentages., test_financial_tokenizer_preserves_financial_entities()

### Community 9 - "HierarchicalChunker"
Cohesion: 0.08
Nodes (38): HierarchicalChunker, Splits ParsedDocument into an ordered list of DocumentChunk entities. Enforces…, Splits narrative text into clean sentence segments., Ingestion module for coordinate-aware parsing, table extraction, and…, ParsedDocument, ParsedPage, BaseModel, Encapsulates extracted narrative and isolated tables for a single PDF page. (+30 more)

### Community 10 - "test_api_routes.py"
Cohesion: 0.13
Nodes (21): TestClient, client(), create_sample_pdf_bytes(), fixture, Integration tests for ApexFin AI FastAPI REST & SSE endpoints. Verifies RFC…, Verify uploading non-pdf yields RFC 7807 ProblemDetails., Verify end-to-end query returns AnalysisReport., Verify invalid query payload produces RFC 7807 validation envelope. (+13 more)

### Community 11 - "DocumentChunk"
Cohesion: 0.11
Nodes (16): DocumentChunk, Atomic unit of retrieved financial text or structured Markdown table., Processes entire ParsedDocument into sequenced DocumentChunks. Yields table…, Chunks page narrative into overlapping windows while respecting sentence…, Performs cosine vector search, returning top-k matching DocumentChunks., Unit tests for FinancialPromptBuilder, XML context segregation, and canary…, Verify document chunks are wrapped in XML tags with CDATA protection., Verify user prompt segregates query and evidence. (+8 more)

### Community 12 - "BM25SearchIndex"
Cohesion: 0.18
Nodes (9): BM25SearchIndex, FinancialTokenizer, Sparse lexical search engine for ApexFin AI using BM25Plus. Specialized for…, Returns total number of chunks currently in the index., Financial-aware lexical tokenizer. Preserves currency figures ($10,000),…, Inverted index using BM25Plus for exact keyword retrieval on financial chunks.…, Unit tests for end-to-end HybridRetriever pipeline., Verify end-to-end multi-arm indexing and hybrid retrieval. (+1 more)

### Community 13 - "MockEmbedder"
Cohesion: 0.11
Nodes (14): BaseEmbedder, MockEmbedder, ABC, Embedding generation adapter for ApexFin AI. Generates 384-dimensional dense…, Abstract interface for dense vector embedding models., Generates dense embeddings for a batch of text chunks., Generates dense embedding for a single user query., Embeds a single query string. (+6 more)

### Community 14 - "ApexFin AI: Production-Grade Financial Intelligence & Audit-Ready Hybrid RAG Engine"
Cohesion: 0.07
Nodes (28): 1. Zero-Cost Production Stack Overview, 2. Docker Compose Deployment (Recommended for Local & VPS), 3. Deploying to Hugging Face Spaces (100% Free Cloud), 4. Deploying to Render.com (Free Web Service), 5. Security & DevSecOps Hardening (OWASP Compliance), Prerequisites, Production Deployment & Operations Guide, Quickstart (+20 more)

### Community 15 - "app.js"
Cohesion: 0.35
Nodes (11): RFC-7807, escapeHtml(), executeStreamingQuery(), refreshDocumentsList(), refreshStats(), renderDocumentsList(), renderIdealReport(), setLoadingState() (+3 more)

### Community 16 - "test_rag_benchmark.py"
Cohesion: 0.18
Nodes (10): MockReranker, Deterministic reranker for offline unit tests. Calculates overlap and preserves…, benchmark_retriever(), golden_dataset(), fixture, Quantitative RAG Evaluation Benchmark Suite for ApexFin AI. Evaluates Hybrid…, Loads the SEC 10-K ground truth benchmark dataset., Builds and populates in-memory hybrid retriever with golden context and… (+2 more)

### Community 17 - "entities.py"
Cohesion: 0.20
Nodes (8): DocumentIngestionResult, BaseModel, Pure Domain Entities for ApexFin AI. Free from ORMs, web frameworks, or third-…, Result summary emitted after ingesting a PDF document., Domain layer containing pure entities and RFC 7807 problem exceptions., Hierarchical context-aware chunker for financial documents. Preserves financial…, Verify DocumentIngestionResult schema., test_document_ingestion_result()

### Community 18 - "DeterministicFactChecker"
Cohesion: 0.16
Nodes (15): Raised when numbers in synthesis fail verbatim check against source., VerificationFactCheckError, DeterministicFactChecker, Deterministic numerical verbatim fact-checker for ApexFin AI. Verifies all…, Mathematical and verbatim validator that protects against LLM hallucinations.…, Extracts and normalizes all numerical candidates from text., Determines whether a numeric token exists verbatim or in normalized format…, Scans executive_summary and extracted_metrics against retrieved chunks. Adds… (+7 more)

### Community 23 - "Product Requirements Document (PRD) & Technical Specification"
Cohesion: 0.12
Nodes (16): 1.1 Problem Statement, 1.2 Solution Vision, 1.3 Target Audience & Recruiter Value Proposition, 1. Executive Summary & Objective, 2.1 Technology Selection Rationale, 2. Technical Stack & Architectural Decisions, 3. Detailed System Architecture, 4.1 Epic 1: Dokumen Ingestion & Table Extraction (+8 more)

### Community 24 - "DualLLMClient"
Cohesion: 0.19
Nodes (10): ModelInferenceError, Raised when upstream LLM API returns unrecoverable error., DualLLMClient, Any, Determines if a key is a real credential and not a template placeholder., Deterministic offline synthesis engine for development and testing. Extracts…, Executes inference with automatic failover from Groq to Gemini., Production dual-provider asynchronous client. Primary: Groq Cloud LPU… (+2 more)

### Community 25 - "Implementation Plan: ApexFin AI"
Cohesion: 0.12
Nodes (15): Architecture Directory Layout, Implementation Plan: ApexFin AI, Phase 1: Environment Foundation, Configuration & Domain Contracts, Phase 2: Coordinate-Aware PDF Ingestion & Table Extraction Engine, Phase 3: Hybrid Retrieval Engine (Dense + Sparse BM25 + Cross-Encoder Reranker), Phase 4: Guaranteed Structured Generation, Guardrails & Fact-Checker, Phase 5: FastAPI Endpoints & High-Density Craftsman UI, Phase 6: Quantitative Evaluation (Ragas Benchmark), CI/CD & Production Deployment (+7 more)

### Community 26 - "MockLLMClient"
Cohesion: 0.20
Nodes (12): RateLimitExceededError, Raised when all LLM providers exceed rate limits., MockLLMClient, Deterministic mock client for offline tests without external network or API…, asyncio, Unit tests for LLM client implementations., Verify MockLLMClient returns valid json and identifier., Verify MockLLMClient can simulate rate limit failures. (+4 more)

### Community 27 - "get_settings"
Cohesion: 0.16
Nodes (7): QdrantClient, get_settings(), Configuration module for ApexFin AI using Pydantic Settings. Enforces fail-fast…, Returns singleton cached instance of Application Settings., Coordinate-aware PDF parser for financial reports using pdfplumber. Extracts…, Verify get_settings returns singleton instance., test_get_settings_cached_singleton()

### Community 28 - "documents.py"
Cohesion: 0.18
Nodes (12): delete, get_chunker(), get_pdf_parser(), Returns coordinate-aware PDF parser., Returns context-aware hierarchical chunker., delete_document(), get_storage_stats(), list_indexed_documents() (+4 more)

### Community 29 - "structured_engine.py"
Cohesion: 0.22
Nodes (8): Generation module containing LLM failover adapters, XML prompt guardrails, and…, BaseLLMClient, ABC, Dual-client LLM adapter with asynchronous failover architecture for ApexFin AI.…, Abstract interface for LLM synthesis clients., Executes completion. Returns: tuple of (raw_json_response_string,…, Prompt templates, XML context segregation, and canary guardrails for ApexFin AI., Structured Generation Engine with Pydantic validation and canary defense for…

### Community 30 - "dependencies.py"
Cohesion: 0.17
Nodes (11): get_app_settings(), get_bm25_index(), get_embedder(), get_fact_checker(), get_reranker(), Dependency injection container for ApexFin AI FastAPI application. Provides…, Returns singleton settings., Returns dense vector embedding model. (+3 more)

### Community 31 - "QdrantVectorStore"
Cohesion: 0.18
Nodes (7): Any, QdrantVectorStore, Vector storage adapter using Qdrant (in-memory or cloud cluster). Provides…, Deletes all indexed chunks associated with a specific document ID., Manages collection lifecycle, chunk indexing, and cosine similarity search in…, Returns total chunk count in collection, optionally filtered by document., Returns metadata summary for all distinct indexed documents.

### Community 32 - ".validate_environment"
Cohesion: 0.27
Nodes (4): field_validator, model_validator, Any, Enforce fail-fast secret validation when running in production. Prevents…

### Community 33 - "get_structured_engine"
Cohesion: 0.33
Nodes (6): get_llm_client(), get_prompt_builder(), get_structured_engine(), Returns dual-provider asynchronous LLM client., Returns financial prompt builder with canary nonce., Returns structured extraction engine.

### Community 34 - "FastEmbedder"
Cohesion: 0.40
Nodes (3): FastEmbedder, Lightweight embedding provider using FastEmbed ONNX or SentenceTransformers as…, Embeds a list of document chunks into 384-dim normalized vectors.

### Community 35 - ".ensure_collection"
Cohesion: 0.40
Nodes (3): Distance, Creates collection if it does not already exist., Stores a batch of DocumentChunks along with their dense embedding vectors.

### Community 36 - "test_sparse_bm25.py"
Cohesion: 0.50
Nodes (3): Unit tests for financial BM25 lexical search and financial tokenization., Verify BM25 returns exact matching financial chunks with sparse_score., test_bm25_search_scoring_and_ranking()

### Community 37 - "QueryRequest"
Cohesion: 0.67
Nodes (3): BaseModel, QueryRequest, Payload contract for financial query requests.

## Knowledge Gaps
- **45 isolated node(s):** `apexfin-ai`, `RFC-7807`, `Project: ApexFin AI — Production-Grade Financial Intelligence & Audit-Ready Hybrid RAG Engine`, `1.1 Problem Statement`, `1.2 Solution Vision` (+40 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 300 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DocumentChunk` connect `DocumentChunk` to `StructuredGenerationEngine`, `AnalysisReport`, `.ensure_collection`, `test_sparse_bm25.py`, `HybridRetriever`, `analysis.py`, `ChunkMetadata`, `.build_index`, `HierarchicalChunker`, `BM25SearchIndex`, `test_rag_benchmark.py`, `entities.py`, `DeterministicFactChecker`, `structured_engine.py`, `QdrantVectorStore`?**
  _High betweenness centrality (0.137) - this node is a cross-community bridge._
- **Why does `Settings` connect `Settings` to `.validate_environment`, `get_settings`, `dependencies.py`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Why does `PDFParser` connect `PDFParser` to `HierarchicalChunker`, `get_settings`, `documents.py`, `dependencies.py`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `DocumentChunk` (e.g. with `DeterministicFactChecker` and `FinancialPromptBuilder`) actually correct?**
  _`DocumentChunk` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `ChunkMetadata` (e.g. with `HierarchicalChunker` and `QdrantVectorStore`) actually correct?**
  _`ChunkMetadata` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `HybridRetriever` (e.g. with `query_financial_report()` and `stream_financial_analysis()`) actually correct?**
  _`HybridRetriever` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `QdrantVectorStore` (e.g. with `delete_document()` and `get_storage_stats()`) actually correct?**
  _`QdrantVectorStore` has 8 INFERRED edges - model-reasoned connections that need verification._