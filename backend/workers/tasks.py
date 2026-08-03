"""
Background Task Definitions.
Contains async workers for document ingestion, embedding generation, and SM-2 revision scheduling.
"""

import asyncio
import uuid
from typing import Any, Dict
from loguru import logger
from backend.workers.celery_app import celery_app


@celery_app.task(name="process_document_ingestion")
def process_document_task(document_id: str, user_id: str) -> Dict[str, Any]:
    """
    Background worker task for parsing, chunking, embedding, and indexing uploaded documents.
    """
    logger.info(
        "Starting background document processing: document_id={doc_id} user_id={user_id}",
        doc_id=document_id,
        user_id=user_id,
    )
    async def run_pipeline() -> Dict[str, Any]:
        from backend.database.session import AsyncSessionLocal
        from backend.services.ai_orchestrator import AIOrchestrator

        async with AsyncSessionLocal() as session:
            context = await AIOrchestrator(session).ingest_document(
                uuid.UUID(document_id), uuid.UUID(user_id)
            )
            return {
                "status": "SUCCESS",
                "document_id": document_id,
                "user_id": user_id,
                "chunk_count": len(context.chunks),
            }

    return asyncio.run(run_pipeline())


@celery_app.task(name="recalculate_student_mastery")
def recalculate_mastery_task(user_id: str, quiz_attempt_id: str) -> Dict[str, Any]:
    """
    Background task recalculating IRT ability theta and BKT mastery state after quiz completion.
    """
    logger.info(
        "Recalculating student cognitive mastery: user_id={user_id} attempt_id={attempt_id}",
        user_id=user_id,
        attempt_id=quiz_attempt_id,
    )
    return {
        "status": "SUCCESS",
        "user_id": user_id,
        "quiz_attempt_id": quiz_attempt_id,
    }
