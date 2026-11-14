"""FastAPI dependency injection."""


from fastapi import Depends, Header, HTTPException, status

from ..agents.rag_agent import RAGAgent, create_rag_agent
from ..generation.llm_client import LLMClient, get_llm_client
from ..observability.logging import get_logger
from ..retrieval.vector_store import VectorStoreRetriever, get_retriever
from ..utils.cache import CacheManager, get_cache_manager
from ..utils.config import Settings, get_settings

logger = get_logger(__name__)

# Global instances
_retriever: VectorStoreRetriever | None = None
_rag_agent: RAGAgent | None = None


async def get_retriever_dependency() -> VectorStoreRetriever:
    """Get or create retriever dependency."""
    global _retriever
    if _retriever is None:
        _retriever = await get_retriever()
    return _retriever


async def get_rag_agent_dependency() -> RAGAgent:
    """Get or create RAG agent dependency."""
    global _rag_agent
    if _rag_agent is None:
        retriever = await get_retriever_dependency()
        _rag_agent = await create_rag_agent(retriever=retriever)
    return _rag_agent


def get_settings_dependency() -> Settings:
    """Get settings dependency."""
    return get_settings()


def get_llm_client_dependency() -> LLMClient:
    """Get LLM client dependency."""
    return get_llm_client()


def get_cache_dependency() -> CacheManager:
    """Get cache manager dependency."""
    return get_cache_manager()


async def verify_api_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    authorization: str | None = Header(None),
    settings: Settings = Depends(get_settings_dependency),
) -> str:
    """
    Verify API key from header.

    Args:
        x_api_key: API key from X-API-Key header
        authorization: Authorization Bearer header
        settings: Application settings

    Returns:
        Verified API key or identity string

    Raises:
        HTTPException: If API key is invalid or missing when auth_enabled=True
    """
    if not settings.auth_enabled:
        return x_api_key or "development"

    key = x_api_key
    if not key and authorization and authorization.startswith("Bearer "):
        key = authorization.split("Bearer ", 1)[1].strip()

    if not key or (settings.app_api_key and key != settings.app_api_key):
        logger.warning("Unauthorized API request: invalid or missing key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Provide header 'X-API-Key' or 'Authorization: Bearer <key>'.",
        )

    logger.debug("API key successfully verified")
    return key


def get_request_id(x_request_id: str | None = Header(None)) -> str:
    """
    Get or generate request ID.

    Args:
        x_request_id: Request ID from header

    Returns:
        Request ID
    """
    import uuid

    return x_request_id or str(uuid.uuid4())
