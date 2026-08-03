"""
Ingestion Pipeline Runner & Resumable State Machine Orchestrator.
Executes sequence of pipeline stages (Parse, OCR, Clean, Chunk, Embed, Index),
updates document status in DB checkpointing, and emits domain events.
"""

import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.core.events import (
    DocumentChunkedEvent,
    DocumentFailedEvent,
    DocumentParsedEvent,
    event_dispatcher,
)
from backend.database.models.document import Document, DocumentProcessingStatus
from backend.database.models.document_chunk import DocumentChunk
from backend.database.repositories.document_repository import DocumentRepository
from backend.rag.pipeline.clean_stage import CleanStage
from backend.rag.pipeline.context import IngestionContext
from backend.rag.pipeline.ocr_stage import OCRStage
from backend.rag.pipeline.parse_stage import ParseStage
from backend.rag.pipeline.chunk_stage import ChunkStage
from backend.rag.pipeline.embedding_stage import EmbeddingStage
from backend.rag.pipeline.indexing_stage import IndexingStage
from backend.rag.pipeline.stage_base import PipelineStage


class IngestionPipelineRunner:
    """Orchestrates document ingestion, embedding, and vector indexing stages."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.stages: List[PipelineStage] = [
            ParseStage(),
            OCRStage(),
            CleanStage(),
            ChunkStage(),
            EmbeddingStage(),
            IndexingStage(),
        ]

    async def run(self, document_id: uuid.UUID, user_id: uuid.UUID) -> IngestionContext:
        """
        Executes complete ingestion, embedding, and indexing pipeline.
        Checkpointing state machine transitions in database.
        """
        doc = await self.doc_repo.get_by_id(document_id, user_id=user_id)
        if not doc:
            raise ValueError(f"Document with ID '{document_id}' not found.")

        ctx = IngestionContext(
            document_id=doc.id,
            user_id=doc.user_id,
            file_path=doc.file_path,
            file_type=doc.file_type,
            current_stage=doc.status,
        )

        logger.info(
            "Starting ingestion, embedding & indexing pipeline: doc_id={id} initial_status={status}",
            id=doc.id,
            status=doc.status,
        )

        try:
            for stage in self.stages:
                # Update DB checkpoint
                doc.status = stage.name
                await self.session.commit()
                logger.info("Pipeline checkpoint: doc_id={id} status={status}", id=doc.id, status=stage.name)

                # Execute stage logic
                ctx = await stage.execute(ctx)

                # Emit specific events after key stages
                if stage.name == DocumentProcessingStatus.PARSING:
                    await event_dispatcher.emit(
                        DocumentParsedEvent(document_id=doc.id, element_count=len(ctx.elements))
                    )
                elif stage.name == DocumentProcessingStatus.CHUNKING:
                    await event_dispatcher.emit(
                        DocumentChunkedEvent(document_id=doc.id, chunk_count=len(ctx.chunks))
                    )

            # Persist extracted chunks and vector pointers to database
            logger.info("Persisting {count} chunks to PostgreSQL...", count=len(ctx.chunks))
            vectors = ctx.metadata.get("vectors", [])

            for idx, chunk_data in enumerate(ctx.chunks):
                vector_id = uuid.UUID(str(chunk_data.metadata["vector_id"]))

                db_chunk = DocumentChunk(
                    document_id=doc.id,
                    user_id=doc.user_id,
                    chunk_index=chunk_data.chunk_index,
                    child_content=chunk_data.child_content,
                    parent_content=chunk_data.parent_content,
                    vector_id=vector_id,
                    page_label=chunk_data.page_label,
                    chunk_metadata_json=chunk_data.metadata,
                )
                self.session.add(db_chunk)

            # Mark Document as READY and set indexed_at timestamp
            import datetime
            doc.chunk_count = len(ctx.chunks)
            doc.status = DocumentProcessingStatus.READY
            doc.indexed_at = datetime.datetime.now(datetime.timezone.utc)
            await self.session.commit()

            logger.info(
                "Ingestion, embedding & indexing completed successfully: doc_id={id} chunks={count}",
                id=doc.id,
                count=len(ctx.chunks),
            )
            return ctx

        except Exception as exc:
            logger.exception("Pipeline failed: doc_id={id} error={err}", id=doc.id, err=str(exc))
            doc.status = DocumentProcessingStatus.FAILED
            await self.session.commit()

            await event_dispatcher.emit(
                DocumentFailedEvent(document_id=doc.id, error_message=str(exc))
            )
            ctx.error_message = str(exc)
            ctx.current_stage = DocumentProcessingStatus.FAILED
            raise
