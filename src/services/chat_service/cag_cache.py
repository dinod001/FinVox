"""
Cache-Augmented Generation (CAG) — semantic vector cache backed by Qdrant.
Stores query-response pairs to serve semantically similar future queries instantly.
"""

import json
import time
import uuid
from typing import Any, Dict, Optional

from infrastructure.log import log
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from src.infrastructure.config import (
    CAG_SIMILARITY_THRESHOLD,
    CAG_CACHE_TTL,
    EMBEDDING_DIM,
    CAG_COLLECTION_NAME,
)
from src.infrastructure.db.qdrant_client import get_qdrant_client, collection_exists


class CAGCache:
    """Qdrant-backed semantic cache for pre-computed RAG responses."""

    def __init__(
        self,
        embedder: Any,
        collection_name: str = CAG_COLLECTION_NAME,
        dim: int = EMBEDDING_DIM,
        similarity_threshold: float = CAG_SIMILARITY_THRESHOLD,
        ttl_seconds: int = CAG_CACHE_TTL,
    ) -> None:
        self.embedder = embedder
        self.collection_name = collection_name
        self.dim = dim
        self.similarity_threshold = similarity_threshold
        self.ttl_seconds = ttl_seconds
        self._available = False

        try:
            self._client = get_qdrant_client()
            if not collection_exists(self.collection_name):
                self._create_collection()
            self._available = True
            log.info(f"✓ CAG cache ready (Qdrant collection='{self.collection_name}')")
        except Exception as exc:
            log.warning(f"CAG cache DISABLED — Qdrant unavailable: {exc}")

    def _create_collection(self) -> None:
        """Creates the Qdrant collection for CAG cache."""
        self._client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.dim,
                distance=Distance.COSINE,
                on_disk=False,
            ),
        )

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """Semantic cache lookup via KNN-1 search."""
        if not self._available:
            return None

        try:
            query_vec = self.embedder.embed_query(query)
            response = self._client.query_points(
                collection_name=self.collection_name,
                query=query_vec,
                limit=1,
                score_threshold=self.similarity_threshold,
            )
        except Exception as exc:
            log.warning(f"CAG cache GET error: {exc}")
            return None

        if not response.points:
            return None

        hit = response.points[0]
        payload = hit.payload or {}

        # TTL filtering
        if self.ttl_seconds > 0:
            entry_ts = payload.get("ts", 0)
            if entry_ts and (time.time() - float(entry_ts)) > self.ttl_seconds:
                try:
                    self._client.delete(
                        collection_name=self.collection_name,
                        points_selector=[hit.id],
                    )
                except Exception:
                    pass
                return None

        cached_query = payload.get("query", "")
        log.info(f"CAG cache HIT: '{query[:50]}' matched '{cached_query[:50]}'")

        sources_raw = payload.get("sources", "[]")
        try:
            sources = json.loads(sources_raw) if isinstance(sources_raw, str) else sources_raw
        except (json.JSONDecodeError, TypeError):
            sources = []

        return {
            "query": cached_query,
            "answer": payload.get("answer", ""),
            "sources": sources,
            "ts": float(payload.get("ts", 0)),
            "score": hit.score,
        }

    def set(self, query: str, response: Dict[str, Any]) -> None:
        """Cache a response, indexed by the query's embedding."""
        if not self._available:
            return

        try:
            query_vec = self.embedder.embed_query(query)
            
            # Clean up existing duplicates
            existing = self._client.query_points(
                collection_name=self.collection_name,
                query=query_vec,
                limit=10,
                score_threshold=0.99,
            )
            if existing.points:
                self._client.delete(
                    collection_name=self.collection_name,
                    points_selector=[p.id for p in existing.points],
                )

            # Upsert new entry
            point_id = str(uuid.uuid4())
            payload = {
                "query": query,
                "answer": response.get("answer", ""),
                "sources": json.dumps(response.get("sources", [])),
                "ts": time.time(),
            }
            self._client.upsert(
                collection_name=self.collection_name,
                points=[PointStruct(id=point_id, vector=query_vec, payload=payload)],
            )
        except Exception as exc:
            log.warning(f"CAG cache SET error: {exc}")

    def clear(self) -> None:
        """Drops the Qdrant collection and recreates an empty one."""
        if not self._available:
            return
        try:
            self._client.delete_collection(self.collection_name)
        except Exception:
            pass
        self._create_collection()


