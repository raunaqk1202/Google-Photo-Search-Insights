"""Data router — browse structured datasets and dashboard metrics."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from api.database import get_db
from api.models.review import RawReview, StructuredReview, FailureMode, ScrapeJob

router = APIRouter(prefix="/data", tags=["Data"])


@router.get("/dashboard")
async def get_dashboard(db: Session = Depends(get_db)):
    """
    GET /api/v1/data/dashboard — Aggregated metrics for the analytics dashboard.
    """
    # 1. Total Scraped
    total_scraped = db.query(func.count(RawReview.id)).scalar() or 0

    # 2. Filtered Count (Relevant)
    filtered_count = db.query(func.count(StructuredReview.id)).filter(
        StructuredReview.is_retrieval_relevant == True
    ).scalar() or 0

    # 3. Sources Breakdown
    sources_query = db.query(
        RawReview.source, func.count(RawReview.id)
    ).group_by(RawReview.source).all()
    
    sources = [{"source": row[0], "count": row[1]} for row in sources_query]

    import math
    
    # 4. All Opportunities (to be ranked by composite score)
    opportunities_query = db.query(
        FailureMode.name,
        FailureMode.description,
        func.count(StructuredReview.id).label("freq"),
        func.avg(StructuredReview.user_pain_score).label("avg_up"),
        func.avg(StructuredReview.business_impact_score).label("avg_bi"),
        func.avg(StructuredReview.evidence_strength_score).label("avg_es")
    ).join(
        StructuredReview, StructuredReview.failure_mode_id == FailureMode.id
    ).filter(
        FailureMode.name != 'other'
    ).group_by(
        FailureMode.id
    ).all()

    scored_opportunities = []
    for row in opportunities_query:
        name = row[0] or "unknown"
        reach_count = row[2]
        
        user_pain = row[3] if row[3] is not None else 3.0
        business_impact = row[4] if row[4] is not None else 3.0
        evidence_strength = row[5] if row[5] is not None else 3.0
        
        # Calculate a 1.0 - 5.0 Reach score based on frequency count
        reach_score = min(5.0, max(1.0, math.log10(reach_count + 1) * 1.5 + 1.0))
        
        # Score = 35% x Reach + 30% x User Pain + 20% x Business Impact + 15% x Evidence Strength
        raw_score = (0.35 * reach_score) + (0.30 * user_pain) + (0.20 * business_impact) + (0.15 * evidence_strength)
        
        # Maps 1.0-5.0 scale to 0-100 composite score
        # Using the standard mapping formula: (score - 1) * 25
        composite_score = (raw_score - 1.0) * 25
        
        scored_opportunities.append({
            "title": name.replace("_", " ").title() if name else "Unknown",
            "description": row[1] or "No description available.",
            "category": "Search & Retrieval",
            "reviewsMatched": reach_count,
            "composite_score": composite_score,
            "reach_score": reach_score,
            "user_pain": user_pain,
            "business_impact": business_impact,
            "evidence_strength": evidence_strength
        })

    # Rank by composite score descending
    scored_opportunities.sort(key=lambda x: x["composite_score"], reverse=True)

    # Take top 5 and assign IDs and formatting
    opportunities = []
    for i, opp in enumerate(scored_opportunities[:5]):
        opp["id"] = f"opp-{i}"
        opp["impact"] = f"Score: {opp['composite_score']:.1f}"
        # Remove the raw score from the final output
        del opp["composite_score"]
        opportunities.append(opp)

    return {
        "totalScraped": total_scraped,
        "filteredCount": filtered_count,
        "sources": sources,
        "opportunities": opportunities
    }


@router.get("/reviews")
async def list_reviews():
    """
    GET /api/v1/data/reviews — Paginated browse of structured reviews.
    """
    return {
        "reviews": [],
        "total": 0,
        "page": 1,
        "per_page": 20,
        "message": "Data browsing not yet implemented.",
    }
