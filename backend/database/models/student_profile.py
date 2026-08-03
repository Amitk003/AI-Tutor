"""
Student Profile, Preferences, Statistics, and Learning State SQLAlchemy Models.
Splits cognitive and behavioral student data into maintainable sub-entities.
"""

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.database.mixins import UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from backend.database.models.user import User


class StudentProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Core student profile entity."""

    __tablename__ = "student_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        doc="Foreign Key to User",
    )
    bio: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
        doc="Student bio / self-description",
    )
    grade_level: Mapped[str] = mapped_column(
        String(100),
        default="Undergraduate",
        nullable=False,
        doc="Academic grade level / track",
    )
    avatar_url: Mapped[str] = mapped_column(
        String(500),
        default="",
        nullable=False,
        doc="Profile avatar image URL",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="profile",
    )

    def __repr__(self) -> str:
        return f"<StudentProfile user_id={self.user_id} grade='{self.grade_level}'>"


class StudentPreferences(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Student pedagogical and UI preferences."""

    __tablename__ = "student_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        doc="Foreign Key to User",
    )
    preferred_explanation_style: Mapped[str] = mapped_column(
        String(50),
        default="Academic",
        nullable=False,
        doc="Explanation style (Socratic, Analogical, Academic, ELI5)",
    )
    preferred_language: Mapped[str] = mapped_column(
        String(10),
        default="en",
        nullable=False,
        doc="ISO language code",
    )
    theme: Mapped[str] = mapped_column(
        String(20),
        default="dark",
        nullable=False,
        doc="UI theme preference (dark, light, system)",
    )
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Spaced repetition notification alerts toggle",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="preferences",
    )


class StudentStatistics(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Aggregate learning analytics and activity statistics."""

    __tablename__ = "student_statistics"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        doc="Foreign Key to User",
    )
    total_study_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Total cumulative study time in seconds",
    )
    documents_uploaded_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Count of uploaded study materials",
    )
    quizzes_completed_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Count of completed quizzes",
    )
    questions_answered_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Count of total quiz items answered",
    )
    overall_accuracy_rate: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="Cumulative quiz accuracy percentage",
    )
    learning_streak_days: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Active daily study streak in days",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="statistics",
    )


class StudentLearningState(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """IRT ability level theta and dynamic cognitive state parameters."""

    __tablename__ = "student_learning_state"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        doc="Foreign Key to User",
    )
    ability_theta: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="Item Response Theory latent ability parameter (-3.0 to +3.0)",
    )
    cognitive_load_capacity: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
        doc="Estimated cognitive load capacity factor",
    )
    current_focus_topic: Mapped[str] = mapped_column(
        String(255),
        default="",
        nullable=False,
        doc="Current topic of active study focus",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="learning_state",
    )
