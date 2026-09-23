"""
Google Play Store scraper — collects Google Photos app reviews.

Uses the `google-play-scraper` package to fetch reviews sorted by relevance,
then filters for retrieval/search-related keywords.
"""

import logging

from scrapers.base_scraper import BaseScraper
from scrapers.config import SCRAPER_CONFIG

logger = logging.getLogger(__name__)


class PlayStoreScraper(BaseScraper):
    """Scrapes Google Photos reviews from the Google Play Store."""

    source_name = "playstore"

    def __init__(self):
        super().__init__()
        self.config = SCRAPER_CONFIG["playstore"]

    def scrape(self) -> list[dict]:
        """
        Fetch reviews from Google Play Store using google-play-scraper.

        Returns a list of dicts with keys: text, source_url, published_at,
        rating, author_handle.
        """
        from google_play_scraper import Sort, reviews as fetch_reviews

        app_id = self.config["app_id"]
        count = self.config["count"]
        keywords = self.config["filter_keywords"]

        self.logger.info(
            "Fetching up to %d reviews for app=%s from Play Store",
            count, app_id,
        )

        # google-play-scraper returns (results_list, continuation_token)
        all_reviews = []
        continuation_token = None
        batch_size = 200  # Max per request

        while len(all_reviews) < count:
            self.wait_for_rate_limit()

            result, continuation_token = fetch_reviews(
                app_id,
                lang=self.config["lang"],
                country=self.config["country"],
                sort=Sort.NEWEST,
                count=batch_size,
                continuation_token=continuation_token,
            )

            if not result:
                self.logger.info("No more reviews available from Play Store")
                break

            all_reviews.extend(result)
            self.logger.debug(
                "Fetched batch of %d reviews (total: %d)",
                len(result), len(all_reviews),
            )

            if continuation_token is None:
                break

        self.logger.info("Total Play Store reviews fetched: %d", len(all_reviews))

        # Filter for relevance keywords
        filtered = []
        for review in all_reviews:
            text = review.get("content", "")
            if not text:
                continue

            text_lower = text.lower()
            if any(kw in text_lower for kw in keywords):
                filtered.append(self._normalize(review))

        self.logger.info(
            "After keyword filtering: %d/%d reviews retained",
            len(filtered), len(all_reviews),
        )
        return filtered

    def validate(self, record: dict) -> bool:
        """Validate a Play Store review record."""
        text = record.get("text", "").strip()
        if not text or len(text) < 10:
            return False
        return True

    @staticmethod
    def _normalize(review: dict) -> dict:
        """Normalize a google-play-scraper review dict to our standard schema."""
        review_id = review.get("reviewId", "")
        published = review.get("at")

        return {
            "text": review.get("content", ""),
            "source_url": (
                f"https://play.google.com/store/apps/details"
                f"?id=com.google.android.apps.photos&reviewId={review_id}"
                if review_id else None
            ),
            "published_at": published.isoformat() if published else None,
            "rating": review.get("score"),
            "author_handle": review.get("userName"),
        }
