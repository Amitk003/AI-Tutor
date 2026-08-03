"""
Document Parser Registry.
Maintains singletons of format-specific document parsers and resolves appropriate parser by file extension.
"""

import os
from typing import Dict, List, Type
from loguru import logger

from backend.core.exceptions import ValidationException
from backend.rag.parsers.base import BaseDocumentParser
from backend.rag.parsers.pdf_parser import PDFDocumentParser
from backend.rag.parsers.docx_parser import DOCXDocumentParser
from backend.rag.parsers.pptx_parser import PPTXDocumentParser
from backend.rag.parsers.txt_parser import TXTDocumentParser
from backend.rag.parsers.web_parser import WebDocumentParser


class ParserRegistry:
    """Factory and registry for format-specific document parsers."""

    def __init__(self):
        self._parsers: List[BaseDocumentParser] = [
            PDFDocumentParser(),
            DOCXDocumentParser(),
            PPTXDocumentParser(),
            TXTDocumentParser(),
            WebDocumentParser(),
        ]

    def register_parser(self, parser: BaseDocumentParser) -> None:
        """Registers a custom document parser implementation."""
        self._parsers.append(parser)

    def get_parser(self, file_path_or_ext: str) -> BaseDocumentParser:
        """
        Resolves registered parser matching given file path or extension.
        Raises ValidationException if unsupported format.
        """
        if file_path_or_ext.startswith("http://") or file_path_or_ext.startswith("https://"):
            ext = "url"
        else:
            _, ext = os.path.splitext(file_path_or_ext.lower())

        for parser in self._parsers:
            if parser.supports_extension(ext):
                return parser

        raise ValidationException(f"No document parser registered for format '{ext}'.")


# Global parser registry instance
parser_registry = ParserRegistry()
