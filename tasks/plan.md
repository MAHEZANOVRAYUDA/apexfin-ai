# Implementation Plan: ApexFin AI
## Production-Grade Financial Intelligence & Audit-Ready Hybrid RAG Platform

> **Guiding Architectural Principles:**
> 1. **Vertical Slicing:** Setiap *phase* menghantarkan fungsionalitas vertikal yang dapat diuji dari ujung ke ujung (*end-to-end*).
> 2. **Hardware Harmony:** 100% ramah laptop RAM 8 GB (eksekusi model berat via Free-Tier Cloud APIs Groq & Gemini Flash).
> 3. **The Testing Trophy:** Pengujian menyeluruh mulai dari *pure domain units* hingga *integration & RAG quantitative evaluation*.
> 4. **Zero AI-Slop:** Antarmuka bergaya *High-Density Data Engine*, aksesibilitas WCAG 2.1 AA, dan font angka `tabular-nums`.

---

## Architecture Directory Layout

```
financial-intelligence-rag/
├── PRD.md                           # Product Requirements & Technical Specs
├── tasks/
│   ├── plan.md                      # Detailed Implementation Plan
│   └── todo.md                      # Actionable Task Checklist
├── pyproject.toml                   # Poetry / uv dependency configuration
├── Dockerfile                       # Multi-stage production container
├── docker-compose.yml               # Local orchestration (Qdrant + App)
├── .env.example                     # Environment template with strict schema
├── src/
│   ├── config/                      # Pydantic Settings & Environment validation
│   ├── domain/                      # Pure Domain Entities & Schemas (Contracts)
│   │   ├── entities.py              # FinancialDocument, Chunk, Citation, Metric
│   │   └── exceptions.py            # RFC 7807 Domain Exceptions
│   ├── ingestion/                   # Document Extraction & Chunking Adapters
│   │   ├── pdf_parser.py            # pdfplumber coordinate-aware text & table parser
│   │   ├── table_extractor.py       # Table-to-Markdown & HTML matrix preserver
│   │   └── chunker.py               # Hierarchical Context-aware Chunker
│   ├── retrieval/                   # Hybrid Search & Reranking Engine
│   │   ├── embedder.py              # FastEmbed ONNX (CPU ultra-lightweight)
│   │   ├── sparse_bm25.py           # Rank-BM25 Lexical Inverted Index
│   │   ├── qdrant_client.py         # Qdrant Cloud / Local Memory Vector Store
│   │   ├── fusion.py                # Reciprocal Rank Fusion (RRF)
│   │   └── reranker.py              # Cross-Encoder Reranker
│   ├── generation/                  # LLM Synthesis, Guardrails & Fact Checking
│   │   ├── llm_client.py            # Groq Llama-3.3-70B & Gemini Flash Adapter
│   │   ├── prompts.py               # XML-delimited system prompts with canary nonces
│   │   ├── structured_engine.py     # Instructor + Pydantic schema enforcer
│   │   └── fact_checker.py          # Deterministic numerical verbatim validator
│   ├── api/                         # FastAPI Web Layer (Ports & Adapters)
│   │   ├── main.py                  # App entry point & middleware (CORS, RFC 7807)
│   │   ├── routes/                  # REST & SSE streaming endpoints
│   │   └── dependencies.py          # Dependency Injection container
│   └── web/                         # Modern High-Density Craftsman UI
│       ├── static/                  # Production assets, CSS design tokens
│       └── templates/               # Responsive HTML/Tailwind/JS interface
├── tests/
│   ├── unit/                        # Unit tests for domain, parser, RRF
│   ├── integration/                 # Integration tests with mocked LLM/Vector DB
│   └── evaluation/                  # Quantitative Ragas benchmark test suite
└── sample_data/                     # Sample SEC 10-K financial reports (Apple, Nvidia)
```

---

## Phase 1: Environment Foundation, Configuration & Domain Contracts
**Goal:** Menyiapkan fondasi proyek dengan *fail-fast environment validation*, kontrak entitas data domain murni (*Pydantic v2*), dan *dependency injection container*.

### Tasks:
* [x] **1.1 Project Setup & Dependency Manifest**
  - Target: `pyproject.toml`, `.env.example`, `.gitignore`
  - Acceptance Criteria: Instalasi dependensi inti (`fastapi`, `uvicorn`, `pydantic-settings`, `pdfplumber`, `fastembed`, `qdrant-client`, `groq`, `google-genai`, `instructor`, `pytest`, `ruff`).
  - Verification Command: `ruff --version && pytest --version`
