# =============================================================================
# FinVox Backend — Production Dockerfile
# =============================================================================
# Multi-stage build:
#   Stage 1 (builder) — installs all Python deps into a venv
#   Stage 2 (runtime) — copies only the venv + app code (no build tools)
#
# Build:  docker build -f Dockerfile.backend -t finvox-backend:latest .
# Run:    docker run --env-file .env -p 8000:8000 finvox-backend:latest
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1 — Builder
# Install all Python dependencies into an isolated virtual environment.
# This stage is discarded after the build; none of the build tools (pip, gcc,
# build-essential) end up in the final image.
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

# Build-time system deps needed to compile some Python packages
# (e.g. psycopg2-binary, lxml, onnxruntime wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libpq-dev \
        libffi-dev \
        libssl-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create and activate a virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Upgrade pip first for better resolver performance
RUN pip install --upgrade pip setuptools wheel

# Copy only requirements first — this layer is cached as long as
# requirements.txt hasn't changed (speeds up iterative rebuilds).
WORKDIR /build
COPY requirements.txt .

# Install all runtime dependencies
# --no-cache-dir   keeps the image lean
# --extra-index-url for PyTorch CPU-only wheel (avoids pulling ~2 GB CUDA build)
RUN pip install --no-cache-dir \
        --extra-index-url https://download.pytorch.org/whl/cpu \
        -r requirements.txt

# Install Playwright browser binaries (used by web-crawling tools)
RUN playwright install chromium --with-deps || true


# -----------------------------------------------------------------------------
# Stage 2 — Runtime
# Minimal image that only contains the venv and application source code.
# No compilers, no pip, no build artifacts.
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# -- Runtime system libraries --------------------------------------------------
# libpq5       -> psycopg2 shared library
# libgomp1     -> OpenMP (required by some ONNX / torch CPU ops)
# ca-certificates -> SSL verification for outbound API calls
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        libgomp1 \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

# -- Security: run as non-root -------------------------------------------------
RUN groupadd --gid 1001 finvox \
    && useradd  --uid 1001 --gid finvox --shell /bin/bash --create-home finvox

# -- Copy virtualenv from builder ----------------------------------------------
COPY --from=builder /opt/venv /opt/venv

# Copy Playwright browser binaries if installed
COPY --from=builder /root/.cache/ms-playwright /home/finvox/.cache/ms-playwright

# Activate venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# -- Pre-download HuggingFace embedding model ---------------------------------
# Bake BAAI/bge-large-en-v1.5 into the image at build time so startup is instant.
# Model is cached to /app/.hf_cache — avoids slow download on every container start.
# NOTE: single-line python -c used because Docker misinterprets multiline 'from ...' as a FROM instruction
ENV HF_HOME=/app/.hf_cache
RUN python -c "from sentence_transformers import SentenceTransformer; print('Baking BAAI/bge-large-en-v1.5 into image...'); SentenceTransformer('BAAI/bge-large-en-v1.5'); print('Model ready!')"

# -- Copy application source ---------------------------------------------------
WORKDIR /app

# Copy source code (only what the runtime needs)
COPY src/       ./src/
COPY config/    ./config/
COPY data/      ./data/
# runtime dep: ingest_service/pipeline.py imports scripts.ingest_file
COPY scripts/   ./scripts/

# -- Environment defaults -------------------------------------------------------
# These are non-secret defaults. Secrets (API keys) must be passed via
# --env-file or Docker secrets at runtime — NEVER baked into the image.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    HOST=0.0.0.0 \
    DEV_MODE=0 \
    LOG_LEVEL=info \
    HF_HOME=/app/.hf_cache

# -- Fix ownership -------------------------------------------------------------
RUN chown -R finvox:finvox /app /home/finvox

# Switch to non-root user
USER finvox

# -- Health check --------------------------------------------------------------
# Pings the /health endpoint every 30 s; marks the container unhealthy after
# 3 consecutive failures (useful for Compose / Kubernetes readiness probes).
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# -- Expose port ---------------------------------------------------------------
EXPOSE 8000

# -- Entry point ---------------------------------------------------------------
CMD ["python", "src/api/run.py"]
