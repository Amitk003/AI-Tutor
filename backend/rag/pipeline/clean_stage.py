"""
Text Cleaning & Normalization Pipeline Stage.
Strips headers/footers, repairs line breaks, and normalizes unicode text.
"""

from loguru import logger
from backend.database.models.document import DocumentProcessingStatus
from backend.rag.pipeline.context import IngestionContext
from backend.rag.pipeline.stage_base import PipelineStage
from backend.utils.helpers import sanitize_text


class CleanStage(PipelineStage):
    """Executes text normalization and cleaning stage."""

    @property
    def name(self) -> str:
        return DocumentProcessingStatus.CLEANING

    async def execute(self, ctx: IngestionContext) -> IngestionContext:
        logger.info("Executing CLEANING stage: doc_id={id} elements={count}", id=ctx.document_id, count=len(ctx.elements))
        cleaned_elements = []

        for elem in ctx.elements:
            cleaned_text = sanitize_text(elem.content)
            if cleaned_text:
                elem.content = cleaned_text
                cleaned_elements.append(elem)

        ctx.elements = cleaned_elements
        ctx.current_stage = self.name
        return ctx
