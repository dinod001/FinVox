from fastapi import Request
from src.agents.orchestrator import AgentOrchestrator
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings import Embeddings

def get_orchestrator(request: Request) -> AgentOrchestrator:
    """
    FastAPI Dependency to retrieve the globally initialized AgentOrchestrator
    from the application state.
    """
    return request.app.state.orchestrator

def get_llm(request: Request) -> BaseChatModel:
    """Retrieve the globally initialized Chat LLM."""
    return request.app.state.llm

def get_embedder(request: Request) -> Embeddings:
    """Retrieve the globally initialized Embeddings model."""
    return request.app.state.embedder

def get_db_engine(request: Request):
    """Retrieve the globally initialized SQLAlchemy Database Engine."""
    return request.app.state.db_engine

def get_qdrant(request: Request):
    """Retrieve the globally initialized Qdrant Vector DB Client."""
    return request.app.state.qdrant
