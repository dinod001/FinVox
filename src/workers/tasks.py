"""
Arq background worker tasks — non-blocking post-turn bookkeeping.

Run with:
    arq src.workers.tasks.WorkerSettings

Tasks:
    save_chat_turn     — write user + assistant turn to short-term memory
    auto_title_session — LLM-rename the session if still using default title
    distill_facts      — extract long-term memory facts from recent turns
"""

from __future__ import annotations

import os
import time
from urllib.parse import urlparse

from arq.connections import RedisSettings
from loguru import logger

# ── Redis settings ─────────────────────────────────────────────────────────────

def _redis_settings() -> RedisSettings:
    url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    parsed = urlparse(url)
    return RedisSettings(
        host=parsed.hostname or "redis",
        port=parsed.port or 6379,
        database=int((parsed.path or "/0").lstrip("/") or "0"),
        password=parsed.password,
    )


# ── Worker lifecycle ───────────────────────────────────────────────────────────

async def _startup(ctx: dict) -> None:
    """Build the orchestrator once at worker boot — reused across all jobs."""
    from dotenv import find_dotenv, load_dotenv
    load_dotenv(find_dotenv(usecwd=True))

    from src.infrastructure.log import setup_logging
    setup_logging()

    logger.info("Arq worker starting — building orchestrator...")
    from src.agents.orchestrator import AgentOrchestrator
    ctx["orchestrator"] = AgentOrchestrator()
    logger.success("Arq worker ready.")


async def _shutdown(ctx: dict) -> None:
    logger.info("Arq worker shutting down.")


# ── Tasks ──────────────────────────────────────────────────────────────────────

async def save_chat_turn(
    ctx: dict,
    *,
    user_id: str,
    session_id: str,
    user_message: str,
    assistant_message: str,
) -> dict:
    """Persist one user + assistant turn into short-term memory."""
    orchestrator = ctx["orchestrator"]
    try:
        orchestrator.memory_manager.process_user_message(user_id, session_id, user_message)
        orchestrator.memory_manager.save_assistant_message(user_id, session_id, assistant_message)
        logger.debug(f"save_chat_turn: session={session_id} user={user_id}")
        return {"status": "ok", "session_id": session_id}
    except Exception as exc:
        logger.error(f"save_chat_turn failed: {exc}")
        raise


async def auto_title_session(
    ctx: dict,
    *,
    user_id: str,
    session_id: str,
) -> dict:
    """LLM-rename the session if it still has the default title."""
    orchestrator = ctx["orchestrator"]
    try:
        from src.api.routers.chat_sessions import maybe_auto_title_sync
        llm = getattr(orchestrator, "llm_fast", None) or orchestrator.llm_chat
        maybe_auto_title_sync(
            session_id=session_id,
            user_id=user_id,
            st_store=orchestrator.st_store,
            llm=llm,
        )
        return {"status": "ok"}
    except Exception as exc:
        logger.warning(f"auto_title_session failed (non-fatal): {exc}")
        return {"status": "skipped", "reason": str(exc)}


async def distill_facts(
    ctx: dict,
    *,
    user_id: str,
    session_id: str,
) -> dict:
    """Extract long-term memory facts from recent turns if heuristic triggers."""
    orchestrator = ctx["orchestrator"]
    try:
        recent = orchestrator.st_store.recent(user_id, session_id, k=5)
        if orchestrator.distiller.should_distill(recent):
            logger.info(f"distill_facts: triggering LT distillation for {user_id}")
            orchestrator.distiller.distill(user_id, recent)
        return {"status": "ok"}
    except Exception as exc:
        logger.warning(f"distill_facts failed (non-fatal): {exc}")
        return {"status": "skipped", "reason": str(exc)}


# ── Arq WorkerSettings ─────────────────────────────────────────────────────────

class WorkerSettings:
    """Arq picks this up via: arq src.workers.tasks.WorkerSettings"""

    functions       = [save_chat_turn, auto_title_session, distill_facts]
    redis_settings  = _redis_settings()
    on_startup      = _startup
    on_shutdown     = _shutdown

    max_jobs                = 10
    job_timeout             = 60        # seconds — anything longer is a bug
    keep_result             = 300       # 5 min result history for debugging
    health_check_interval   = 30
