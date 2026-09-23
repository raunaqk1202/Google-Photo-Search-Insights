import os
import json
import logging
import spacy
from typing import Dict, Any

from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Try loading spacy model; if not downloaded, it will fail gracefully or download later
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("Spacy model 'en_core_web_sm' not found. NLP features will be skipped.")
    nlp = None

PROMPT_TEMPLATE = """You are a UX research data analyst. Given the following user review about Google Photos, 
extract a structured JSON object with these fields:

- memory_cues: list of things the user remembers about the photo (e.g., "trip to Goa", "red dress", "restaurant")
- forgotten_attributes: list of things the user has forgotten (e.g., "exact date", "location name", "album")
- search_behavior: list of actions the user took to find the photo (e.g., "searched by keyword", "scrolled manually", "asked friend")
- failure_mode: the primary reason retrieval failed (one of: memory_failure, query_translation_failure, vocabulary_mismatch, metadata_dependency, context_loss, temporal_uncertainty, location_uncertainty, person_ambiguity, search_strategy_failure, result_ranking_failure, retrieval_confidence_failure, other)
- outcome: one of: retrieved, partial, abandoned, unknown
- photo_category: type of photo (e.g., travel, medical, receipt, screenshot, food, event, document, personal_memory, other)
- retrieval_archetype: one of: event_based_memory, story_based_memory, visual_memory_retrieval, approximate_time_retrieval, relationship_based_retrieval, object_based_retrieval, text_memory_retrieval, other
- user_effort_signal: brief description of frustration or effort indicators
- user_pain_score: rate the user's pain/frustration from 1.0 to 5.0 (float) based on the review.
- business_impact_score: rate the potential business impact of fixing this issue from 1.0 to 5.0 (float).
- evidence_strength_score: rate the clarity and strength of the evidence in this review from 1.0 to 5.0 (float).

If a field cannot be determined from the review, set it to null.

Review: "{review_text}"

Respond with valid JSON only. Do not include markdown formatting or explanations."""

class FeatureExtractor:
    def __init__(self, api_key: str):
        from api.config import get_settings
        settings = get_settings()
        self.client = Groq(api_key=api_key)
        self.model = settings.groq_model
        
    def extract_nlp_features(self, text: str) -> Dict[str, Any]:
        """Extracts basic NER features using SpaCy."""
        if not nlp:
            return {}
            
        doc = nlp(text)
        entities = {}
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            if ent.text not in entities[ent.label_]:
                entities[ent.label_].append(ent.text)
                
        return {"entities": entities}

    # Robust rate-limit handling with exponential backoff (wait 2^x * 1 seconds between retries, up to 10 seconds max)
    @retry(
        stop=stop_after_attempt(7), 
        wait=wait_exponential(multiplier=1, min=2, max=60),
        reraise=True
    )
    def extract_llm_features(self, text: str) -> Dict[str, Any]:
        """Calls Groq API to extract UX research fields with robust retries for rate limits."""
        prompt = PROMPT_TEMPLATE.format(review_text=text)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        
        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from LLM: {content}")
            return {}

    def extract_generator(self, raw_reviews: list):
        """
        Takes a list of RawReview models.
        Yields dicts with extraction results one by one.
        """
        logger.info(f"Starting extraction for {len(raw_reviews)} reviews (with rate limit handling)...")
        
        for i, rev in enumerate(raw_reviews):
            if i > 0 and i % 50 == 0:
                logger.info(f"  Extracted {i}/{len(raw_reviews)}...")
                
            text = rev.original_text
            nlp_feats = self.extract_nlp_features(text)
            
            try:
                llm_feats = self.extract_llm_features(text)
            except Exception as e:
                logger.error(f"Failed LLM extraction for review {rev.id} after retries: {e}")
                llm_feats = {}
                
            yield {
                "raw_review_id": rev.id,
                "source": rev.source,
                "source_url": rev.source_url,
                "cleaned_text": text,
                "nlp_features": nlp_feats,
                "llm_features": llm_feats
            }
            
        logger.info(f"Extraction complete for {len(raw_reviews)} reviews.")
