"""
Document SQLAlchemy Model.
Represents uploaded student study materials with SHA-256 hash deduplication,
expanded processing state machine stages, and embedding metadata versioning.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.database.mixins import UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from backend.database.models.user import User
    from backend.database.models.document_chunk import DocumentChunk
    from backend.database.models.quiz import Quiz


class DocumentProcessingStatus:
    """Explicit resumable document ingestion state machine stages."""
    UPLOADED = "UPLOADED"
    PARSING = "PARSING"
    OCR = "OCR"
    CLEANING = "CLEANING"
    CHUNKING = "CHUNKING"
    EMBEDDING = "EMBEDDING"
    INDEXING = "INDEXING"
    READY = "READY"
    FAILED = "FAILED"


class Document(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Uploaded study material document entity with embedding versioning and SHA-256 hash deduplication."""

    __tablename__ = "documents"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign Key to owning User for multi-tenant isolation",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Document display title",
    )
    file_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="File extension / format (PDF, DOCX, PPTX, TXT, URL)",
    )
    file_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Local or S3 storage path",
    )
    file_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        doc="SHA-256 hash checksum for duplicate document detection",
    )
    file_size_bytes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="File size in bytes",
    )
    chunk_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of extracted parent-child chunks",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default=DocumentProcessingStatus.UPLOADED,
        nullable=False,
        index=True,
        doc="Resumable status: UPLOADED, PARSING, OCR, CLEANING, CHUNKING, EMBEDDING, INDEXING, READY, FAILED",
    )

    # Embedding Metadata Versioning
    embedding_model_name: Mapped[str] = mapped_column(
        String(100),
        default="BAAI/bge-small-en-v1.5",
        nullable=False,
        doc="Name of sentence transformer embedding model used",
    )
    embedding_dimension: Mapped[int] = mapped_column(
        Integer,
        default=384,
        nullable=False,
        doc="Vector embedding dimensions (e.g. 384d, 1024d)",
    )
    chunking_strategy_version: Mapped[str] = mapped_column(
        String(50),
        default="v1.0-parent-child",
        nullable=False,
        doc="Version of chunking algorithm used",
    )
    indexed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when vector indexing completed",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="documents",
    )
    chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    quizzes: Mapped[List["Quiz"]] = relationship(
        "Quiz",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} title='{self.title}' status='{self.status}' hash='{self.file_hash[:8] if self.file_hash else 'none'}'>"
