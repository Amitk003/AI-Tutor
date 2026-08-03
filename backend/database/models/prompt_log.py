"""
Prompt Log SQLAlchemy Model.
Tracks LLM prompt transactions, system prompts, injected context, token counts, and latency.
"""

import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Float, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.database.mixins import UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from backend.database.models.user import User


class PromptLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """LLM inference prompt log entity."""

    __tablename__ = "prompt_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign Key to User",
    )
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Foreign Key to ChatSession",
    )
    model_name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Name of LLM model executed",
    )
    system_prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Synthesized system prompt containing pedagogical persona",
    )
    user_prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Raw user query text",
    )
    context_injected: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Retrieved document context injected into prompt",
    )
    response_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Generated LLM response text",
    )
    input_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Input prompt token count",
    )
    output_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Generated output token count",
    )
    latency_ms: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="Inference execution latency in milliseconds",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="prompt_logs",
    )

    def __repr__(self) -> str:
        return f"<PromptLog id={self.id} user_id={self.user_id} model='{self.model_name}' latency={self.latency_ms:.1f}ms>"
