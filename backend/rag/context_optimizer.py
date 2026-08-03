"""
Context Optimization & Confidence Guardrail Engine.
Merges overlapping parent text chunks, computes composite confidence scores,
enforces refusal threshold guardrails, and extracts verified citation metadata.
"""

from typing import Any, Dict, List, Optional, Tuple
from loguru import logger

CONFIDENCE_THRESHOLD = 0.35  # Tau threshold below which retrieval is refused


class ContextOptimizer:
    """Context optimization, confidence scoring, and citation verification engine."""

    def compute_composite_confidence(self, hits: List[Dict[str, Any]]) -> float:
        """
        Computes composite confidence score combining dense, sparse, and reranker scores.
        Confidence = 0.5 * reranker_score + 0.3 * dense_score + 0.2 * sparse_score
        """
        if not hits:
            return 0.0

        top_hit = hits[0]
        rerank_score = float(top_hit.get("rerank_score", 0.5))
        telemetry = top_hit.get("fusion_telemetry", {})
        dense_score = float(telemetry.get("dense_score", top_hit.get("score", 0.5)))
        sparse_score = float(telemetry.get("sparse_score", 0.0))

        # Normalize sparse BM25 score to [0, 1] range if needed
        norm_sparse = min(sparse_score / 20.0, 1.0) if sparse_score > 0 else 0.5

        confidence = (0.5 * rerank_score) + (0.3 * dense_score) + (0.2 * norm_sparse)
        return min(max(confidence, 0.0), 1.0)

    def optimize_and_verify(
        self,
        query: str,
        reranked_hits: List[Dict[str, Any]],
        threshold: float = CONFIDENCE_THRESHOLD,
    ) -> Dict[str, Any]:
        """
        Optimizes context, checks confidence threshold, and structures citation metadata.
        """
        confidence = self.compute_composite_confidence(reranked_hits)
        is_refusal = confidence < threshold

        if is_refusal or not reranked_hits:
            logger.warning(
                "Retrieval confidence ({conf:.3f}) below threshold ({thresh:.3f}). Triggering refusal guardrail.",
                conf=confidence,
                thresh=threshold,
            )
            return {
                "is_refusal": True,
                "confidence_score": confidence,
                "refusal_reason": "The uploaded study materials do not contain sufficient evidence to answer this question accurately.",
                "formatted_context": "",
                "citations": [],
            }

        # Deduplicate and merge overlapping parent contexts
        seen_texts = set()
        optimized_blocks = []
        citations = []

        for idx, hit in enumerate(reranked_hits):
            payload = hit.get("payload", {})
            child_text = payload.get("child_content", "")
            parent_text = payload.get("parent_content", child_text).strip()
            page_label = payload.get("page_label", "1")
            section_title = payload.get("section_title", "Section")
            doc_id = payload.get("document_id", "")
            rerank_score = hit.get("rerank_score", 0.0)

            if parent_text in seen_texts:
                continue
            seen_texts.add(parent_text)

            header = f"### Citation [{idx+1}] (Page: {page_label}, Section: {section_title})"
            block = f"{header}\n{parent_text}"
            optimized_blocks.append(block)

            citations.append({
                "citation_index": idx + 1,
                "document_id": doc_id,
                "page_label": page_label,
                "section_title": section_title,
                "confidence_score": round(rerank_score, 4),
                "snippet_text": child_text[:250],
            })

        formatted_context = "\n\n---\n\n".join(optimized_blocks)

        return {
            "is_refusal": False,
            "confidence_score": round(confidence, 4),
            "refusal_reason": None,
            "formatted_context": formatted_context,
            "citations": citations,
        }


# Global context optimizer singleton
context_optimizer = ContextOptimizer()
