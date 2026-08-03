"""
Repositories Package.
Exports generic BaseRepository and domain-specific repository classes.
"""

from backend.database.repositories.base import BaseRepository
from backend.database.repositories.user_repository import UserRepository
from backend.database.repositories.document_repository import DocumentRepository
from backend.database.repositories.chat_repository import ChatRepository
from backend.database.repositories.student_repository import (
    StudentProfileRepository,
    ConceptMasteryRepository,
)
from backend.database.repositories.quiz_repository import QuizRepository
from backend.database.repositories.revision_repository import RevisionRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "DocumentRepository",
    "ChatRepository",
    "StudentProfileRepository",
    "ConceptMasteryRepository",
    "QuizRepository",
    "RevisionRepository",
]
