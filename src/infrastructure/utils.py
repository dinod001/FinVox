from typing import List
from langchain_core.documents import Document

def format_docs(docs: List[Document]) -> str:
    """Formats a list of LangChain Documents into a single string with source citations."""
    formatted = []
    for doc in docs:
        source = doc.metadata.get("source", doc.metadata.get("document_id", "Unknown"))
        formatted.append(f"[Source: {source}]\n{doc.page_content}")
    return "\n\n".join(formatted)

def calculate_confidence(docs: list, query: str) -> float:
    """
    Calculate confidence score for retrieved documents.

    Multi-factor heuristic:
    1. Keyword overlap (query ∩ docs)
    2. Content richness (avg doc length)
    3. Strategy diversity (multiple chunking strategies)

    Args:
        docs: List of retrieved documents
        query: User query string

    Returns:
        Confidence score 0.0 to 1.0
    """
    if not docs:
        return 0.0

    # Extract query keywords
    query_words = set(query.lower().split())

    # Factor 1: Keyword overlap
    overlaps = []
    for doc in docs:
        doc_words = set(doc.page_content.lower().split())
        overlap = len(query_words & doc_words) / len(query_words) if query_words else 0
        overlaps.append(overlap)
    keyword_score = sum(overlaps) / len(overlaps)

    # Factor 2: Content richness
    avg_length = sum(len(doc.page_content) for doc in docs) / len(docs)
    length_score = min(avg_length / 500, 1.0)

    # Factor 3: Strategy diversity
    strategies = set([doc.metadata.get('strategy', 'unknown') for doc in docs])
    diversity_score = len(strategies) / 3.0  # We have 3 strategies max

    # Weighted average
    confidence = (
        0.5 * keyword_score +
        0.3 * length_score +
        0.2 * diversity_score
    )

    return confidence
