import logging
from typing import List, Dict, Any

from pipeline.vector_db import VectorDB
from pipeline.embedder import Embedder
from pipeline.reranker import Reranker

logger = logging.getLogger(__name__)

class Retriever:
    def __init__(self):
        logger.info("Initializing Retriever services...")
        self.vector_db = VectorDB()
        self.collection = self.vector_db.get_collection()
        
        self.embedder = Embedder()
        self.reranker = Reranker()

    def search(self, query: str, top_k: int = 15, filters: dict = None) -> List[Dict[str, Any]]:
        """
        End-to-end semantic search pipeline:
        1. Embed the query.
        2. Retrieve top-50 from ChromaDB.
        3. Rerank the top-50 down to top_k using a Cross-Encoder.
        """
        logger.info(f"Executing search for query: '{query}'")
        
        # 1. Embed Query
        query_embedding = self.embedder.embed_text(query)
        
        # 2. Vector Search (Top 50)
        # ChromaDB where filter e.g. {"source": "reddit"}
        where_clause = filters if filters else None
        
        vector_results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=50,
            where=where_clause
        )
        
        if not vector_results["ids"] or not vector_results["ids"][0]:
            logger.info("No results found in ChromaDB.")
            return []
            
        # Parse ChromaDB output format into a list of dicts for the reranker
        documents = []
        for i in range(len(vector_results["ids"][0])):
            documents.append({
                "id": vector_results["ids"][0][i],
                "text": vector_results["documents"][0][i],
                "metadata": vector_results["metadatas"][0][i],
                "vector_distance": vector_results["distances"][0][i] if vector_results["distances"] else None
            })
            
        logger.info(f"Retrieved {len(documents)} candidates from vector database. Reranking...")
        
        # 3. Rerank (Top K)
        final_results = self.reranker.rerank(query=query, documents=documents, top_k=top_k)
        
        logger.info(f"Returning top {len(final_results)} reranked results.")
        return final_results
