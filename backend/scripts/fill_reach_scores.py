import os
import sys
import logging
from dotenv import load_dotenv

# Setup path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
load_dotenv(os.path.join(os.path.dirname(backend_dir), ".env"))

from groq import Groq
from api.database import SessionLocal
from api.models.review import StructuredReview
from pipeline.extractor import FeatureExtractor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fill_reach")

def run():
    db = SessionLocal()
    
    # Fetch only the reviews that are missing a reach score to resume
    unscored_reviews = db.query(StructuredReview).filter(StructuredReview.reach_score == None).all()
    
    if not unscored_reviews:
        logger.info("No unscored reviews found. All done.")
        db.close()
        return
        
    logger.info(f"Processing remaining {len(unscored_reviews)} reviews with LLM to resume progress...")
    
    api_key = os.getenv("GROQ_API_KEY")
    valid_model = "canopylabs/orpheus-v1-english"
    
    logger.info(f"Using model: {valid_model}")
    
    extractor = FeatureExtractor(api_key=api_key)
    extractor.model = valid_model
    
    for i, review in enumerate(unscored_reviews):
        try:
            feats = extractor.extract_llm_features(review.cleaned_text)
            if feats and "reach_score" in feats:
                reach = feats.get("reach_score")
                if reach is not None:
                    review.reach_score = float(reach)
                    db.commit()
                    logger.info(f"Updated {i+1}/{len(unscored_reviews)}: ID {review.id} -> reach_score {reach}")
                else:
                    logger.error(f"Missing reach_score for {review.id}")
            else:
                logger.error(f"Invalid features for {review.id}")
        except Exception as e:
            logger.error(f"Error processing {review.id}: {e}")

    logger.info("Finished updating reach_scores.")
    db.close()

if __name__ == "__main__":
    run()
