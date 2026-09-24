import logging
from typing import List, Dict, Any
logger = logging.getLogger(__name__)

class Reranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        logger.info("Reranker disabled to save RAM on Railway deployment.")

    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 15) -> List[Dict[str, Any]]:
        """
        Pass-through function since PyTorch CrossEncoder has been disabled to save memory.
        """
        if not documents:
            return []
            
        return documents[:top_k]
