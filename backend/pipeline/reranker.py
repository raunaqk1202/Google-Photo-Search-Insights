import logging
from typing import List, Dict, Any
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

class Reranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        logger.info(f"Loading cross-encoder model: {model_name}")
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 15) -> List[Dict[str, Any]]:
        """
        Re-ranks a list of documents using a cross-encoder model.
        Expects a list of dicts, where each dict has at least a 'text' field.
        Returns the top_k most relevant documents.
        """
        if not documents:
            return []
            
        # CrossEncoder expects pairs of (query, document)
        pairs = [[query, doc["text"]] for doc in documents]
        
        # Predict scores
        scores = self.model.predict(pairs)
        
        # Add scores to documents
        for doc, score in zip(documents, scores):
            doc["cross_encoder_score"] = float(score)
            
        # Sort by score descending
        ranked_documents = sorted(documents, key=lambda x: x["cross_encoder_score"], reverse=True)
        
        # Return top K
        return ranked_documents[:top_k]
