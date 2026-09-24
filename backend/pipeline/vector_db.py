import os
import logging
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(os.path.dirname(backend_dir), ".env"))

logger = logging.getLogger(__name__)

class VectorDB:
    def __init__(self):
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_data")
        logger.info(f"Connecting to ChromaDB at {db_path}")
        
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(allow_reset=True)
        )
        
        # Architecture 9.1 specifies collection name `discovery_reviews`
        self.collection_name = "discovery_reviews"
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        try:
            # cosine similarity is explicitly specified in the architecture
            return self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            logger.error(f"Failed to connect or create ChromaDB collection: {e}")
            raise

    def get_collection(self):
        return self.collection

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db = VectorDB()
    print(f"Collection initialized: {db.get_collection().name}")
    print(f"Current count: {db.get_collection().count()}")
