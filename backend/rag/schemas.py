"""
RAG Ingestion Schemas & Layout Element Data Models.
Defines layout element types, extracted document blocks, and structured chunks.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ElementType(str, Enum):
    """Document layout element types."""
    HEADING_1 = "HEADING_1"
    HEADING_2 = "HEADING_2"
    HEADING_3 = "HEADING_3"
    PARAGRAPH = "PARAGRAPH"
    TABLE = "TABLE"
    FIGURE = "FIGURE"
    CAPTION = "CAPTION"
    LIST_ITEM = "LIST_ITEM"
    HEADER_FOOTER = "HEADER_FOOTER"
    OCR_TEXT = "OCR_TEXT"


class ExtractedElement(BaseModel):
    """Single layout-preserved block extracted from a document."""

    element_type: ElementType = Field(..., description="Document element classification")
    content: str = Field(..., description="Raw or formatted text content")
    page_number: int = Field(default=1, description="1-based page or slide number")
    heading_path: List[str] = Field(default_factory=list, description="Hierarchical breadcrumb of parent headings")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Bounding box, font info, or table grid")


class StructuredChunk(BaseModel):
    """Parent-Child semantic chunk produced by chunking pipeline."""

    chunk_index: int = Field(..., description="Sequential chunk index within document")
    child_content: str = Field(..., description="Granular child text (~300 tokens) for vector search")
    parent_content: str = Field(..., description="Parent context (~1200 tokens) for LLM context injection")
    page_label: str = Field(default="1", description="Page or slide label for citations")
    heading_path: List[str] = Field(default_factory=list, description="Breadcrumb of section headers")
    section_title: str = Field(default="", description="Immediate parent section title")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Rich chunk metadata")
