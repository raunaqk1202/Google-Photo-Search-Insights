"""Chat router — conversational query endpoint."""

import json
import logging
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

from api.services.rag_service import RAGService

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None

# Singleton RAG service — initialized once, reused across all requests.
# This avoids re-downloading the 79MB ONNX model on every request.
_rag_service: Optional[RAGService] = None

def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        logger.info("Initializing singleton RAGService...")
        _rag_service = RAGService()
        logger.info("RAGService singleton ready.")
    return _rag_service

@router.post("")
async def chat_query(request: ChatRequest):
    """
    POST /api/v1/chat — Submit a conversational query.
    Returns a Server-Sent Events (SSE) stream containing text tokens and citations.
    """
    try:
        rag_service = get_rag_service()
    except Exception as e:
        logger.error(f"Failed to initialize RAGService: {e}")
        async def error_gen():
            yield json.dumps({"type": "error", "content": f"Service initialization failed: {str(e)}"}) + "\n"
        return StreamingResponse(error_gen(), media_type="text/event-stream")

    generator = rag_service.query_stream(
        query=request.query,
        filters=request.filters,
        session_id=request.session_id
    )
    
    return StreamingResponse(generator, media_type="text/event-stream")
