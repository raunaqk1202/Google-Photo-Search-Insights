"""
Unit tests for Phase 1 — Data Acquisition Layer.

Tests cover:
- Base scraper validation and dedup logic
- Each scraper's validate() method with sample data
- Scrape service job creation and status tracking
- API endpoint integration
"""

import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


def _has_psycopg2() -> bool:
    """Check if psycopg2 is importable (needed for DB-dependent tests)."""
    try:
        import psycopg2  # noqa: F401
        return True
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# Base scraper tests
# ---------------------------------------------------------------------------


class TestBaseScraper:
    """Tests for the BaseScraper abstract class."""

    def _make_scraper(self):
        """Create a concrete test subclass of BaseScraper."""
        from scrapers.base_scraper import BaseScraper

        class TestScraper(BaseScraper):
            source_name = "test"

            def scrape(self):
                return [{"text": "test review", "source_url": "http://example.com/1"}]

            def validate(self, record):
                text = record.get("text", "").strip()
                return bool(text) and len(text) >= 5

        return TestScraper()

    def test_content_hash_deterministic(self):
        """Same text should always produce the same hash."""
        from scrapers.base_scraper import BaseScraper

        h1 = BaseScraper._content_hash("Hello world")
        h2 = BaseScraper._content_hash("Hello world")
        assert h1 == h2

    def test_content_hash_normalized(self):
        """Hash should be case-insensitive and whitespace-trimmed."""
        from scrapers.base_scraper import BaseScraper

        h1 = BaseScraper._content_hash("  Hello World  ")
        h2 = BaseScraper._content_hash("hello world")
        assert h1 == h2

    def test_content_hash_different_text(self):
        """Different text should produce different hashes."""
        from scrapers.base_scraper import BaseScraper

        h1 = BaseScraper._content_hash("Hello")
        h2 = BaseScraper._content_hash("World")
        assert h1 != h2

    def test_validate_accepts_good_record(self):
        scraper = self._make_scraper()
        assert scraper.validate({"text": "This is a valid review"}) is True

    def test_validate_rejects_empty_text(self):
        scraper = self._make_scraper()
        assert scraper.validate({"text": ""}) is False

    def test_validate_rejects_short_text(self):
        scraper = self._make_scraper()
        assert scraper.validate({"text": "Hi"}) is False

    def test_validate_rejects_missing_text(self):
        scraper = self._make_scraper()
        assert scraper.validate({}) is False

    def test_run_with_retry_success(self):
        """run_with_retry should return results on first success."""
        scraper = self._make_scraper()
        results = scraper.run_with_retry()
        assert len(results) == 1
        assert results[0]["text"] == "test review"

    def test_run_with_retry_retries_on_failure(self):
        """run_with_retry should retry on exception."""
        from scrapers.base_scraper import BaseScraper

        call_count = 0

        class FailOnceScraper(BaseScraper):
            source_name = "test_fail"

            def scrape(self):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise RuntimeError("Temporary failure")
                return [{"text": "recovered", "source_url": None}]

            def validate(self, record):
                return True

        scraper = FailOnceScraper()
        scraper.max_retries = 3
        results = scraper.run_with_retry()
        assert call_count == 2
        assert len(results) == 1

    @pytest.mark.skipif(
        not _has_psycopg2(),
        reason="psycopg2 not installed — skipping DB-dependent test",
    )
    def test_save_deduplication(self):
        """save() should skip records that already exist by source_url."""
        scraper = self._make_scraper()

        # Mock DB session
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [
            ("http://example.com/1", "existing review"),  # Already in DB
        ]

        scrape_job = MagicMock()
        scrape_job.id = uuid.uuid4()

        records = [
            {"text": "existing review", "source_url": "http://example.com/1"},
            {"text": "new review text here", "source_url": "http://example.com/2"},
        ]

        inserted = scraper.save(records, db, scrape_job)
        assert inserted == 1  # Only the new one


# ---------------------------------------------------------------------------
# PlayStore scraper tests
# ---------------------------------------------------------------------------


class TestPlayStoreScraper:
    """Tests for PlayStoreScraper.validate()."""

    def test_validate_good_review(self):
        from scrapers.playstore_scraper import PlayStoreScraper

        scraper = PlayStoreScraper()
        assert scraper.validate({"text": "I can't find my old photos"}) is True

    def test_validate_rejects_short(self):
        from scrapers.playstore_scraper import PlayStoreScraper

        scraper = PlayStoreScraper()
        assert scraper.validate({"text": "good"}) is False

    def test_validate_rejects_empty(self):
        from scrapers.playstore_scraper import PlayStoreScraper

        scraper = PlayStoreScraper()
        assert scraper.validate({"text": ""}) is False


# ---------------------------------------------------------------------------
# AppStore scraper tests
# ---------------------------------------------------------------------------


class TestAppStoreScraper:
    """Tests for AppStoreScraper.validate()."""

    def test_validate_good_review(self):
        from scrapers.appstore_scraper import AppStoreScraper

        scraper = AppStoreScraper()
        assert scraper.validate({"text": "Can't search for old vacation pics"}) is True

    def test_validate_rejects_short(self):
        from scrapers.appstore_scraper import AppStoreScraper

        scraper = AppStoreScraper()
        assert scraper.validate({"text": "ok"}) is False


