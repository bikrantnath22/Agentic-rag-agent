"""Query endpoints for RAG system."""

import hashlib
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ...agents.rag_agent import RAGAgent
from ...api.dependencies import get_cache_dependency, get_rag_agent_dependency, get_request_id
from ...api.models import DocumentResponse, QueryRequest, QueryResponse
from ...observability.logging import get_logger
from ...observability.metrics import (
    rag_documents_retrieved,
    rag_queries_total,
    rag_query_duration_seconds,
    rag_reflection_score,
)
from ...utils.cache import CacheManager
from ...utils.exceptions import RAGException

logger = get_logger(__name__)

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def query_rag(
    request: QueryRequest,
    agent: RAGAgent = Depends(get_rag_agent_dependency),
    cache: CacheManager = Depends(get_cache_dependency),
    request_id: str = Depends(get_request_id),
) -> QueryResponse:
    """
    Query the RAG system.

    Args:
        request: Query request
        agent: RAG agent instance
        cache: Cache manager instance
        request_id: Request ID for tracking

    Returns:
        Query response with answer and documents

    Raises:
        HTTPException: If query fails
    """
    logger.info(f"Query request [{request_id}]: {request.query}")
    start_time = time.time()

    # Generate cache key from normalized query and parameters
    normalized_query = request.query.strip().lower()
    cache_key = f"rag_query:{hashlib.sha256(f'{normalized_query}:{request.top_k}:{request.use_reflection}'.encode()).hexdigest()}"

    # Try cache first
    try:
        cached_result = await cache.get(cache_key)
        if cached_result:
            logger.info(f"Query cache hit [{request_id}]")
            cached_result["metadata"] = cached_result.get("metadata", {})
            cached_result["metadata"]["cached"] = True
            rag_queries_total.labels(status="cached").inc()
            return QueryResponse(**cached_result)
    except Exception as e:
        logger.debug(f"Cache lookup bypassed: {e}")

    try:
        # Execute agent
        result = await agent.run(
            query=request.query,
            top_k=request.top_k,
            use_reflection=request.use_reflection,
        )

        query_duration = time.time() - start_time

        # Record Prometheus metrics
        rag_queries_total.labels(status="success").inc()
        rag_query_duration_seconds.observe(query_duration)
        rag_documents_retrieved.observe(len(result.get("documents", [])))
        if result.get("reflection", {}).get("score") is not None:
            rag_reflection_score.observe(float(result["reflection"]["score"]))

        # Format response
        response = QueryResponse(
            query=result["query"],
            answer=result["answer"],
            documents=[
                DocumentResponse(
                    id=doc["id"],
                    score=doc["score"],
                    content=doc["content"],
                )
                for doc in result["documents"]
            ],
            reflection=result.get("reflection"),
            metadata=result.get("metadata", {}),
        )

        # Store in cache
        try:
            await cache.set(cache_key, response.model_dump())
        except Exception as e:
            logger.debug(f"Cache write bypassed: {e}")

        logger.info(f"Query completed [{request_id}] in {query_duration:.2f}s")
        return response

    except RAGException as e:
        rag_queries_total.labels(status="error").inc()
        logger.error(f"RAG error [{request_id}]: {e}")
        raise HTTPException(
            status_code=500,
            detail=e.to_dict(),
        )
    except Exception as e:
        rag_queries_total.labels(status="error").inc()
        logger.error(f"Unexpected error [{request_id}]: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "message": str(e)},
        )


@router.post("/stream")
async def query_rag_stream(
    request: QueryRequest,
    agent: RAGAgent = Depends(get_rag_agent_dependency),
    request_id: str = Depends(get_request_id),
):
    """
    Stream RAG query results.

    Args:
        request: Query request
        agent: RAG agent instance
        request_id: Request ID for tracking

    Returns:
        Streaming response with events
    """
    logger.info(f"Stream query request [{request_id}]: {request.query}")

    async def event_generator():
        """Generate server-sent events."""
        try:
            async for event in agent.stream(query=request.query):
                import json

                yield f"data: {json.dumps(event)}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Stream error [{request_id}]: {e}")
            import json

            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
