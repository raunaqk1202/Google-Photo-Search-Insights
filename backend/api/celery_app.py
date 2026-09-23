"""Celery application for background task processing."""

from celery import Celery

from api.config import get_settings

settings = get_settings()

celery_app = Celery(
    "discovery_engine",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,  # Re-deliver tasks if worker crashes mid-execution
    worker_prefetch_multiplier=1,  # One task at a time per worker for scraping
)

# Auto-discover tasks in the scrapers and pipeline packages
celery_app.autodiscover_tasks(["scrapers", "pipeline"])
