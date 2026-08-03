"""
Misconception Detector.
Detects repeated misunderstandings, prerequisite gaps, and conflicting student responses.
Emits MisconceptionDetected domain event and triggers tutor intervention.
"""

import uuid
from typing import Any, Dict, List
from loguru import logger

from backend.core.events import MisconceptionDetected, TutorInterventionTriggered, event_dispatcher


class MisconceptionDetector:
    """Detects student conceptual misunderstandings and triggers tutor interventions."""

    async def check_misconceptions(
        self,
        user_id: uuid.UUID,
        concept_name: str,
        recent_questions: List[str],
        incorrect_quiz_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Analyzes recent dialogue patterns and quiz mistakes for conceptual gaps.
        """
        has_misconception = False
        detail = ""

        if incorrect_quiz_count >= 3:
            has_misconception = True
            detail = f"Student has missed {incorrect_quiz_count} consecutive questions on '{concept_name}'."
        elif len(recent_questions) >= 3 and len(set(recent_questions)) == 1:
            has_misconception = True
            detail = f"Student has repeatedly asked identical questions about '{concept_name}'."

        if has_misconception:
            logger.info("Misconception detected for user_id={uid}: concept='{c}' detail='{d}'", uid=user_id, c=concept_name, d=detail)
            
            # Emit MisconceptionDetected domain event
            await event_dispatcher.emit(
                MisconceptionDetected(
                    user_id=user_id,
                    concept_name=concept_name,
                    misconception_detail=detail,
                )
            )

            # Emit TutorInterventionTriggered domain event
            await event_dispatcher.emit(
                TutorInterventionTriggered(
                    user_id=user_id,
                    reason=f"Misconception on '{concept_name}': {detail}",
                )
            )

        return {
            "has_misconception": has_misconception,
            "detail": detail,
        }


# Global misconception detector instance
misconception_detector = MisconceptionDetector()
