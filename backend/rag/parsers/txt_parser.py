"""
Plain Text and Markdown Layout Parser.
Extracts headings (via Markdown # syntax) and paragraphs from plain text files.
"""

import os
from typing import List
from loguru import logger

from backend.rag.parsers.base import BaseDocumentParser
from backend.rag.schemas import ElementType, ExtractedElement
from backend.utils.helpers import sanitize_text


class TXTDocumentParser(BaseDocumentParser):
    """Plain text and markdown document parser."""

    def supports_extension(self, extension: str) -> bool:
        return extension.lower() in (".txt", ".md", ".markdown")

    async def parse(self, file_path: str) -> List[ExtractedElement]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Text file not found at path: {file_path}")

        elements: List[ExtractedElement] = []
        heading_path: List[str] = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            logger.info("Parsing TXT/Markdown file: path={path} lines={count}", path=file_path, count=len(lines))

            current_paragraph: List[str] = []

            for line in lines:
                stripped = line.strip()
                if not stripped:
                    if current_paragraph:
                        para_text = sanitize_text(" ".join(current_paragraph))
                        if para_text:
                            elements.append(
                                ExtractedElement(
                                    element_type=ElementType.PARAGRAPH,
                                    content=para_text,
                                    page_number=1,
                                    heading_path=list(heading_path),
                                )
                            )
                        current_paragraph = []
                    continue

                # Markdown heading syntax detection
                if stripped.startswith("# "):
                    if current_paragraph:
                        elements.append(
                            ExtractedElement(
                                element_type=ElementType.PARAGRAPH,
                                content=sanitize_text(" ".join(current_paragraph)),
                                page_number=1,
                                heading_path=list(heading_path),
                            )
                        )
                        current_paragraph = []

                    title = sanitize_text(stripped[2:])
                    heading_path = [title]
                    elements.append(
                        ExtractedElement(
                            element_type=ElementType.HEADING_1,
                            content=title,
                            page_number=1,
                            heading_path=list(heading_path),
                        )
                    )
                elif stripped.startswith("## "):
                    if current_paragraph:
                        elements.append(
                            ExtractedElement(
                                element_type=ElementType.PARAGRAPH,
                                content=sanitize_text(" ".join(current_paragraph)),
                                page_number=1,
                                heading_path=list(heading_path),
                            )
                        )
                        current_paragraph = []

                    title = sanitize_text(stripped[3:])
                    heading_path = [heading_path[0], title] if heading_path else [title]
                    elements.append(
                        ExtractedElement(
                            element_type=ElementType.HEADING_2,
                            content=title,
                            page_number=1,
                            heading_path=list(heading_path),
                        )
                    )
                else:
                    current_paragraph.append(stripped)

            if current_paragraph:
                elements.append(
                    ExtractedElement(
                        element_type=ElementType.PARAGRAPH,
                        content=sanitize_text(" ".join(current_paragraph)),
                        page_number=1,
                        heading_path=list(heading_path),
                    )
                )

            logger.info("TXT parsing complete: path={path} elements={count}", path=file_path, count=len(elements))
            return elements
        except Exception as e:
            logger.error("Failed to parse TXT file: path={path} error={err}", path=file_path, err=str(e))
            raise
