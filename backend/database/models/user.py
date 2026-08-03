"""
User SQLAlchemy Model.
Represents user credentials, system role, and authentication status.
"""

import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.database.mixins import UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from backend.database.models.student_profile import (
        StudentProfile,
        StudentPreferences,
        StudentStatistics,
        StudentLearningState,
    )
    from backend.database.models.document import Document
    from backend.database.models.chat import ChatSession
    from backend.database.models.concept_mastery import ConceptMastery
    from backend.database.models.quiz import QuizAttempt
    from backend.database.models.revision_schedule import RevisionSchedule
    from backend.database.models.audit_log import AuditLog
    from backend.database.models.prompt_log import PromptLog
    from backend.database.models.retrieval_metrics import RetrievalMetric


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """User account entity."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="User unique email address",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Bcrypt hashed password",
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="User full display name",
    )
    role: Mapped[str] = mapped_column(
        String(50),
        default="student",
        nullable=False,
        doc="User role (student, educator, admin)",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Account activation status",
    )

    # Relationships
    profile: Mapped[Optional["StudentProfile"]] = relationship(
        "StudentProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    preferences: Mapped[Optional["StudentPreferences"]] = relationship(
        "StudentPreferences",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    statistics: Mapped[Optional["StudentStatistics"]] = relationship(
        "StudentStatistics",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    learning_state: Mapped[Optional["StudentLearningState"]] = relationship(
        "StudentLearningState",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    chat_sessions: Mapped[List["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    concept_masteries: Mapped[List["ConceptMastery"]] = relationship(
        "ConceptMastery",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    quiz_attempts: Mapped[List["QuizAttempt"]] = relationship(
        "QuizAttempt",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    revisions: Mapped[List["RevisionSchedule"]] = relationship(
        "RevisionSchedule",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    prompt_logs: Mapped[List["PromptLog"]] = relationship(
        "PromptLog",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    retrieval_metrics: Mapped[List["RetrievalMetric"]] = relationship(
        "RetrievalMetric",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email='{self.email}' role='{self.role}'>"
