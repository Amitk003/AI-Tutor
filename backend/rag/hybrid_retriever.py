"""
Hybrid Search Engine & Retrieval Orchestrator.
Combines Query Processing Layer, Dense Vector Search, Sparse BM25 Search,
Reciprocal Rank Fusion (RRF), Cross-Encoder Reranking, Context Optimization,
Confidence Threshold Guardrails, Redis Cache, and IR Benchmark Metrics.
"""

import hashlib
import time
import uuid
from typing import Any, Dict, List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.database.models.retrieval_metrics import RetrievalMetric
from backend.database.repositories.document_repository import DocumentRepository
from backend.nlu.query_processor import QueryProcessor, query_processor
from backend.rag.bm25_retriever import BM25Retriever, bm25_retriever
from backend.rag.context_optimizer import ContextOptimizer, context_optimizer
from backend.rag.embeddings import BatchEmbeddingService, embedding_service
from backend.rag.evaluator import evaluate_retrieval_metrics
from backend.rag.reranker import CrossEncoderReranker, cross_encoder_reranker
from backend.rag.retrieval_cache import RetrievalCache, retrieval_cache
from backend.rag.rrf import reciprocal_rank_fusion
from backend.vector_store.qdrant_client import QdrantVectorStore, qdrant_store


class HybridRetriever:
    """Hybrid search orchestrator with Cross-Encoder reranking and refusal guardrails."""

    def __init__(
        self,
        q_processor: Optional[QueryProcessor] = None,
        embed_service: Optional[BatchEmbeddingService] = None,
        store: Optional[QdrantVectorStore] = None,
        bm25: Optional[BM25Retriever] = None,
        reranker: Optional[CrossEncoderReranker] = None,
        optimizer: Optional[ContextOptimizer] = None,
        cache: Optional[RetrievalCache] = None,
    ):
        self.q_processor = q_processor or query_processor
        self.embed_service = embed_service or embedding_service
        self.store = store or qdrant_store
        self.bm25 = bm25 or bm25_retriever
        self.reranker = reranker or cross_encoder_reranker
        self.optimizer = optimizer or context_optimizer
        self.cache = cache or retrieval_cache

    async def retrieve_hybrid(
        self,
        user_id: uuid.UUID,
        query_text: str,
        document_ids: Optional[List[uuid.UUID]] = None,
        ground_truth_chunk_ids: Optional[Set[str]] = None,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Executes complete hybrid search, reranking, and context optimization pipeline.
        """
        start_time = time.perf_counter()

        # 1. Query Processing Layer
        processed_query = self.q_processor.process(query_text)
        top_k = processed_query.adaptive_top_k

        # Check Cache
        doc_key = "-".join(str(d) for d in sorted(document_ids)) if document_ids else "all"
        cache_hash = hashlib.sha256(f"{user_id}:{processed_query.normalized_query}:{doc_key}".encode()).hexdigest()
        cache_key = f"rag:hybrid:v2:{cache_hash}"

        cached = await self.cache.get(cache_key)
        if cached:
            cached["from_cache"] = True
            return cached

        logger.info("Executing Hybrid Retrieval + Reranking: user_id={uid} query='{q}'", uid=user_id, q=processed_query.normalized_query[:30])

        # 2. Dense Semantic Retrieval
        query_vector = self.embed_service.embed_text(processed_query.normalized_query)
        dense_hits = self.store.search_dense(
            query_vector=query_vector,
            user_id=user_id,
            document_ids=document_ids,
            top_k=top_k,
        )

        # 3. Sparse BM25 Search
        sparse_hits: List[Dict[str, Any]] = []
        if session:
            doc_repo = DocumentRepository(session)
            user_chunks = []
            if document_ids:
                for doc_id in document_ids:
                    chunks = await doc_repo.get_document_chunks(doc_id, user_id)
                    user_chunks.extend(chunks)
            else:
                user_docs = await doc_repo.get_user_documents(user_id)
                for doc in user_docs:
                    chunks = await doc_repo.get_document_chunks(doc.id, user_id)
                    user_chunks.extend(chunks)

            sparse_hits = self.bm25.search_chunks(
                query=processed_query.normalized_query,
                chunks=user_chunks,
                top_k=top_k,
            )

        # 4. Reciprocal Rank Fusion (RRF)
        fused_hits = reciprocal_rank_fusion(
            dense_hits=dense_hits,
            sparse_hits=sparse_hits,
            top_k=top_k,
        )

        # 5. Cross-Encoder Reranking
        reranked_hits = self.reranker.rerank(
            query=processed_query.normalized_query,
            hits=fused_hits,
            top_n=5,
        )

        # 6. Context Optimization & Refusal Threshold Guardrail
        optimized = self.optimizer.optimize_and_verify(
            query=processed_query.normalized_query,
            reranked_hits=reranked_hits,
        )

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # 7. Benchmark Evaluation Metrics
        retrieved_ids = [h["point_id"] for h in reranked_hits]
        metrics = evaluate_retrieval_metrics(
            retrieved_ids=retrieved_ids,
            ground_truth_ids=ground_truth_chunk_ids or set(),
            latency_ms=latency_ms,
            k=min(len(retrieved_ids), 5) if retrieved_ids else 5,
        )

        result = {
            "query": query_text,
            "processed_query": {
                "normalized": processed_query.normalized_query,
                "intent": processed_query.intent,
                "adaptive_top_k": processed_query.adaptive_top_k,
            },
            "is_refusal": optimized["is_refusal"],
            "refusal_reason": optimized["refusal_reason"],
            "confidence_score": optimized["confidence_score"],
            "formatted_context": optimized["formatted_context"],
            "citations": optimized["citations"],
            "reranked_hits": reranked_hits,
            "evaluation_metrics": metrics,
            "from_cache": False,
        }

        # Cache result
        await self.cache.set(cache_key, result, ttl_seconds=3600)

        # Persist metric log if session available
        if session:
            metric_record = RetrievalMetric(
                user_id=user_id,
                query_text=query_text,
                retrieved_candidate_count=len(reranked_hits),
                top_rerank_score=optimized["confidence_score"],
                confidence_threshold_met=(not optimized["is_refusal"]),
                retrieval_latency_ms=latency_ms,
            )
            session.add(metric_record)

        return result


# Global hybrid retriever instance
hybrid_retriever = HybridRetriever()
