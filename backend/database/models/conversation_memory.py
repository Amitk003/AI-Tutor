"""
Conversation Memory SQLAlchemy Model.
Stores rolling chat summaries and context window memory states for chat sessions.
"""

import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.database.mixins import UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from backend.database.models.chat import ChatSession


class ConversationMemory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Summarized conversation memory entity."""

    __tablename__ = "conversation_memories"

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        doc="Foreign Key to ChatSession",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign Key to User",
    )
    summary_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Rolling conversation summary text",
    )
    token_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Token count of summary text",
    )
    last_summarized_message_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        nullable=True,
        doc="Pointer to last processed ChatMessage UUID",
    )

    # Relationships
    session: Mapped["ChatSession"] = relationship(
        "ChatSession",
        back_populates="memory",
    )
