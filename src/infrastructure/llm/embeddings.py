"""
Embedding model provider.

Routes through OpenRouter when PROVIDER=openrouter, otherwise direct OpenAI.
"""

from typing import Any
from langchain_openai import OpenAIEmbeddings

from src.infrastructure.config import EMBEDDING_MODEL, PROVIDER, EMBEDDING_PROVIDER, OPENROUTER_BASE_URL, get_api_key

def get_embeddings(
    batch_size: int = 100,
    show_progress: bool = False,
    **kwargs: Any
) -> Any:
    """
    Get an Embeddings instance configured for the active embedding provider.

    Returns:
        A ready-to-use Embeddings instance (OpenAIEmbeddings or HuggingFaceEmbeddings).
    """
    if EMBEDDING_PROVIDER == "huggingface":
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
        except ImportError:
            from langchain_huggingface import HuggingFaceEmbeddings
            
        return HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            show_progress=show_progress,
            encode_kwargs={'batch_size': batch_size, **kwargs}
        )

    llm_kwargs: dict[str, Any] = dict(
        model=EMBEDDING_MODEL,
        show_progress_bar=show_progress,
        **kwargs,
    )

    if EMBEDDING_PROVIDER == "openrouter":
        llm_kwargs["openai_api_base"] = OPENROUTER_BASE_URL
        llm_kwargs["openai_api_key"] = get_api_key("openrouter")
    elif EMBEDDING_PROVIDER == "openai":
        llm_kwargs["openai_api_key"] = get_api_key("openai")

    return OpenAIEmbeddings(**llm_kwargs)
