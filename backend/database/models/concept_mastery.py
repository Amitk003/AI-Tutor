"""
Concept Mastery SQLAlchemy Model.
Tracks student concept mastery probability P(L) using Bayesian Knowledge Tracing (BKT).
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.database.mixins import UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from backend.database.models.user import User


class ConceptMastery(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Concept mastery state entity."""

    __tablename__ = "concept_mastery"

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
        doc="Name / topic label of concept",
    )
    mastery_prob: Mapped[float] = mapped_column(
        Float,
        default=0.1,
        nullable=False,
        doc="BKT probability of mastery P(L) between 0.0 and 1.0",
    )
    total_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Total questions attempted for this concept",
    )
    correct_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of correctly answered questions",
    )
    last_practiced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of last practice session",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="concept_masteries",
    )

    def __repr__(self) -> str:
        return f"<ConceptMastery user_id={self.user_id} concept='{self.concept_name}' P(L)={self.mastery_prob:.2f}>"
