"""
Reciprocal Rank Fusion (RRF) Engine.
Combines dense semantic search and BM25 sparse keyword rankings into unified hybrid search score.
"""

from typing import Any, Dict, List
from loguru import logger


def reciprocal_rank_fusion(
    dense_hits: List[Dict[str, Any]],
    sparse_hits: List[Dict[str, Any]],
    rrf_k: int = 60,
    top_k: int = 20,
) -> List[Dict[str, Any]]:
    """
    Fuses dense and sparse search rankings using Reciprocal Rank Fusion formula:
    RRF_Score(d) = 1 / (k + rank_dense) + 1 / (k + rank_sparse)

    Args:
        dense_hits: List of candidate hit dicts from vector search.
        sparse_hits: List of candidate hit dicts from BM25 search.
        rrf_k: RRF smoothing constant (default: 60).
        top_k: Max candidate hits to return.

    Returns:
        Sorted list of fused hit dicts with combined RRF score and ranking telemetry.
    """
    rrf_scores: Dict[str, float] = {}
    payload_map: Dict[str, Dict[str, Any]] = {}
    rank_telemetry: Dict[str, Dict[str, Any]] = {}

    # Process Dense hits
    for rank, hit in enumerate(dense_hits):
        point_id = str(hit["point_id"])
        payload_map[point_id] = hit["payload"]
        rrf_scores[point_id] = rrf_scores.get(point_id, 0.0) + (1.0 / (rrf_k + rank + 1))

        if point_id not in rank_telemetry:
            rank_telemetry[point_id] = {"dense_rank": rank + 1, "sparse_rank": None, "dense_score": hit["score"]}

    # Process Sparse hits
    for rank, hit in enumerate(sparse_hits):
        point_id = str(hit["point_id"])
        if point_id not in payload_map:
            payload_map[point_id] = hit["payload"]

        rrf_scores[point_id] = rrf_scores.get(point_id, 0.0) + (1.0 / (rrf_k + rank + 1))

        if point_id not in rank_telemetry:
            rank_telemetry[point_id] = {"dense_rank": None, "sparse_rank": rank + 1, "sparse_score": hit["score"]}
        else:
            rank_telemetry[point_id]["sparse_rank"] = rank + 1
            rank_telemetry[point_id]["sparse_score"] = hit["score"]

    # Sort candidates by combined RRF score descending
    sorted_ids = sorted(rrf_scores.keys(), key=lambda pid: rrf_scores[pid], reverse=True)[:top_k]

    fused_results = []
    for pid in sorted_ids:
        score = rrf_scores[pid]
        telemetry = rank_telemetry[pid]

        fused_results.append({
            "point_id": pid,
            "score": float(score),
            "payload": payload_map[pid],
            "fusion_telemetry": telemetry,
        })

    logger.info(
        "RRF Fusion complete: dense_hits={d} sparse_hits={s} fused_count={f}",
        d=len(dense_hits),
        s=len(sparse_hits),
        f=len(fused_results),
    )
    return fused_results
