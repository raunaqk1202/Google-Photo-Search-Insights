"""
Seed script — populates lookup tables with initial data.

Run with: python scripts/seed_db.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from api.database import SessionLocal  # noqa: E402
from api.models.review import FailureMode, RetrievalArchetype  # noqa: E402


FAILURE_MODES = [
    ("memory_failure", "The user cannot remember the information required to formulate an effective search. This often happens with older photos where specific details have faded over time."),
    ("query_translation_failure", "The user remembers the photo conceptually but cannot translate that memory into searchable language. They struggle to find the exact keywords that the system expects."),
    ("vocabulary_mismatch", "The user's wording differs from the terms understood/indexed by the system. This leads to frustrating empty result pages despite the photo existing."),
    ("metadata_dependency", "Successful retrieval depends on information the user no longer remembers. Metadata like exact dates or locations are easily forgotten by users."),
    ("context_loss", "The user remembers an event or story rather than searchable attributes of the image. The emotional context doesn't map well to objective image tags."),
    ("multimodal_mismatch", "The user remembers visual characteristics that are difficult to express through text. Colors, shapes, and layouts are notoriously hard to describe accurately."),
    ("temporal_uncertainty", "The user remembers 'around last summer' rather than an exact date. This fuzzy timeline prevents them from using strict date filters effectively."),
    ("location_uncertainty", "The user remembers a trip/event but not the precise location. They might know the general region without recalling the specific city or landmark."),
    ("person_ambiguity", "The user remembers who was involved but cannot identify the person in a way the system can use. Sometimes faces are obscured, or the system hasn't tagged them correctly."),
    ("search_strategy_failure", "The user does not know which search mechanism or filter to use. They might default to a simple keyword search when a combination of filters would be more effective."),
    ("result_ranking_failure", "Relevant photos may exist but are difficult to recognize among results. The sheer volume of matches overwhelms the user's ability to spot their target."),
    ("retrieval_confidence_failure", "Users are unsure whether the photo exists and therefore do not know whether to continue searching. This doubt leads them to abandon the search prematurely."),
    ("other", "Failure mode not covered by the predefined categories. These represent edge cases or novel ways users attempt to find their media."),
]

RETRIEVAL_ARCHETYPES = [
    ("event_based_memory", "I remember the trip/event but not when the image was taken."),
    ("story_based_memory", "I remember what happened around the photo rather than the photo itself."),
    ("visual_memory_retrieval", "I remember what the image looked like but cannot describe it precisely."),
    ("approximate_time_retrieval", "I know it was sometime last year/summer/weekend."),
    ("relationship_based_retrieval", "I remember being with someone but cannot identify the photo through conventional search."),
    ("object_based_retrieval", "I remember taking a picture of a particular object/product/document."),
    ("text_memory_retrieval", "I remember seeing some text but not the exact wording."),
    ("other", "Retrieval archetype not covered by the predefined categories."),
]


def seed():
    """Insert initial lookup data into failure_mode and retrieval_archetype tables."""
    db = SessionLocal()
    try:
        # Seed failure modes
        for name, description in FAILURE_MODES:
            existing = db.query(FailureMode).filter_by(name=name).first()
            if not existing:
                db.add(FailureMode(name=name, description=description))
                print(f"  + FailureMode: {name}")
            else:
                existing.description = description
                print(f"  = FailureMode: {name} (updated)")

        # Seed retrieval archetypes
        for name, description in RETRIEVAL_ARCHETYPES:
            existing = db.query(RetrievalArchetype).filter_by(name=name).first()
            if not existing:
                db.add(RetrievalArchetype(name=name, description=description))
                print(f"  + RetrievalArchetype: {name}")
            else:
                existing.description = description
                print(f"  = RetrievalArchetype: {name} (updated)")

        db.commit()
        print("\n✅ Seed data inserted successfully.")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 Seeding database with lookup table data...\n")
    seed()
