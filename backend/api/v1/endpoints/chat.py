"""
RAG Retrieval & Chat API v1 Router.
Exposes RESTful endpoints for dense search, hybrid search, full RAG LLM query generation,
and SSE token streaming responses.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.authentication.deps import get_current_active_user
from backend.database.models.user import User
from backend.database.session import get_db
from backend.llm.orchestrator import rag_orchestrator
from backend.rag.hybrid_retriever import HybridRetriever
from backend.rag.retriever import DenseRetriever

router = APIRouter(prefix="/chat")


class SearchRequest(BaseModel):
    """Retrieval search request payload schema."""

    query: str = Field(..., min_length=2, description="User question or query text")
    document_ids: Optional[List[uuid.UUID]] = Field(default=None, description="Optional list of document UUIDs to filter search")
    top_k: int = Field(default=20, ge=1, le=100, description="Max candidate items to retrieve")


class RAGQueryRequest(BaseModel):
    """Full RAG LLM query request payload schema."""

    question: str = Field(..., min_length=2, description="Student question string")
    session_id: Optional[uuid.UUID] = Field(default=None, description="Optional chat session UUID for conversation memory")
    template_type: str = Field(default="explain", description="Template: explain, summary, quiz, flashcards, code_explanation, comparison, revision")
    document_ids: Optional[List[uuid.UUID]] = Field(default=None, description="Optional document filter UUIDs")


@router.post(
    "/search",
    status_code=status.HTTP_200_OK,
    summary="Execute dense semantic search and context assembly",
)
async def search_dense(
    payload: SearchRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """Executes multi-tenant dense vector similarity search and returns formatted context."""
    retriever = DenseRetriever()
    return await retriever.retrieve_dense(
        user_id=current_user.id,
        query_text=payload.query,
        document_ids=payload.document_ids,
        top_k=payload.top_k,
        session=session,
    )


@router.post(
    "/hybrid-search",
    status_code=status.HTTP_200_OK,
    summary="Execute hybrid search (Dense + BM25 + RRF Fusion + Redis Cache)",
)
async def search_hybrid(
    payload: SearchRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """Executes query processing, dense search, BM25 search, RRF fusion, and Redis caching."""
    retriever = HybridRetriever()
    return await retriever.retrieve_hybrid(
        user_id=current_user.id,
        query_text=payload.query,
        document_ids=payload.document_ids,
        session=session,
    )


@router.post(
    "/query",
    status_code=status.HTTP_200_OK,
    summary="Execute complete RAG LLM inference pipeline with citations and telemetry",
)
async def query_rag_llm(
    payload: RAGQueryRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Executes full grounded RAG pipeline:
    Question -> Memory -> Profile -> Prompt Builder -> LLM Gateway -> Citations -> Telemetry.
    """
    return await rag_orchestrator.execute_rag_pipeline(
        session=session,
        user_id=current_user.id,
        session_id=payload.session_id,
        question=payload.question,
        template_type=payload.template_type,
        document_ids=payload.document_ids,
    )


@router.post(
    "/stream",
    status_code=status.HTTP_200_OK,
    summary="Stream RAG response via Server-Sent Events (SSE)",
)
async def stream_rag_llm(
    payload: RAGQueryRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Streams RAG LLM response tokens asynchronously using Server-Sent Events (SSE).
    """
    generator = rag_orchestrator.execute_rag_stream(
        session=session,
        user_id=current_user.id,
        session_id=payload.session_id,
        question=payload.question,
        template_type=payload.template_type,
        document_ids=payload.document_ids,
    )
    return StreamingResponse(generator, media_type="text/event-stream")
