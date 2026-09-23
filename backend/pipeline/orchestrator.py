import os
import sys
import uuid
import logging
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
load_dotenv(os.path.join(os.path.dirname(backend_dir), ".env"))

from api.database import SessionLocal
from api.models.review import RawReview, StructuredReview, MemoryCue, FailureMode, RetrievalArchetype
from pipeline.cleaner import DataCleaner
from pipeline.classifier import RelevanceClassifier
from pipeline.extractor import FeatureExtractor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("orchestrator")

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

def run_pipeline(reprocess=False, classify_only=False):
    logger.info(f"Starting Data Processing Pipeline... (reprocess={reprocess}, classify_only={classify_only})")
    db = SessionLocal()
    
    if reprocess:
        logger.info("Reprocess flag set. Resetting status and wiping existing structured reviews...")
        db.query(MemoryCue).delete()
        db.query(StructuredReview).delete()
        db.query(RawReview).update({RawReview.classification_status: "unprocessed"})
        db.commit()
    
    # --- PHASE 1: CLASSIFICATION ---
    logger.info("Fetching unprocessed raw reviews for classification...")
    unprocessed_reviews = db.query(RawReview).filter(RawReview.classification_status == 'unprocessed').all()
    
    if unprocessed_reviews:
        logger.info(f"Found {len(unprocessed_reviews)} unprocessed reviews. Starting Phase 1...")
        
        # 1. Cleaner (Deduplication + Spam)
        cleaner = DataCleaner()
        clean_results = cleaner.clean(unprocessed_reviews)
        
        clean_reviews = []
        for rev, status in clean_results:
            if status == "clean":
                clean_reviews.append(rev)
            else:
                rev.classification_status = status
        db.commit()  # Commit cleaner statuses
        
        # 2. Classifier (Relevance)
        if clean_reviews:
            classifier = RelevanceClassifier()
            class_results = classifier.classify_batch(clean_reviews)
            
            for rev, status in class_results:
                rev.classification_status = status
            db.commit()  # Commit classifier statuses
    else:
        logger.info("No unprocessed reviews found. Phase 1 skipped.")

    if classify_only:
        logger.info("Classify-only flag is set. Exiting before extraction.")
        db.close()
        return

    # --- PHASE 2: EXTRACTION ---
    logger.info("Fetching relevant reviews for deep extraction...")
    relevant_reviews = db.query(RawReview).outerjoin(StructuredReview).filter(
        RawReview.classification_status == 'relevant',
        StructuredReview.id == None
    ).all()
    
    logger.info(f"Found {len(relevant_reviews)} unextracted relevant reviews.")
    
    if not relevant_reviews:
        logger.info("No new relevant reviews to extract. Exiting.")
        db.close()
        return

    # 3. Extractor (NER + LLM)
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY is not set. Cannot run extraction.")
        db.close()
        return
        
    extractor = FeatureExtractor(api_key=api_key)
    extracted_data = extractor.extract_generator(relevant_reviews)
    
    # 4. Persist to DB
    logger.info("Saving structured data to database one-by-one...")
    for item in extracted_data:
        llm = item["llm_features"]
        if not llm:
            continue
            
        # Resolve foreign keys
        fm_id = None
        if llm.get("failure_mode"):
            fm = get_or_create(db, FailureMode, name=llm["failure_mode"])
            fm_id = fm.id
            
        arch_id = None
        if llm.get("retrieval_archetype"):
            arch = get_or_create(db, RetrievalArchetype, name=llm["retrieval_archetype"])
            arch_id = arch.id
            
        # Create StructuredReview
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
            is_retrieval_relevant=True,
            user_pain_score=llm.get("user_pain_score"),
            business_impact_score=llm.get("business_impact_score"),
            evidence_strength_score=llm.get("evidence_strength_score")
        )
        db.add(sr)
        db.flush()
        
        # Create MemoryCues
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
                
        forgotten = llm.get("forgotten_attributes", [])
        if isinstance(forgotten, list):
            for cue in forgotten:
                mc = MemoryCue(
                    id=uuid.uuid4(),
                    structured_review_id=sr.id,
                    cue_type="forgotten",
                    cue_value=str(cue)
                )
                db.add(mc)
                
        # Commit ONE BY ONE so the frontend dashboard updates live!
        db.commit()
        
    logger.info("Pipeline execution complete! Data successfully saved.")
    db.close()

if __name__ == "__main__":
    import sys
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--reprocess", action="store_true")
    parser.add_argument("--classify-only", action="store_true")
    args = parser.parse_args()
    run_pipeline(reprocess=args.reprocess, classify_only=args.classify_only)
