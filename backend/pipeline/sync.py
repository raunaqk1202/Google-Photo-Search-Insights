import os
import sys
import logging
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
load_dotenv(os.path.join(os.path.dirname(backend_dir), ".env"))

from api.database import SessionLocal
from api.models.review import StructuredReview, FailureMode, RetrievalArchetype
from pipeline.vector_db import VectorDB
from pipeline.embedder import Embedder

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sync")

def sync_to_chroma():
    logger.info("Initializing Sync to ChromaDB...")
    db = SessionLocal()
    
    # 1. Fetch relevant structured reviews
    logger.info("Fetching structured reviews from Postgres...")
    reviews = db.query(StructuredReview).filter(StructuredReview.is_retrieval_relevant == True).all()
    
    if not reviews:
        logger.info("No reviews found to sync.")
        db.close()
        return
        
    logger.info(f"Found {len(reviews)} reviews to embed and sync.")
    
    # 2. Initialize Chroma and Embedder
    vector_db = VectorDB()
    collection = vector_db.get_collection()
    embedder = Embedder()
    
    # 3. Process and batch insert
    batch_ids = []
    batch_embeddings = []
    batch_metadatas = []
    batch_documents = []
    
    # Pre-fetch lookup tables for performance
    failure_modes = {fm.id: fm.name for fm in db.query(FailureMode).all()}
    archetypes = {arch.id: arch.name for arch in db.query(RetrievalArchetype).all()}
    
    total_chunks = 0
    
    for i, review in enumerate(reviews):
        # Prepare metadata
        metadata = {
            "source": str(review.source),
            "photo_category": str(review.photo_category) if review.photo_category else "unknown",
            "outcome": str(review.outcome) if review.outcome else "unknown",
        }
        
        if review.failure_mode_id:
            metadata["failure_mode"] = failure_modes.get(review.failure_mode_id, "unknown")
            
        if review.retrieval_archetype_id:
            metadata["retrieval_archetype"] = archetypes.get(review.retrieval_archetype_id, "unknown")
            
        # Extract and chunk
        chunks = embedder.process_review(
            review_id=str(review.id),
            text=review.cleaned_text,
            metadata=metadata
        )
        
        for chunk in chunks:
            batch_ids.append(chunk["id"])
            batch_embeddings.append(chunk["embedding"])
            batch_metadatas.append(chunk["metadata"])
            batch_documents.append(chunk["text"])
            total_chunks += 1
            
        # Batch insert into ChromaDB every 100 reviews to avoid massive memory spikes
        if (i + 1) % 100 == 0 or (i + 1) == len(reviews):
            logger.info(f"  Upserting batch... ({i+1}/{len(reviews)} reviews, {len(batch_ids)} chunks)")
            if batch_ids:
                collection.upsert(
                    ids=batch_ids,
                    embeddings=batch_embeddings,
                    metadatas=batch_metadatas,
                    documents=batch_documents
                )
            
            # Reset batch
            batch_ids = []
            batch_embeddings = []
            batch_metadatas = []
            batch_documents = []

    logger.info(f"Sync complete! Inserted {total_chunks} chunks into ChromaDB.")
    db.close()

if __name__ == "__main__":
    sync_to_chroma()
