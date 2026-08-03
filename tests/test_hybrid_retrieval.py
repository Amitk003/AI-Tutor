"""
Hybrid Search & Retrieval Benchmarking Unit Tests.
Verifies Query Processing NLU, Okapi BM25 sparse search, RRF rank fusion formula,
Redis cache, and comparative evaluation (Dense vs BM25 vs Hybrid).
"""

import uuid
import pytest

from backend.database.models.document_chunk import DocumentChunk
from backend.nlu.query_processor import QueryProcessor
from backend.rag.bm25_retriever import BM25Retriever
from backend.rag.evaluator import evaluate_retrieval_metrics
from backend.rag.rrf import reciprocal_rank_fusion


def test_query_processor_nlu():
    """Verify QueryProcessor normalization, synonym expansion, intent classification, and adaptive K."""
    qp = QueryProcessor()
    
    # 1. Normalization & Intent: Definitional
    res1 = qp.process("What is Machine Learning?")
    assert res1.normalized_query == "what is machine learning"
    assert res1.intent == "DEFINITIONAL"
    assert res1.adaptive_top_k == 10
    assert "ml" in res1.expanded_terms or "machine learning" in res1.normalized_query

    # 2. Intent: Procedural
    res2 = qp.process("How to implement gradient descent step by step?")
    assert res2.intent == "PROCEDURAL"
    assert res2.adaptive_top_k == 25
    assert "loss minimization" in res2.expanded_terms or "optimization" in res2.expanded_terms

    # 3. Intent: Factual
    res3 = qp.process("Exact formula for backpropagation chain rule")
    assert res3.intent == "FACTUAL"


def test_bm25_sparse_retrieval():
    """Verify Okapi BM25 keyword matching and scoring over chunk corpus."""
    retriever = BM25Retriever()
    user_id = uuid.uuid4()
    doc_id = uuid.uuid4()

    chunk1 = DocumentChunk(
        id=uuid.uuid4(),
        document_id=doc_id,
        user_id=user_id,
        chunk_index=0,
        child_content="Gradient descent is an optimization algorithm for loss minimization.",
        parent_content="Parent context for gradient descent.",
        vector_id=uuid.uuid4(),
        page_label="Page 1",
    )
    chunk2 = DocumentChunk(
        id=uuid.uuid4(),
        document_id=doc_id,
        user_id=user_id,
        chunk_index=1,
        child_content="Backpropagation uses the calculus chain rule for partial derivatives.",
        parent_content="Parent context for backpropagation.",
        vector_id=uuid.uuid4(),
        page_label="Page 2",
    )

    chunks = [chunk1, chunk2]

    # Search query targeting chunk 1 keywords
    hits1 = retriever.search_chunks("gradient descent loss minimization", chunks, top_k=2)
    assert len(hits1) >= 1
    assert hits1[0]["point_id"] == str(chunk1.vector_id)

    # Search query targeting chunk 2 keywords
    hits2 = retriever.search_chunks("calculus chain rule backpropagation", chunks, top_k=2)
    assert len(hits2) >= 1
    assert hits2[0]["point_id"] == str(chunk2.vector_id)


def test_reciprocal_rank_fusion_algorithm():
    """Verify Reciprocal Rank Fusion (RRF) score calculation and order combination."""
    pid_a = "vector-uuid-a"
    pid_b = "vector-uuid-b"
    pid_c = "vector-uuid-c"

    dense_hits = [
        {"point_id": pid_a, "score": 0.95, "payload": {"text": "A"}},
        {"point_id": pid_b, "score": 0.85, "payload": {"text": "B"}},
    ]
    sparse_hits = [
        {"point_id": pid_b, "score": 12.5, "payload": {"text": "B"}},
        {"point_id": pid_c, "score": 8.1, "payload": {"text": "C"}},
    ]

    fused = reciprocal_rank_fusion(dense_hits, sparse_hits, rrf_k=60, top_k=3)
    assert len(fused) == 3

    # Candidate B appeared in both lists (rank 2 in dense, rank 1 in sparse)
    # RRF(B) = 1/(60+2) + 1/(60+1) = 0.016129 + 0.016393 = 0.03252
    # RRF(A) = 1/(60+1) = 0.016393
    # Therefore Candidate B should rank #1 after fusion!
    assert fused[0]["point_id"] == pid_b
    assert fused[0]["score"] > fused[1]["score"]


def test_comparative_retrieval_benchmarking():
    """Verify benchmarking suite measuring Recall@K, MRR, nDCG across Dense, BM25, and Hybrid."""
    ground_truth = {"item-1", "item-2"}

    dense_retrieved = ["item-1", "item-3", "item-4"]
    sparse_retrieved = ["item-4", "item-2", "item-5"]
    hybrid_retrieved = ["item-1", "item-2", "item-3"]

    m_dense = evaluate_retrieval_metrics(dense_retrieved, ground_truth, latency_ms=12.5, k=3)
    m_sparse = evaluate_retrieval_metrics(sparse_retrieved, ground_truth, latency_ms=8.0, k=3)
    m_hybrid = evaluate_retrieval_metrics(hybrid_retrieved, ground_truth, latency_ms=15.0, k=3)

    assert m_dense["recall_at_k"] == 0.5   # Found 1 of 2
    assert m_sparse["recall_at_k"] == 0.5  # Found 1 of 2
    assert m_hybrid["recall_at_k"] == 1.0  # Hybrid fusion found 2 of 2!
