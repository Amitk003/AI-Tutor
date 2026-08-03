"""
Citation SQLAlchemy Model.
Normalized table linking ChatMessage to DocumentChunk and Document with score and snippet details.
"""

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.database.mixins import UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from backend.database.models.chat import ChatMessage
    from backend.database.models.document import Document
    from backend.database.models.document_chunk import DocumentChunk


class Citation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Normalized document chunk citation entity."""

    __tablename__ = "citations"

    message_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign Key to parent ChatMessage",
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign Key to cited Document",
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_chunks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign Key to cited DocumentChunk",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign Key to owning User for tenant isolation",
    )
    page_label: Mapped[str] = mapped_column(
        String(50),
        default="1",
        nullable=False,
        doc="Page / slide number label",
    )
    similarity_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Retrieval reranker relevance score",
    )
    snippet_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Cited text snippet excerpt",
    )

    # Relationships
    message: Mapped["ChatMessage"] = relationship(
        "ChatMessage",
        back_populates="citations",
    )

    def __repr__(self) -> str:
        return f"<Citation id={self.id} msg_id={self.message_id} page='{self.page_label}' score={self.similarity_score:.3f}>"
