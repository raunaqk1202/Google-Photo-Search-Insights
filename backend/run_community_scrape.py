"""
Community scraper — alternative approach using Apify Google Search Results Scraper
to find Google Photos community threads, then extracting content via 
Google's cache/web text extraction.

Falls back to scraping Google search snippets if thread pages are JS-rendered.
"""

import sys
import os
import json
import logging
import re
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("community_scraper_v2")


def scrape_via_apify_google_search():
    """
    Use Apify's Google Search Results Scraper to find community threads.
    Each search result includes a title + snippet with actual thread content.
    """
    from apify_client import ApifyClient
    from api.config import get_settings

    settings = get_settings()
    client = ApifyClient(settings.apify_api_token)

    search_queries = [
        'site:support.google.com/photos/thread "can\'t find" photo',
        'site:support.google.com/photos/thread "search" photos problem',
        'site:support.google.com/photos/thread "missing photos"',
        'site:support.google.com/photos/thread "old photos" find',
        'site:support.google.com/photos/thread "photo search" not working',
        'site:support.google.com/photos/thread "looking for" photo',
        'site:support.google.com/photos/thread "find my photo"',
        'site:support.google.com/photos/thread "disappeared" photos',
        'site:support.google.com/photos/thread "search not showing"',
        'site:support.google.com/photos/thread "where are my photos"',
    ]

    all_records = []
    seen_urls = set()

    for query in search_queries:
        logger.info("Searching Google: %s", query)

        try:
            run_input = {
                "queries": query,
                "maxPagesPerQuery": 3,
                "resultsPerPage": 10,
                "languageCode": "en",
                "mobileResults": False,
            }

            # Use the official Apify Google Search Results Scraper
            run = client.actor("apify/google-search-scraper").call(
                run_input=run_input,
                timeout_secs=120,
            )

            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            logger.info("Got %d search result pages for query", len(items))

            for page in items:
                organic = page.get("organicResults", [])
                logger.info("  Page has %d organic results", len(organic))

                for result in organic:
                    url = result.get("url", "")
                    title = result.get("title", "")
                    snippet = result.get("description", "")

                    # Only keep Google Photos community threads
                    if "support.google.com/photos/thread" not in url:
                        continue

                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    # Combine title and snippet as the text
                    text = f"{title}\n\n{snippet}".strip()
                    if text and len(text) > 30:
                        all_records.append({
                            "text": text,
                            "source_url": url,
                            "published_at": None,
                            "rating": None,
                            "author_handle": None,
                        })

        except Exception as exc:
            logger.warning("Google search failed for query '%s': %s", query, exc)
            continue

        # Small delay between queries
        time.sleep(2)

    return all_records


def scrape_via_httpx_threads():
    """
    Fallback: scrape thread listing pages from Google Support directly.
    Even though individual threads are JS-rendered, the listing pages 
    contain thread titles which we can collect.
    """
    import httpx

    logger.info("Fallback: scraping thread titles from listing pages")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # Try different listing pages
    urls = [
        "https://support.google.com/photos/threads?hl=en",
        "https://support.google.com/photos/community?hl=en",
    ]

    all_thread_ids = set()
    for url in urls:
        try:
            r = httpx.get(url, headers=headers, follow_redirects=True, timeout=15)
            if r.status_code == 200:
                ids = set(re.findall(r'/photos/thread/(\d+)', r.text))
                all_thread_ids.update(ids)
                logger.info("Found %d thread IDs from %s", len(ids), url)
        except Exception as exc:
            logger.warning("Failed to fetch %s: %s", url, exc)

    logger.info("Total unique thread IDs: %d", len(all_thread_ids))

    # For each thread, try to get content via Google's text cache
    records = []
    for tid in all_thread_ids:
        thread_url = f"https://support.google.com/photos/thread/{tid}?hl=en"

        # Try webcache version which is sometimes plain text
        cache_url = f"https://webcache.googleusercontent.com/search?q=cache:support.google.com/photos/thread/{tid}"
        try:
            r = httpx.get(cache_url, headers=headers, follow_redirects=True, timeout=15)
            if r.status_code == 200 and len(r.text) > 500:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(r.text, "html.parser")
                text = soup.get_text(separator=" ", strip=True)
                # Clean up
                text = re.sub(r"\s+", " ", text)
                if len(text) > 100:
                    records.append({
                        "text": text[:3000],
                        "source_url": thread_url,
                        "published_at": None,
                        "rating": None,
                        "author_handle": None,
                    })
        except Exception:
            pass

        time.sleep(1)

    return records


def main():
    logger.info("=" * 60)
    logger.info("Community Scraper V2 — Google Photos Help Community")
    logger.info("=" * 60)

    # Primary approach: Apify Google Search
    records = scrape_via_apify_google_search()
    logger.info("Apify Google Search yielded %d records", len(records))

    # If that didn't work well, try the fallback
    if len(records) < 20:
        logger.info("Low yield from search, trying fallback approach...")
        fallback_records = scrape_via_httpx_threads()
        logger.info("Fallback yielded %d records", len(fallback_records))
        
        # Merge, deduplicating by URL
        seen = {r["source_url"] for r in records if r.get("source_url")}
        for r in fallback_records:
            if r.get("source_url") not in seen:
                records.append(r)
                seen.add(r["source_url"])

    # Filter valid records
    valid = [r for r in records if r.get("text") and len(r["text"].strip()) > 30]
    logger.info("Total valid community records: %d", len(valid))

    # Save to the scraped_data directory
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scraped_data")
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"community_{timestamp}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(valid, f, indent=2, default=str)

    logger.info("Results saved to %s", output_path)

    # Print summary
    logger.info("=" * 60)
    logger.info("COMMUNITY SCRAPE COMPLETE")
    logger.info("  Total records:  %d", len(valid))
    logger.info("  Output file:    %s", output_path)
    logger.info("=" * 60)

    if valid:
        logger.info("Sample record:")
        sample = valid[0]
        for k, v in sample.items():
            val_str = str(v)[:150] if v else "(empty)"
            logger.info("  %s: %s", k, val_str)


if __name__ == "__main__":
    main()
