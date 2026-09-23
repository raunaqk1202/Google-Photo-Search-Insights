"""
Reddit scraper — collects Google Photos-related posts and comments via Apify.

Uses the `apify-client` Python package to run a Reddit Scraper Actor on the
Apify platform. Apify handles proxy rotation and anti-bot measures internally.
"""

import logging

from scrapers.base_scraper import BaseScraper
from scrapers.config import SCRAPER_CONFIG

logger = logging.getLogger(__name__)


class RedditScraper(BaseScraper):
    """Scrapes Reddit posts and comments about Google Photos via Apify."""

    source_name = "reddit"

    def __init__(self):
        super().__init__()
        self.config = SCRAPER_CONFIG["reddit"]

    def scrape(self) -> list[dict]:
        """
        Run the Apify Reddit Scraper Actor and collect results.

        Returns a list of dicts with keys: text, source_url, published_at,
        rating (score), author_handle.
        """
        from apify_client import ApifyClient
        from api.config import get_settings

        settings = get_settings()
        token = settings.apify_api_token
        if not token:
            self.logger.error("APIFY_API_TOKEN is not configured")
            raise ValueError("APIFY_API_TOKEN is required for the Reddit scraper")

        client = ApifyClient(token)
        actor_id = self.config["apify_actor_id"]
        subreddits = self.config["subreddits"]
        queries = self.config["search_queries"]
        max_items = self.config["max_items_per_query"]

        all_records: list[dict] = []

        # Run a scrape for each subreddit + query combination
        for subreddit in subreddits:
            for query in queries:
                self.wait_for_rate_limit()

                self.logger.info(
                    "Apify: scraping r/%s for query='%s' (max_items=%d)",
                    subreddit, query, max_items,
                )

                try:
                    run_input = {
                        "startUrls": [
                            {"url": f"https://www.reddit.com/r/{subreddit}/search/?q={query}&restrict_sr=1&sort=relevance&t=year"}
                        ],
                        "maxItems": max_items,
                        "maxPostCount": max_items,
                        "maxComments": 10,
                        "scrollTimeout": 40,
                        "navigationTimeout": 60,
                        "proxy": {
                            "useApifyProxy": True,
                            "apifyProxyGroups": ["RESIDENTIAL"],
                        },
                    }

                    run = client.actor(actor_id).call(run_input=run_input)

                    # Fetch results from the dataset
                    dataset_items = list(
                        client.dataset(run["defaultDatasetId"]).iterate_items()
                    )

                    self.logger.info(
                        "Apify returned %d items for r/%s query='%s'",
                        len(dataset_items), subreddit, query,
                    )

                    for item in dataset_items:
                        records = self._normalize(item, subreddit)
                        all_records.extend(records)

                except Exception as exc:
                    self.logger.warning(
                        "Apify scrape failed for r/%s query='%s': %s",
                        subreddit, query, exc,
                    )
                    continue

        self.logger.info("Total Reddit records collected: %d", len(all_records))
        return all_records

    def validate(self, record: dict) -> bool:
        """Validate a Reddit record."""
        text = record.get("text", "").strip()
        if not text or len(text) < 15:
            return False
        # Skip deleted/removed content
        if text.lower() in ("[deleted]", "[removed]"):
            return False
        return True

    @staticmethod
    def _normalize(item: dict, subreddit: str) -> list[dict]:
        """
        Normalize an Apify Reddit Scraper Lite item to our standard schema.

        reddit-scraper-lite returns flat items — each post and comment is a
        separate dict with 'dataType' of 'post' or 'comment'.
        """
        records = []

        data_type = item.get("dataType", "post")
        title = item.get("title", "")
        body = item.get("body", "") or ""

        # Build text: include title for posts, just body for comments
        if data_type == "post":
            text = f"{title}\n\n{body}".strip() if title else body.strip()
        else:
            text = body.strip()

        if text:
            records.append({
                "text": text,
                "source_url": item.get("url"),
                "published_at": item.get("createdAt"),
                "rating": None,  # reddit-scraper-lite doesn't return scores
                "author_handle": item.get("username"),
            })

        return records
