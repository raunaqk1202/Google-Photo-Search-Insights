"""
Google Photos Help Community scraper — collects questions, replies, and discussion
from the Google Support community forums.

Uses `httpx` + `BeautifulSoup` for HTML scraping.
"""

import logging
import re
from urllib.parse import urljoin, quote

from scrapers.base_scraper import BaseScraper
from scrapers.config import SCRAPER_CONFIG

logger = logging.getLogger(__name__)

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]


class CommunityScraper(BaseScraper):
    """Scrapes the Google Photos Help Community forums."""

    source_name = "community"

    def __init__(self):
        super().__init__()
        self.config = SCRAPER_CONFIG["community"]
        self._user_agent_index = 0

    def _get_user_agent(self) -> str:
        """Rotate user agents across requests."""
        ua = USER_AGENTS[self._user_agent_index % len(USER_AGENTS)]
        self._user_agent_index += 1
        return ua

    def scrape(self) -> list[dict]:
        """
        Scrape the Google Photos Help Community for search-related threads.

        Returns a list of dicts with keys: text, source_url, published_at,
        author_handle.
        """
        import httpx
        from bs4 import BeautifulSoup

        base_url = self.config["base_url"]
        categories = self.config["categories"]
        max_pages = self.config["max_pages"]

        all_records: list[dict] = []

        # Scrape search results for each category
        for category in categories:
            self.logger.info(
                "Community: scraping category='%s' (max_pages=%d)",
                category, max_pages,
            )

            page = 0
            while page < max_pages:
                self.wait_for_rate_limit()

                # Build search URL
                search_url = (
                    f"https://support.google.com/photos/search?"
                    f"q={quote(category)}&hl=en"
                )
                if page > 0:
                    search_url += f"&start={page * 10}"

                try:
                    headers = {
                        "User-Agent": self._get_user_agent(),
                        "Accept": "text/html,application/xhtml+xml",
                        "Accept-Language": "en-US,en;q=0.9",
                    }

                    response = httpx.get(
                        search_url,
                        headers=headers,
                        timeout=30.0,
                        follow_redirects=True,
                    )

                    if response.status_code == 429:
                        self.logger.warning("Rate limited by Google Support (429)")
                        break

                    if response.status_code != 200:
                        self.logger.warning(
                            "Community page returned %d for url=%s",
                            response.status_code, search_url,
                        )
                        break

                    soup = BeautifulSoup(response.text, "html.parser")

                    # Extract thread links from search results
                    thread_links = self._extract_thread_links(soup, base_url)

                    if not thread_links:
                        self.logger.debug(
                            "No more threads found for category='%s' at page=%d",
                            category, page,
                        )
                        break

                    # Fetch each thread
                    for thread_url in thread_links:
                        self.wait_for_rate_limit()
                        thread_records = self._scrape_thread(thread_url)
                        all_records.extend(thread_records)

                except Exception as exc:
                    self.logger.warning(
                        "Community scrape error for category='%s' page=%d: %s",
                        category, page, exc,
                    )

                page += 1

        self.logger.info("Total Community records collected: %d", len(all_records))
        return all_records

    def _extract_thread_links(self, soup, base_url: str) -> list[str]:
        """Extract thread URLs from a search results page."""
        links = []

        # Google Support community thread links
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            # Community thread URLs typically contain /thread/ or /community/
            if "/thread/" in href or "/community/" in href:
                full_url = urljoin("https://support.google.com", href)
                if full_url not in links:
                    links.append(full_url)

        return links[:20]  # Limit threads per page

    def _scrape_thread(self, thread_url: str) -> list[dict]:
        """Scrape a single community thread for the question and replies."""
        import httpx
        from bs4 import BeautifulSoup

        records = []

        try:
            headers = {
                "User-Agent": self._get_user_agent(),
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
            }

            response = httpx.get(
                thread_url,
                headers=headers,
                timeout=30.0,
                follow_redirects=True,
            )

            if response.status_code != 200:
                return records

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract the main question / thread title
            title_elem = soup.find("h1") or soup.find("title")
            title = title_elem.get_text(strip=True) if title_elem else ""

            # Extract the body content — try common Google Support layouts
            body_texts = []

            # Look for post content containers
            for selector in [
                "div.thread-question",
                "div.thread-message",
                "div[class*='question']",
                "div[class*='post-content']",
                "div[class*='message-body']",
                "article",
            ]:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(separator=" ", strip=True)
                    if text and len(text) > 20:
                        body_texts.append(text)

            # If no structured content found, fall back to main content area
            if not body_texts:
                main = soup.find("main") or soup.find("div", {"role": "main"})
                if main:
                    text = main.get_text(separator=" ", strip=True)
                    # Clean up excessive whitespace
                    text = re.sub(r"\s+", " ", text)
                    if len(text) > 50:
                        body_texts.append(text[:5000])  # Cap at 5000 chars

            # Combine title + body into a record
            for body in body_texts:
                full_text = f"{title}\n\n{body}".strip() if title else body.strip()
                if full_text:
                    records.append({
                        "text": full_text,
                        "source_url": thread_url,
                        "published_at": None,  # Hard to extract reliably from HTML
                        "author_handle": None,
                    })

            # Also look for reply/answer content
            for selector in [
                "div.thread-reply",
                "div[class*='reply']",
                "div[class*='answer']",
                "div[class*='response']",
            ]:
                for elem in soup.select(selector):
                    reply_text = elem.get_text(separator=" ", strip=True)
                    if reply_text and len(reply_text) > 20:
                        records.append({
                            "text": reply_text,
                            "source_url": thread_url,
                            "published_at": None,
                            "author_handle": None,
                        })

        except Exception as exc:
            self.logger.debug("Thread scrape error for %s: %s", thread_url, exc)

        return records

    def validate(self, record: dict) -> bool:
        """Validate a community forum record."""
        text = record.get("text", "").strip()
        if not text or len(text) < 20:
            return False
        # Filter out navigation/boilerplate text
        boilerplate = [
            "sign in", "community content", "google account",
            "terms of service", "privacy policy", "cookie",
        ]
        text_lower = text.lower()
        if any(bp in text_lower and len(text) < 100 for bp in boilerplate):
            return False
        return True
