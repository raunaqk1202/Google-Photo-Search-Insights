"""
Standalone scrape runner — runs scrapers directly without Celery or PostgreSQL.

Saves raw scraped data to JSON files in backend/scraped_data/ for later ingestion.
"""

import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Load .env file before anything else
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("scrape_runner")

# Output directory
OUTPUT_DIR = Path(__file__).parent / "scraped_data"
OUTPUT_DIR.mkdir(exist_ok=True)


def run_scraper(source_name: str):
    """Run a single scraper and save results to JSON."""
    from scrapers import SCRAPER_REGISTRY

    if source_name not in SCRAPER_REGISTRY:
        logger.error("Unknown source: %s", source_name)
        return

    logger.info("=" * 60)
    logger.info("Starting scraper: %s", source_name)
    logger.info("=" * 60)

    scraper_cls = SCRAPER_REGISTRY[source_name]
    scraper = scraper_cls()

    try:
        records = scraper.run_with_retry()
        logger.info("Raw records collected: %d", len(records))

        # Filter through validate
        valid_records = [r for r in records if scraper.validate(r)]
        logger.info("Valid records after validation: %d", len(valid_records))

        # Save to JSON
        output_file = OUTPUT_DIR / f"{source_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(valid_records, f, indent=2, ensure_ascii=False, default=str)

        logger.info("Saved %d records to %s", len(valid_records), output_file)
        return valid_records

    except Exception as exc:
        logger.error("Scraper %s failed: %s", source_name, exc, exc_info=True)
        return []


def main():
    """Run all scrapers or a specific one."""
    from scrapers import VALID_SOURCES

    # Check which scrapers to run
    if len(sys.argv) > 1:
        sources = [s for s in sys.argv[1:] if s in VALID_SOURCES]
        if not sources:
            print(f"Usage: python run_scrapers.py [source1] [source2] ...")
            print(f"Valid sources: {VALID_SOURCES}")
            sys.exit(1)
    else:
        sources = VALID_SOURCES

    logger.info("Will run scrapers: %s", sources)

    results = {}
    for source in sources:
        records = run_scraper(source)
        results[source] = len(records) if records else 0

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("SCRAPE SUMMARY")
    logger.info("=" * 60)
    total = 0
    for source, count in results.items():
        logger.info("  %-15s: %d records", source, count)
        total += count
    logger.info("  %-15s: %d records", "TOTAL", total)
    logger.info("Output directory: %s", OUTPUT_DIR)


if __name__ == "__main__":
    main()
