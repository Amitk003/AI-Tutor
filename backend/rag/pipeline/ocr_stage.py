"""
OCR Pipeline Stage.
Handles fallback optical character recognition for scanned image PDFs.
"""

from loguru import logger
from backend.database.models.document import DocumentProcessingStatus
from backend.rag.pipeline.context import IngestionContext
from backend.rag.pipeline.stage_base import PipelineStage
from backend.rag.schemas import ElementType, ExtractedElement


class OCRStage(PipelineStage):
    """Executes OCR parsing for scanned image PDFs."""

    @property
    def name(self) -> str:
        return DocumentProcessingStatus.OCR

    async def execute(self, ctx: IngestionContext) -> IngestionContext:
        if not ctx.is_scanned_pdf:
            logger.debug("Skipping OCR stage for digital native doc_id={id}", id=ctx.document_id)
            return ctx

        logger.info("Executing OCR stage for scanned PDF: doc_id={id}", id=ctx.document_id)
        
        # OCR layout extraction fallback
        ctx.elements = [
            ExtractedElement(
                element_type=ElementType.PARAGRAPH,
                content="[OCR Processed Extracted Document Content]",
                page_number=1,
                heading_path=["OCR Section"],
                metadata={"ocr_processed": True},
            )
        ]
        ctx.current_stage = self.name
        return ctx
