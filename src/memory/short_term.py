from typing import List
from sqlalchemy import text

from src.memory.schemas import ConversationTurn, ShortTermStore
from src.infrastructure.db.crm_client import engine
from src.infrastructure.log import log


class PostgresShortTermStore(ShortTermStore):
    """
    Short-term memory store using Supabase Postgres.
    Implements the ShortTermStore protocol.
    """

    def __init__(self):
        """Initialize the store and ensure the table exists."""
        self._ensure_table()

    def _ensure_table(self):
        """Creates the st_turns table if it doesn't exist."""
        if not engine:
            log.error("Database engine not initialized. Cannot create st_turns.")
            return

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id UUID NOT NULL,
            user_id VARCHAR(50) NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            ts DOUBLE PRECISION NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        -- Index for fast retrieval of recent messages for a specific session
        CREATE INDEX IF NOT EXISTS idx_chat_messages_session_ts ON chat_messages(session_id, ts DESC);
        """
        try:
            with engine.begin() as conn:
                conn.execute(text(create_table_sql))
            log.info("✓ chat_messages table checked/created successfully.")
        except Exception as e:
            log.error(f"Failed to ensure chat_messages table: {e}")

    def append(
        self,
        turn: ConversationTurn,
        max_turns: int,
        ttl_seconds: int,
    ) -> None:
        """
        Add a new turn to the chat_messages table.
        (Pruning has been removed to preserve full chat history for the frontend).
        """
        if not engine:
            return

        # Calculate the expiration threshold based on TTL
        expiry_ts = turn.ts - ttl_seconds

        try:
            with engine.begin() as conn:
                # 1. Insert the new turn
                insert_sql = """
                INSERT INTO chat_messages (user_id, session_id, role, content, ts)
                VALUES (:u, CAST(:s AS UUID), :r, :c, :t)
                """
                conn.execute(
                    text(insert_sql),
                    {
                        "u": turn.user_id,
                        "s": turn.session_id,
                        "r": turn.role,
                        "c": turn.content,
                        "t": turn.ts
                    }
                )

                # 2. Delete messages older than the TTL for this session
                # [REMOVED]: We no longer delete messages because chat_messages acts as permanent chat history.
                
                # 3. Prune to keep only max_turns (Ring Buffer logic)
                # [REMOVED]: The LLM context is kept small safely because `recent()` uses `LIMIT K`.
                
        except Exception as e:
            log.error(f"Failed to append to ShortTermStore: {e}")

    def recent(
        self,
        user_id: str,
        session_id: str,
        k: int,
    ) -> List[ConversationTurn]:
        """
        Retrieve the most recent `k` turns for a given session.
        Results are returned in chronological order (oldest first).
        """
        if not engine:
            return []

        try:
            with engine.connect() as conn:
                # Fetch newest K messages, but we order by DESC to limit, 
                # then we must reverse them to return in normal conversational order (ASC).
                select_sql = """
                SELECT user_id, CAST(session_id AS TEXT), role, content, ts
                FROM chat_messages
                WHERE session_id = CAST(:s AS UUID) AND user_id = :u
                ORDER BY ts DESC
                LIMIT :k
                """
                result = conn.execute(text(select_sql), {"s": session_id, "u": user_id, "k": k})
                rows = result.fetchall()

                # Convert to objects
                turns = [
                    ConversationTurn(
                        user_id=row[0],
                        session_id=row[1],
                        role=row[2],
                        content=row[3],
                        ts=row[4]
                    )
                    for row in rows
                ]
                
                # Reverse the list so the oldest is first, newest is last (chronological)
                turns.reverse()
                return turns
                
        except Exception as e:
            log.error(f"Failed to fetch from ShortTermStore: {e}")
            return []
