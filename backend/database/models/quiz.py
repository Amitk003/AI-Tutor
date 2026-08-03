"""
Quiz, Quiz Question, Quiz Attempt, and User Answer SQLAlchemy Models.
Represents generated quizzes, calibrated item difficulties (IRT b), student attempt submissions,
and distractor explanation responses.
"""

import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.database.mixins import UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from backend.database.models.user import User
    from backend.database.models.document import Document


class Quiz(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Generated quiz entity."""

    __tablename__ = "quizzes"

    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign Key to source Document",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign Key to owning User",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Quiz display title",
    )
    total_questions: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False,
        doc="Number of questions in quiz",
    )

    # Relationships
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="quizzes",
    )
    questions: Mapped[List["QuizQuestion"]] = relationship(
        "QuizQuestion",
        back_populates="quiz",
        cascade="all, delete-orphan",
    )
    attempts: Mapped[List["QuizAttempt"]] = relationship(
        "QuizAttempt",
        back_populates="quiz",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Quiz id={self.id} title='{self.title}' questions={self.total_questions}>"


class QuizQuestion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Quiz item question entity with IRT difficulty parameter b."""

    __tablename__ = "quiz_questions"

    quiz_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign Key to parent Quiz",
    )
    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Question text prompt",
    )
    question_type: Mapped[str] = mapped_column(
        String(50),
        default="MCQ",
        nullable=False,
        doc="Question format (MCQ, TRUE_FALSE, SHORT_ANSWER)",
    )
    options_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        doc="Multiple choice choices JSON dictionary",
    )
    correct_option: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Correct choice key or answer string",
    )
    explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Educational explanation for correct choice and distractors",
    )
    difficulty_b: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="IRT question difficulty parameter b (-3.0 to +3.0)",
    )

    # Relationships
    quiz: Mapped["Quiz"] = relationship(
        "Quiz",
        back_populates="questions",
    )

    def __repr__(self) -> str:
        return f"<QuizQuestion id={self.id} quiz_id={self.quiz_id} difficulty_b={self.difficulty_b:.2f}>"


class QuizAttempt(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Quiz submission attempt record."""

    __tablename__ = "quiz_attempts"

    quiz_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign Key to attempted Quiz",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign Key to User",
    )
    score_percentage: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Score percentage achieved (0.0 to 100.0)",
    )
    delta_theta: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        doc="Recalibrated IRT student ability change",
    )

    # Relationships
    quiz: Mapped["Quiz"] = relationship(
        "Quiz",
        back_populates="attempts",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="quiz_attempts",
    )
    answers: Mapped[List["UserAnswer"]] = relationship(
        "UserAnswer",
        back_populates="attempt",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<QuizAttempt id={self.id} user_id={self.user_id} score={self.score_percentage:.1f}%>"


class UserAnswer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User response to individual quiz question."""

    __tablename__ = "user_answers"

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quiz_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign Key to parent QuizAttempt",
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quiz_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign Key to answered QuizQuestion",
    )
    selected_option: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Option key or text chosen by user",
    )
    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        doc="Whether choice was correct",
    )

    # Relationships
    attempt: Mapped["QuizAttempt"] = relationship(
        "QuizAttempt",
        back_populates="answers",
    )

    def __repr__(self) -> str:
        return f"<UserAnswer attempt_id={self.attempt_id} correct={self.is_correct}>"
