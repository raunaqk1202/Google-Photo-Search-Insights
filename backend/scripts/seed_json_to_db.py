import os
import sys
import json
import glob
import uuid
import logging
from datetime import datetime
import dateutil.parser

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from api.database import SessionLocal
from api.models.review import ScrapeJob, RawReview

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed")

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return dateutil.parser.parse(date_str).replace(tzinfo=None)
    except Exception:
        return None

def main():
    db = SessionLocal()
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scraped_data")
    json_files = glob.glob(os.path.join(data_dir, "*.json"))
    
    # We want to only process the best/latest file for each source to avoid inserting 0-record files
    best_files = {}
    for f in sorted(json_files):
        source = os.path.basename(f).split('_')[0]
        if source == "reddit" and "recovered" not in f:
            continue # Use reddit_recovered.json
            
        with open(f, 'r') as fh:
            data = json.load(fh)
        
        count = len(data) if isinstance(data, list) else 0
        if source not in best_files or count > best_files[source]['count']:
            best_files[source] = {'file': f, 'count': count, 'data': data}

    total_inserted = 0
    
    for source, info in best_files.items():
        data = info['data']
        count = info['count']
        
        if count == 0:
            continue
            
        logger.info(f"Processing {source}: {count} records from {os.path.basename(info['file'])}")
        
        # Create a ScrapeJob for this source
        job = ScrapeJob(
            id=uuid.uuid4(),
            source=source,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            total_collected=count,
            status="completed"
        )
        db.add(job)
        db.flush()
        
        # Insert records
        inserted_for_source = 0
        for i, record in enumerate(data):
            try:
                raw_review = RawReview(
                    id=uuid.uuid4(),
                    scrape_job_id=job.id,
                    source=source,
                    source_url=record.get("source_url") or record.get("url"),
                    original_text=record.get("text", ""),
                    published_at=parse_date(record.get("published_at")),
                    scraped_at=datetime.utcnow(),
                    rating=record.get("rating"),
                    author_handle=record.get("author_handle")
                )
                db.add(raw_review)
                inserted_for_source += 1
                
                if inserted_for_source % 1000 == 0:
                    db.commit()
                    logger.info(f"  Inserted {inserted_for_source}/{count}...")
                    
            except Exception as e:
                logger.warning(f"  Error inserting record: {e}")
                
        db.commit()
        total_inserted += inserted_for_source
        logger.info(f"Finished {source}: {inserted_for_source} records inserted.")
        
    logger.info(f"Seeding complete! Total inserted: {total_inserted}")
    db.close()

if __name__ == "__main__":
    main()
