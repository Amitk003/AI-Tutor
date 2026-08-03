"""
Lightweight Domain Event Dispatcher.
Enables event-driven architecture across Ingestion, Indexing, Student Modeling,
Psychometric Engine, Adaptive Tutor Engine, and Adaptive Quiz Engine.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Type
from loguru import logger


@dataclass
class DomainEvent:
    """Base class for all system domain events."""

    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def event_name(self) -> str:
        return self.__class__.__name__


# Ingestion Events
@dataclass
class DocumentUploadedEvent(DomainEvent):
    document_id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    file_path: str = ""
    file_hash: str = ""


@dataclass
class DocumentParsedEvent(DomainEvent):
    document_id: uuid.UUID = field(default_factory=uuid.uuid4)
    element_count: int = 0


@dataclass
class DocumentChunkedEvent(DomainEvent):
    document_id: uuid.UUID = field(default_factory=uuid.uuid4)
    chunk_count: int = 0


@dataclass
class DocumentEmbeddedEvent(DomainEvent):
    document_id: uuid.UUID = field(default_factory=uuid.uuid4)
    vector_count: int = 0
    model_name: str = ""


@dataclass
class DocumentIndexedEvent(DomainEvent):
    document_id: uuid.UUID = field(default_factory=uuid.uuid4)
    collection_name: str = ""
    point_count: int = 0


@dataclass
class DocumentFailedEvent(DomainEvent):
    document_id: uuid.UUID = field(default_factory=uuid.uuid4)
    error_message: str = ""


# Student Modeling Events
@dataclass
class StudentLearnedConcept(DomainEvent):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    concept_name: str = ""
    mastery_score: float = 0.0


@dataclass
class ConceptMastered(DomainEvent):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    concept_name: str = ""
    mastery_score: float = 0.0


@dataclass
class WeakTopicDetected(DomainEvent):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    concept_name: str = ""
    weakness_score: float = 0.0
    reason: str = ""


@dataclass
class LearningSessionCompleted(DomainEvent):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    session_id: uuid.UUID = field(default_factory=uuid.uuid4)
    duration_seconds: int = 0
    concepts_studied_count: int = 0


# Psychometric Events
@dataclass
class AbilityUpdated(DomainEvent):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    old_theta: float = 0.0
    new_theta: float = 0.0
    delta_theta: float = 0.0


@dataclass
class MasteryUpdated(DomainEvent):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    concept_name: str = ""
    old_mastery: float = 0.0
    new_mastery: float = 0.0


@dataclass
class RevisionScheduled(DomainEvent):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    concept_name: str = ""
    next_review_date: str = ""
    interval_days: int = 1


@dataclass
class RevisionCompleted(DomainEvent):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    concept_name: str = ""
    grade_quality: int = 4


@dataclass
class RevisionRecommended(DomainEvent):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    concept_name: str = ""
    prerequisite: str = ""
    explanation: str = ""


@dataclass
class LearningProgressUpdated(DomainEvent):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    overall_progress: float = 0.0


# Adaptive Tutor Domain Events
@dataclass
class TeachingStrategySelected(DomainEvent):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    strategy_name: str = ""
    rationale: str = ""


@dataclass
class ExplanationGenerated(DomainEvent):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    concept_name: str = ""
    strategy: str = ""
    difficulty_level: str = ""


@dataclass
class MisconceptionDetected(DomainEvent):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    concept_name: str = ""
    misconception_detail: str = ""


@dataclass
class LearningGoalCompleted(DomainEvent):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    goal_title: str = ""


@dataclass
class TutorInterventionTriggered(DomainEvent):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    reason: str = ""


# Adaptive Quiz Engine Domain Events
@dataclass
class QuizStarted(DomainEvent):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    quiz_id: uuid.UUID = field(default_factory=uuid.uuid4)
    concept_name: str = ""
    target_difficulty: float = 0.0


@dataclass
class QuestionGenerated(DomainEvent):
    quiz_id: uuid.UUID = field(default_factory=uuid.uuid4)
    question_type: str = ""
    calibrated_difficulty: float = 0.0


@dataclass
class QuestionAnswered(DomainEvent):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    quiz_id: uuid.UUID = field(default_factory=uuid.uuid4)
    question_id: str = ""
    is_correct: bool = False
    time_spent_seconds: float = 0.0


@dataclass
class QuizCompleted(DomainEvent):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    quiz_id: uuid.UUID = field(default_factory=uuid.uuid4)
    score_percentage: float = 0.0
    total_questions: int = 0


@dataclass
class AssessmentUpdated(DomainEvent):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    new_theta: float = 0.0
    new_mastery: float = 0.0


class EventDispatcher:
    """Async event dispatcher maintaining subscribers and emitting domain events."""

    def __init__(self):
        self._handlers: Dict[str, List[Callable[[DomainEvent], Any]]] = {}

    def subscribe(self, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], Any]) -> None:
        """Subscribes an async or sync handler function to an event type."""
        event_name = event_type.__name__
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)
        logger.debug("Subscribed handler {handler} to event {event}", handler=handler.__name__, event=event_name)

    async def emit(self, event: DomainEvent) -> None:
        """Emits a domain event to all registered subscribers."""
        event_name = event.event_name
        logger.info("Emitting domain event: {event_name} id={id}", event_name=event_name, id=event.event_id)

        handlers = self._handlers.get(event_name, [])
        for handler in handlers:
            try:
                import asyncio
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error("Error executing event handler {handler} for event {event}: {err}", handler=handler.__name__, event=event_name, err=str(e))


# Global event dispatcher instance
event_dispatcher = EventDispatcher()
