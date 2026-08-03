"""
LLM Telemetry & Audit Logger.
Logs LLM generation telemetry (prompt/completion tokens, latency, model, temperature, confidence, refusal)
to PromptLog database table separately from chat history.
"""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.database.models.prompt_log import PromptLog


class LLMTelemetryLogger:
    """Logs LLM inference metrics to PostgreSQL database."""

    async def log_inference(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        session_id: Optional[uuid.UUID],
        prompt_text: str,
        response_text: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        model_name: str,
        provider_name: str,
        temperature: float,
        retrieval_confidence: float,
        is_refusal: bool,
        citation_count: int,
    ) -> PromptLog:
        """
        Persists LLM inference telemetry record into PromptLog table.
        """
        log_entry = PromptLog(
            user_id=user_id,
            session_id=session_id,
            system_prompt=prompt_text[:1000],  # Truncated snapshot
            user_prompt=prompt_text[-500:],
            response_text=response_text[:2000],
            model_name=f"{provider_name}:{model_name}",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=latency_ms,
            temperature=temperature,
            status_code=400 if is_refusal else 200,
        )

        session.add(log_entry)
        await session.commit()

        logger.info(
            "Telemetry logged: user_id={uid} model={m} tokens={toks} latency={lat:.1f}ms refusal={ref} citations={cits}",
            uid=user_id,
            m=model_name,
            toks=prompt_tokens + completion_tokens,
            lat=latency_ms,
            ref=is_refusal,
            cits=citation_count,
        )
        return log_entry


# Global telemetry logger singleton
telemetry_logger = LLMTelemetryLogger()
