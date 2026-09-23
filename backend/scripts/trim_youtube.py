import sys
import os
import random
import logging

sys.path.insert(0, '/app')
from api.database import SessionLocal
from api.models.review import RawReview, StructuredReview

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trim_youtube")

def main():
    db = SessionLocal()
    
    # 1. Get all YouTube raw reviews
    all_youtube = db.query(RawReview).filter(RawReview.source == 'youtube').all()
    logger.info(f"Total YouTube reviews in DB: {len(all_youtube)}")
    
    if len(all_youtube) <= 800:
        logger.info("Already at or below 800. Exiting.")
        return

    # 2. Separate into those WITH structured reviews vs WITHOUT
    with_structured = []
    without_structured = []
    
    # Pre-fetch structured reviews to avoid N+1 queries
    processed_ids = {
        sr.raw_review_id for sr in db.query(StructuredReview.raw_review_id).filter(
            StructuredReview.source == 'youtube'
        ).all()
    }
    
    for rev in all_youtube:
        if rev.id in processed_ids:
            with_structured.append(rev)
        else:
            without_structured.append(rev)
            
    logger.info(f"YouTube reviews WITH structured insights: {len(with_structured)}")
    logger.info(f"YouTube reviews WITHOUT insights: {len(without_structured)}")
    
    # 3. Calculate how many to keep
    # We want exactly 800 total. We MUST keep all `with_structured`.
    num_to_keep_without = max(0, 800 - len(with_structured))
    
    logger.info(f"Will keep {num_to_keep_without} additional reviews to reach 800.")
    
    # Shuffle and pick the ones to delete
    random.shuffle(without_structured)
    to_delete = without_structured[num_to_keep_without:]
    
    logger.info(f"Deleting {len(to_delete)} excess YouTube reviews...")
    
    for idx, rev in enumerate(to_delete):
        db.delete(rev)
        if idx > 0 and idx % 500 == 0:
            db.commit()
            
    db.commit()
    logger.info("Successfully trimmed YouTube dataset to exactly 800 records.")
    
    # Verify count
    new_count = db.query(RawReview).filter(RawReview.source == 'youtube').count()
    logger.info(f"New YouTube count: {new_count}")
    
    db.close()

if __name__ == "__main__":
    main()
