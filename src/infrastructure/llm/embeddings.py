"""
Embedding model provider.

Routes through OpenRouter when PROVIDER=openrouter, otherwise direct OpenAI.

HuggingFace models are cached as a module-level singleton to avoid reloading
the model weights multiple times during server startup (saves ~20-25s).
"""

from typing import Any
from langchain_openai import OpenAIEmbeddings

from src.infrastructure.config import EMBEDDING_MODEL, PROVIDER, EMBEDDING_PROVIDER, OPENROUTER_BASE_URL, get_api_key

# Module-level singleton cache — HuggingFace model is heavy, load it only once
_HUGGINGFACE_SINGLETON: Any = None

def get_embeddings(
    batch_size: int = 100,
    show_progress: bool = False,
    **kwargs: Any
) -> Any:
    """
    Get an Embeddings instance configured for the active embedding provider.

    For HuggingFace, returns a cached singleton to avoid reloading model weights
    multiple times during startup.

    Returns:
        A ready-to-use Embeddings instance (OpenAIEmbeddings or HuggingFaceEmbeddings).
    """
    global _HUGGINGFACE_SINGLETON

    if EMBEDDING_PROVIDER == "huggingface":
        if _HUGGINGFACE_SINGLETON is not None:
            return _HUGGINGFACE_SINGLETON

        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
        except ImportError:
            from langchain_huggingface import HuggingFaceEmbeddings
            
        _HUGGINGFACE_SINGLETON = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            show_progress=show_progress,
            encode_kwargs={'batch_size': batch_size, **kwargs}
        )
        return _HUGGINGFACE_SINGLETON

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
