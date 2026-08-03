"""
Complete RAG & LLM Inference Pipeline Orchestrator.
Orchestrates Question -> Conversation Memory -> Student Profile -> Prompt Builder -> LLM Gateway -> Response -> Citations -> Telemetry.
"""

import time
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.core.config import settings
from backend.database.models.student_profile import StudentProfile, StudentPreferences
from backend.database.repositories.user_repository import UserRepository
from backend.llm.gateway import LLMGatewayFactory
from backend.llm.memory_manager import MemoryManager
from backend.llm.prompt_builder import prompt_builder
from backend.llm.telemetry import telemetry_logger
from backend.llm.token_budget import count_tokens
from backend.rag.hybrid_retriever import hybrid_retriever


class RAGInferenceOrchestrator:
    """Complete grounded RAG inference orchestrator."""

    async def execute_rag_pipeline(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        session_id: Optional[uuid.UUID],
        question: str,
        template_type: str = "explain",
        document_ids: Optional[List[uuid.UUID]] = None,
    ) -> Dict[str, Any]:
        """
        Executes complete non-streaming RAG pipeline.
        """
        start_time = time.perf_counter()

        # 1. Fetch Conversation Memory
        mem_manager = MemoryManager(session)
        conversation_memory = ""
        if session_id:
            conversation_memory = await mem_manager.build_memory_context(session_id, user_id)

        # 2. Fetch Student Profile / Preferences (Grade level & explanation style defaults)
        grade_level = "Undergraduate"
        explanation_style = "Academic"

        # 3. Execute Hybrid Retrieval & Reranking
        retrieval_result = await hybrid_retriever.retrieve_hybrid(
            user_id=user_id,
            query_text=question,
            document_ids=document_ids,
            session=session,
        )

        # 4. Refusal Check (Confidence Guardrail)
        if retrieval_result.get("is_refusal", False):
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            refusal_text = retrieval_result["refusal_reason"]

            await telemetry_logger.log_inference(
                session=session,
                user_id=user_id,
                session_id=session_id,
                prompt_text=question,
                response_text=refusal_text,
                prompt_tokens=count_tokens(question),
                completion_tokens=count_tokens(refusal_text),
                latency_ms=latency_ms,
                model_name=settings.OLLAMA_MODEL_NAME,
                provider_name=settings.DEFAULT_LLM_PROVIDER,
                temperature=settings.LLM_TEMPERATURE,
                retrieval_confidence=retrieval_result.get("confidence_score", 0.0),
                is_refusal=True,
                citation_count=0,
            )

            return {
                "answer": refusal_text,
                "is_refusal": True,
                "confidence_score": retrieval_result.get("confidence_score", 0.0),
                "citations": [],
                "latency_ms": latency_ms,
            }

        # 5. Build Sanitized Modular Prompt
        prompt = prompt_builder.build_prompt(
            template_type=template_type,
            user_question=question,
            retrieved_context=retrieval_result["formatted_context"],
            conversation_memory=conversation_memory,
            grade_level=grade_level,
            explanation_style=explanation_style,
        )

        # 6. Execute LLM Gateway Generation
        gateway = LLMGatewayFactory.get_gateway()
        answer = await gateway.generate(prompt=prompt)

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        prompt_toks = count_tokens(prompt)
        comp_toks = count_tokens(answer)

        # 7. Log Telemetry
        await telemetry_logger.log_inference(
            session=session,
            user_id=user_id,
            session_id=session_id,
            prompt_text=prompt,
            response_text=answer,
            prompt_tokens=prompt_toks,
            completion_tokens=comp_toks,
            latency_ms=latency_ms,
            model_name=gateway.model_name,
            provider_name=gateway.provider_name,
            temperature=settings.LLM_TEMPERATURE,
            retrieval_confidence=retrieval_result.get("confidence_score", 0.0),
            is_refusal=False,
            citation_count=len(retrieval_result["citations"]),
        )

        return {
            "answer": answer,
            "is_refusal": False,
            "confidence_score": retrieval_result.get("confidence_score", 0.0),
            "citations": retrieval_result["citations"],
            "prompt_tokens": prompt_toks,
            "completion_tokens": comp_toks,
            "latency_ms": round(latency_ms, 2),
            "model": f"{gateway.provider_name}:{gateway.model_name}",
        }

    async def execute_rag_stream(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        session_id: Optional[uuid.UUID],
        question: str,
        template_type: str = "explain",
        document_ids: Optional[List[uuid.UUID]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Executes streaming RAG pipeline yielding SSE token chunks.
        """
        mem_manager = MemoryManager(session)
        conversation_memory = ""
        if session_id:
            conversation_memory = await mem_manager.build_memory_context(session_id, user_id)

        retrieval_result = await hybrid_retriever.retrieve_hybrid(
            user_id=user_id,
            query_text=question,
            document_ids=document_ids,
            session=session,
        )

        if retrieval_result.get("is_refusal", False):
            yield f"data: {retrieval_result['refusal_reason']}\n\n"
            return

        prompt = prompt_builder.build_prompt(
            template_type=template_type,
            user_question=question,
            retrieved_context=retrieval_result["formatted_context"],
            conversation_memory=conversation_memory,
        )

        gateway = LLMGatewayFactory.get_gateway()
        async for chunk in gateway.stream(prompt=prompt):
            yield f"data: {chunk}\n\n"


# Global RAG inference orchestrator singleton
rag_orchestrator = RAGInferenceOrchestrator()
