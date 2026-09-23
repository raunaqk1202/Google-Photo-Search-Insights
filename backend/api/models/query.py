"""Pydantic models for chat query and response (API contract §10.2)."""

from pydantic import BaseModel, Field
from typing import Optional


class ChatFilters(BaseModel):
    """Optional filters to scope the RAG search."""

    sources: Optional[list[str]] = Field(
        default=None,
        description="Filter by source platforms (e.g., ['reddit', 'playstore'])",
    )
    date_range: Optional[dict[str, str]] = Field(
        default=None,
        description="Date range filter with 'from' and 'to' keys (ISO format)",
    )
    photo_category: Optional[str] = Field(
        default=None,
        description="Filter by photo category (e.g., 'travel', 'medical')",
    )
    failure_mode: Optional[str] = Field(
        default=None,
        description="Filter by failure mode",
    )


class ChatRequest(BaseModel):
    """Request body for the POST /api/v1/chat endpoint."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The investigative question from the PM",
    )
    filters: Optional[ChatFilters] = None
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for multi-turn conversations",
    )


class CitationRef(BaseModel):
    """A single citation reference returned in a chat response."""

    id: str
    ref_number: int
    text: str
    source: str
    source_url: Optional[str] = None
    published_at: Optional[str] = None
    photo_category: Optional[str] = None
    failure_mode: Optional[str] = None


class ChatResponse(BaseModel):
    """Structured response from the RAG pipeline."""

    answer: str
    citations: list[CitationRef] = []
    confidence: Optional[str] = None  # high | moderate | low
    evidence_type: Optional[str] = None  # direct | pattern | hypothesis
    sample_size: Optional[int] = None
    session_id: Optional[str] = None
