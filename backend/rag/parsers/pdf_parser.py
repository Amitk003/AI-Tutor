"""
PDF Layout Parser using PyMuPDF (fitz).
Extracts headings, paragraphs, tables, and page numbers while preserving visual hierarchy.
Detects scanned PDFs for OCR routing.
"""

import os
from typing import List
import fitz  # PyMuPDF
from loguru import logger

from backend.rag.parsers.base import BaseDocumentParser
from backend.rag.schemas import ElementType, ExtractedElement
from backend.utils.helpers import sanitize_text


class PDFDocumentParser(BaseDocumentParser):
    """Layout-aware PDF document parser."""

    def supports_extension(self, extension: str) -> bool:
        return extension.lower() in (".pdf",)

    async def parse(self, file_path: str) -> List[ExtractedElement]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found at path: {file_path}")

        elements: List[ExtractedElement] = []
        heading_path: List[str] = []

        try:
            doc = fitz.open(file_path)
            total_pages = len(doc)
            logger.info("Parsing PDF document: path={path} pages={pages}", path=file_path, pages=total_pages)

            # Check if PDF is scanned (low overall text count across pages)
            total_char_count = sum(len(page.get_text()) for page in doc)
            avg_chars_per_page = total_char_count / max(total_pages, 1)

            if avg_chars_per_page < 50:
                logger.warning("Scanned PDF detected (avg chars/page: {avg:.1f}). Flagging for OCR.", avg=avg_chars_per_page)
                return [
                    ExtractedElement(
                        element_type=ElementType.OCR_TEXT,
                        content="[SCANNED_PDF_REQUIRES_OCR]",
                        page_number=1,
                        heading_path=[],
                        metadata={"is_scanned": True, "avg_chars_per_page": avg_chars_per_page},
                    )
                ]

            for page_idx in range(total_pages):
                page = doc[page_idx]
                page_num = page_idx + 1
                page_label = f"Page {page_num}"

                # 1. Extract tables if available
                tables = []
                try:
                    tabs = page.find_tables()
                    for tab in tabs:
                        table_data = tab.extract()
                        if table_data:
                            table_text = self._format_table_as_markdown(table_data)
                            elements.append(
                                ExtractedElement(
                                    element_type=ElementType.TABLE,
                                    content=table_text,
                                    page_number=page_num,
                                    heading_path=list(heading_path),
                                    metadata={"page_label": page_label, "rows": len(table_data)},
                                )
                            )
                            tables.append(tab)
                except Exception as e:
                    logger.debug("Table detection skipped for page {num}: {err}", num=page_num, err=str(e))

                # 2. Extract text blocks and font sizes for heading detection
                blocks = page.get_text("dict")["blocks"]
                for block in blocks:
                    if block.get("type") == 0:  # Text block
                        for line in block.get("lines", []):
                            line_text = "".join(span.get("text", "") for span in line.get("spans", []))
                            line_text = sanitize_text(line_text)

                            if not line_text:
                                continue

                            # Detect max font size in line
                            font_sizes = [span.get("size", 10) for span in line.get("spans", [])]
                            max_font_size = max(font_sizes) if font_sizes else 10.0

                            # Classify heading vs paragraph based on font size threshold
                            if max_font_size >= 16.0:
                                element_type = ElementType.HEADING_1
                                heading_path = [line_text]
                            elif max_font_size >= 13.0:
                                element_type = ElementType.HEADING_2
                                if len(heading_path) > 0:
                                    heading_path = [heading_path[0], line_text]
                                else:
                                    heading_path = [line_text]
                            elif max_font_size >= 11.5:
                                element_type = ElementType.HEADING_3
                                heading_path.append(line_text)
                            else:
                                element_type = ElementType.PARAGRAPH

                            elements.append(
                                ExtractedElement(
                                    element_type=element_type,
                                    content=line_text,
                                    page_number=page_num,
                                    heading_path=list(heading_path),
                                    metadata={
                                        "page_label": page_label,
                                        "font_size": max_font_size,
                                    },
                                )
                            )

            doc.close()
            logger.info("PDF parsing complete: path={path} elements={count}", path=file_path, count=len(elements))
            return elements

        except Exception as e:
            logger.error("Failed to parse PDF file: path={path} error={err}", path=file_path, err=str(e))
            raise

    def _format_table_as_markdown(self, table_data: List[List[str]]) -> str:
        """Formats 2D table grid into markdown table string."""
        if not table_data:
            return ""
        lines = []
        # Header row
        header = " | ".join(str(cell or "").strip() for cell in table_data[0])
        lines.append(f"| {header} |")
        lines.append("| " + " | ".join("---" for _ in table_data[0]) + " |")
        # Body rows
        for row in table_data[1:]:
            row_str = " | ".join(str(cell or "").strip() for cell in row)
            lines.append(f"| {row_str} |")
        return "\n".join(lines)
