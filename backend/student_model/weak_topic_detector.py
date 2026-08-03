"""
Weak Topic Detector.
Identifies struggling concepts based on quiz inaccuracies, repeated queries, and low confidence.
Emits WeakTopicDetected domain event and flags concepts for revision.
"""

import uuid
from typing import Any, Dict, List, Optional
from loguru import logger

from backend.core.config import settings
from backend.core.events import WeakTopicDetected, event_dispatcher


class WeakTopicDetector:
    """Detects concepts requiring student revision."""

    def __init__(self, weakness_threshold: float = settings.WEAK_TOPIC_MASTERY_THRESHOLD):
        self.weakness_threshold = weakness_threshold

    async def analyze_topic(
        self,
        user_id: uuid.UUID,
        concept_name: str,
        mastery_score: float,
        incorrect_quiz_attempts: int = 0,
        repeated_query_count: int = 0,
        low_confidence_occurrences: int = 0,
    ) -> Dict[str, Any]:
        """
        Analyzes student performance indicators for a concept.
        Triggers WeakTopicDetected domain event if performance falls below threshold.
        """
        # Calculate composite weakness score
        is_weak = False
        reasons = []

        if mastery_score < self.weakness_threshold:
            is_weak = True
            reasons.append(f"Low mastery score ({mastery_score:.2f} < {self.weakness_threshold:.2f})")

        if incorrect_quiz_attempts >= settings.REVISION_ATTEMPT_THRESHOLD:
            is_weak = True
            reasons.append(f"Repeated incorrect quiz answers ({incorrect_quiz_attempts} attempts)")

        if repeated_query_count >= 3:
            is_weak = True
            reasons.append(f"Repeated student questions on same concept ({repeated_query_count} queries)")

        reason_summary = "; ".join(reasons) if reasons else "Normal performance"

        if is_weak:
            logger.info("Weak topic detected for user_id={uid}: concept='{c}' reason='{r}'", uid=user_id, c=concept_name, r=reason_summary)
            # Emit WeakTopicDetected event
            await event_dispatcher.emit(
                WeakTopicDetected(
                    user_id=user_id,
                    concept_name=concept_name,
                    weakness_score=round(1.0 - mastery_score, 2),
                    reason=reason_summary,
                )
            )

        return {
            "concept_name": concept_name,
            "is_weak": is_weak,
            "mastery_score": mastery_score,
            "reasons": reasons,
        }


# Global weak topic detector instance
weak_topic_detector = WeakTopicDetector()
