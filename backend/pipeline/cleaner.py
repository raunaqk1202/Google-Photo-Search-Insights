import re
import logging
from datasketch import MinHash, MinHashLSH
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# For consistent language detection results
DetectorFactory.seed = 0

logger = logging.getLogger(__name__)

class DataCleaner:
    def __init__(self, threshold=0.85, num_perm=128):
        self.threshold = threshold
        self.num_perm = num_perm
        self.lsh = MinHashLSH(threshold=self.threshold, num_perm=self.num_perm)
        self.seen_ids = set()
        
    def _get_minhash(self, text):
        m = MinHash(num_perm=self.num_perm)
        # Simple tokenization: lowercase and alphanumeric only
        tokens = re.findall(r'\b\w+\b', text.lower())
        for token in tokens:
            m.update(token.encode('utf8'))
        return m

    def is_english(self, text):
        try:
            return detect(text) == 'en'
        except LangDetectException:
            return False
            
    def is_spam(self, text):
        if not text or len(text.strip()) < 10:
            return True
        # If it's all emojis or non-alphanumeric
        if not re.search(r'[a-zA-Z]', text):
            return True
        return False

    def clean(self, raw_reviews):
        """
        Takes a list of RawReview objects.
        Returns a list of tuples: (RawReview, status)
        where status is one of: 'spam', 'non_english', 'duplicate', 'clean'
        """
        processed_reviews = []
        stats = {"total": len(raw_reviews), "non_english": 0, "spam": 0, "duplicate": 0, "passed": 0}
        
        for rev in raw_reviews:
            text = rev.original_text
            
            if self.is_spam(text):
                stats["spam"] += 1
                processed_reviews.append((rev, "spam"))
                continue
                
            if not self.is_english(text):
                stats["non_english"] += 1
                processed_reviews.append((rev, "non_english"))
                continue
                
            m = self._get_minhash(text)
            # Query for exact or near duplicates
            result = self.lsh.query(m)
            
            if result:
                stats["duplicate"] += 1
                processed_reviews.append((rev, "duplicate"))
                continue
                
            # If unique, insert into LSH
            self.lsh.insert(str(rev.id), m)
            self.seen_ids.add(str(rev.id))
            processed_reviews.append((rev, "clean"))
            stats["passed"] += 1
            
        logger.info(f"Cleaner Stats: {stats}")
        return processed_reviews
