"""
Document Chunk SQLAlchemy Model.
Represents parent-child semantic text chunks extracted from uploaded documents.
Includes user_id for multi-tenant isolation, rich metadata JSON, and vector_id pointing to Qdrant.
"""

import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.database.mixins import UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from backend.database.models.document import Document


class DocumentChunk(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Extracted text chunk entity with rich metadata."""

    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign Key to parent Document",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign Key to User for multi-tenant vector/chunk isolation",
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Sequential index of chunk within document",
    )
    child_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Granular child text (~300 tokens) used for vector embedding",
    )
    parent_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Surrounding parent context (~1200 tokens) injected into LLM prompt",
    )
    vector_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
        index=True,
        doc="Pointer UUID to Qdrant vector point",
    )
    page_label: Mapped[str] = mapped_column(
        String(50),
        default="1",
        nullable=False,
        doc="Document page / slide label for source citation",
    )
    chunk_metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Rich metadata (heading path, section title, bbox, element types, timestamps)",
    )

    # Relationships
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="chunks",
    )

    def __repr__(self) -> str:
        return f"<DocumentChunk id={self.id} doc_id={self.document_id} index={self.chunk_index}>"
