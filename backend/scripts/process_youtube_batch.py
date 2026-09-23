import sys
import os
import random
import logging
from dotenv import load_dotenv
import time

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
load_dotenv(os.path.join(os.path.dirname(backend_dir), ".env"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("process_youtube")

from api.database import SessionLocal
from api.models.review import RawReview, StructuredReview, FailureMode, RetrievalArchetype, MemoryCue
from pipeline.cleaner import DataCleaner
from pipeline.classifier import RelevanceClassifier
from pipeline.extractor import FeatureExtractor
import uuid

def is_ambiguous(text):
    """Simple heuristics to discard very random/ambiguous reviews."""
    if not text:
        return True
    text = text.strip()
    words = text.split()
    if len(words) <= 4:
        return True
    if len(text) < 30:
        return True
    return False

def get_or_create(db, model, defaults=None, **kwargs):
    instance = db.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        params = dict((k, v) for k, v in kwargs.items())
        params.update(defaults or {})
        instance = model(**params)
        db.add(instance)
        db.flush()
        return instance

def main():
    db = SessionLocal()
    
    # Fetch all unprocessed YouTube reviews
    logger.info("Fetching unprocessed YouTube reviews...")
    unprocessed_youtube = db.query(RawReview).outerjoin(
        StructuredReview
    ).filter(
        StructuredReview.id == None,
        RawReview.source == 'youtube'
    ).all()
    
    logger.info(f"Found {len(unprocessed_youtube)} unprocessed YouTube reviews.")
    if not unprocessed_youtube:
        return

    # 1. Discard ambiguous and random reviews
    logger.info("Discarding ambiguous and random reviews...")
    to_delete = []
    to_keep = []
    
    for rev in unprocessed_youtube:
        if is_ambiguous(rev.original_text):
            to_delete.append(rev)
        else:
            to_keep.append(rev)
            
    logger.info(f"Identified {len(to_delete)} ambiguous reviews to discard, {len(to_keep)} are good quality.")
    
    # Delete the ambiguous ones permanently
    for rev in to_delete:
        db.delete(rev)
    db.commit()
    logger.info("Successfully deleted ambiguous reviews from database.")

    # 2. Take only 800 for pipeline processing
    sample_size = min(800, len(to_keep))
    selected_for_pipeline = random.sample(to_keep, sample_size)
    logger.info(f"Selected {sample_size} high-quality YouTube reviews for pipeline processing.")
    
    # 3. Process them
    logger.info("Starting pipeline components...")
    
    cleaner = DataCleaner()
    clean_reviews = cleaner.clean(selected_for_pipeline)
    
    classifier = RelevanceClassifier()
    # Batch classification (this runs locally and takes a bit of time)
    relevant_reviews = classifier.classify_batch(clean_reviews)
    
    logger.info(f"{len(relevant_reviews)} out of {sample_size} passed the relevance threshold.")
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY is not set! Aborting extraction.")
        return
        
    extractor = FeatureExtractor(api_key=api_key)
    extracted_data = extractor.extract_generator(relevant_reviews)
    
    saved_count = 0
    for item in extracted_data:
        llm = item["llm_features"]
        if not llm:
            continue
            
        fm_id = None
        if llm.get("failure_mode"):
            fm = get_or_create(db, FailureMode, name=llm["failure_mode"])
            fm_id = fm.id
            
        arch_id = None
        if llm.get("retrieval_archetype"):
            arch = get_or_create(db, RetrievalArchetype, name=llm["retrieval_archetype"])
            arch_id = arch.id
            
        sr = StructuredReview(
            id=uuid.uuid4(),
            raw_review_id=item["raw_review_id"],
            cleaned_text=item["cleaned_text"],
            source=item["source"],
            source_url=item["source_url"],
            photo_category=llm.get("photo_category"),
            outcome=llm.get("outcome"),
            user_effort_signal=llm.get("user_effort_signal"),
            retrieval_archetype_id=arch_id,
            failure_mode_id=fm_id,
            is_retrieval_relevant=True
        )
        db.add(sr)
        db.flush()
        
        cues = llm.get("memory_cues", [])
        if isinstance(cues, list):
            for cue in cues:
                mc = MemoryCue(
                    id=uuid.uuid4(),
                    structured_review_id=sr.id,
                    cue_type="remembered",
                    cue_value=str(cue)
                )
                db.add(mc)
                
        db.commit()
        saved_count += 1
        
    logger.info(f"Pipeline complete! Successfully processed and saved {saved_count} structured reviews.")
    db.close()

if __name__ == "__main__":
    start = time.time()
    main()
    print(f"Elapsed: {time.time() - start:.2f}s")