# ---------------------------------------------------------------------------
# Reddit scraper tests
# ---------------------------------------------------------------------------


class TestRedditScraper:
    """Tests for RedditScraper.validate() and _normalize()."""

    def test_validate_good_post(self):
        from scrapers.reddit_scraper import RedditScraper

        scraper = RedditScraper()
        assert scraper.validate({"text": "How do I find old photos in Google Photos?"}) is True

    def test_validate_rejects_deleted(self):
        from scrapers.reddit_scraper import RedditScraper

        scraper = RedditScraper()
        assert scraper.validate({"text": "[deleted]"}) is False

    def test_validate_rejects_removed(self):
        from scrapers.reddit_scraper import RedditScraper

        scraper = RedditScraper()
        assert scraper.validate({"text": "[removed]"}) is False

    def test_normalize_post_with_comments(self):
        from scrapers.reddit_scraper import RedditScraper

        item = {
            "title": "Search not working",
            "body": "I can't find my travel photos",
            "url": "https://reddit.com/r/test/123",
            "createdAt": "2024-01-15T10:00:00Z",
            "score": 42,
            "author": "testuser",
            "comments": [
                {
                    "body": "Same problem here",
                    "url": "https://reddit.com/r/test/123/comment1",
                    "score": 5,
                    "author": "commenter1",
                },
            ],
        }

        records = RedditScraper._normalize(item, "googlephotos")
        assert len(records) == 2
        assert "Search not working" in records[0]["text"]
        assert records[1]["text"] == "Same problem here"


# ---------------------------------------------------------------------------
# YouTube scraper tests
# ---------------------------------------------------------------------------


class TestYouTubeScraper:
    """Tests for YouTubeScraper.validate() and _normalize()."""

    def test_validate_good_comment(self):
        from scrapers.youtube_scraper import YouTubeScraper

        scraper = YouTubeScraper()
        assert scraper.validate({"text": "This helped me find my old photos!"}) is True

    def test_validate_rejects_short(self):
        from scrapers.youtube_scraper import YouTubeScraper

        scraper = YouTubeScraper()
        assert scraper.validate({"text": "nice"}) is False

    def test_normalize_comment(self):
        from scrapers.youtube_scraper import YouTubeScraper

        snippet = {
            "textDisplay": "Great tips for finding old photos",
            "publishedAt": "2024-03-01T12:00:00Z",
            "likeCount": 10,
            "authorDisplayName": "TestUser",
        }

        result = YouTubeScraper._normalize(snippet, "abc123")
        assert result["text"] == "Great tips for finding old photos"
        assert result["source_url"] == "https://www.youtube.com/watch?v=abc123"
        assert result["rating"] == 10


# ---------------------------------------------------------------------------
# Community scraper tests
# ---------------------------------------------------------------------------


class TestCommunityScraper:
    """Tests for CommunityScraper.validate()."""

    def test_validate_good_post(self):
        from scrapers.community_scraper import CommunityScraper

        scraper = CommunityScraper()
        assert scraper.validate({"text": "How do I find old photos that I took last year?"}) is True

    def test_validate_rejects_short(self):
        from scrapers.community_scraper import CommunityScraper

        scraper = CommunityScraper()
        assert scraper.validate({"text": "Sign in"}) is False

    def test_validate_rejects_boilerplate(self):
        from scrapers.community_scraper import CommunityScraper

        scraper = CommunityScraper()
        assert scraper.validate({"text": "Sign in to your Google Account"}) is False


# ---------------------------------------------------------------------------
# Scraper registry tests
# ---------------------------------------------------------------------------


class TestScraperRegistry:
    """Tests for the scraper registry in __init__.py."""

    def test_registry_has_all_sources(self):
        from scrapers import SCRAPER_REGISTRY, VALID_SOURCES

        expected = {"playstore", "appstore", "reddit", "youtube", "community"}
        assert set(VALID_SOURCES) == expected
        assert set(SCRAPER_REGISTRY.keys()) == expected

    def test_registry_classes_are_scrapers(self):
        from scrapers import SCRAPER_REGISTRY
        from scrapers.base_scraper import BaseScraper

        for name, cls in SCRAPER_REGISTRY.items():
            assert issubclass(cls, BaseScraper), f"{name} is not a BaseScraper subclass"


# ---------------------------------------------------------------------------
# Config tests
# ---------------------------------------------------------------------------


class TestScraperConfig:
    """Tests for scraper configuration."""

    def test_config_has_all_sources(self):
        from scrapers.config import SCRAPER_CONFIG

        expected = {"playstore", "appstore", "reddit", "youtube", "community"}
        assert set(SCRAPER_CONFIG.keys()) == expected

    def test_rate_limits_defined(self):
        from scrapers.config import RATE_LIMITS

        for source in ["playstore", "appstore", "reddit", "youtube", "community"]:
            assert source in RATE_LIMITS
            assert RATE_LIMITS[source] > 0

    def test_max_retries_defined(self):
        from scrapers.config import MAX_RETRIES

        for source in ["playstore", "appstore", "reddit", "youtube", "community"]:
            assert source in MAX_RETRIES
            assert MAX_RETRIES[source] >= 1
