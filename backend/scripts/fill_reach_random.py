import os
import sys
import random
import logging
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
load_dotenv(os.path.join(os.path.dirname(backend_dir), ".env"))

from api.database import SessionLocal
from api.models.review import StructuredReview

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fill_reach_random")

def run():
    db = SessionLocal()
    unscored_reviews = db.query(StructuredReview).filter(StructuredReview.reach_score == None).all()
    
    if not unscored_reviews:
        logger.info("No unscored reviews found.")
        db.close()
        return

    logger.info(f"Found {len(unscored_reviews)} reviews missing reach_score. Filling randomly...")
    
    for review in unscored_reviews:
        review.reach_score = round(random.uniform(1.0, 5.0), 1)
        
    db.commit()
    logger.info("Finished updating reach_scores with simulated values.")
    db.close()

if __name__ == "__main__":
    run()
