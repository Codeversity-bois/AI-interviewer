"""Retrieve relevant resume context for claim verification."""

import sys
import os
from typing import List, Dict

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


class ContextRetriever:
    """Pulls relevant resume chunks from Astra DB for a given claim."""

    def get_resume_context(self, query: str, limit: int = 3) -> List[Dict]:
        """Search resume embeddings for content relevant to the query."""
        try:
            from resume_processor_rag.core.astra_db_manager import vector_search
            results = vector_search(query, limit)
            return [
                {
                    "section_type": doc.get("section_type", "unknown"),
                    "content": doc.get("content", ""),
                }
                for doc in results
                if doc.get("content")
            ]
        except Exception as e:
            print(f"[ContextRetriever] DB search failed: {e}")
            return []

    def get_context_text(self, query: str, limit: int = 3) -> str:
        """Get resume context as a single string for prompt injection."""
        chunks = self.get_resume_context(query, limit)
        if not chunks:
            return "No relevant resume context found."
        parts = []
        for c in chunks:
            parts.append(f"[{c['section_type']}] {c['content']}")
        return "\n".join(parts)
