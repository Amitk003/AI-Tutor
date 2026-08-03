"""
SQLAlchemy Models Package Init.
Exports all database ORM model entities to ensure declarative registration by Alembic.
"""

from backend.database.base import Base
from backend.database.models.user import User
from backend.database.models.student_profile import (
    StudentProfile,
    StudentPreferences,
    StudentStatistics,
    StudentLearningState,
)
from backend.database.models.document import Document
from backend.database.models.document_chunk import DocumentChunk
from backend.database.models.chat import ChatSession, ChatMessage
from backend.database.models.conversation_memory import ConversationMemory
from backend.database.models.citation import Citation
from backend.database.models.concept_mastery import ConceptMastery
from backend.database.models.quiz import Quiz, QuizQuestion, QuizAttempt, UserAnswer
from backend.database.models.revision_schedule import RevisionSchedule
from backend.database.models.audit_log import AuditLog
from backend.database.models.llm_registry import LLMRegistry
from backend.database.models.prompt_log import PromptLog
from backend.database.models.retrieval_metrics import RetrievalMetric

__all__ = [
    "Base",
    "User",
    "StudentProfile",
    "StudentPreferences",
    "StudentStatistics",
    "StudentLearningState",
    "Document",
    "DocumentChunk",
    "ChatSession",
    "ChatMessage",
    "ConversationMemory",
    "Citation",
    "ConceptMastery",
    "Quiz",
    "QuizQuestion",
    "QuizAttempt",
    "UserAnswer",
    "RevisionSchedule",
    "AuditLog",
    "LLMRegistry",
    "PromptLog",
    "RetrievalMetric",
]
