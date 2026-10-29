# Production Deployment & Operations Guide

> **ApexFin AI** is engineered from First Principles to run on a **100% Free, Open-Source, and Self-Hostable** stack. This guide documents deployment strategies for local production environments, Docker orchestration, and zero-cost cloud deployment (Hugging Face Spaces / Render).

---

## 1. Zero-Cost Production Stack Overview

| Component | Free-Tier Provider / Engine | Role | Spec / Limit |
|---|---|---|---|
| **Primary LLM** | Groq Cloud (`Llama-3.3-70B-Versatile`) | Fast Structured Synthesis | ~300 tokens/sec, 30 RPM free |
| **Fallback LLM** | Google AI Studio (`Gemini-2.0-Flash`) | Rate-limit Failover | 15 RPM, 1M context window free |
| **Vector DB** | Qdrant Cloud Free Tier (or Local Docker) | 384-d Dense Indexing | 1 Cluster (1GB RAM) free forever |
| **Embeddings** | FastEmbed ONNX (`bge-small-en-v1.5`) | CPU Dense Embeddings | Zero GPU required (< 200MB RAM) |
| **Hosting** | Hugging Face Spaces / Render Free Tier | FastAPI + Craftsman Web UI | Free Docker container |

---

## 2. Docker Compose Deployment (Recommended for Local & VPS)

### Prerequisites
- Docker Engine $\ge 24.0$
- Docker Compose $\ge 2.20$
- Free API Keys:
  - [Groq Console](https://console.groq.com)
  - [Google AI Studio](https://aistudio.google.com)

### Quickstart
1. Clone the repository and navigate into the root directory:
   ```bash
   git clone https://github.com/mahezanovrayuda/apexfin-ai.git
   cd apexfin-ai
   ```

2. Configure environment credentials:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and fill in your keys:
   ```env
   GROQ_API_KEY=gsk_your_groq_api_key_here
   GEMINI_API_KEY=AIzaSy_your_gemini_api_key_here
   ENVIRONMENT=production
   ```

3. Launch orchestration:
   ```bash
   docker compose up -d --build
   ```

4. Verify service health:
   ```bash
   docker compose ps
   curl http://localhost:8000/health
   ```

5. Access the High-Density Web UI in your browser at `http://localhost:8000`.

---

## 3. Deploying to Hugging Face Spaces (100% Free Cloud)

Hugging Face Spaces offers free 16 GB RAM CPU instances with Docker support:

1. Create a new Space on [Hugging Face Spaces](https://huggingface.co/spaces).
2. Select **Docker** as the Space SDK and choose the **Blank** template.
3. In your Space's **Settings** $\rightarrow$ **Variables and secrets**, add:
   - Secret `GROQ_API_KEY`: Your Groq API key
   - Secret `GEMINI_API_KEY`: Your Gemini API key
   - Variable `ENVIRONMENT`: `production`
   - Variable `QDRANT_URL`: `:memory:` (or your free Qdrant Cloud cluster endpoint)
4. Push the ApexFin repository to the Hugging Face Space Git remote:
   ```bash
   git remote add space https://huggingface.co/spaces/YOUR_USERNAME/apexfin-ai
   git push space main
   ```
5. Hugging Face builds the multi-stage `Dockerfile` automatically and launches the application at `https://YOUR_USERNAME-apexfin-ai.hf.space`.

---

## 4. Deploying to Render.com (Free Web Service)

1. Create a **New Web Service** from your GitHub repository on [Render](https://render.com).
2. Select **Docker** runtime.
3. Under Environment Variables:
   - `ENVIRONMENT` = `production`
   - `GROQ_API_KEY` = your secret
   - `GEMINI_API_KEY` = your secret
   - `QDRANT_URL` = `:memory:` (or remote Qdrant Cloud URL)
4. Deploy service. Render automatically probes `/health` to confirm healthy deployment.

---

## 5. Security & DevSecOps Hardening (OWASP Compliance)

- **Non-Root User Container Execution:** The `Dockerfile` drops root privileges and executes as unprivileged user `apexuser` (UID 10001).
- **Network Isolation:** Qdrant internal gRPC port `6334` is isolated inside Docker network bridge.
- **Fail-Fast Startup Gate:** Application validates all configuration and credentials during boot via Pydantic Settings before opening socket connections.
- **Canary Injection Defense:** Every LLM synthesis session dynamically generates an unpredictable 16-byte hex cryptographic nonce (`<financial_context nonce="...">`). Prompt injection attempts that compromise the boundary are caught and terminated with RFC 7807 `422 Unprocessable Content`.

