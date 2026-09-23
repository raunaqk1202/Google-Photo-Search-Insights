from typing import List, Dict, Any, Tuple

class PromptEngine:
    """Handles system prompt definitions and context assembly for the RAG pipeline."""
    
    @staticmethod
    def get_system_prompt() -> str:
        return """You are a Senior UX Researcher analyzing user feedback for Google Photos.
Your goal is to help Product Managers understand the core friction users face when searching for or retrieving photos.

CRITICAL INSTRUCTIONS:
1. Ground all your answers ONLY in the evidence provided below. Do not hallucinate or use outside knowledge.
2. If the provided evidence does not answer the user's question, state clearly that you don't have enough data.
3. You MUST cite your sources inline using [n] notation, where n is the source number. 
   Example: "Users struggle to find photos by temporal queries [1]."
4. Distinguish between direct evidence (what users explicitly state) and inference (what we can deduce). Do NOT include any hypothesis or a hypothesis section.
5. Where appropriate, quantify the issues with caveats (e.g., "In the provided sample, 3 users mentioned...").
6. Structure your responses logically, highlighting: Problem → Evidence → Failure Mode.
"""

    @staticmethod
    def format_evidence(documents: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Formats retrieved documents into a numbered evidence block.
        Returns the formatted string and the structured citation map.
        """
        evidence_lines = ["--- EVIDENCE ---"]
        citations = []
        
        for i, doc in enumerate(documents, start=1):
            source = doc.get("metadata", {}).get("source", "Unknown")
            photo_category = doc.get("metadata", {}).get("photo_category", "Unknown")
            outcome = doc.get("metadata", {}).get("outcome", "Unknown")
            
            # The 'id' from chroma usually looks like 'review_id-chunk-idx'
            # We will use this ID to fetch the full review later if needed.
            doc_id = doc.get("id", str(i))
            
            evidence_lines.append(f"[{i}] Source: {source} | Category: {photo_category} | Outcome: {outcome}")
            evidence_lines.append(f"Text: \"{doc['text']}\"")
            evidence_lines.append("") # blank line for readability
            
            citations.append({
                "citation_id": i,
                "document_id": doc_id,
                "source": source,
                "photo_category": photo_category,
                "outcome": outcome,
                "snippet": doc["text"][:100] + "..." if len(doc["text"]) > 100 else doc["text"]
            })
            
        evidence_lines.append("----------------")
        
        return "\n".join(evidence_lines), citations
