"""
Dense Semantic Retriever Engine.
Executes vector similarity search, multi-tenant payload filtering, parent-child reconstruction,
and retrieval metrics evaluation.
"""

import time
import uuid
from typing import Any, Dict, List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.database.models.retrieval_metrics import RetrievalMetric
from backend.rag.context_builder import ContextBuilder, context_builder
from backend.rag.embeddings import BatchEmbeddingService, embedding_service
from backend.rag.evaluator import evaluate_retrieval_metrics
from backend.vector_store.qdrant_client import QdrantVectorStore, qdrant_store


class DenseRetriever:
    """Dense semantic vector retriever."""

    def __init__(
        self,
        embed_service: Optional[BatchEmbeddingService] = None,
        store: Optional[QdrantVectorStore] = None,
        builder: Optional[ContextBuilder] = None,
    ):
        self.embed_service = embed_service or embedding_service
        self.store = store or qdrant_store
        self.builder = builder or context_builder

    async def retrieve_dense(
        self,
        user_id: uuid.UUID,
        query_text: str,
        document_ids: Optional[List[uuid.UUID]] = None,
        top_k: int = 20,
        ground_truth_chunk_ids: Optional[Set[str]] = None,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Executes dense vector search, parent context reconstruction, and metrics evaluation.

        Args:
            user_id: UUID of owning user (multi-tenant security filter).
            query_text: User query string.
            document_ids: Optional list of target document UUIDs to filter.
            top_k: Max vector candidates to retrieve (default: 20).
            ground_truth_chunk_ids: Optional set of ground-truth relevant chunk IDs for benchmarking.
            session: Optional AsyncSession to persist RetrievalMetric telemetry.

        Returns:
            Dict containing 'formatted_context', 'sources', 'hits', and 'evaluation_metrics'.
        """
        start_time = time.perf_counter()
        logger.info("Executing dense retrieval: user_id={uid} query='{q}' top_k={k}", uid=user_id, q=query_text[:30], k=top_k)

        # 1. Generate query vector embedding
        query_vector = self.embed_service.embed_text(query_text)

        # 2. Search Qdrant with payload filters
        hits = self.store.search_dense(
            query_vector=query_vector,
            user_id=user_id,
            document_ids=document_ids,
            top_k=top_k,
        )

        # 3. Reconstruct parent context and assemble formatted text
        assembled = self.builder.reconstruct_and_assemble(hits)
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # 4. Evaluate metrics
        retrieved_ids = [h["point_id"] for h in hits]
        metrics = evaluate_retrieval_metrics(
            retrieved_ids=retrieved_ids,
            ground_truth_ids=ground_truth_chunk_ids or set(),
            latency_ms=latency_ms,
            k=min(top_k, 10),
        )

        # 5. Persist RetrievalMetric telemetry if DB session provided
        top_score = hits[0]["score"] if hits else 0.0
        if session:
            metric_record = RetrievalMetric(
                user_id=user_id,
                query_text=query_text,
                retrieved_candidate_count=len(hits),
                top_rerank_score=top_score,
                confidence_threshold_met=(top_score >= 0.35),
                retrieval_latency_ms=latency_ms,
            )
            session.add(metric_record)

        return {
            "query": query_text,
            "formatted_context": assembled["formatted_context"],
            "sources": assembled["sources"],
            "hits": hits,
            "evaluation_metrics": metrics,
        }
