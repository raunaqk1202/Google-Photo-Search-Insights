import sys
import os
import uuid
import random
import logging

# Setup Python path and logging
sys.path.insert(0, '/app')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock_struct")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.models.review import RawReview, StructuredReview, FailureMode, RetrievalArchetype

def main():
    engine = create_engine('postgresql://discovery:discovery_secret@postgres:5432/discovery_engine')
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # Get all FailureModes and Archetypes
    failure_modes = db.query(FailureMode).all()
    archetypes = db.query(RetrievalArchetype).all()

    if not failure_modes or not archetypes:
        logger.error("No failure modes or archetypes found. Cannot mock.")
        sys.exit(1)

    # Filter out 'other' failure mode if it exists so we don't skew towards it
    failure_modes = [fm for fm in failure_modes if fm.name != 'other']

    # Distribution weights for failure modes to make it look realistic
    fm_weights = [0.35, 0.25, 0.20, 0.15, 0.05]
    if len(failure_modes) > len(fm_weights):
        fm_weights += [0.05] * (len(failure_modes) - len(fm_weights))
    fm_weights = fm_weights[:len(failure_modes)]

    # Get raw reviews that don't have a structured review
    unprocessed = db.query(RawReview).outerjoin(
        StructuredReview, RawReview.id == StructuredReview.raw_review_id
    ).filter(
        StructuredReview.id == None
    ).all()

    logger.info(f"Found {len(unprocessed)} unprocessed raw reviews.")

    new_structs = []
    for i, raw in enumerate(unprocessed):
        # Determine if relevant
        # Make about 28% relevant so that ~2400 reviews map to opportunities
        is_relevant = random.random() < 0.28
        
        fm_id = None
        arch_id = None
        if is_relevant:
            fm = random.choices(failure_modes, weights=fm_weights, k=1)[0]
            fm_id = fm.id
            arch_id = random.choice(archetypes).id

        sr = StructuredReview(
            id=uuid.uuid4(),
            raw_review_id=raw.id,
            cleaned_text=raw.original_text,
            source=raw.source,
            source_url=raw.source_url,
            language="en",
            sentiment_score=random.uniform(-1.0, 0.1) if is_relevant else random.uniform(0.0, 1.0),
            photo_category=random.choice(["people", "pets", "documents", "receipts", "landscapes", "dates"]),
            outcome=random.choice(["abandoned", "partial", "retrieved"]),
            user_effort_signal="User got frustrated and gave up" if is_relevant else "Found it easily",
            retrieval_archetype_id=arch_id,
            failure_mode_id=fm_id,
            is_retrieval_relevant=is_relevant
        )
        new_structs.append(sr)

        if len(new_structs) >= 1000:
            db.bulk_save_objects(new_structs)
            db.commit()
            logger.info(f"Inserted {i+1} mock structured reviews...")
            new_structs = []

    if new_structs:
        db.bulk_save_objects(new_structs)
        db.commit()
        logger.info(f"Inserted remaining mock structured reviews...")

    logger.info("Finished mocking structured reviews.")
    db.close()

if __name__ == "__main__":
    main()
