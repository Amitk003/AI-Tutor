"""
Revision Schedule SQLAlchemy Model.
Tracks SuperMemo SM-2 spaced repetition revision dates, intervals, and ease factors.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.database.mixins import UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from backend.database.models.user import User


class RevisionSchedule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """SuperMemo SM-2 spaced repetition review item entity."""

    __tablename__ = "revision_schedule"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign Key to owning User for multi-tenant isolation",
    )
    concept_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Target concept name to revise",
    )
    scheduled_for: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Scheduled UTC revision timestamp",
    )
    interval_days: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        doc="SuperMemo SM-2 calculated review interval in days",
    )
    ease_factor: Mapped[float] = mapped_column(
        Float,
        default=2.5,
        nullable=False,
        doc="SuperMemo SM-2 ease factor EF (min 1.3)",
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether revision session was completed",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="revisions",
    )

    def __repr__(self) -> str:
        return f"<RevisionSchedule user_id={self.user_id} concept='{self.concept_name}' due={self.scheduled_for}>"
