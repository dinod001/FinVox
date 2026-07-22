from typing import Dict, Any
from langchain_core.tools import tool
from src.infrastructure.log import log

# We will lazy-load the CAG service so it doesn't initialize on import until needed.
_cag_service = None

def get_cag_service():
    global _cag_service
    if _cag_service is None:
        log.info("Initializing CAG Service for RAG Tool...")
        from src.services.chat_service.crag_service import CRAGService
        from src.services.chat_service.cag_service import CAGService
        from src.services.chat_service.cag_cache import CAGCache
        from src.services.chat_service.rag_service import QdrantRetriever
        from src.infrastructure.llm.embeddings import get_embeddings
        from src.infrastructure.llm.llm_provider import get_chat_llm
        
        embedder = get_embeddings()
        llm = get_chat_llm(temperature=0)
        
        retriever = QdrantRetriever(
            embedder=embedder,
            top_k=4,
            score_threshold=0.5
        )
        
        crag_service = CRAGService(retriever=retriever, llm=llm)
        cag_cache = CAGCache(embedder=embedder)
        
        _cag_service = CAGService(crag_service=crag_service, cache=cag_cache)
        
    return _cag_service

@tool
def search_internal_knowledge(query: str) -> str:
    """
    Search the internal knowledge base (PDFs, Company Documents, Previous Notes) 
    for answers using the RAG (Retrieval-Augmented Generation) system.
    Use this tool when the user asks about uploaded documents, company strategy, 
    or internal guidelines.
    
    Args:
        query: The specific question to ask the internal knowledge base.
        
    Returns:
        The generated answer based on internal documents.
    """
    try:
        cag = get_cag_service()
        log.info(f"RAG Tool searching for: '{query}'")
        result = cag.generate(query=query)
        
        answer = result.get("answer", "")
        if not answer:
            return "No relevant information found in the internal knowledge base."
            
        return answer
    except Exception as e:
        log.error(f"RAG Tool failed: {e}")
        return f"Failed to retrieve internal knowledge: {str(e)}"
