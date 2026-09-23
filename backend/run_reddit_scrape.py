"""
Quick runner script to execute the Reddit scraper via Apify.

Usage: python -m run_reddit_scrape
"""

import sys
import os
import json
import logging

# Ensure the backend directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env from project root
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("run_reddit_scrape")


def main():
    from scrapers.reddit_scraper import RedditScraper

    logger.info("=" * 60)
    logger.info("Starting Reddit scrape via Apify")
    logger.info("=" * 60)

    scraper = RedditScraper()

    # Run the scraper (with retry logic from base class)
    records = scraper.run_with_retry()

    if not records:
        logger.warning("No records collected. Check logs above for errors.")
        return

    # Filter valid records
    valid = [r for r in records if scraper.validate(r)]
    logger.info("Collected %d raw records, %d valid after validation", len(records), len(valid))

    # Save results to a JSON file for inspection
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "reddit_scrape_results.json",
    )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(valid, f, indent=2, default=str)
    logger.info("Results saved to %s", output_path)

    # Also try to persist to the database if available
    try:
        import uuid
        from datetime import datetime
        from api.database import SessionLocal
        from api.models.review import ScrapeJob

        db = SessionLocal()
        try:
            # Create a scrape job record
            job = ScrapeJob(
                id=uuid.uuid4(),
                source="reddit",
                started_at=datetime.utcnow(),
                status="running",
            )
            db.add(job)
            db.flush()

            inserted = scraper.save(valid, db, job)

            job.completed_at = datetime.utcnow()
            job.total_collected = inserted
            job.status = "completed"
            db.commit()

            logger.info("Database persistence complete: %d records inserted", inserted)

        except Exception as db_err:
            db.rollback()
            logger.warning("Database persistence failed (data still saved to JSON): %s", db_err)
        finally:
            db.close()

    except Exception as import_err:
        logger.info("Database not available (%s) — JSON output is your primary result", import_err)

    # Print summary
    logger.info("=" * 60)
    logger.info("SCRAPE COMPLETE")
    logger.info("  Total records:  %d", len(records))
    logger.info("  Valid records:  %d", len(valid))
    logger.info("  Output file:    %s", output_path)
    logger.info("=" * 60)

    # Show a sample
    if valid:
        logger.info("Sample record:")
        sample = valid[0]
        for k, v in sample.items():
            val_str = str(v)[:120] if v else "(empty)"
            logger.info("  %s: %s", k, val_str)


if __name__ == "__main__":
    main()
