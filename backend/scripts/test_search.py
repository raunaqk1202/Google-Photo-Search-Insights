import os
import sys
import logging

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from pipeline.vector_db import VectorDB
from pipeline.embedder import Embedder
from pipeline.retriever import Retriever

logging.basicConfig(level=logging.INFO)

def main():
    print("=== Testing Phase 3 Semantic Search Pipeline ===")
    
    # 1. Insert mock data directly into ChromaDB for testing
    vector_db = VectorDB()
    collection = vector_db.get_collection()
    embedder = Embedder()
    
    mock_reviews = [
        {"id": "mock-1", "text": "I can't find the photo of my dog playing in the park from last summer. I searched for 'dog' and 'park' but nothing came up. It's so frustrating.", "metadata": {"source": "reddit", "photo_category": "pets", "outcome": "abandoned"}},
        {"id": "mock-2", "text": "Google photos is great for backing up my receipts, but when I try to find a specific receipt from Walmart, it never shows up.", "metadata": {"source": "playstore", "photo_category": "receipt", "outcome": "partial"}},
        {"id": "mock-3", "text": "Trying to find a picture of my wife in a red dress from our anniversary dinner. The search algorithm sucks.", "metadata": {"source": "appstore", "photo_category": "event", "outcome": "abandoned"}}
    ]
    
    print("\n[1] Embedding mock documents...")
    batch_ids = []
    batch_embeddings = []
    batch_metadatas = []
    batch_documents = []
    
    for review in mock_reviews:
        chunks = embedder.process_review(review["id"], review["text"], review["metadata"])
        for chunk in chunks:
            batch_ids.append(chunk["id"])
            batch_embeddings.append(chunk["embedding"])
            batch_metadatas.append(chunk["metadata"])
            batch_documents.append(chunk["text"])
            
    print(f"Upserting {len(batch_ids)} chunks into ChromaDB...")
    collection.upsert(
        ids=batch_ids,
        embeddings=batch_embeddings,
        metadatas=batch_metadatas,
        documents=batch_documents
    )
    
    # 2. Test Retrieval
    print("\n[2] Testing Semantic Search...")
    retriever = Retriever()
    
    queries = [
        "looking for pictures of my pet",
        "shopping receipt search not working",
        "trying to find my spouse in specific clothing"
    ]
    
    for query in queries:
        print(f"\nQuery: '{query}'")
        results = retriever.search(query, top_k=2)
        
        for i, res in enumerate(results):
            print(f"  Rank {i+1}: Score: {res.get('cross_encoder_score', 'N/A'):.4f} | Source: {res['metadata'].get('source')} | Text: {res['text']}")

if __name__ == "__main__":
    main()
