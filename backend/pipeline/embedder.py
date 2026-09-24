import os
import logging
from typing import List, Dict, Any
from chromadb.utils import embedding_functions
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter


logger = logging.getLogger(__name__)

class Embedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        logger.info("Loading lightweight ONNX embedding model via ChromaDB to save RAM")
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        
        # Splitter config from architecture (512 tokens max, 50 token overlap)
        # We approximate tokens with characters (1 token ~= 4 chars)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000, 
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", " ", ""]
        )

    def embed_text(self, text: str) -> List[float]:
        """Generate an embedding for a single string."""
        return self.ef([text])[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of strings."""
        return self.ef(texts)

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
