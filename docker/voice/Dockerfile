# =============================================================================
# FinVox Voice Agent — Production Dockerfile
# =============================================================================
# Multi-stage build:
#   Stage 1 (builder) — installs Python deps (same venv as backend)
#   Stage 2 (runtime) — runs the LiveKit voice worker
#
# The voice agent is a SEPARATE process from the FastAPI backend because:
#   - LiveKit agents use a persistent WebSocket connection to LiveKit Cloud
#   - It needs a long-running worker process (not HTTP request/response)
#   - Can be scaled independently from the API
#   - Has different resource needs (audio processing, Silero VAD, TTS/STT)
#
# Build:  docker build -f docker/voice/Dockerfile -t finvox-voice:latest .
# Run:    docker run --env-file .env finvox-voice:latest
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1 — Builder
# Same as backend — installs all Python deps into a venv.
# We share the same requirements.txt since voice imports src.agents.orchestrator
# (the full agent brain), Silero VAD, torch, deepgram-sdk, elevenlabs, etc.
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

# Build-time system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libpq-dev \
        libffi-dev \
        libssl-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --upgrade pip setuptools wheel

WORKDIR /build
COPY requirements.txt .

# Install all deps with CPU-only PyTorch
# (Silero VAD uses torch — GPU not needed for inference)
RUN pip install --no-cache-dir \
        --extra-index-url https://download.pytorch.org/whl/cpu \
        -r requirements.txt


# -----------------------------------------------------------------------------
# Stage 2 — Runtime
# Minimal image — just the venv + app source + voice worker entrypoint.
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# Runtime system deps
# libpq5    -> psycopg2 (orchestrator accesses Supabase DB)
# libgomp1  -> OpenMP required by torch/onnxruntime (Silero VAD)
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

# Activate venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# -- Pre-download HuggingFace embedding model ---------------------------------
# Voice imports AgentOrchestrator which uses the same HF embedding model.
# Bake it in at build time so startup is instant.
ENV HF_HOME=/app/.hf_cache
RUN python -c "from sentence_transformers import SentenceTransformer; print('Baking BAAI/bge-large-en-v1.5 into voice image...'); SentenceTransformer('BAAI/bge-large-en-v1.5'); print('Model ready!')"

# -- Copy application source ---------------------------------------------------
WORKDIR /app

COPY src/       ./src/
COPY config/    ./config/
COPY data/      ./data/
# runtime dep: orchestrator chain imports scripts.ingest_file
COPY scripts/   ./scripts/

# -- Environment defaults -------------------------------------------------------
# NEVER bake secrets into the image — pass via --env-file at runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    HF_HOME=/app/.hf_cache

# -- Fix ownership -------------------------------------------------------------
RUN chown -R finvox:finvox /app /home/finvox

USER finvox

# -- Health check --------------------------------------------------------------
# LiveKit agents don't expose an HTTP port by default.
# We check that the Python process is alive using a process check.
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep -f "src/voice/run.py" || exit 1

# -- Entry point ---------------------------------------------------------------
# LiveKit agents CLI starts the persistent worker process.
# `start` mode = production (connects to LiveKit Cloud and waits for jobs)
CMD ["python", "src/voice/run.py", "start"]
