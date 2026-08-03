"""
Document Parsers Package Init.
"""

from backend.rag.parsers.base import BaseDocumentParser
from backend.rag.parsers.pdf_parser import PDFDocumentParser
from backend.rag.parsers.docx_parser import DOCXDocumentParser
from backend.rag.parsers.pptx_parser import PPTXDocumentParser
from backend.rag.parsers.txt_parser import TXTDocumentParser
from backend.rag.parsers.web_parser import WebDocumentParser
from backend.rag.parsers.registry import ParserRegistry, parser_registry

__all__ = [
    "BaseDocumentParser",
    "PDFDocumentParser",
    "DOCXDocumentParser",
    "PPTXDocumentParser",
    "TXTDocumentParser",
    "WebDocumentParser",
    "ParserRegistry",
    "parser_registry",
]
