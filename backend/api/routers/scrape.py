"""Scrape router — trigger and monitor scrape jobs."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sqlalchemy.orm import Session

from api.database import get_db
from api.services.scrape_service import ScrapeService
from scrapers import VALID_SOURCES

router = APIRouter(prefix="/scrape", tags=["Scraping"])


@router.post("/trigger")
async def trigger_scrape(
    source: Optional[str] = Query(
        default=None,
        description=f"Source to scrape. One of: {VALID_SOURCES}. Omit to scrape all sources.",
    ),
    db: Session = Depends(get_db),
):
    """
    POST /api/v1/scrape/trigger — Manually trigger a scrape job.

    Pass `?source=playstore` to scrape a single source, or omit to scrape all.
    Returns job ID(s) for status tracking.
    """
    service = ScrapeService(db)
    try:
        result = service.trigger_scrape(source)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/status")
async def list_scrape_jobs(
    limit: int = Query(default=50, ge=1, le=200, description="Max jobs to return"),
    db: Session = Depends(get_db),
):
    """
    GET /api/v1/scrape/status — List recent scrape jobs.

    Returns the most recent scrape jobs with their status and counts.
    """
    service = ScrapeService(db)
    jobs = service.list_jobs(limit=limit)
    return {"jobs": jobs, "total": len(jobs)}


@router.get("/status/{job_id}")
async def get_scrape_status(
    job_id: str,
    db: Session = Depends(get_db),
):
    """
    GET /api/v1/scrape/status/{job_id} — Check a specific job's status.

    Returns the job details or 404 if not found.
    """
    service = ScrapeService(db)
    result = service.get_status(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Scrape job not found: {job_id}")
    return result
