"""
Strong Topic Detector.
Identifies mastered concepts and emits ConceptMastered domain event to guide future adaptive tutoring.
"""

import uuid
from typing import Any, Dict
from loguru import logger

from backend.core.config import settings
from backend.core.events import ConceptMastered, event_dispatcher


class StrongTopicDetector:
    """Detects concepts mastered by student."""

    def __init__(self, mastery_threshold: float = settings.STRONG_TOPIC_MASTERY_THRESHOLD):
        self.mastery_threshold = mastery_threshold

    async def analyze_topic(
        self,
        user_id: uuid.UUID,
        concept_name: str,
        mastery_score: float,
    ) -> Dict[str, Any]:
        """
        Analyzes concept performance for mastery.
        Triggers ConceptMastered domain event if score >= threshold.
        """
        is_mastered = mastery_score >= self.mastery_threshold

        if is_mastered:
            logger.info("Concept mastered by user_id={uid}: concept='{c}' score={s:.2f}", uid=user_id, c=concept_name, s=mastery_score)
            await event_dispatcher.emit(
                ConceptMastered(
                    user_id=user_id,
                    concept_name=concept_name,
                    mastery_score=mastery_score,
                )
            )

        return {
            "concept_name": concept_name,
            "is_mastered": is_mastered,
            "mastery_score": mastery_score,
        }


# Global strong topic detector instance
strong_topic_detector = StrongTopicDetector()
