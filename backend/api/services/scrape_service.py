"""Scrape service — manages the scraping lifecycle."""

import uuid
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from api.models.review import ScrapeJob
from scrapers import VALID_SOURCES

logger = logging.getLogger(__name__)


class ScrapeService:
    """Manages scrape job creation, triggering, and status tracking."""

    def __init__(self, db: Session):
        self.db = db

    def trigger_scrape(self, source: Optional[str] = None) -> dict:
        """
        Trigger a new scrape job for one or all sources.

        Creates ScrapeJob record(s), dispatches Celery tasks, returns job info.
        """
        from scrapers.tasks import scrape_source, scrape_all

        if source and source not in VALID_SOURCES:
            raise ValueError(
                f"Invalid source '{source}'. Valid sources: {VALID_SOURCES}"
            )

        if source:
            # Single source scrape
            job = ScrapeJob(
                id=uuid.uuid4(),
                source=source,
                started_at=datetime.utcnow(),
                status="pending",
            )
            self.db.add(job)
            self.db.commit()

            # Dispatch Celery task
            scrape_source.delay(source, str(job.id))

            logger.info("Triggered scrape for source=%s, job_id=%s", source, job.id)

            return {
                "job_id": str(job.id),
                "source": source,
                "status": "pending",
                "message": f"Scrape job dispatched for {source}",
            }
        else:
            # Scrape all sources
            jobs = []
            for src in VALID_SOURCES:
                job = ScrapeJob(
                    id=uuid.uuid4(),
                    source=src,
                    started_at=datetime.utcnow(),
                    status="pending",
                )
                self.db.add(job)
                jobs.append({"job_id": str(job.id), "source": src, "status": "pending"})

            self.db.commit()

            # Dispatch the batch task
            scrape_all.delay()

            logger.info("Triggered scrape_all for %d sources", len(VALID_SOURCES))

            return {
                "jobs": jobs,
                "status": "pending",
                "message": f"Scrape jobs dispatched for all {len(VALID_SOURCES)} sources",
            }

    def get_status(self, job_id: str) -> Optional[dict]:
        """Get the status of a specific scrape job."""
        try:
            job_uuid = uuid.UUID(job_id)
        except ValueError:
            return None

        job = self.db.query(ScrapeJob).filter(ScrapeJob.id == job_uuid).first()
        if not job:
            return None

        return self._job_to_dict(job)

    def list_jobs(self, limit: int = 50) -> list[dict]:
        """List recent scrape jobs, most recent first."""
        jobs = (
            self.db.query(ScrapeJob)
            .order_by(ScrapeJob.started_at.desc())
            .limit(limit)
            .all()
        )
        return [self._job_to_dict(j) for j in jobs]

    @staticmethod
    def _job_to_dict(job: ScrapeJob) -> dict:
        """Convert a ScrapeJob ORM object to a dict."""
        return {
            "job_id": str(job.id),
            "source": job.source,
            "status": job.status,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "total_collected": job.total_collected,
        }
