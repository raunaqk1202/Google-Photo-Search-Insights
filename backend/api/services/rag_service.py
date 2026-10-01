"""RAG service — orchestrates the retrieval-augmented generation pipeline."""

import os
import json
import logging
from typing import AsyncGenerator, Optional
from groq import Groq

from pipeline.retriever import Retriever
from api.services.prompt_engine import PromptEngine

logger = logging.getLogger(__name__)

class RAGService:
    """Orchestrates: embed query → vector search → rerank → prompt → Groq → response."""

    def __init__(self):
        logger.info("Initializing RAG Service...")
        self.retriever = Retriever()
        self.prompt_engine = PromptEngine()
        
        groq_api_key = os.environ.get("GROQ_API_KEY")
        if not groq_api_key:
            logger.warning("GROQ_API_KEY not found in environment!")
            
        self.client = Groq(api_key=groq_api_key)
        logger.info("RAG Service initialized successfully.")

    async def query_stream(self, query: str, filters: Optional[dict] = None, session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        Process a conversational query through the RAG pipeline and stream back tokens.
        At the end of the stream, emits a custom event containing the structured citations.
        """
        try:
            logger.info(f"RAG Service processing query: '{query}'")
            
            # 1. Check VectorDB health
            doc_count = self.retriever.collection.count()
            logger.info(f"VectorDB document count: {doc_count}")
            
            if doc_count == 0:
                yield json.dumps({"type": "token", "content": "The vector database is still syncing. Please wait a minute and try again."}) + "\n"
                return
            
            # 2. Retrieve & Rerank (Top 15)
            retrieved_docs = self.retriever.search(query=query, top_k=15, filters=filters)
            
            if not retrieved_docs:
                yield json.dumps({"type": "token", "content": "I couldn't find any relevant reviews to answer your question. The vector database may still be syncing — please try again in a minute."}) + "\n"
                return
            
            logger.info(f"Retrieved {len(retrieved_docs)} documents for query.")
            
            # 3. Format Evidence
            evidence_str, citations = self.prompt_engine.format_evidence(retrieved_docs)
            
            # 4. Build Chat Messages
            messages = [
                {
                    "role": "system",
                    "content": self.prompt_engine.get_system_prompt()
                },
                {
                    "role": "user",
                    "content": f"Here is the evidence:\n\n{evidence_str}\n\nBased on this evidence, please answer the following query:\n{query}"
                }
            ]
            
            # 5. Stream from Groq
            from api.config import get_settings
            settings = get_settings()
            
            # Use a reliable, fast model
            model = settings.groq_model
            logger.info(f"Calling Groq API (model={model}, evidence_docs={len(retrieved_docs)})...")
            
            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=settings.groq_temperature,
                max_tokens=settings.groq_max_tokens,
                stream=True
            )
            
            # Yield tokens as they arrive
            token_count = 0
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    token_count += 1
                    yield json.dumps({"type": "token", "content": chunk.choices[0].delta.content}) + "\n"
            
            logger.info(f"Stream complete. Yielded {token_count} tokens.")
            
            # 6. Append citations at the end of the stream
            yield json.dumps({"type": "citations", "citations": citations}) + "\n"
            
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}", exc_info=True)
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"
