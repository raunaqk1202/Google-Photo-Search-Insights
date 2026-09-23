"""Pydantic models for citation detail responses."""

from pydantic import BaseModel
from typing import Optional


class CitationDetail(BaseModel):
    """Full citation detail returned by GET /api/v1/citations/{id}."""

    id: str
    original_text: str
    cleaned_text: Optional[str] = None
    source: str
    source_url: Optional[str] = None
    published_at: Optional[str] = None
    scraped_at: Optional[str] = None
    photo_category: Optional[str] = None
    failure_mode: Optional[str] = None
    retrieval_archetype: Optional[str] = None
    outcome: Optional[str] = None
    sentiment_score: Optional[float] = None
    memory_cues: list[dict[str, str]] = []
    user_effort_signal: Optional[str] = None
