"""
Enqueue helper — pushes post-turn bookkeeping jobs onto the Arq/Redis queue.

Usage:
    from src.workers.enqueue import enqueue_chat_bookkeeping
    await enqueue_chat_bookkeeping(user_id=..., session_id=..., ...)

If Redis is down or ARQ_WORKER_ENABLED is not set, returns False and the
caller falls back to inline FastAPI BackgroundTasks — no silent data loss.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

from loguru import logger

# ── Config ────────────────────────────────────────────────────────────────────

REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
WORKER_ENABLED: bool = os.getenv("ARQ_WORKER_ENABLED", "false").lower() in ("true", "1", "yes")

# ── Redis pool (lazy, one per process) ────────────────────────────────────────

_pool = None


async def _get_pool():
    """Create the Arq Redis pool once and reuse it."""
    global _pool
    if _pool is None:
        from arq import create_pool
        from arq.connections import RedisSettings

        parsed = urlparse(REDIS_URL)
        _pool = await create_pool(RedisSettings(
            host=parsed.hostname or "redis",
            port=parsed.port or 6379,
            database=int((parsed.path or "/0").lstrip("/") or "0"),
            password=parsed.password,
        ))
    return _pool


# ── Public API ────────────────────────────────────────────────────────────────

async def enqueue_chat_bookkeeping(
    *,
    user_id: str,
    session_id: str,
    user_message: str,
    assistant_message: str,
) -> bool:
    """
    Enqueue 3 post-turn background jobs:
        1. save_chat_turn     — persist the turn to short-term memory
        2. auto_title_session — LLM-rename session if still default
        3. distill_facts      — extract long-term facts every N turns

    Returns True if enqueued successfully, False if caller should fall back
    to inline BackgroundTasks.
    """
    if not WORKER_ENABLED:
        return False

    try:
        pool = await _get_pool()
        await pool.enqueue_job("save_chat_turn",
            user_id=user_id,
            session_id=session_id,
            user_message=user_message,
            assistant_message=assistant_message,
        )
        await pool.enqueue_job("auto_title_session",
            user_id=user_id,
            session_id=session_id,
        )
        await pool.enqueue_job("distill_facts",
            user_id=user_id,
            session_id=session_id,
        )
        return True
    except Exception as exc:
        logger.warning(f"Arq enqueue failed — falling back to BackgroundTasks: {exc}")
        return False
