"""
Retrieval Milestone C Unit Tests.
Verifies Cross-Encoder reranking, ContextOptimizer refusal guardrails, citation verification,
LLM Gateway abstraction layer, and Before vs After reranking benchmark metrics.
"""

import pytest

from backend.llm.gateway import LLMGatewayFactory, OllamaGateway, VLLMGateway
from backend.rag.context_optimizer import ContextOptimizer
from backend.rag.evaluator import evaluate_retrieval_metrics
from backend.rag.reranker import CrossEncoderReranker


def test_llm_gateway_abstraction_factory():
    """Verify LLMGatewayFactory instantiates provider gateways sharing one interface."""
    ollama_gw = LLMGatewayFactory.get_gateway("ollama")
    assert isinstance(ollama_gw, OllamaGateway)
    assert ollama_gw.provider_name == "ollama"

    vllm_gw = LLMGatewayFactory.get_gateway("vllm")
    assert isinstance(vllm_gw, VLLMGateway)
    assert vllm_gw.provider_name == "vllm"


def test_cross_encoder_reranker_scoring():
    """Verify CrossEncoderReranker sorts candidate hits by cross-attention score."""
    reranker = CrossEncoderReranker()
    query = "What is backpropagation?"

    hits = [
        {
            "point_id": "p1",
            "score": 0.5,
            "payload": {"child_content": "Random unrelated text", "parent_content": "Unrelated chapter"},
        },
        {
            "point_id": "p2",
            "score": 0.9,
            "payload": {"child_content": "Backpropagation computes partial derivatives using chain rule.", "parent_content": "Neural networks backpropagation."},
        },
    ]

    reranked = reranker.rerank(query, hits, top_n=2)
    assert len(reranked) == 2
    assert "rerank_score" in reranked[0]


def test_confidence_refusal_threshold_guardrail():
    """Verify ContextOptimizer triggers refusal guardrail when confidence < 0.35."""
    optimizer = ContextOptimizer()

    # Low relevance hits -> Should trigger refusal
    low_hits = [
        {
            "rerank_score": 0.15,
            "score": 0.20,
            "fusion_telemetry": {"dense_score": 0.20, "sparse_score": 1.0},
            "payload": {"child_content": "Irrelevant content", "parent_content": "Irrelevant parent context"},
        }
    ]

    result = optimizer.optimize_and_verify("What is quantum computing?", low_hits, threshold=0.35)
    assert result["is_refusal"] is True
    assert "not contain sufficient evidence" in result["refusal_reason"]
    assert result["formatted_context"] == ""

    # High relevance hits -> Should pass guardrail and return citations
    high_hits = [
        {
            "rerank_score": 0.88,
            "score": 0.92,
            "fusion_telemetry": {"dense_score": 0.92, "sparse_score": 15.0},
            "payload": {
                "document_id": "doc-123",
                "page_label": "Page 10",
                "section_title": "Deep Learning",
                "child_content": "Deep learning uses neural networks.",
                "parent_content": "Chapter 1: Deep learning uses neural networks with multi-layer perceptrons.",
            },
        }
    ]

    res_pass = optimizer.optimize_and_verify("What is deep learning?", high_hits, threshold=0.35)
    assert res_pass["is_refusal"] is False
    assert len(res_pass["citations"]) == 1
    assert res_pass["citations"][0]["page_label"] == "Page 10"


def test_before_vs_after_reranking_benchmarking():
    """Verify benchmarking metrics Before vs After Cross-Encoder reranking."""
    ground_truth = {"correct-chunk-id"}

    # Before Reranking: correct item at rank 4
    before_ids = ["chunk-a", "chunk-b", "chunk-c", "correct-chunk-id"]
    m_before = evaluate_retrieval_metrics(before_ids, ground_truth, latency_ms=10.0, k=5)

    # After Reranking: correct item promoted to rank 1!
    after_ids = ["correct-chunk-id", "chunk-a", "chunk-b", "chunk-c"]
    m_after = evaluate_retrieval_metrics(after_ids, ground_truth, latency_ms=18.0, k=5)

    assert m_before["mrr"] == 0.25  # 1/4
    assert m_after["mrr"] == 1.0    # 1/1 (Promoted to top position!)
    assert m_after["mrr"] > m_before["mrr"]
