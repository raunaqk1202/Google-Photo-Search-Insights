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
3. Your response MUST strictly follow this exact structure, to the point with no repetition:
   - **Highlighted Problem Header**: Provide a highlighted heading using EXACTLY an `###` markdown header (e.g., `### Problem: [Issue Description]`). This triggers the highlighted style in our UI. Do NOT use `###` for any other section.
   - **Problem Description**: Exactly 2-3 lines summarizing the problem based on the evidence.
   - **Evidence Table**: A Markdown table with EXACTLY two columns: "User Quotes" and "Inference". Include a maximum of 4 rows of user quotes. 
     - CRITICAL: DO NOT include any extra columns (like "#", "ID", "Evidence", etc.).
     - CRITICAL: Remove columns with random numbers. There should be NO random numbers along with the user reviews or inside the quotes.
   - **Failure Modes**: A section detailing the failure modes derived from the evidence. Use `**Failure Modes**` as the section title, NOT `###`.
   - **Conclusion**: A brief conclusion wrapping up the findings. Use `**Conclusion**` as the section title, NOT `###`.
4. Do NOT present any kind of solution to a particular opportunity. Focus solely on analyzing the problem.
5. Clean up quotes: DO NOT include HTML elements, trailing hyphens with numbers, or any source/citation numbers (like [1], [2], 1, 2) anywhere in your text, quotes, or tables.
6. Expand all shorthands and acronyms: If you mention any acronyms or technical shorthands (e.g., EXIF, AI, OCR), you MUST mention their full form in brackets immediately after the first use (e.g., EXIF (Exchangeable Image File Format)).
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
