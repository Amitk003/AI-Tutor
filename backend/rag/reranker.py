"""
Cross-Encoder Reranking Engine.
Reranks hybrid search candidates using deep Cross-Encoder attention models (e.g., BAAI/bge-reranker-large).
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from backend.core.config import settings


class CrossEncoderReranker:
    """Cross-Encoder deep relevance reranking engine."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.RERANKER_MODEL_NAME
        self._model = None

    def _load_model(self):
        """Lazy loads sentence_transformers CrossEncoder model."""
        if self._model is None:
            logger.info("Loading CrossEncoder reranker model: {name}", name=self.model_name)
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self.model_name)
                logger.info("CrossEncoder model loaded successfully.")
            except Exception as e:
                logger.warning("Could not load CrossEncoder model '{name}' ({err}). Using fallback scoring.", name=self.model_name, err=str(e))
                self._model = "FALLBACK"

    def rerank(
        self,
        query: str,
        hits: List[Dict[str, Any]],
        top_n: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Reranks hybrid candidate hits by computing query-passage cross-attention scores.

        Args:
            query: Query string.
            hits: List of candidate hit dicts containing payloads.
            top_n: Number of top reranked hits to return (default: 5).

        Returns:
            Reranked list of hit dicts with 'rerank_score' attached.
        """
        if not hits:
            return []

        self._load_model()

        # Fallback if model not available in test env
        if self._model == "FALLBACK":
            for hit in hits:
                hit["rerank_score"] = float(hit.get("score", 0.5))
            return sorted(hits, key=lambda h: h["rerank_score"], reverse=True)[:top_n]

        # Build (query, text) pairs
        pairs = []
        for hit in hits:
            payload = hit.get("payload", {})
            text = payload.get("parent_content") or payload.get("child_content", "")
            pairs.append([query, text])

        logger.info("Executing CrossEncoder reranking: candidates={count} top_n={n}", count=len(pairs), n=top_n)

        # Compute cross-encoder scores
        scores = self._model.predict(pairs)

        reranked_hits = []
        for idx, hit in enumerate(hits):
            score = float(scores[idx])
            # Apply sigmoid if scores raw logits
            if score < -10.0 or score > 10.0:
                import math
                score = 1.0 / (1.0 + math.exp(-score))

            hit_copy = dict(hit)
            hit_copy["rerank_score"] = score
            reranked_hits.append(hit_copy)

        # Sort descending by rerank_score
        reranked_hits = sorted(reranked_hits, key=lambda h: h["rerank_score"], reverse=True)[:top_n]
        return reranked_hits


# Global cross-encoder reranker instance
cross_encoder_reranker = CrossEncoderReranker()
