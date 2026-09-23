"""
Apple App Store scraper — collects Google Photos iOS app reviews.

Uses the iTunes RSS feed API to fetch recent reviews directly.
"""

import logging
from datetime import datetime

from scrapers.base_scraper import BaseScraper
from scrapers.config import SCRAPER_CONFIG

logger = logging.getLogger(__name__)


class AppStoreScraper(BaseScraper):
    """Scrapes Google Photos reviews from the Apple App Store."""

    source_name = "appstore"

    def __init__(self):
        super().__init__()
        self.config = SCRAPER_CONFIG["appstore"]

    def scrape(self) -> list[dict]:
        """
        Fetch reviews from the Apple App Store via iTunes RSS feed.

        Returns a list of dicts with keys: text, source_url, published_at,
        rating, author_handle.
        """
        import httpx

        app_id = self.config["app_id"]
        country = self.config.get("country", "us")

        self.logger.info("Fetching reviews for app_id=%s from App Store via RSS", app_id)

        all_raw_reviews = []
        
        # iTunes RSS feed paginates from 1 to 10
        with httpx.Client(timeout=15.0) as client:
            for page in range(1, 11):
                url = f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortBy=mostRecent/json"
                try:
                    response = client.get(url)
                    if response.status_code != 200:
                        self.logger.warning(
                            "App Store RSS returned %d for page %d", response.status_code, page
                        )
                        break
                        
                    data = response.json()
                    entries = data.get("feed", {}).get("entry", [])
                    if not entries:
                        break
                        
                    # Skip the first entry which is often the app itself, not a review
                    for entry in entries:
                        if entry.get("author") and entry.get("content"):
                            all_raw_reviews.append(entry)
                            
                except Exception as exc:
                    self.logger.error("App Store scraper error on page %d: %s", page, exc)
                    break
                    
                self.wait_for_rate_limit()

        self.logger.info("Total App Store reviews fetched: %d", len(all_raw_reviews))

        # Normalize to our standard schema
        records = [self._normalize(r) for r in all_raw_reviews]

        # Filter for relevance keywords (same as Play Store)
        keywords = SCRAPER_CONFIG["playstore"]["filter_keywords"]
        filtered = []
        for record in records:
            text_lower = record["text"].lower()
            if any(kw in text_lower for kw in keywords):
                filtered.append(record)

        self.logger.info(
            "After keyword filtering: %d/%d reviews retained",
            len(filtered), len(records),
        )
        return filtered

    def validate(self, record: dict) -> bool:
        """Validate an App Store review record."""
        text = record.get("text", "").strip()
        if not text or len(text) < 10:
            return False
        return True

    @staticmethod
    def _normalize(entry: dict) -> dict:
        """Normalize an iTunes RSS review entry to our standard schema."""
        try:
            content = entry.get("content", {}).get("label", "")
            title = entry.get("title", {}).get("label", "")
            # Combine title and content
            text = f"{title}\n\n{content}" if title and title != content else content
            
            author = entry.get("author", {}).get("name", {}).get("label")
            rating_str = entry.get("im:rating", {}).get("label", "0")
            rating = int(rating_str) if rating_str.isdigit() else 0
            
            # iTunes format: "2024-03-05T08:35:10-07:00"
            updated_str = entry.get("updated", {}).get("label")
            published_at = None
            if updated_str:
                # Try to parse it, fall back to string if fails
                try:
                    published_at = datetime.fromisoformat(updated_str).isoformat()
                except ValueError:
                    published_at = updated_str
            
            return {
                "text": text.strip(),
                "source_url": None,
                "published_at": published_at,
                "rating": rating,
                "author_handle": author,
            }
        except Exception:
            return {
                "text": "",
                "source_url": None,
                "published_at": None,
                "rating": 0,
                "author_handle": None,
            }

