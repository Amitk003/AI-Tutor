"""
Parsing Pipeline Stage.
Resolves parser from ParserRegistry and extracts layout elements.
"""

from loguru import logger
from backend.database.models.document import DocumentProcessingStatus
from backend.rag.parsers.registry import parser_registry
from backend.rag.pipeline.context import IngestionContext
from backend.rag.pipeline.stage_base import PipelineStage
from backend.rag.schemas import ElementType


class ParseStage(PipelineStage):
    """Executes format-specific parsing stage."""

    @property
    def name(self) -> str:
        return DocumentProcessingStatus.PARSING

    async def execute(self, ctx: IngestionContext) -> IngestionContext:
        logger.info("Executing PARSING stage: doc_id={id} path={path}", id=ctx.document_id, path=ctx.file_path)
        parser = parser_registry.get_parser(ctx.file_path)
        elements = await parser.parse(ctx.file_path)

        # Check if scanned PDF flag returned
        if elements and elements[0].element_type == ElementType.OCR_TEXT and elements[0].content == "[SCANNED_PDF_REQUIRES_OCR]":
            ctx.is_scanned_pdf = True
            logger.info("PARSING stage detected scanned PDF flag for doc_id={id}", id=ctx.document_id)
        else:
            ctx.elements = elements

        ctx.current_stage = self.name
        return ctx
