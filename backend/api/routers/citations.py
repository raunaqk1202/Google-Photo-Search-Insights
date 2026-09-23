"""Citations router — drill-down citation explorer."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from api.database import get_db
from api.models.review import StructuredReview

router = APIRouter(prefix="/citations", tags=["Citations"])

class CitationResponse(BaseModel):
    id: str
    source: str
    source_url: str
    original_text: str
    photo_category: Optional[str]
    outcome: Optional[str]

@router.get("/{citation_id}", response_model=CitationResponse)
async def get_citation(citation_id: str, db: Session = Depends(get_db)):
    """
    GET /api/v1/citations/{id} — Retrieve full citation details from Postgres.
    Expects citation_id to be the chunk ID (e.g. '123-chunk-0') or just the review ID.
    """
    # Extract the underlying structured_review ID
    review_id_str = citation_id.split("-chunk-")[0]
    
    # In case it's a mock ID from testing
    if review_id_str.startswith("mock-"):
        return CitationResponse(
            id=citation_id,
            source="mock",
            source_url="http://mock.test",
            original_text="This is a mock review from testing.",
            photo_category="mock",
            outcome="mock"
        )
        
    try:
        review_id = int(review_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid citation ID format.")
        
    review = db.query(StructuredReview).filter(StructuredReview.id == review_id).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Citation not found.")
        
    return CitationResponse(
        id=citation_id,
        source=str(review.source.value),
        source_url=review.source_url,
        original_text=review.cleaned_text,
        photo_category=str(review.photo_category.value) if review.photo_category else None,
        outcome=str(review.outcome.value) if review.outcome else None
    )
