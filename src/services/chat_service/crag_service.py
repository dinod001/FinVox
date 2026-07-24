"""
CRAG (Corrective RAG) service with self-correcting retrieval.
Automatically expands search scope if initial retrieval confidence is low.
"""

from src.infrastructure.log import log
from typing import Any, Dict
import time

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.retrievers import BaseRetriever

from src.infrastructure.config import (
    CRAG_CONFIDENCE_THRESHOLD,
    CRAG_EXPANDED_K,
    TOP_K_RESULTS
)
from src.services.chat_service.rag_templates import RAG_TEMPLATE
from src.services.chat_service.rag_service import QdrantRetriever
from src.infrastructure.utils import format_docs, calculate_confidence


class CRAGService:
    """Corrective RAG service with automatic self-correction."""
    
    def __init__(
        self,
        retriever: BaseRetriever,
        llm: Any,
        initial_k: int = TOP_K_RESULTS,
        expanded_k: int = CRAG_EXPANDED_K
    ):
        self.retriever = retriever
        self.llm = llm
        self.initial_k = initial_k
        self.expanded_k = expanded_k
        self.prompt = ChatPromptTemplate.from_template(RAG_TEMPLATE)

    def _set_k(self, k: int) -> None:
        if isinstance(self.retriever, QdrantRetriever):
            self.retriever.top_k = k
        elif hasattr(self.retriever, "search_kwargs"):
            self.retriever.search_kwargs["k"] = k
    
    def generate(
        self,
        query: str,
        confidence_threshold: float = CRAG_CONFIDENCE_THRESHOLD,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """Generate answer with CRAG workflow."""
        if verbose:
            log.info(f"CRAG Query: {query}")
            log.info(f"Confidence threshold: {confidence_threshold}")
        
        # Step 1: Initial retrieval
        if verbose:
            log.info(f"Initial retrieval (k={self.initial_k})...")
        
        self._set_k(self.initial_k)
        docs_initial = self.retriever.invoke(query)
        confidence_initial = calculate_confidence(docs_initial, query)
        
        if verbose:
            log.info(f"Initial Confidence: {confidence_initial:.2f}")
        
        # Step 2: Check if correction needed
        if confidence_initial >= confidence_threshold:
            if verbose:
                log.info(f"Confidence sufficient. Proceeding with initial retrieval.")
            final_docs = docs_initial
            confidence_final = confidence_initial
            correction_applied = False
        else:
            if verbose:
                log.warning(f"Low confidence. Applying corrective retrieval...")
            
            # Step 3: Corrective retrieval
            self._set_k(self.expanded_k)
            docs_corrected = self.retriever.invoke(query)
            confidence_final = calculate_confidence(docs_corrected, query)
            
            if verbose:
                log.info(f"Corrected confidence: {confidence_final:.2f}")
            
            final_docs = docs_corrected
            correction_applied = True
        
        # Step 4: Generate answer
        if verbose:
            log.info(f"Generating answer...")
        
        start = time.time()
        context = format_docs(final_docs)
        prompt_input = {"context": context, "question": query}
        answer = (self.prompt | self.llm | StrOutputParser()).invoke(prompt_input)
        
        elapsed = time.time() - start
        
        # Extract sources
        sources = list(set([
            doc.metadata.get("source", doc.metadata.get("document_id", "Unknown"))
            for doc in final_docs
        ]))
        
        return {
            'answer': answer,
            'confidence_initial': confidence_initial,
            'confidence_final': confidence_final,
            'correction_applied': correction_applied,
            'docs_used': len(final_docs),
            'generation_time': elapsed,
            'sources': sources,
            'evidence': final_docs
        }


__all__ = ['CRAGService']
