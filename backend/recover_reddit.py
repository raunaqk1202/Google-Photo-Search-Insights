import sys
import os
import json
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("recover_reddit")

def main():
    from apify_client import ApifyClient
    from api.config import get_settings
    from scrapers.reddit_scraper import RedditScraper
    
    settings = get_settings()
    client = ApifyClient(settings.apify_api_token)
    scraper = RedditScraper()
    
    # These are the 5 run IDs for r/googlephotos from the previous killed task
    run_ids = [
        'A4YWtqwlToWVOJN12', 
        'CZvKKKppS6c2nGLMA', 
        'vYgoShAmVGTn9J1xg', 
        'ozraFwyaYvlrftdpw', 
        'Ua28SLqEbFdGv7RNx'
    ]
    
    all_valid = []
    
    for run_id in run_ids:
        logger.info("Fetching dataset for run %s", run_id)
        run = client.run(run_id).get()
        if not run:
            continue
            
        dataset_id = run["defaultDatasetId"]
        items = list(client.dataset(dataset_id).iterate_items())
        
        # Normalize and validate just like the scraper does
        for item in items:
            normalized_records = scraper._normalize(item, "googlephotos")
            for record in normalized_records:
                if scraper.validate(record):
                    all_valid.append(record)
                    
    logger.info("Recovered %d valid records!", len(all_valid))
    
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "scraped_data",
        "reddit_recovered.json",
    )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_valid, f, indent=2, default=str)
        
    logger.info("Saved to %s", output_path)

if __name__ == "__main__":
    main()
