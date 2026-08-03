"""
Context Assembly & Parent-Child Reconstruction Engine.
Reconstructs ~1200 token parent context blocks from granular vector child hits,
deduplicates overlapping text, and formats structured context for LLM prompt injection.
"""

from typing import Any, Dict, List, Set
from loguru import logger


class ContextBuilder:
    """Parent-Child context reconstruction and assembly engine."""

    def __init__(self, max_context_chars: int = 6000):  # ~1500 words / tokens
        self.max_context_chars = max_context_chars

    def reconstruct_and_assemble(self, hits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Reconstructs parent context from vector hits, deduplicates overlapping blocks,
        and formats markdown context string.

        Args:
            hits: List of candidate hit dicts from vector search containing payloads.

        Returns:
            Dict containing 'formatted_context', 'sources', and 'total_char_count'.
        """
        if not hits:
            return {
                "formatted_context": "",
                "sources": [],
                "total_char_count": 0,
            }

        sources: List[Dict[str, Any]] = []
        seen_parent_texts: Set[str] = set()
        context_parts: List[str] = []
        accumulated_chars = 0

        for idx, hit in enumerate(hits):
            payload = hit.get("payload", {})
            child_text = payload.get("child_content", "")
            parent_text = payload.get("parent_content", child_text)
            page_label = payload.get("page_label", "1")
            section_title = payload.get("section_title", "Document Section")
            doc_id = payload.get("document_id", "")
            score = hit.get("score", 0.0)

            # Deduplicate exact or overlapping parent text
            clean_parent = parent_text.strip()
            if clean_parent in seen_parent_texts:
                continue
            seen_parent_texts.add(clean_parent)

            # Check context length limit
            if accumulated_chars + len(clean_parent) > self.max_context_chars:
                logger.debug("Context length limit reached ({max} chars). Stopping assembly.", max=self.max_context_chars)
                break

            header = f"### Source [{page_label}] — {section_title} (Relevance Score: {score:.3f})"
            context_block = f"{header}\n{clean_parent}"
            context_parts.append(context_block)
            accumulated_chars += len(context_block)

            sources.append({
                "document_id": doc_id,
                "page_label": page_label,
                "section_title": section_title,
                "similarity_score": score,
                "snippet": child_text[:200],
            })

        formatted_context = "\n\n---\n\n".join(context_parts)

        logger.info(
            "Context assembly complete: candidates={total} selected_sources={count} total_chars={chars}",
            total=len(hits),
            count=len(sources),
            chars=accumulated_chars,
        )

        return {
            "formatted_context": formatted_context,
            "sources": sources,
            "total_char_count": accumulated_chars,
        }


# Global context builder singleton
context_builder = ContextBuilder()
