"""
RAG (Retrieval-Augmented Generation) service using LangChain LCEL.
Backed by Qdrant Cloud for vector retrieval.
"""

import time
from typing import Any, Dict, List, Optional
from infrastructure.log import log

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, Runnable
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.retrievers import BaseRetriever

from infrastructure.config import TOP_K_RESULTS, SIMILARITY_THRESHOLD
from services.chat_service.rag_templates import RAG_TEMPLATE
from infrastructure.db.qdrant_client import search_chunks
from infrastructure.utils import format_docs


class QdrantRetriever(BaseRetriever):
    """LangChain-compatible retriever backed by Qdrant Cloud."""

    embedder: Any = None
    top_k: int = TOP_K_RESULTS
    score_threshold: float = SIMILARITY_THRESHOLD

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Optional[CallbackManagerForRetrieverRun] = None,
    ) -> List[Document]:
        query_vec = self.embedder.embed_query(query)
        hits = search_chunks(
            query_vector=query_vec,
            top_k=self.top_k,
            score_threshold=self.score_threshold,
        )

        seen_parents: set = set()
        docs = []
        for hit in hits:
            parent_text = hit.get("parent_text")
            parent_id = hit.get("parent_id")

            if parent_id and parent_id in seen_parents:
                continue
            if parent_id:
                seen_parents.add(parent_id)

            page_content = parent_text if parent_text else hit["chunk_text"]
            docs.append(
                Document(
                    page_content=page_content,
                    metadata={
                        "source": hit.get("source", ""),
                        "document_id": hit.get("document_id", ""),
                        "title": hit.get("title", ""),
                        "strategy": hit.get("strategy", ""),
                        "chunk_index": hit.get("chunk_index", 0),
                        "score": hit.get("score", 0.0),
                        "child_text": hit["chunk_text"],
                    },
                )
            )
        return docs


def build_rag_chain(
    retriever: BaseRetriever,
    llm: Any,
    k: int = TOP_K_RESULTS,
    template: str = RAG_TEMPLATE,
) -> Runnable:
    """Builds LCEL RAG chain."""
    if hasattr(retriever, "search_kwargs"):
        retriever.search_kwargs["k"] = k

    rag_prompt = ChatPromptTemplate.from_template(template)
    rag_chain = (
        RunnableParallel(
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
        )
        | rag_prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain


class RAGService:
    """High-level RAG service for question answering."""

    def __init__(
        self,
        embedder: Any,
        llm: Any,
        k: int = TOP_K_RESULTS,
        score_threshold: float = SIMILARITY_THRESHOLD,
    ):
        self.embedder = embedder
        self.llm = llm
        self.k = k

        # Initialize the Retriever here and save it to 'self'
        self.retriever = QdrantRetriever(
            embedder=embedder,
            top_k=k,
            score_threshold=score_threshold,
        )
        self.chain = build_rag_chain(self.retriever, llm, k)

    def generate(self, query: str) -> Dict[str, Any]:
        """Generates answer using RAG and extracts unique sources."""
        start = time.time()
        
        # 'self.retriever' is available because it was created in __init__
        evidence = self.retriever.invoke(query)
        answer = self.chain.invoke(query)
        
        elapsed = time.time() - start

        sources = list(set(doc.metadata.get("source", "") or doc.metadata.get("document_id", "") for doc in evidence))
        sources = [s for s in sources if s]

        return {
            "answer": answer,
            "evidence": evidence,
            "sources": sources,
            "generation_time": elapsed,
            "num_docs": len(evidence),
        }


__all__ = ["build_rag_chain", "RAGService", "QdrantRetriever"]
