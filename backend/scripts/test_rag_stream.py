import os
import sys
import asyncio

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from api.services.rag_service import RAGService

async def test_stream():
    print("Initializing RAG Service...")
    rag = RAGService()
    
    print("\n--- Starting Query Stream ---")
    query = "What happens when someone tries to find a photo of a specific receipt?"
    
    async for token in rag.query_stream(query):
        # The token is a JSON string stringified in RAGService, let's print it raw
        sys.stdout.write(token)
        sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(test_stream())
