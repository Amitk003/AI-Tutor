"""
Retrieval Evaluation Metrics Engine.
Computes Recall@K, Mean Reciprocal Rank (MRR), nDCG@K, Hit Rate@K, and latency benchmarking.
"""

import math
from typing import Any, Dict, List, Set


def calculate_recall_at_k(retrieved_ids: List[str], ground_truth_ids: Set[str], k: int) -> float:
    """
    Calculates Recall@K metric.
    Fraction of ground truth relevant items retrieved in top-K.
    """
    if not ground_truth_ids:
        return 0.0
    top_k_retrieved = set(retrieved_ids[:k])
    relevant_retrieved = top_k_retrieved.intersection(ground_truth_ids)
    return len(relevant_retrieved) / len(ground_truth_ids)


def calculate_hit_rate(retrieved_ids: List[str], ground_truth_ids: Set[str], k: int) -> float:
    """
    Calculates Hit Rate@K (1.0 if at least one ground truth item appears in top-K, else 0.0).
    """
    if not ground_truth_ids:
        return 0.0
    top_k_retrieved = set(retrieved_ids[:k])
    return 1.0 if bool(top_k_retrieved.intersection(ground_truth_ids)) else 0.0


def calculate_mrr(retrieved_ids: List[str], ground_truth_ids: Set[str]) -> float:
    """
    Calculates Mean Reciprocal Rank (MRR).
    Reciprocal rank of first relevant item retrieved.
    """
    if not ground_truth_ids:
        return 0.0
    for idx, item_id in enumerate(retrieved_ids):
        if item_id in ground_truth_ids:
            return 1.0 / (idx + 1)
    return 0.0


def calculate_ndcg(retrieved_ids: List[str], ground_truth_ids: Set[str], k: int) -> float:
    """
    Calculates Normalized Discounted Cumulative Gain (nDCG@K).
    """
    if not ground_truth_ids:
        return 0.0

    top_k = retrieved_ids[:k]
    dcg = 0.0

    for i, item_id in enumerate(top_k):
        if item_id in ground_truth_ids:
            dcg += 1.0 / math.log2(i + 2)

    # Calculate Ideal DCG (IDCG)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(len(ground_truth_ids), k)))
    if idcg == 0.0:
        return 0.0

    return dcg / idcg


def evaluate_retrieval_metrics(
    retrieved_ids: List[str],
    ground_truth_ids: Set[str],
    latency_ms: float,
    k: int = 10,
) -> Dict[str, Any]:
    """
    Computes complete benchmark evaluation suite for a retrieval result.

    Returns:
        Dict containing recall_at_k, mrr, ndcg_at_k, hit_rate_at_k, and latency_ms.
    """
    return {
        "k": k,
        "recall_at_k": calculate_recall_at_k(retrieved_ids, ground_truth_ids, k),
        "mrr": calculate_mrr(retrieved_ids, ground_truth_ids),
        "ndcg_at_k": calculate_ndcg(retrieved_ids, ground_truth_ids, k),
        "hit_rate_at_k": calculate_hit_rate(retrieved_ids, ground_truth_ids, k),
        "latency_ms": round(latency_ms, 2),
    }
