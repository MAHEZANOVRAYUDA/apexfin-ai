# ==============================================================================
# Multi-Stage Production Dockerfile for ApexFin AI
# Hardened for OWASP security, non-root execution, minimal image footprint (<450MB)
# ==============================================================================

# Stage 1: Build Dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir .

# Stage 2: Hardened Production Runtime
FROM python:3.11-slim AS runner

WORKDIR /app

# Install curl for container healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production \
    APP_PORT=8000

# Create secure non-root user and group
RUN groupadd -g 10001 apexgroup && \
    useradd -u 10001 -g apexgroup -s /bin/bash -m apexuser

# Copy application source code and assets
COPY --chown=apexuser:apexgroup src/ /app/src/
COPY --chown=apexuser:apexgroup sample_data/ /app/sample_data/
COPY --chown=apexuser:apexgroup pyproject.toml /app/pyproject.toml

USER apexuser

EXPOSE 8000

# Container health probe checking RFC 7807 compliant health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

