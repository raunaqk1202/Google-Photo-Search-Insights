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
        # Assume retriever is initialized once or per request depending on usage
        self.retriever = Retriever()
        self.prompt_engine = PromptEngine()
        
        groq_api_key = os.environ.get("GROQ_API_KEY")
        if not groq_api_key:
            logger.warning("GROQ_API_KEY not found in environment!")
            
        self.client = Groq(api_key=groq_api_key)

    async def query_stream(self, query: str, filters: Optional[dict] = None, session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        Process a conversational query through the RAG pipeline and stream back tokens.
        At the end of the stream, emits a custom event containing the structured citations.
        """
        try:
            logger.info(f"RAG Service processing query: '{query}'")
            
            # 1. Retrieve & Rerank (Top 15)
            # This is currently synchronous. In a fully async system, Retriever would be async.
            retrieved_docs = self.retriever.search(query=query, top_k=15, filters=filters)
            
            if not retrieved_docs:
                yield "I couldn't find any relevant reviews to answer your question."
                return
            
            # 2. Format Evidence
            evidence_str, citations = self.prompt_engine.format_evidence(retrieved_docs)
            
            # 3. Build Chat Messages
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
            
            # 4. Stream from Groq
            from api.config import get_settings
            settings = get_settings()
            logger.info(f"Calling Groq API ({settings.groq_model})...")
            stream = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=messages,
                temperature=settings.groq_temperature,
                max_tokens=settings.groq_max_tokens,
                stream=True
            )
            
            # Yield tokens as they arrive
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    # SSE data format
                    # yielding just the text fragment. SSE format handled by FastAPI or we can format it here.
                    # We will yield raw text and let the router wrap it in SSE.
                    yield json.dumps({"type": "token", "content": chunk.choices[0].delta.content}) + "\n"
            
            # 5. Append citations at the end of the stream
            logger.info("Stream complete, appending citations.")
            yield json.dumps({"type": "citations", "citations": citations}) + "\n"
            
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}")
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"
