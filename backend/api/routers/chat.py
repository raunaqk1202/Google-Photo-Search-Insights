"""Chat router — conversational query endpoint."""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

from api.services.rag_service import RAGService

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None

# Dependency injection for RAGService
def get_rag_service():
    return RAGService()

@router.post("")
async def chat_query(request: ChatRequest, rag_service: RAGService = Depends(get_rag_service)):
    """
    POST /api/v1/chat — Submit a conversational query.
    Returns a Server-Sent Events (SSE) stream containing text tokens and citations.
    """
    # Create generator
    generator = rag_service.query_stream(
        query=request.query,
        filters=request.filters,
        session_id=request.session_id
    )
    
    # Return StreamingResponse with text/event-stream media type
    return StreamingResponse(generator, media_type="text/event-stream")
