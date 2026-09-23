"""
Abstract base scraper — defines the interface and shared behavior for all scrapers.

Provides:
- Abstract `scrape()` and `validate()` methods
- Shared `save()` with duplicate detection
- Retry logic with exponential backoff
- Per-source rate limiting
- Structured logging
"""

import hashlib
import logging
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy.orm import Session

from scrapers.config import RATE_LIMITS, MAX_RETRIES


class BaseScraper(ABC):
    """
    Abstract base class for all scrapers.

    Subclasses must implement:
        - scrape() → list[dict]
        - validate(record: dict) → bool
    """

    # Override in subclasses
    source_name: str = "unknown"

    def __init__(self):
        self.logger = logging.getLogger(f"scrapers.{self.source_name}")
        self.rate_limit = RATE_LIMITS.get(self.source_name, 1.0)
        self.max_retries = MAX_RETRIES.get(self.source_name, 3)
        self._last_request_time: float = 0.0

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def scrape(self) -> list[dict]:
        """
        Collect raw data from the source.

        Returns a list of dicts, each representing one piece of user feedback.
        Required keys: 'text', 'source_url'
        Optional keys: 'published_at', 'rating', 'author_handle', 'extra_metadata'
        """
        ...

    @abstractmethod
    def validate(self, record: dict) -> bool:
        """
        Validate a single scraped record.

        Returns True if the record is valid and should be saved, False otherwise.
        At minimum, check that 'text' is present and non-empty.
        """
        ...

    # ------------------------------------------------------------------
    # Rate limiting
    # ------------------------------------------------------------------

    def wait_for_rate_limit(self):
        """Sleep to respect the per-source rate limit."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit:
            sleep_time = self.rate_limit - elapsed
            self.logger.debug("Rate limit: sleeping %.2fs", sleep_time)
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    # ------------------------------------------------------------------
    # Retry logic
    # ------------------------------------------------------------------

    def run_with_retry(self) -> list[dict]:
        """
        Execute scrape() with exponential backoff retry on failure.

        Returns the scraped records on success, or an empty list after exhausting retries.
        """
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                self.logger.info(
                    "Scrape attempt %d/%d for source=%s",
                    attempt, self.max_retries, self.source_name,
                )
                records = self.scrape()
                self.logger.info(
                    "Scrape succeeded: %d raw records from source=%s",
                    len(records), self.source_name,
                )
                return records

            except Exception as exc:
                last_error = exc
                backoff = 2 ** attempt  # 2s, 4s, 8s, ...
                self.logger.warning(
                    "Scrape attempt %d/%d failed for source=%s: %s — retrying in %ds",
                    attempt, self.max_retries, self.source_name, exc, backoff,
                )
                time.sleep(backoff)

        self.logger.error(
            "All %d scrape attempts exhausted for source=%s. Last error: %s",
            self.max_retries, self.source_name, last_error,
        )
        return []

    # ------------------------------------------------------------------
    # Deduplication
    # ------------------------------------------------------------------

    @staticmethod
    def _content_hash(text: str) -> str:
        """Generate a stable SHA-256 hash of review text for duplicate detection."""
        normalized = text.strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _get_existing_hashes(self, db: Session) -> set[str]:
        """
        Load content hashes of all existing raw reviews for this source.

        Uses the source_url as a proxy for dedup when available,
        and falls back to text hashing.
        """
        from api.models.review import RawReview

        existing_urls = set()
        rows = (
            db.query(RawReview.source_url, RawReview.original_text)
            .filter(RawReview.source == self.source_name)
            .all()
        )
        for url, text in rows:
            if url:
                existing_urls.add(url)
            else:
                existing_urls.add(self._content_hash(text))
        return existing_urls

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(
        self,
        records: list[dict],
        db: Session,
        scrape_job,
    ) -> int:
        """
        Validate and persist scraped records to the raw_review table.

        Performs dedup against existing records for this source.
        Returns the count of newly inserted records.
        """
        from api.models.review import RawReview

        existing = self._get_existing_hashes(db)
        inserted = 0
        skipped_invalid = 0
        skipped_dup = 0

        for record in records:
            # Validate
            if not self.validate(record):
                skipped_invalid += 1
                continue

            text = record["text"].strip()
            source_url = record.get("source_url")

            # Dedup check
            dedup_key = source_url if source_url else self._content_hash(text)
            if dedup_key in existing:
                skipped_dup += 1
                continue

            # Parse published_at
            published_at = record.get("published_at")
            if isinstance(published_at, str):
                try:
                    published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    published_at = None

            # Create RawReview record
            review = RawReview(
                id=uuid.uuid4(),
                scrape_job_id=scrape_job.id,
                source=self.source_name,
                source_url=source_url,
                original_text=text,
                published_at=published_at,
                scraped_at=datetime.utcnow(),
                rating=record.get("rating"),
                author_handle=record.get("author_handle"),
            )
            db.add(review)
            existing.add(dedup_key)
            inserted += 1

        # Flush in batch
        if inserted > 0:
            db.flush()

        self.logger.info(
            "Save results for source=%s: inserted=%d, skipped_invalid=%d, skipped_dup=%d",
            self.source_name, inserted, skipped_invalid, skipped_dup,
        )
        return inserted
