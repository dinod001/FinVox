"""
CAG (Cache-Augmented Generation) service combining caching with CRAG.

Pipeline:
    Query --> Semantic Cache (Qdrant cag_cache KNN-1)
          --> HIT? Return instantly
          --> MISS? --> CRAGService (self-correcting retrieval)
                    --> Cache the result for future hits
                    --> Return answer
"""

from infrastructure.log import log
from typing import Any, Dict
import time

from services.chat_service.cag_cache import CAGCache
from services.chat_service.crag_service import CRAGService


class CAGService:
    """
    Cache-Augmented Generation backed by Corrective RAG.

    Layer 1: Semantic cache (Qdrant cag_cache)
    Layer 2: CRAG (confidence-gated retrieval) -- self-correcting
    """

    def __init__(self, crag_service: CRAGService, cache: CAGCache):
        self.crag_service = crag_service
        self.cache = cache

    def generate(
        self,
        query: str,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate answer with CAG + CRAG pipeline.

        1. Check semantic cache (cosine >= threshold = HIT)
        2. On miss: run CRAGService (confidence-gated retrieval)
        3. Cache the result for future semantic hits
        """
        start = time.time()

        if use_cache:
            cached = self.cache.get(query)
            if cached:
                log.info(
                    "CAG cache HIT (score={:.3f}) for: {}",
                    cached.get("score", 0),
                    query[:60],
                )
                return {
                    "answer": cached["answer"],
                    "sources": cached.get("sources", []),
                    "cache_hit": True,
                    "cache_score": cached.get("score", 0),
                    "generation_time": 0.0,
                }

        # Cache miss -- run CRAG (self-correcting retrieval)
        crag_result = self.crag_service.generate(query, verbose=False)

        answer = crag_result.get("answer", "")
        sources = crag_result.get("sources", [])

        result: Dict[str, Any] = {
            "answer": answer,
            "sources": sources,
            "cache_hit": False,
            "confidence_initial": crag_result.get("confidence_initial", 0),
            "confidence_final": crag_result.get("confidence_final", 0),
            "correction_applied": crag_result.get("correction_applied", False),
            "generation_time": crag_result.get("generation_time", 0),
            "num_docs": crag_result.get("docs_used", 0),
        }

        if use_cache and answer:
            self.cache.set(query, {"answer": answer, "sources": sources})
            log.info("CAG cache MISS -> cached for: {}", query[:60])

        return result


    def clear_cache(self) -> None:
        self.cache.clear()


__all__ = ["CAGService"]
