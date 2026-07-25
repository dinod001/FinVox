import json
import time
from typing import List
from sqlalchemy import text

from src.memory.schemas import Episode, EpisodicStore, ConversationTurn
from src.infrastructure.db.crm_client import engine
from src.infrastructure.log import log
from src.infrastructure.config import EMBEDDING_DIM
from src.infrastructure.llm.embeddings import get_embeddings

class PostgresEpisodicStore(EpisodicStore):
    """
    Episodic memory store using Supabase Postgres with pgvector.
    Stores conversation session summaries with embeddings for semantic retrieval.
    """

    def __init__(self):
        """Initialize the store, embedder, and ensure the vector table exists."""
        self.embedder = get_embeddings()
        self._ensure_table()

    def _ensure_table(self):
        """Creates the mem_episodes table with pgvector if it doesn't exist."""
        if not engine:
            log.error("Database engine not initialized. Cannot create mem_episodes.")
            return

        create_extension_sql = "CREATE EXTENSION IF NOT EXISTS vector;"
        
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS mem_episodes (
            id TEXT PRIMARY KEY,
            user_id VARCHAR(50) NOT NULL REFERENCES users(username) ON DELETE CASCADE,
            session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
            summary TEXT NOT NULL,
            embedding VECTOR({EMBEDDING_DIM}),
            topic_tags JSONB DEFAULT '[]'::jsonb,
            turns JSONB DEFAULT '[]'::jsonb,
            start_at DOUBLE PRECISION,
            end_at DOUBLE PRECISION,
            turn_count INTEGER DEFAULT 0,
            ttl_at DOUBLE PRECISION
        );
        """
        
        # HNSW Index for fast similarity search
        create_index_sql = """
        CREATE INDEX IF NOT EXISTS idx_mem_episodes_embedding 
        ON mem_episodes USING hnsw (embedding vector_cosine_ops);
        """
        
        try:
            with engine.begin() as conn:
                conn.execute(text(create_extension_sql))
                conn.execute(text(create_table_sql))
                conn.execute(text(create_index_sql))
            log.info(f"✓ mem_episodes table (dim={EMBEDDING_DIM}) checked/created successfully.")
        except Exception as e:
            log.error(f"Failed to ensure mem_episodes table: {e}")

    def upsert(self, episode: Episode) -> None:
        """
        Insert or update a conversation episode.
        Generates an embedding for the summary before storing.
        """
        if not engine:
            return

        try:
            # 1. Generate embedding for the episode summary
            log.info(f"Generating embedding for episode summary (ID: {episode.id})...")
            embedding = self.embedder.embed_query(episode.summary)
        except Exception as e:
            log.error(f"Failed to generate embedding for episode {episode.id}: {e}")
            return

        # 2. Upsert into database
        upsert_sql = """
        INSERT INTO mem_episodes (id, user_id, session_id, summary, embedding, topic_tags, turns, start_at, end_at, turn_count, ttl_at)
        VALUES (:id, :uid, CAST(:sid AS UUID), :sum, :emb, :tags, :turns, :start, :end, :count, :ttl)
        ON CONFLICT (id) DO UPDATE SET
            summary = EXCLUDED.summary,
            embedding = EXCLUDED.embedding,
            topic_tags = EXCLUDED.topic_tags,
            turns = EXCLUDED.turns,
            start_at = EXCLUDED.start_at,
            end_at = EXCLUDED.end_at,
            turn_count = EXCLUDED.turn_count,
            ttl_at = EXCLUDED.ttl_at;
        """
        
        # Convert turns list to list of dicts for JSONB storage
        turns_data = [turn.to_dict() for turn in episode.turns]
        
        try:
            with engine.begin() as conn:
                conn.execute(
                    text(upsert_sql),
                    {
                        "id": episode.id,
                        "uid": episode.user_id,
                        "sid": episode.session_id,
                        "sum": episode.summary,
                        "emb": str(embedding),
                        "tags": json.dumps(episode.topic_tags),
                        "turns": json.dumps(turns_data),
                        "start": episode.start_at,
                        "end": episode.end_at,
                        "count": episode.turn_count,
                        "ttl": episode.ttl_at
                    }
                )
            log.info(f"Successfully upserted episode {episode.id} into Episodic Memory.")
        except Exception as e:
            log.error(f"Failed to upsert memory episode: {e}")

    def query(
        self,
        user_id: str,
        text_query: str,
        k: int,
        threshold: float,
    ) -> List[Episode]:
        """
        Retrieve the top-K most semantically similar episodes using Cosine Similarity.
        Only returns episodes where similarity >= threshold.
        """
        if not engine:
            return []

        # 1. Embed the search query
        try:
            query_embedding = self.embedder.embed_query(text_query)
        except Exception as e:
            log.error(f"Failed to embed search query: {e}")
            return []

        # 2. Search using pgvector cosine distance (<=>)
        max_distance = 1.0 - threshold

        search_sql = """
        SELECT id, user_id, CAST(session_id AS TEXT), summary, topic_tags, turns, start_at, end_at, turn_count, ttl_at,
               1 - (embedding <=> :q_emb) AS similarity
        FROM mem_episodes
        WHERE user_id = :uid 
          AND (embedding <=> :q_emb) <= :max_dist
          AND (ttl_at IS NULL OR ttl_at > :now)
        ORDER BY embedding <=> :q_emb
        LIMIT :k;
        """

        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text(search_sql),
                    {
                        "q_emb": str(query_embedding),
                        "uid": user_id,
                        "max_dist": max_distance,
                        "now": time.time(),
                        "k": k
                    }
                )
                rows = result.fetchall()

                episodes = []
                for row in rows:
                    raw_tags = row[4]
                    raw_turns = row[5]
                    
                    tags = raw_tags if isinstance(raw_tags, list) else json.loads(raw_tags)
                    turns_data = raw_turns if isinstance(raw_turns, list) else json.loads(raw_turns)
                    
                    turns = [ConversationTurn.from_dict(t) for t in turns_data]
                    
                    episodes.append(
                        Episode(
                            id=row[0],
                            user_id=row[1],
                            session_id=row[2],
                            summary=row[3],
                            topic_tags=tags,
                            turns=turns,
                            start_at=row[6],
                            end_at=row[7],
                            turn_count=row[8],
                            ttl_at=row[9]
                        )
                    )
                return episodes
        except Exception as e:
            log.error(f"Failed to query Episodic Memory: {e}")
            return []

    def decay_and_prune(self, now: float) -> int:
        """
        Hard delete expired episodes (ttl_at < now).
        Returns the number of rows deleted.
        """
        if not engine:
            return 0
            
        prune_sql = """
        DELETE FROM mem_episodes 
        WHERE (ttl_at IS NOT NULL AND ttl_at < :now)
        """
        try:
            with engine.begin() as conn:
                result = conn.execute(text(prune_sql), {"now": now})
                return result.rowcount
        except Exception as e:
            log.error(f"Failed to decay/prune memory episodes: {e}")
            return 0
