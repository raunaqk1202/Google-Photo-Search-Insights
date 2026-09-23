"""
Quick test script — runs the Reddit scraper against ONE subreddit with a small
item limit to verify the new Apify actor (reddit-scraper-lite) works.
"""

import sys
import os
import json
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("test_reddit")


def main():
    from apify_client import ApifyClient
    from api.config import get_settings

    settings = get_settings()
    token = settings.apify_api_token
    if not token:
        logger.error("APIFY_API_TOKEN not set")
        return

    client = ApifyClient(token)

    # Small test: 1 subreddit, 1 query, 10 items max
    run_input = {
        "startUrls": [
            {"url": "https://www.reddit.com/r/googlephotos/search/?q=find+old+photo&restrict_sr=1&sort=relevance&t=year"}
        ],
        "maxItems": 10,
        "maxPostCount": 10,
        "maxComments": 5,
        "scrollTimeout": 40,
        "navigationTimeout": 60,
        "proxy": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
        },
    }

    logger.info("Running test scrape with reddit-scraper-lite...")
    logger.info("Input: %s", json.dumps(run_input, indent=2))

    try:
        run = client.actor("trudax/reddit-scraper-lite").call(run_input=run_input)
        logger.info("Run completed! Status: %s", run.get("status"))

        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        logger.info("Got %d items from Apify", len(items))

        # Save raw response for inspection
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "reddit_test_output.json",
        )
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, default=str)
        logger.info("Raw items saved to %s", output_path)

        # Show first item structure
        if items:
            logger.info("=== First item keys: %s", list(items[0].keys()))
            logger.info("=== First item preview:")
            for k, v in items[0].items():
                val_str = str(v)[:150] if v else "(empty)"
                logger.info("  %s: %s", k, val_str)

    except Exception as exc:
        logger.error("Scrape failed: %s", exc)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
