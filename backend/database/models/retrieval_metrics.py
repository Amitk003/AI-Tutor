"""
Retrieval Metrics SQLAlchemy Model.
Tracks vector search performance, candidate counts, top rerank scores, and threshold refusals.
"""

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.database.mixins import UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from backend.database.models.user import User


class RetrievalMetric(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Vector retrieval metric entity."""

    __tablename__ = "retrieval_metrics"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign Key to User",
    )
    query_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="User query string",
    )
    retrieved_candidate_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of candidate vector matches retrieved",
    )
    top_rerank_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="Highest relevance score from cross-encoder reranker",
    )
    confidence_threshold_met: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether top rerank score met confidence threshold (tau >= 0.35)",
    )
    retrieval_latency_ms: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="Total retrieval & reranking latency in milliseconds",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="retrieval_metrics",
    )

    def __repr__(self) -> str:
        return f"<RetrievalMetric query='{self.query_text[:20]}' top_score={self.top_rerank_score:.3f} threshold_met={self.confidence_threshold_met}>"
