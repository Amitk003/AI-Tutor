"""
Chunking Pipeline Stage.
Executes HierarchicalChunker to generate Parent-Child StructuredChunks with rich metadata.
"""

from loguru import logger
from backend.database.models.document import DocumentProcessingStatus
from backend.rag.chunker import HierarchicalChunker
from backend.rag.pipeline.context import IngestionContext
from backend.rag.pipeline.stage_base import PipelineStage


class ChunkStage(PipelineStage):
    """Executes semantic parent-child chunking stage."""

    def __init__(self, chunker: HierarchicalChunker = None):
        self.chunker = chunker or HierarchicalChunker()

    @property
    def name(self) -> str:
        return DocumentProcessingStatus.CHUNKING

    async def execute(self, ctx: IngestionContext) -> IngestionContext:
        logger.info("Executing CHUNKING stage: doc_id={id}", id=ctx.document_id)
        chunks = self.chunker.chunk_elements(ctx.elements)
        ctx.chunks = chunks
        ctx.current_stage = self.name
        return ctx
