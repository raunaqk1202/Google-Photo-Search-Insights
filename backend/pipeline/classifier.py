import logging
from transformers import pipeline

logger = logging.getLogger(__name__)

class RelevanceClassifier:
    def __init__(self, threshold=0.6):
        # We use a smaller zero-shot model for speed, but fall back to bart-large if needed
        # cross-encoder/nli-distilroberta-base is fast and good for zero-shot
        logger.info("Loading zero-shot classification model...")
        self.classifier = pipeline(
            "zero-shot-classification", 
            model="cross-encoder/nli-distilroberta-base", 
            device=-1 # CPU
        )
        self.threshold = threshold
        # The hypothesis: "This review is about trying to find or search for an old photo"
        self.candidate_labels = [
            "struggling to find or search for a specific photo",
            "complaining about app crashing or storage limits",
            "general feedback about the app",
        ]

    def is_relevant(self, text):
        """
        Returns True if the text is relevant to our retrieval failure study.
        """
        # Truncate text to avoid max length issues with transformers (usually 512 tokens)
        truncated_text = text[:1500] 
        
        result = self.classifier(
            truncated_text, 
            candidate_labels=self.candidate_labels, 
            multi_label=False
        )
        
        # Check if the top label is our target label
        top_label = result['labels'][0]
        top_score = result['scores'][0]
        
        if top_label == self.candidate_labels[0] and top_score >= self.threshold:
            return True
            
        return False
        
    def classify_batch(self, clean_reviews):
        """
        Takes a list of clean RawReview objects.
        Returns a list of tuples: (RawReview, status)
        where status is one of: 'relevant', 'irrelevant'
        """
        processed_reviews = []
        stats = {"total": len(clean_reviews), "relevant": 0, "discarded": 0}
        
        logger.info(f"Classifying {len(clean_reviews)} reviews for relevance...")
        for i, rev in enumerate(clean_reviews):
            if i > 0 and i % 100 == 0:
                logger.info(f"  Classified {i}/{len(clean_reviews)}...")
                
            if self.is_relevant(rev.original_text):
                processed_reviews.append((rev, "relevant"))
                stats["relevant"] += 1
            else:
                processed_reviews.append((rev, "irrelevant"))
                stats["discarded"] += 1
                
        logger.info(f"Classification Stats: {stats}")
        return processed_reviews
