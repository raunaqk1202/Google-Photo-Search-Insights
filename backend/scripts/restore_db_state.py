import sys
import os

# Add backend directory to path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.database import SessionLocal
from api.models.review import StructuredReview, RawReview

def restore_database():
    db = SessionLocal()
    
    # 1. Delete all mock StructuredReviews
    mock_structs = db.query(StructuredReview).filter(
        StructuredReview.user_effort_signal.in_(['User got frustrated and gave up', 'Found it easily'])
    ).all()
    
    print(f"Deleting {len(mock_structs)} mock structured reviews...")
    for ms in mock_structs:
        db.delete(ms)
    db.commit()
    
    # 2. Delete all 'unprocessed' RawReviews
    unprocessed_raws = db.query(RawReview).filter(
        RawReview.classification_status == 'unprocessed'
    ).all()
    
    print(f"Deleting {len(unprocessed_raws)} unprocessed raw reviews...")
    for ur in unprocessed_raws:
        db.delete(ur)
    db.commit()

    # 3. Verify counts
    final_raw = db.query(RawReview).count()
    final_struct = db.query(StructuredReview).count()
    
    print(f"Database successfully restored!")
    print(f"Final RawReview count: {final_raw}")
    print(f"Final StructuredReview count: {final_struct}")
    
    db.close()

if __name__ == "__main__":
    restore_database()
