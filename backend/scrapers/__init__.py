"""Scrapers package — data acquisition layer.

Exports SCRAPER_REGISTRY mapping source names to scraper classes.
"""

from scrapers.playstore_scraper import PlayStoreScraper
from scrapers.appstore_scraper import AppStoreScraper
from scrapers.reddit_scraper import RedditScraper
from scrapers.youtube_scraper import YouTubeScraper
from scrapers.community_scraper import CommunityScraper

# Registry of all available scrapers: source_name → ScraperClass
SCRAPER_REGISTRY = {
    "playstore": PlayStoreScraper,
    "appstore": AppStoreScraper,
    "reddit": RedditScraper,
    "youtube": YouTubeScraper,
    "community": CommunityScraper,
}

VALID_SOURCES = list(SCRAPER_REGISTRY.keys())

__all__ = [
    "SCRAPER_REGISTRY",
    "VALID_SOURCES",
    "PlayStoreScraper",
    "AppStoreScraper",
    "RedditScraper",
    "YouTubeScraper",
    "CommunityScraper",
]
