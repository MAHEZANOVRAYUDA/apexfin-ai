# ApexFin AI: Actionable Implementation Checklist

- [x] **Phase 1: Foundation, Configuration & Domain Contracts**
  - [x] 1.1 Inisialisasi manifest proyek (`pyproject.toml`, `.env.example`, `.gitignore`)
  - [x] 1.2 Implementasi skema konfigurasi lingkungan (*fail-fast Pydantic settings*) di `src/config/settings.py`
  - [x] 1.3 Implementasi entitas domain murni dan standardisasi error RFC 7807 di `src/domain/entities.py`
  - [x] 1.4 Verifikasi pengujian unit untuk konfigurasi & entitas domain

- [x] **Phase 2: PDF Parsing & Table Extraction Engine**
  - [x] 2.1 Implementasi parser PDF berbasis koordinat dengan ekstraksi tabel Markdown di `src/ingestion/`
  - [x] 2.2 Implementasi chunking cerdas berbasis hierarki dan pengawetan tabel atomik di `src/ingestion/chunker.py`
  - [x] 2.3 Verifikasi pengujian unit untuk parser dan ekstraktor tabel PDF

- [x] **Phase 3: Hybrid Retrieval & Reranking Engine**
  - [x] 3.1 Integrasi FastEmbed ONNX (CPU-friendly) dan konektor Qdrant (dengan fallback in-memory) di `src/retrieval/`
  - [x] 3.2 Implementasi mesin pencari leksikal Rank-BM25 untuk istilah finansial di `src/retrieval/sparse_bm25.py`
  - [x] 3.3 Implementasi Reciprocal Rank Fusion (RRF) dan Cross-Encoder Re-ranker di `src/retrieval/`
  - [x] 3.4 Verifikasi pengujian unit & integrasi untuk hybrid search dan ranking

- [x] **Phase 4: Structured Generation, Guardrails & Fact Checking**
  - [x] 4.1 Implementasi dual client LLM asinkron (Groq Llama-3.3-70B + Gemini 2.0 Flash fallback) di `src/generation/llm_client.py`
  - [x] 4.2 Isolasi prompt XML, canary nonces, dan validasi skema Pydantic via Instructor di `src/generation/structured_engine.py`
  - [x] 4.3 Implementasi pemeriksa fakta numerik deterministik (*verbatim fact-checker*) di `src/generation/fact_checker.py`
  - [x] 4.4 Verifikasi pengujian integrasi LLM dan validasi anti-halusinasi

- [x] **Phase 5: FastAPI Layer & Craftsman High-Density UI**
  - [x] 5.1 Implementasi REST & SSE Streaming endpoint di `src/api/`
  - [x] 5.2 Pembuatan antarmuka visual bergaya *High-Density Data Engine* (Linear/Bloomberg) dengan 6 UI states di `src/web/`
  - [x] 5.3 Integrasi panel pratinjau dokumen PDF dengan penyorotan sitasi visual
  - [x] 5.4 Verifikasi endpoint API dan penanganan error RFC 7807

- [x] **Phase 6: Evaluation, Dockerization & Production Deployment**
  - [x] 6.1 Pembuatan skrip evaluasi kuantitatif benchmark RAG (Faithfulness & Answer Relevance) di `tests/evaluation/`
  - [x] 6.2 Pembuatan multi-stage Dockerfile dan docker-compose.yml
  - [x] 6.3 Pembuatan pipeline CI GitHub Actions dan dokumentasi rilis produksi di `README.md` & `docs/DEPLOYMENT.md`

