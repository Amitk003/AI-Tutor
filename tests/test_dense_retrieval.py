"""
Dense Retrieval & Metrics Evaluation Unit Tests.
Verifies Recall@K, MRR, nDCG@K, Hit Rate@K math formulas, ContextBuilder parent reconstruction,
and DenseRetriever query execution.
"""

import uuid
import pytest

from backend.rag.evaluator import (
    calculate_hit_rate,
    calculate_mrr,
    calculate_ndcg,
    calculate_recall_at_k,
    evaluate_retrieval_metrics,
)
from backend.rag.context_builder import ContextBuilder


def test_evaluator_recall_at_k():
    """Verify Recall@K metric formula."""
    ground_truth = {"id1", "id2", "id3"}
    retrieved = ["id1", "id4", "id2", "id5", "id6"]

    # Top 3 retrieved: id1, id4, id2 -> 2 out of 3 found
    recall_3 = calculate_recall_at_k(retrieved, ground_truth, k=3)
    assert abs(recall_3 - (2 / 3)) < 0.001

    # Top 5 retrieved: id1, id4, id2, id5, id6 -> 2 out of 3 found
    recall_5 = calculate_recall_at_k(retrieved, ground_truth, k=5)
    assert abs(recall_5 - (2 / 3)) < 0.001


def test_evaluator_mrr():
    """Verify Mean Reciprocal Rank (MRR) metric formula."""
    ground_truth = {"target_id"}

    # Target item at rank 1 -> MRR = 1/1 = 1.0
    assert calculate_mrr(["target_id", "other"], ground_truth) == 1.0

    # Target item at rank 2 -> MRR = 1/2 = 0.5
    assert calculate_mrr(["other", "target_id"], ground_truth) == 0.5

    # Target item at rank 4 -> MRR = 1/4 = 0.25
    assert calculate_mrr(["a", "b", "c", "target_id"], ground_truth) == 0.25

    # Target item not found -> MRR = 0.0
    assert calculate_mrr(["a", "b", "c"], ground_truth) == 0.0


def test_evaluator_hit_rate():
    """Verify Hit Rate@K metric formula."""
    ground_truth = {"id_x"}
    assert calculate_hit_rate(["id_a", "id_x", "id_b"], ground_truth, k=3) == 1.0
    assert calculate_hit_rate(["id_a", "id_b", "id_x"], ground_truth, k=2) == 0.0


def test_evaluator_ndcg():
    """Verify Normalized Discounted Cumulative Gain (nDCG@K)."""
    ground_truth = {"doc1", "doc2"}
    retrieved = ["doc1", "doc2", "doc3"]

    ndcg = calculate_ndcg(retrieved, ground_truth, k=3)
    assert 0.0 <= ndcg <= 1.0
    # Perfect ranking doc1, doc2 at rank 1 & 2 -> nDCG should be 1.0
    assert abs(ndcg - 1.0) < 0.001


def test_context_builder_parent_reconstruction():
    """Verify ContextBuilder reconstructs parent text and deduplicates redundant hits."""
    builder = ContextBuilder(max_context_chars=1000)

    hits = [
        {
            "score": 0.92,
            "payload": {
                "document_id": str(uuid.uuid4()),
                "page_label": "Page 12",
                "section_title": "Gradient Descent",
                "child_content": "Gradient descent minimizes loss.",
                "parent_content": "Chapter 2: Optimization. Gradient descent minimizes loss by computing partial derivatives.",
            },
        },
        {
            # Exact duplicate parent content -> should be deduped
            "score": 0.88,
            "payload": {
                "document_id": str(uuid.uuid4()),
                "page_label": "Page 12",
                "section_title": "Gradient Descent",
                "child_content": "Loss functions in models.",
                "parent_content": "Chapter 2: Optimization. Gradient descent minimizes loss by computing partial derivatives.",
            },
        },
    ]

    assembled = builder.reconstruct_and_assemble(hits)
    assert len(assembled["sources"]) == 1
    assert "Page 12" in assembled["formatted_context"]
    assert "Gradient Descent" in assembled["formatted_context"]
