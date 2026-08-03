"""
AI Orchestrator Service.
Central coordinator service managing document ingestion, SHA-256 deduplication,
batch vector embedding, Qdrant indexing, and domain events.
"""

import hashlib
import os
import uuid
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.core.events import DocumentUploadedEvent, event_dispatcher
from backend.database.models.document import Document
from backend.database.repositories.document_repository import DocumentRepository
from backend.rag.pipeline.context import IngestionContext
from backend.rag.pipeline.runner import IngestionPipelineRunner


def compute_file_sha256(file_path: str) -> str:
    """Computes SHA-256 hash checksum of file for deduplication."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


class AIOrchestrator:
    """Central AI orchestrator managing document pipeline and domain events."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.pipeline_runner = IngestionPipelineRunner(session)

    async def register_uploaded_document(
        self,
        user_id: uuid.UUID,
        title: str,
        file_type: str,
        file_path: str,
        file_size_bytes: int,
    ) -> Document:
        """
        Calculates SHA-256 hash, checks for duplicate document owned by user,
        creates Document record, and emits DocumentUploadedEvent.
        """
        # Calculate SHA-256 hash if file exists on disk
        file_hash = compute_file_sha256(file_path) if os.path.exists(file_path) else None

        if file_hash:
            existing = await self.doc_repo.get_by_hash(user_id=user_id, file_hash=file_hash)
            if existing:
                logger.info("Duplicate document detected for user: doc_id={id} hash={hash}", id=existing.id, hash=file_hash[:8])
                return existing

        doc = Document(
            id=uuid.uuid4(),
            user_id=user_id,
            title=title,
            file_type=file_type.upper(),
            file_path=file_path,
            file_size_bytes=file_size_bytes,
            file_hash=file_hash,
            status="UPLOADED",
        )
        self.session.add(doc)
        await self.session.commit()
        await self.session.refresh(doc)

        # Emit DocumentUploadedEvent
        await event_dispatcher.emit(
            DocumentUploadedEvent(
                document_id=doc.id,
                user_id=user_id,
                file_path=file_path,
                file_hash=file_hash or "",
            )
        )

        return doc

    async def ingest_document(self, document_id: uuid.UUID, user_id: uuid.UUID) -> IngestionContext:
        """
        Orchestrates universal document ingestion, embedding, and vector indexing pipeline.
        """
        logger.info("AIOrchestrator initiating ingestion, embedding & indexing: doc_id={id}", id=document_id)
        return await self.pipeline_runner.run(document_id, user_id)

    async def resume_ingestion(self, document_id: uuid.UUID, user_id: uuid.UUID) -> IngestionContext:
        """Resumes a failed or interrupted document pipeline from checkpoint."""
        logger.info("AIOrchestrator resuming pipeline: doc_id={id}", id=document_id)
        return await self.pipeline_runner.run(document_id, user_id)
