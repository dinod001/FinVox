from typing import Any

from src.infrastructure.log import log


class RAGTool:
    """
    Encapsulates the full CAG/CRAG pipeline as an injectable singleton class.
    The embedder and LLM are wired in once at app startup and reused.
    """

    def __init__(self, embedder: Any, llm: Any):
        log.info("Initializing RAGTool (CAG + CRAG pipeline)...")

        from src.services.chat_service.rag_service import QdrantRetriever
        from src.services.chat_service.crag_service import CRAGService
        from src.services.chat_service.cag_cache import CAGCache
        from src.services.chat_service.cag_service import CAGService

        retriever = QdrantRetriever(
            embedder=embedder,
            top_k=4,
            score_threshold=0.5
        )
        crag_service = CRAGService(retriever=retriever, llm=llm)
        cag_cache = CAGCache(embedder=embedder)

        self._cag = CAGService(crag_service=crag_service, cache=cag_cache)
        log.info("RAGTool initialized successfully.")

    # ── Public Interface ──────────────────────────────────────────────────────

    def search(self, query: str) -> str:
        """
        Search the internal knowledge base (PDFs, company documents) using
        the full CAG/CRAG pipeline.

        Args:
            query: The specific question to ask the knowledge base.

        Returns:
            A generated answer grounded in internal documents.
        """
        log.info(f"RAGTool.search called: '{query}'")
        try:
            result = self._cag.generate(query=query)
            answer = result.get("answer", "")
            if not answer:
                return "No relevant information found in the internal knowledge base."
            return answer
        except Exception as e:
            log.error(f"RAGTool.search failed: {e}")
            return f"Failed to retrieve internal knowledge: {str(e)}"
