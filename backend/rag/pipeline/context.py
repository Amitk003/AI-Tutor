"""
Ingestion Pipeline Context.
Encapsulates current document processing state, extracted elements, chunks, and metadata.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.rag.schemas import ExtractedElement, StructuredChunk


@dataclass
class IngestionContext:
    """State context passed along event-driven pipeline stages."""

    document_id: uuid.UUID
    user_id: uuid.UUID
    file_path: str
    file_type: str
    current_stage: str = "UPLOADED"
    elements: List[ExtractedElement] = field(default_factory=list)
    chunks: List[StructuredChunk] = field(default_factory=list)
    is_scanned_pdf: bool = False
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
