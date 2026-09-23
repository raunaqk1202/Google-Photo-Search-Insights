"""
Celery tasks for scrape orchestration.

Each scraper runs as a Celery task that:
1. Creates a ScrapeJob record (status=running)
2. Runs the scraper with retry logic
3. Saves results to raw_review table
4. Updates the ScrapeJob to completed/failed with counts
"""

import logging
import uuid
from datetime import datetime

from api.celery_app import celery_app
from api.database import SessionLocal
from api.models.review import ScrapeJob

logger = logging.getLogger(__name__)


def _get_scraper_class(source_name: str):
    """Dynamically import and return the scraper class for a given source."""
    from scrapers import SCRAPER_REGISTRY
    cls = SCRAPER_REGISTRY.get(source_name)
    if cls is None:
        raise ValueError(f"Unknown scraper source: {source_name}")
    return cls


@celery_app.task(bind=True, name="scrapers.tasks.scrape_source")
def scrape_source(self, source_name: str, job_id: str | None = None):
    """
    Run a single scraper and persist results.

    Args:
        source_name: One of 'playstore', 'appstore', 'reddit', 'youtube', 'community'
        job_id: Optional pre-created ScrapeJob ID. If None, one is created.

    Returns:
        dict with job_id, status, total_collected.
    """
    db = SessionLocal()

    try:
        # Create or fetch the ScrapeJob
        if job_id:
            scrape_job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
            if not scrape_job:
                raise ValueError(f"ScrapeJob not found: {job_id}")
        else:
            scrape_job = ScrapeJob(
                id=uuid.uuid4(),
                source=source_name,
                started_at=datetime.utcnow(),
                status="running",
            )
            db.add(scrape_job)
            db.commit()

        # Mark as running
        scrape_job.status = "running"
        scrape_job.started_at = datetime.utcnow()
        db.commit()

        logger.info("Starting scrape job %s for source=%s", scrape_job.id, source_name)

        # Get the scraper and run it
        scraper_cls = _get_scraper_class(source_name)
        scraper = scraper_cls()
        records = scraper.run_with_retry()

        # Save results
        inserted = scraper.save(records, db, scrape_job)

        # Update job status
        scrape_job.status = "completed"
        scrape_job.completed_at = datetime.utcnow()
        scrape_job.total_collected = inserted
        db.commit()

        logger.info(
            "Scrape job %s completed: source=%s, collected=%d",
            scrape_job.id, source_name, inserted,
        )

        return {
            "job_id": str(scrape_job.id),
            "source": source_name,
            "status": "completed",
            "total_collected": inserted,
        }

    except Exception as exc:
        logger.error(
            "Scrape job failed for source=%s: %s", source_name, exc, exc_info=True,
        )

        # Try to mark the job as failed
        try:
            if 'scrape_job' in locals() and scrape_job:
                scrape_job.status = "failed"
                scrape_job.completed_at = datetime.utcnow()
                db.commit()
        except Exception:
            db.rollback()

        return {
            "job_id": job_id or "unknown",
            "source": source_name,
            "status": "failed",
            "error": str(exc),
        }

    finally:
        db.close()


@celery_app.task(bind=True, name="scrapers.tasks.scrape_all")
def scrape_all(self):
    """
    Run all scrapers sequentially.

    Creates a separate ScrapeJob for each source and runs them one by one
    to respect rate limits and avoid overwhelming external services.

    Returns:
        list of results from each scrape_source call.
    """
    from scrapers import SCRAPER_REGISTRY

    sources = list(SCRAPER_REGISTRY.keys())
    results = []

    logger.info("Starting scrape_all for %d sources: %s", len(sources), sources)

    for source_name in sources:
        logger.info("Scraping source: %s", source_name)
        try:
            result = scrape_source(source_name)
            results.append(result)
        except Exception as exc:
            logger.error("scrape_all: source=%s failed: %s", source_name, exc)
            results.append({
                "source": source_name,
                "status": "failed",
                "error": str(exc),
            })

    completed = sum(1 for r in results if r.get("status") == "completed")
    total_collected = sum(r.get("total_collected", 0) for r in results)

    logger.info(
        "scrape_all finished: %d/%d sources completed, %d total records collected",
        completed, len(sources), total_collected,
    )

    return results
