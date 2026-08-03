"""
Chat Session and Chat Message SQLAlchemy Models.
Represents user interactive RAG chat history, message roles, and source citations.
"""

import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.database.mixins import UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from backend.database.models.user import User
    from backend.database.models.conversation_memory import ConversationMemory
    from backend.database.models.citation import Citation


class ChatSession(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Chat session container entity."""

    __tablename__ = "chat_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign Key to owning User for multi-tenant isolation",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        default="New Learning Session",
        nullable=False,
        doc="Chat session title",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="chat_sessions",
    )
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    memory: Mapped[Optional["ConversationMemory"]] = relationship(
        "ConversationMemory",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ChatSession id={self.id} user_id={self.user_id} title='{self.title}'>"


class ChatMessage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Individual chat message entity."""

    __tablename__ = "chat_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign Key to parent ChatSession",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign Key to User for multi-tenant isolation",
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Message role (user, assistant, system)",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Message text content",
    )

    # Relationships
    session: Mapped["ChatSession"] = relationship(
        "ChatSession",
        back_populates="messages",
    )
    citations: Mapped[List["Citation"]] = relationship(
        "Citation",
        back_populates="message",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ChatMessage id={self.id} session_id={self.session_id} role='{self.role}'>"
