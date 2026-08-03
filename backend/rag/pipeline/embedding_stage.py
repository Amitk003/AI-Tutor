"""
Embedding Pipeline Stage.
Generates batch vector embeddings for child chunk texts using BatchEmbeddingService.
Emits DocumentEmbeddedEvent.
"""

from loguru import logger
from backend.core.events import DocumentEmbeddedEvent, event_dispatcher
from backend.database.models.document import DocumentProcessingStatus
from backend.rag.embeddings import embedding_service, BatchEmbeddingService
from backend.rag.pipeline.context import IngestionContext
from backend.rag.pipeline.stage_base import PipelineStage


class EmbeddingStage(PipelineStage):
    """Executes batch vector embedding generation for chunks."""

    def __init__(self, embed_service: BatchEmbeddingService = None):
        self.embed_service = embed_service or embedding_service

    @property
    def name(self) -> str:
        return DocumentProcessingStatus.EMBEDDING

    async def execute(self, ctx: IngestionContext) -> IngestionContext:
        if not ctx.chunks:
            logger.warning("No chunks found for embedding in doc_id={id}", id=ctx.document_id)
            return ctx

        logger.info("Executing EMBEDDING stage for doc_id={id} chunks={count}", id=ctx.document_id, count=len(ctx.chunks))

        child_texts = [chunk.child_content for chunk in ctx.chunks]
        vectors = self.embed_service.embed_batch(child_texts, batch_size=32)

        ctx.metadata["vectors"] = vectors
        ctx.current_stage = self.name

        # Emit DocumentEmbeddedEvent
        await event_dispatcher.emit(
            DocumentEmbeddedEvent(
                document_id=ctx.document_id,
                vector_count=len(vectors),
                model_name=self.embed_service.model_name,
            )
        )

        return ctx
