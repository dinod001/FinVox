import asyncio
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from loguru import logger

# Import Core Infrastructure
from src.infrastructure.db.crm_client import engine
from src.infrastructure.db.qdrant_client import get_qdrant_client
from src.infrastructure.llm.embeddings import get_embeddings
from src.infrastructure.llm.llm_provider import get_chat_llm, get_router_llm
from src.agents.orchestrator import AgentOrchestrator

# Import Routers and Middleware
from src.api.middleware import ProcessTimeMiddleware
from src.api.routers import health, auth, chat_sessions, ingestion, chat

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup (Warmup) and Shutdown events.
    Concurrently warms up DB, Embeddings, LLMs (Chat & Router), and Qdrant Vector DB 
    to eliminate cold-start latency for incoming user queries.
    """
    logger.info("Initializing FinVox Server Concurrent Warmup Sequence...")

    async def _warmup_db():
        def _exec():
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            # Ensure core utility tables exist
            from src.infrastructure.db.table_manager import ensure_table_registry, ensure_kpi_registry
            ensure_table_registry()
            ensure_kpi_registry()
            
        try:
            await asyncio.to_thread(_exec)
            logger.info("✓ Database connection established and registries verified")
        except Exception as e:
            logger.error(f"✗ Database warmup failed: {e}")

    async def _warmup_embeddings():
        try:
            embedder = get_embeddings()
            await asyncio.to_thread(embedder.embed_query, "warmup")
            logger.info("✓ Embeddings model loaded and warmed up")
            return embedder
        except Exception as e:
            logger.error(f"✗ Embeddings warmup failed: {e}")
            return None

    async def _warmup_llms():
        try:
            chat_llm = get_chat_llm()
            router_llm = get_router_llm()
            await asyncio.gather(
                asyncio.to_thread(chat_llm.invoke, "ping"),
                asyncio.to_thread(router_llm.invoke, "ping"),
                return_exceptions=True
            )
            logger.info("✓ Chat & Router LLMs connected and warmed up")
            return chat_llm
        except Exception as e:
            logger.error(f"✗ LLM warmup failed: {e}")
            return None

    async def _warmup_qdrant():
        try:
            def _exec():
                qc = get_qdrant_client()
                qc.get_collections()
                return qc
            qc = await asyncio.to_thread(_exec)
            logger.info("✓ Qdrant Vector DB connection established")
            return qc
        except Exception as e:
            logger.error(f"✗ Qdrant Vector DB warmup failed: {e}")
            return None

    # Run all heavy network and model warmups concurrently
    _, embedder, llm, qdrant_client = await asyncio.gather(
        _warmup_db(),
        _warmup_embeddings(),
        _warmup_llms(),
        _warmup_qdrant(),
        return_exceptions=True
    )

    # Initialize Orchestrator (Singletons loaded into app.state)
    logger.info("Building Agent Orchestrator Singletons...")
    orchestrator = await asyncio.to_thread(AgentOrchestrator)
    
    app.state.orchestrator = orchestrator
    app.state.llm = llm
    app.state.embedder = embedder
    app.state.db_engine = engine
    app.state.qdrant = qdrant_client
    
    logger.info("✓ Orchestrator, Models, DB Engine & Qdrant injected into app state")
    logger.info("FinVox API is fully warmed up and ready to accept traffic! 🚀")

    yield  # Server is running

    logger.info("Shutting down FinVox Server...")
    if engine:
        engine.dispose()


# Initialize FastAPI App
app = FastAPI(
    title="FinVox API",
    description="Backend API for FinVox AI Assistant",
    version="1.0.0",
    lifespan=lifespan
)

# ── Middleware Configuration ──────────────────────────────────────────

# 1. Custom Process Time Logging Middleware
app.add_middleware(ProcessTimeMiddleware)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production to specific frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global Exception Handler ────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler to prevent raw stack traces from reaching clients."""
    req_id = str(uuid.uuid4())
    logger.exception(f"Unhandled error on {request.method} {request.url.path} [req_id={req_id}]")
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": req_id},
        headers={"x-request-id": req_id},
    )

# ── Routers Configuration ───────────────────────────────────────────

from src.api.routers import health, auth, chat_sessions, ingestion, chat, management, kpis

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(chat_sessions.router)
app.include_router(ingestion.router)
app.include_router(chat.router)
app.include_router(kpis.router)
app.include_router(management.router)
