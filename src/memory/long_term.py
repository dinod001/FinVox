import json
import time
from typing import List, Iterable
from sqlalchemy import text

from src.memory.schemas import MemoryFact, LongTermStore
from src.infrastructure.db.crm_client import engine
from src.infrastructure.log import log
from src.infrastructure.config import EMBEDDING_DIM
from src.infrastructure.llm.embeddings import get_embeddings

class PostgresLongTermStore(LongTermStore):
    """
    Long-term memory store using Supabase Postgres with pgvector.
    Extracts facts, generates embeddings, and stores them for semantic retrieval.
    """

    def __init__(self):
        """Initialize the store, embedder, and ensure the vector table exists."""
        self.embedder = get_embeddings()
        self._ensure_table()

    def _ensure_table(self):
        """Creates the mem_vectors table with pgvector if it doesn't exist."""
        if not engine:
            log.error("Database engine not initialized. Cannot create mem_vectors.")
            return

        create_extension_sql = "CREATE EXTENSION IF NOT EXISTS vector;"
        
        # We use EMBEDDING_DIM from config to set the vector size correctly
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS mem_vectors (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            text TEXT NOT NULL,
            embedding VECTOR({EMBEDDING_DIM}),
            score DOUBLE PRECISION DEFAULT 1.0,
            tags JSONB DEFAULT '[]'::jsonb,
            created_at DOUBLE PRECISION,
            last_used_at DOUBLE PRECISION,
            ttl_at DOUBLE PRECISION,
            pin BOOLEAN DEFAULT FALSE,
            deleted BOOLEAN DEFAULT FALSE
        );
        """
        
        # HNSW Index for fast similarity search
        create_index_sql = """
        CREATE INDEX IF NOT EXISTS idx_mem_vectors_embedding 
        ON mem_vectors USING hnsw (embedding vector_cosine_ops);
        """
        
        try:
            with engine.begin() as conn:
                conn.execute(text(create_extension_sql))
                conn.execute(text(create_table_sql))
                conn.execute(text(create_index_sql))
            log.info(f"✓ mem_vectors table (dim={EMBEDDING_DIM}) checked/created successfully.")
        except Exception as e:
            log.error(f"Failed to ensure mem_vectors table: {e}")

    def upsert(self, facts: Iterable[MemoryFact]) -> None:
        """
        Insert or update a batch of memory facts.
        Generates embeddings for the facts before storing.
        """
        if not engine:
            return

        facts_list = list(facts)
        if not facts_list:
            return

        # 1. Generate embeddings for all facts in one batch
        texts_to_embed = [fact.text for fact in facts_list]
        try:
            log.info(f"Generating embeddings for {len(texts_to_embed)} facts...")
            embeddings = self.embedder.embed_documents(texts_to_embed)
        except Exception as e:
            log.error(f"Failed to generate embeddings for memory facts: {e}")
            return

        # 2. Upsert into database
        upsert_sql = """
        INSERT INTO mem_vectors (id, user_id, text, embedding, score, tags, created_at, last_used_at, ttl_at, pin, deleted)
        VALUES (:id, :uid, :txt, :emb, :score, :tags, :cat, :lat, :ttl, :pin, FALSE)
        ON CONFLICT (id) DO UPDATE SET
            text = EXCLUDED.text,
            embedding = EXCLUDED.embedding,
            score = EXCLUDED.score,
            tags = EXCLUDED.tags,
            last_used_at = EXCLUDED.last_used_at,
            ttl_at = EXCLUDED.ttl_at,
            pin = EXCLUDED.pin,
            deleted = FALSE;
        """
        
        try:
            with engine.begin() as conn:
                for fact, emb in zip(facts_list, embeddings):
                    conn.execute(
                        text(upsert_sql),
                        {
                            "id": fact.id,
                            "uid": fact.user_id,
                            "txt": fact.text,
                            "emb": str(emb),  # pgvector accepts string representation of list
                            "score": fact.score,
                            "tags": json.dumps(fact.tags),
                            "cat": fact.created_at or time.time(),
                            "lat": fact.last_used_at or time.time(),
                            "ttl": fact.ttl_at,
                            "pin": fact.pin
                        }
                    )
            log.info(f"Successfully upserted {len(facts_list)} facts into Long-Term Memory.")
        except Exception as e:
            log.error(f"Failed to upsert memory facts: {e}")

    def query(
        self,
        user_id: str,
        text_query: str,
        k: int,
        threshold: float,
    ) -> List[MemoryFact]:
        """
        Retrieve the top-K most semantically similar facts for a user using Cosine Similarity.
        Only returns facts where similarity >= threshold, and deleted = FALSE.
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
        # Cosine distance = 1 - Cosine Similarity. So distance <= (1 - threshold)
        max_distance = 1.0 - threshold

        search_sql = """
        SELECT id, user_id, text, score, tags, created_at, last_used_at, ttl_at, pin,
               1 - (embedding <=> :q_emb) AS similarity
        FROM mem_vectors
        WHERE user_id = :uid 
          AND deleted = FALSE
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

                facts = []
                for row in rows:
                    # Update last_used_at in the background (fire and forget for now, or update sync)
                    # For performance, we skip the UPDATE here, or do it asynchronously.
                    
                    facts.append(
                        MemoryFact(
                            id=row[0],
                            user_id=row[1],
                            text=row[2],
                            score=row[3],
                            tags=row[4] if isinstance(row[4], list) else json.loads(row[4]),
                            created_at=row[5],
                            last_used_at=row[6],
                            ttl_at=row[7],
                            pin=row[8]
                        )
                    )
                return facts
        except Exception as e:
            log.error(f"Failed to query Long-Term Memory: {e}")
            return []

    def soft_delete(self, user_id: str, fact_id: str) -> None:
        """Mark a memory fact as deleted without physically removing the row."""
        if not engine:
            return
            
        delete_sql = "UPDATE mem_vectors SET deleted = TRUE WHERE user_id = :uid AND id = :id"
        try:
            with engine.begin() as conn:
                conn.execute(text(delete_sql), {"uid": user_id, "id": fact_id})
        except Exception as e:
            log.error(f"Failed to soft delete memory fact {fact_id}: {e}")

    def decay_and_prune(self, now: float) -> int:
        """
        Hard delete expired facts (ttl_at < now) or facts marked as deleted.
        Returns the number of rows deleted.
        """
        if not engine:
            return 0
            
        prune_sql = """
        DELETE FROM mem_vectors 
        WHERE deleted = TRUE 
           OR (ttl_at IS NOT NULL AND ttl_at < :now)
        """
        try:
            with engine.begin() as conn:
                result = conn.execute(text(prune_sql), {"now": now})
                return result.rowcount
        except Exception as e:
            log.error(f"Failed to decay/prune memory facts: {e}")
            return 0
