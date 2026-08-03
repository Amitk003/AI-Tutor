"""
Sparse BM25 Keyword Search Engine.
Implements Okapi BM25 sparse keyword matching over document chunks.
"""

import re
from typing import Any, Dict, List, Optional
from rank_bm25 import BM25Okapi
from loguru import logger

from backend.database.models.document_chunk import DocumentChunk


def tokenize_text(text: str) -> List[str]:
    """Tokenizes text into lowercase alphanumeric words for BM25 indexing."""
    cleaned = re.sub(r"[^\w\s]", "", text.lower())
    return [w for w in cleaned.split() if len(w) > 1]


class BM25Retriever:
    """Okapi BM25 sparse retrieval engine."""

    def search_chunks(
        self,
        query: str,
        chunks: List[DocumentChunk],
        top_k: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Performs BM25 keyword matching over a tenant's document chunk collection.

        Args:
            query: Query string.
            chunks: List of DocumentChunk ORM models or chunk dicts.
            top_k: Max candidate hits to return.

        Returns:
            List of hit dicts containing point_id, score, and payload.
        """
        if not chunks:
            return []

        # Tokenize corpus and query
        corpus_tokens = [tokenize_text(c.child_content if hasattr(c, "child_content") else c.get("child_content", "")) for c in chunks]
        query_tokens = tokenize_text(query)

        if not query_tokens:
            return []

        # Initialize BM25Okapi indexer
        bm25 = BM25Okapi(corpus_tokens)
        scores = bm25.get_scores(query_tokens)

        # Sort indices by score descending
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for idx in ranked_indices:
            score = float(scores[idx])
            # BM25 can legitimately assign zero/negative IDF in tiny corpora.
            # Exact token overlap remains a valid sparse retrieval candidate and is
            # subsequently combined with dense ranking through RRF.
            if not set(corpus_tokens[idx]).intersection(query_tokens):
                continue

            chunk = chunks[idx]
            chunk_metadata = (getattr(chunk, "chunk_metadata_json", None) or {}) if hasattr(chunk, "chunk_metadata_json") else chunk.get("payload", {})
            chunk_id = str(chunk.id if hasattr(chunk, "id") else chunk.get("id"))
            vector_id = str(chunk.vector_id if hasattr(chunk, "vector_id") else chunk.get("vector_id", chunk_id))
            doc_id = str(chunk.document_id if hasattr(chunk, "document_id") else chunk.get("document_id"))
            user_id = str(chunk.user_id if hasattr(chunk, "user_id") else chunk.get("user_id"))

            results.append({
                "point_id": vector_id,
                "score": score,
                "payload": {
                    "document_id": doc_id,
                    "user_id": user_id,
                    "chunk_index": chunk.chunk_index if hasattr(chunk, "chunk_index") else chunk.get("chunk_index"),
                    "page_label": chunk.page_label if hasattr(chunk, "page_label") else chunk.get("page_label"),
                    "section_title": chunk_metadata.get("section_title", "Document Section"),
                    "heading_path": chunk_metadata.get("heading_path", []),
                    "child_content": chunk.child_content if hasattr(chunk, "child_content") else chunk.get("child_content"),
                    "parent_content": chunk.parent_content if hasattr(chunk, "parent_content") else chunk.get("parent_content"),
                },
            })

        logger.debug("BM25 search completed: query='{q}' candidates={c} top_k={k}", q=query[:20], c=len(results), k=top_k)
        return results


# Global BM25 retriever instance
bm25_retriever = BM25Retriever()