* [x] **1.2 Strict Environment Settings Schema**
  - Target: `src/config/settings.py`
  - Acceptance Criteria: Validasi API key (`GROQ_API_KEY`, `GEMINI_API_KEY`, `QDRANT_API_KEY`, `QDRANT_URL`). Aplikasi menolak start jika key kritis kosong dengan pesan kesalahan informatif (*fail-fast*).
  - Verification Command: `pytest tests/unit/test_settings.py`
* [x] **1.3 Pure Domain Entities & RFC 7807 Error Envelope**
  - Target: `src/domain/entities.py`, `src/domain/exceptions.py`
  - Acceptance Criteria: Skema Pydantic untuk `FinancialMetric`, `CitationSource`, `AnalysisReport`, `ChunkMetadata`, dan standardisasi error envelope RFC 7807.
  - Verification Command: `pytest tests/unit/test_entities.py`

---

## Phase 2: Coordinate-Aware PDF Ingestion & Table Extraction Engine
**Goal:** Membangun *ingestion engine* yang mengekstrak teks naratif dan mengisolasi tabel finansial multikolom menjadi format Markdown terstruktur tanpa memecah integritas data.

### Tasks:
* [x] **2.1 Coordinate-Aware PDF & Table Parser**
  - Target: `src/ingestion/pdf_parser.py`, `src/ingestion/table_extractor.py`
  - Acceptance Criteria: Mengekstrak teks per halaman menggunakan `pdfplumber`, mendeteksi struktur garis kisi tabel, dan mengonversinya menjadi format Markdown tabel (`| Col1 | Col2 |`).
  - Verification Command: `pytest tests/unit/test_table_extractor.py`
* [x] **2.2 Hierarchical Context-Aware Chunker**
  - Target: `src/ingestion/chunker.py`
  - Acceptance Criteria: Membagi narasi menjadi chunk 512 token dengan 64 token overlap, sementara tabel finansial dijaga sebagai satu unit atomik utuh (`is_table=True`).
  - Verification Command: `pytest tests/unit/test_chunker.py`

---

## Phase 3: Hybrid Retrieval Engine (Dense + Sparse BM25 + Cross-Encoder Reranker)
**Goal:** Membangun sistem temu kembali informasi hibrida yang memadukan pencarian semantik vektor dengan pencarian leksikal eksak serta penyaringan relevansi tingkat tinggi.

### Tasks:
* [x] **3.1 Lightweight FastEmbed & Vector Indexer**
  - Target: `src/retrieval/embedder.py`, `src/retrieval/qdrant_client.py`
  - Acceptance Criteria: Menggunakan FastEmbed ONNX (model `bge-small-en`, konsumsi RAM < 200MB) untuk membuat embedding vektor 384-dimensi dan menyimpannya ke Qdrant (dengan fallback in-memory untuk lokal).
  - Verification Command: `pytest tests/integration/test_vector_store.py`
* [x] **3.2 Sparse Lexical BM25 Search Engine**
  - Target: `src/retrieval/sparse_bm25.py`
  - Acceptance Criteria: Mengindeks term kunci finansial (seperti "EBITDA", "CapEx", "Form 10-K Item 8") untuk pencarian berbasis kata kunci eksak.
  - Verification Command: `pytest tests/unit/test_bm25.py`
* [x] **3.3 Reciprocal Rank Fusion (RRF) & Cross-Encoder Reranker**
  - Target: `src/retrieval/fusion.py`, `src/retrieval/reranker.py`
  - Acceptance Criteria: Menggabungkan 25 kandidat Dense + 25 kandidat Sparse dengan bobot RRF ($k=60$), lalu menyaringnya menjadi 5 kandidat terbaik menggunakan model reranker berlatensi rendah.
  - Verification Command: `pytest tests/unit/test_fusion_reranker.py`

---

## Phase 4: Guaranteed Structured Generation, Guardrails & Fact-Checker
**Goal:** Menghubungkan Groq (Llama-3.3-70B) dan Gemini 2.0 Flash dengan skema validasi Pydantic ketat dan verifikasi numerik deterministik bebas halusinasi.

