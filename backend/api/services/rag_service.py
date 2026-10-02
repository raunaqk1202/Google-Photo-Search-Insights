"""RAG service — orchestrates the retrieval-augmented generation pipeline."""

import os
import json
import time
import hashlib
import logging
from typing import AsyncGenerator, Optional
from collections import OrderedDict
from groq import Groq

from pipeline.retriever import Retriever
from api.services.prompt_engine import PromptEngine

logger = logging.getLogger(__name__)


class ResponseCache:
    """Simple in-memory TTL cache for RAG responses to avoid burning Groq tokens
    on repeated or similar queries. Keyed by (query + filters) hash."""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self._cache: OrderedDict[str, dict] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl_seconds

    @staticmethod
    def _make_key(query: str, filters: Optional[dict]) -> str:
        """Deterministic cache key from query + filters."""
        raw = f"{query.strip().lower()}|{json.dumps(filters, sort_keys=True) if filters else ''}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, query: str, filters: Optional[dict]) -> Optional[dict]:
        key = self._make_key(query, filters)
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["ts"] < self._ttl:
                self._cache.move_to_end(key)
                logger.info(f"Cache HIT for query '{query[:50]}…' — saving Groq tokens.")
                return entry
            else:
                del self._cache[key]
        return None

    def put(self, query: str, filters: Optional[dict], full_text: str, citations: list):
        key = self._make_key(query, filters)
        if len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)  # evict oldest
        self._cache[key] = {
            "ts": time.time(),
            "full_text": full_text,
            "citations": citations,
        }


# Module-level singleton so the cache persists across requests within a process
_response_cache = ResponseCache(max_size=100, ttl_seconds=3600)


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
        self.cache = _response_cache
        logger.info("RAG Service initialized successfully.")

    async def query_stream(self, query: str, filters: Optional[dict] = None, session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        Process a conversational query through the RAG pipeline and stream back tokens.
        At the end of the stream, emits a custom event containing the structured citations.

        Optimizations applied:
        - In-memory TTL cache to avoid re-calling Groq for repeated queries
        - Reduced max_tokens (600) to stay within free-tier TPM/TPD budgets
        - Exponential backoff for rate-limit retries
        """
        try:
            logger.info(f"RAG Service processing query: '{query}'")

            # ── 0. Check cache first — avoids Groq call entirely ──
            cached = self.cache.get(query, filters)
            if cached:
                yield json.dumps({"type": "token", "content": cached["full_text"]}) + "\n"
                yield json.dumps({"type": "citations", "citations": cached["citations"]}) + "\n"
                return

            # ── 1. Check VectorDB health ──
            doc_count = self.retriever.collection.count()
            logger.info(f"VectorDB document count: {doc_count}")

            if doc_count == 0:
                yield json.dumps({"type": "token", "content": "The vector database is still syncing. Please wait a minute and try again."}) + "\n"
                return

            # ── 2. Retrieve & Rerank (Top 5) ──
            retrieved_docs = self.retriever.search(query=query, top_k=5, filters=filters)

            if not retrieved_docs:
                yield json.dumps({"type": "token", "content": "I couldn't find any relevant reviews to answer your question. The vector database may still be syncing — please try again in a minute."}) + "\n"
                return

            logger.info(f"Retrieved {len(retrieved_docs)} documents for query.")

            # ── 3. Format Evidence ──
            evidence_str, citations = self.prompt_engine.format_evidence(retrieved_docs)

            # ── 4. Build Chat Messages ──
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

            # ── 5. Stream from Groq (with exponential backoff for rate limits) ──
            from api.config import get_settings
            settings = get_settings()

            model = settings.groq_model
            max_tokens = min(settings.groq_max_tokens, 600)  # Cap output to conserve tokens
            logger.info(f"Calling Groq API (model={model}, max_tokens={max_tokens}, evidence_docs={len(retrieved_docs)})...")

            max_retries = 3
            full_response_text = ""

            for attempt in range(max_retries):
                try:
                    stream = self.client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=settings.groq_temperature,
                        max_tokens=max_tokens,
                        stream=True
                    )

                    # Yield tokens as they arrive and accumulate for cache
                    token_count = 0
                    for chunk in stream:
                        if chunk.choices and chunk.choices[0].delta.content:
                            token_count += 1
                            content = chunk.choices[0].delta.content
                            full_response_text += content
                            yield json.dumps({"type": "token", "content": content}) + "\n"

                    logger.info(f"Stream complete. Yielded {token_count} tokens.")
                    break  # Success — exit retry loop

                except Exception as groq_err:
                    err_str = str(groq_err)
                    if "rate_limit" in err_str.lower() and attempt < max_retries - 1:
                        # Exponential backoff: 30s, 60s, 120s
                        wait_time = 30 * (2 ** attempt)
                        logger.warning(f"Rate limited by Groq. Waiting {wait_time}s before retry (attempt {attempt + 1}/{max_retries})...")
                        yield json.dumps({"type": "token", "content": f"⏳ Rate limited — waiting {wait_time}s before retrying..."}) + "\n"
                        time.sleep(wait_time)
                        full_response_text = ""  # Reset accumulated text on retry
                    else:
                        raise groq_err

            # ── 6. Cache the response for future identical queries ──
            if full_response_text:
                self.cache.put(query, filters, full_response_text, citations)
                logger.info(f"Cached response for query '{query[:50]}…' ({len(full_response_text)} chars).")

            # ── 7. Append citations at the end of the stream ──
            yield json.dumps({"type": "citations", "citations": citations}) + "\n"

        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}", exc_info=True)
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"
