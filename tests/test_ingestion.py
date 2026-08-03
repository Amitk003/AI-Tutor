"""
Universal Document Ingestion Pipeline Unit Tests.
Verifies multi-format parser resolution, layout element extraction, Parent-Child chunking,
rich metadata attachment, and AIOrchestrator pipeline execution.
"""

import os
import tempfile
import uuid
import pytest

from backend.rag.schemas import ElementType, ExtractedElement
from backend.rag.parsers.registry import parser_registry, ParserRegistry
from backend.rag.parsers.pdf_parser import PDFDocumentParser
from backend.rag.parsers.docx_parser import DOCXDocumentParser
from backend.rag.parsers.pptx_parser import PPTXDocumentParser
from backend.rag.parsers.txt_parser import TXTDocumentParser
from backend.rag.parsers.web_parser import WebDocumentParser
from backend.rag.chunker import HierarchicalChunker
from backend.core.exceptions import ValidationException


def test_parser_registry_resolution():
    """Verify ParserRegistry resolves appropriate parsers for supported file types."""
    pdf_parser = parser_registry.get_parser("document.pdf")
    assert isinstance(pdf_parser, PDFDocumentParser)

    docx_parser = parser_registry.get_parser("report.docx")
    assert isinstance(docx_parser, DOCXDocumentParser)

    pptx_parser = parser_registry.get_parser("slides.pptx")
    assert isinstance(pptx_parser, PPTXDocumentParser)

    txt_parser = parser_registry.get_parser("notes.txt")
    assert isinstance(txt_parser, TXTDocumentParser)

    md_parser = parser_registry.get_parser("README.md")
    assert isinstance(md_parser, TXTDocumentParser)

    web_parser = parser_registry.get_parser("https://example.com/article")
    assert isinstance(web_parser, WebDocumentParser)


def test_parser_registry_unsupported_format():
    """Verify registry raises ValidationException for unsupported file extensions."""
    with pytest.raises(ValidationException):
        parser_registry.get_parser("unsupported_file.xyz")


@pytest.mark.asyncio
async def test_txt_parser_heading_and_paragraph_extraction():
    """Verify TXTDocumentParser extracts Markdown headings and paragraphs."""
    content = "# Chapter 1: Introduction\n\nThis is a test paragraph.\n\n## Section 1.1: Scope\n\nScope paragraph details."
    
    with tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False, encoding="utf-8") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        parser = TXTDocumentParser()
        elements = await parser.parse(tmp_path)

        assert len(elements) >= 4
        assert elements[0].element_type == ElementType.HEADING_1
        assert elements[0].content == "Chapter 1: Introduction"

        assert elements[1].element_type == ElementType.PARAGRAPH
        assert "test paragraph" in elements[1].content
        assert elements[1].heading_path == ["Chapter 1: Introduction"]

        assert elements[2].element_type == ElementType.HEADING_2
        assert elements[2].content == "Section 1.1: Scope"

        assert elements[3].element_type == ElementType.PARAGRAPH
        assert elements[3].heading_path == ["Chapter 1: Introduction", "Section 1.1: Scope"]
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_hierarchical_chunker_parent_child_linking():
    """Verify HierarchicalChunker generates linked child and parent context chunks."""
    elements = [
        ExtractedElement(
            element_type=ElementType.HEADING_1,
            content="Chapter 1: Optimization Algorithms",
            page_number=1,
            heading_path=["Chapter 1: Optimization Algorithms"],
        ),
        ExtractedElement(
            element_type=ElementType.PARAGRAPH,
            content="Gradient descent is an optimization algorithm used to minimize loss functions in machine learning models. " * 15,
            page_number=1,
            heading_path=["Chapter 1: Optimization Algorithms"],
        ),
        ExtractedElement(
            element_type=ElementType.PARAGRAPH,
            content="Backpropagation computes partial derivatives using calculus chain rule. " * 15,
            page_number=2,
            heading_path=["Chapter 1: Optimization Algorithms", "Section 1.1: Backpropagation"],
        ),
    ]

    chunker = HierarchicalChunker(target_child_chars=500, target_parent_chars=2000, overlap_chars=50)
    chunks = chunker.chunk_elements(elements)

    assert len(chunks) > 0
    first_chunk = chunks[0]
    assert first_chunk.chunk_index == 0
    assert len(first_chunk.child_content) > 0
    assert len(first_chunk.parent_content) >= len(first_chunk.child_content)
    assert first_chunk.section_title != ""
    assert "start_page" in first_chunk.metadata
