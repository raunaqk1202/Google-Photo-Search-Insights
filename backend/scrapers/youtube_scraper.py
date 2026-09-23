"""
YouTube Comments scraper — collects comments from Google Photos-related videos.

Uses the YouTube Data API v3 via `google-api-python-client` to:
1. Search for relevant videos about Google Photos search/retrieval
2. Fetch comment threads from each video
"""

import logging

from scrapers.base_scraper import BaseScraper
from scrapers.config import SCRAPER_CONFIG

logger = logging.getLogger(__name__)


class YouTubeScraper(BaseScraper):
    """Scrapes YouTube comments from Google Photos-related videos."""

    source_name = "youtube"

    def __init__(self):
        super().__init__()
        self.config = SCRAPER_CONFIG["youtube"]

    def scrape(self) -> list[dict]:
        """
        Search YouTube for relevant videos and collect comments.

        Returns a list of dicts with keys: text, source_url, published_at,
        rating (like_count), author_handle.
        """
        from googleapiclient.discovery import build
        from api.config import get_settings

        settings = get_settings()
        api_key = settings.youtube_api_key
        if not api_key:
            self.logger.error("YOUTUBE_API_KEY is not configured")
            raise ValueError("YOUTUBE_API_KEY is required for the YouTube scraper")

        youtube = build("youtube", "v3", developerKey=api_key)

        queries = self.config["search_queries"]
        max_results = self.config["max_results_per_query"]
        max_comments = self.config["max_comments_per_video"]

        all_records: list[dict] = []
        seen_video_ids: set[str] = set()

        # Step 1: Search for relevant videos
        for query in queries:
            self.wait_for_rate_limit()
            self.logger.info("YouTube: searching for '%s' (max=%d)", query, max_results)

            try:
                search_response = (
                    youtube.search()
                    .list(
                        q=query,
                        part="id,snippet",
                        type="video",
                        maxResults=max_results,
                        order="relevance",
                        relevanceLanguage="en",
                    )
                    .execute()
                )

                video_ids = []
                for item in search_response.get("items", []):
                    vid = item["id"].get("videoId")
                    if vid and vid not in seen_video_ids:
                        video_ids.append(vid)
                        seen_video_ids.add(vid)

                self.logger.info(
                    "Found %d new videos for query='%s'",
                    len(video_ids), query,
                )

                # Step 2: Fetch comments for each video
                for video_id in video_ids:
                    comments = self._fetch_comments(youtube, video_id, max_comments)
                    all_records.extend(comments)

            except Exception as exc:
                self.logger.warning(
                    "YouTube search failed for query='%s': %s", query, exc,
                )
                continue

        self.logger.info("Total YouTube comments collected: %d", len(all_records))
        return all_records

    def _fetch_comments(
        self, youtube, video_id: str, max_comments: int
    ) -> list[dict]:
        """Fetch comment threads for a single video."""
        self.wait_for_rate_limit()
        records = []

        try:
            next_page_token = None
            fetched = 0

            while fetched < max_comments:
                response = (
                    youtube.commentThreads()
                    .list(
                        videoId=video_id,
                        part="snippet",
                        maxResults=min(100, max_comments - fetched),
                        order="relevance",
                        textFormat="plainText",
                        pageToken=next_page_token,
                    )
                    .execute()
                )

                for item in response.get("items", []):
                    snippet = item["snippet"]["topLevelComment"]["snippet"]
                    record = self._normalize(snippet, video_id)
                    records.append(record)
                    fetched += 1

                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break

                self.wait_for_rate_limit()

        except Exception as exc:
            # Comments might be disabled on some videos
            self.logger.debug(
                "Could not fetch comments for video=%s: %s", video_id, exc,
            )

        return records

    def validate(self, record: dict) -> bool:
        """Validate a YouTube comment record."""
        text = record.get("text", "").strip()
        if not text or len(text) < 10:
            return False
        return True

    @staticmethod
    def _normalize(snippet: dict, video_id: str) -> dict:
        """Normalize a YouTube comment snippet to our standard schema."""
        return {
            "text": snippet.get("textDisplay", ""),
            "source_url": f"https://www.youtube.com/watch?v={video_id}",
            "published_at": snippet.get("publishedAt"),
            "rating": snippet.get("likeCount", 0),
            "author_handle": snippet.get("authorDisplayName"),
        }
