import asyncio
import uuid
from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Request
from loguru import logger
from sqlalchemy import text

from src.infrastructure.db.crm_client import engine
from src.api.schemas import (
    ChatSessionCreateRequest,
    ChatSessionListResponse,
    ChatSessionMeta,
    ChatSessionUpdateRequest,
)

router = APIRouter(prefix="/chat_sessions", tags=["Chat sessions"])

# ── Helpers ─────────────────────────────────────────────────────────

def _gen_session_id() -> str:
    return str(uuid.uuid4())

def _default_title() -> str:
    now = datetime.now(timezone.utc)
    return f"Conversation {now.strftime('%Y-%m-%d %H:%M')}"

def _to_meta(row) -> ChatSessionMeta:
    # row is a SQLAlchemy RowMapping/dict-like object
    return ChatSessionMeta(
        id=str(row.id),
        user_id=row.user_id,
        title=row.title,
        created_at=row.created_at.isoformat() if hasattr(row.created_at, 'isoformat') else str(row.created_at),
        updated_at=row.updated_at.isoformat() if hasattr(row.updated_at, 'isoformat') else str(row.updated_at),
    )

def touch_session_sync(user_id: str, session_id: str) -> None:
    """
    Ensure a chat_sessions row exists for (user_id, session_id) and
    bump its ``updated_at`` to now.
    Called from the chat hot path on every successful reply.
    """
    try:
        with engine.begin() as conn:
            # Upsert logic for PostgreSQL
            upsert_sql = """
                INSERT INTO chat_sessions (id, user_id, title, updated_at)
                VALUES (:sid, :uid, :title, NOW())
                ON CONFLICT (id) DO UPDATE 
                SET updated_at = NOW();
            """
            conn.execute(text(upsert_sql), {
                "sid": session_id,
                "uid": user_id,
                "title": _default_title()
            })
    except Exception as exc:
        logger.warning(f"touch_session failed for {user_id}/{session_id}: {exc}")

# ── Endpoints ───────────────────────────────────────────────────────

@router.get("", response_model=ChatSessionListResponse)
async def list_sessions(
    request: Request,
    user_id: str = Query(..., min_length=1, description="Username/user_id"),
    limit: int = Query(100, ge=1, le=500),
) -> ChatSessionListResponse:
    """List a user's chat sessions, newest activity first."""
    engine = request.app.state.db_engine
    def _query():
        with engine.connect() as conn:
            sql = """
                SELECT id, user_id, title, created_at, updated_at
                FROM chat_sessions
                WHERE user_id = :uid
                ORDER BY updated_at DESC, created_at DESC
                LIMIT :limit
            """
            result = conn.execute(text(sql), {"uid": user_id, "limit": limit})
            return result.fetchall()

    rows = await asyncio.to_thread(_query)
    return ChatSessionListResponse(sessions=[_to_meta(r) for r in rows])


@router.post("", response_model=ChatSessionMeta, status_code=201)
async def create_session(request: Request, req: ChatSessionCreateRequest) -> ChatSessionMeta:
    """Create a new session row. A UUID is auto-generated."""
    engine = request.app.state.db_engine
    def _insert():
        sid = _gen_session_id()
        title = req.title or _default_title()
        with engine.begin() as conn:
            sql = """
                INSERT INTO chat_sessions (id, user_id, title)
                VALUES (:sid, :uid, :title)
                RETURNING id, user_id, title, created_at, updated_at;
            """
            result = conn.execute(text(sql), {
                "sid": sid,
                "uid": req.user_id,
                "title": title
            })
            return result.fetchone()

    try:
        row = await asyncio.to_thread(_insert)
        if not row:
            raise HTTPException(status_code=500, detail="Failed to create session.")
        return _to_meta(row)
    except Exception as e:
        logger.error(f"Failed to create chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{session_id}", response_model=ChatSessionMeta)
async def update_session(request: Request, session_id: str, req: ChatSessionUpdateRequest) -> ChatSessionMeta:
    """Rename a chat session."""
    engine = request.app.state.db_engine
    def _update():
        with engine.begin() as conn:
            sql = """
                UPDATE chat_sessions
                SET title = :title, updated_at = NOW()
                WHERE id = :sid
                RETURNING id, user_id, title, created_at, updated_at;
            """
            result = conn.execute(text(sql), {
                "title": req.title.strip(),
                "sid": session_id
            })
            return result.fetchone()

    row = await asyncio.to_thread(_update)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return _to_meta(row)


@router.delete("/{session_id}")
async def delete_session(request: Request, session_id: str) -> dict:
    """Hard-delete a session. Associated chat_messages are dropped via CASCADE."""
    engine = request.app.state.db_engine
    def _delete():
        with engine.begin() as conn:
            sql = "DELETE FROM chat_sessions WHERE id = :sid"
            result = conn.execute(text(sql), {"sid": session_id})
            return result.rowcount > 0

    ok = await asyncio.to_thread(_delete)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"deleted": True, "session_id": session_id}


@router.get("/{session_id}/messages")
async def get_session_messages(request: Request, session_id: str, limit: int = Query(100, ge=1, le=500)):
    """Fetch chat history for a session."""
    engine = request.app.state.db_engine
    def _query():
        with engine.connect() as conn:
            sql = """
                SELECT id, role, content, ts, created_at
                FROM chat_messages
                WHERE session_id = CAST(:sid AS UUID)
                ORDER BY ts ASC
                LIMIT :limit
            """
            result = conn.execute(text(sql), {"sid": session_id, "limit": limit})
            # Convert to dict list for JSON serialization
            return [dict(r._mapping) for r in result]

    try:
        rows = await asyncio.to_thread(_query)
        # Convert timestamp to string if needed
        for row in rows:
            if hasattr(row['id'], '__str__'): row['id'] = str(row['id'])
            if hasattr(row['created_at'], 'isoformat'): row['created_at'] = row['created_at'].isoformat()
        return rows
    except Exception as e:
        logger.error(f"Failed to fetch messages for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error")