### Tasks:
* [x] **4.1 Dual LLM Provider Client (Groq + Gemini Flash Fallback)**
  - Target: `src/generation/llm_client.py`
  - Acceptance Criteria: Client asinkron yang memprioritaskan Groq API (~300 token/detik) dengan fallback otomatis ke Gemini 2.0 Flash jika terjadi *rate limit* (HTTP 429).
  - Verification Command: `pytest tests/integration/test_llm_client.py`
* [x] **4.2 XML Prompt Isolation, Canary Nonces & Structured Pydantic Output**
  - Target: `src/generation/prompts.py`, `src/generation/structured_engine.py`
  - Acceptance Criteria: Konteks terisolasi dalam `<financial_context nonce="...">` untuk menolak injeksi *prompt*. Respons dipaksa menghasilkan skema `AnalysisReport` via *Instructor*.
  - Verification Command: `pytest tests/unit/test_structured_engine.py`
* [x] **4.3 Deterministic Numerical & Citation Fact-Checker**
  - Target: `src/generation/fact_checker.py`
  - Acceptance Criteria: Algoritma pre-flight yang memvalidasi bahwa setiap angka/rasio finansial yang dilaporkan ada secara verbatim di dalam kutipan sumber teks yang terambil. Jika tidak cocok, ditandai sebagai peringatan audit (*audit warning*).
  - Verification Command: `pytest tests/unit/test_fact_checker.py`

---

## Phase 5: FastAPI Endpoints & High-Density Craftsman UI
**Goal:** Membangun antarmuka pengguna interaktif dan responsif bergaya *High-Density Data Engine* dengan dukungan streaming SSE.

### Tasks:
* [x] **5.1 REST & Server-Sent Events (SSE) Streaming Endpoints**
  - Target: `src/api/main.py`, `src/api/routes/analysis.py`, `src/api/routes/documents.py`
  - Acceptance Criteria: Endpoint `POST /api/documents/upload`, `POST /api/analysis/query` (JSON & SSE streaming), dan `GET /health` sesuai RFC 7807.
  - Verification Command: `pytest tests/integration/test_api_endpoints.py`
* [x] **5.2 Craftsman High-Density Financial Dashboard**
  - Target: `src/web/templates/index.html`, `src/web/static/app.js`, `src/web/static/style.css`
  - Acceptance Criteria: Tampilan modern bergaya Bloomberg/Linear, font `tabular-nums`, kartu metrik keuangan interaktif, modal penampil sitasi dokumen asli, dan penanganan lengkap 6 status UI (Ideal, Empty, Loading Skeleton, Error with Retry, Overflow, Optimistic).
  - Verification Command: Pengujian visual manual di browser & verifikasi responsivitas.

---

## Phase 6: Quantitative Evaluation (Ragas Benchmark), CI/CD & Production Deployment
**Goal:** Mengukur kualitas RAG secara kuantitatif, membuat automasi pengujian di GitHub Actions, dan menyediakan blueprint deploy gratis.

### Tasks:
* [x] **6.1 Quantitative RAG Evaluation Suite (Ragas Metric Benchmark)**
  - Target: `tests/evaluation/benchmark_ragas.py`, `sample_data/golden_dataset.json`
  - Acceptance Criteria: Skrip evaluasi otomatis yang menghitung skor *Faithfulness* ($\ge 0.95$) dan *Answer Relevance* ($\ge 0.90$) pada sampel laporan keuangan 10-K.
  - Verification Command: `python tests/evaluation/benchmark_ragas.py`
* [x] **6.2 Multi-Stage Dockerfile & Local Orchestration**
  - Target: `Dockerfile`, `docker-compose.yml`, `.dockerignore`
  - Acceptance Criteria: Multi-stage container berbasis `python:3.11-slim` dengan ukuran *image* minimal (< 450MB) yang dapat dijalankan secara instan dengan `docker compose up -d`.
  - Verification Command: `docker build -t apexfin-ai:latest .`
* [x] **6.3 GitHub Actions CI Pipeline & Production Deployment Blueprint**
  - Target: `.github/workflows/ci.yml`, `docs/DEPLOYMENT.md`, `README.md`
  - Acceptance Criteria: Pipeline CI otomatis yang menjalankan Ruff linter, type-checking, dan Pytest. Dokumentasi panduan *one-click deployment* ke Hugging Face Spaces / Render / Vercel dengan kredensial gratis.

