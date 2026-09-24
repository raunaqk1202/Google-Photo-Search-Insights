import os
import logging
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        class RecursiveCharacterTextSplitter:
            def __init__(self, chunk_size=2000, chunk_overlap=200, separators=None):
                self.chunk_size = chunk_size
                self.chunk_overlap = chunk_overlap

            def split_text(self, text: str) -> List[str]:
                if not text:
                    return []
                chunks = []
                start = 0
                while start < len(text):
                    end = start + self.chunk_size
                    chunks.append(text[start:end])
                    start += self.chunk_size - self.chunk_overlap
                return chunks


logger = logging.getLogger(__name__)

class Embedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        # Splitter config from architecture (512 tokens max, 50 token overlap)
        # We approximate tokens with characters (1 token ~= 4 chars)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000, 
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", " ", ""]
        )

    def embed_text(self, text: str) -> List[float]:
        """Generate an embedding for a single string."""
        embedding = self.model.encode(text)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of strings."""
        embeddings = self.model.encode(texts)
        return embeddings.tolist()

    def process_review(self, review_id: str, text: str, metadata: dict) -> List[Dict[str, Any]]:
        """
        Chunks a review and returns a list of dictionaries ready for ChromaDB.
        Each dict has: id, text, embedding, metadata
        """
        chunks = self.text_splitter.split_text(text)
        
        results = []
        # Pre-embed the chunks in a batch for efficiency
        embeddings = self.embed_batch(chunks)
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_index"] = i
            chunk_metadata["parent_id"] = review_id
            
            results.append({
                "id": f"{review_id}-chunk-{i}",
                "text": chunk,
                "embedding": embedding,
                "metadata": chunk_metadata
            })
            
        return results
