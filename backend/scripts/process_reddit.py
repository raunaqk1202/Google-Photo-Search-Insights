import sys
import os
import logging
from dotenv import load_dotenv
import time

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
load_dotenv(os.path.join(os.path.dirname(backend_dir), ".env"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("process_reddit")

from api.database import SessionLocal
from api.models.review import RawReview, StructuredReview, FailureMode, RetrievalArchetype, MemoryCue
from pipeline.cleaner import DataCleaner
from pipeline.classifier import RelevanceClassifier
from pipeline.extractor import FeatureExtractor
import uuid

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
    
    # Fetch all unprocessed Reddit reviews
    logger.info("Fetching unprocessed Reddit reviews...")
    unprocessed = db.query(RawReview).outerjoin(
        StructuredReview
    ).filter(
        StructuredReview.id == None,
        RawReview.source == 'reddit'
    ).all()
    
    logger.info(f"Found {len(unprocessed)} unprocessed Reddit reviews.")
    if not unprocessed:
        return

    # Process them
    logger.info("Starting pipeline components...")
    
    cleaner = DataCleaner()
    clean_reviews = cleaner.clean(unprocessed)
    
    classifier = RelevanceClassifier()
    # Batch classification (this runs locally)
    relevant_reviews = classifier.classify_batch(clean_reviews)
    
    logger.info(f"{len(relevant_reviews)} out of {len(unprocessed)} passed the relevance threshold.")
    
    if not relevant_reviews:
        logger.info("No relevant reviews to extract. Exiting.")
        return
        
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
