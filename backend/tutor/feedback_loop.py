"""
Tutor Feedback Loop.
Executes post-interaction feedback updates across Learning State, BKT Mastery, IRT Theta,
Topic Memory, and Recommendation Engine.
"""

import uuid
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.student_model.bkt_engine import bkt_engine
from backend.student_model.irt_engine import irt_engine
from backend.student_model.state_engine import LearningStateEngine


class TutorFeedbackLoop:
    """Post-interaction student model update loop."""

    async def process_feedback(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        concept_name: str,
        is_correct_response: bool,
        item_difficulty: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Updates student ability (IRT theta), concept mastery (BKT P(L)), and focus state after interaction.
        """
        # 1. Update IRT Theta
        new_theta = await irt_engine.update_student_ability(
            session=session,
            user_id=user_id,
            is_correct=is_correct_response,
            item_difficulty=item_difficulty,
        )

        # 2. Update BKT Concept Mastery
        new_mastery = await bkt_engine.update_concept_mastery(
            session=session,
            user_id=user_id,
            concept_name=concept_name,
            is_correct=is_correct_response,
        )

        # 3. Update Learning Focus State
        state_engine = LearningStateEngine(session)
        await state_engine.update_focus_topic(user_id=user_id, focus_topic=concept_name)

        logger.info(
            "Feedback loop executed: user_id={uid} concept='{c}' theta={t:.2f} mastery={m:.2f}",
            uid=user_id,
            c=concept_name,
            t=new_theta,
            m=new_mastery,
        )

        return {
            "user_id": str(user_id),
            "concept_name": concept_name,
            "new_theta": new_theta,
            "new_mastery": new_mastery,
        }


# Global tutor feedback loop instance
tutor_feedback_loop = TutorFeedbackLoop()
