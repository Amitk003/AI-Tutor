"""
Learning State Engine.
Maintains active topic, chapter, concept focus, mastery estimates, and learning progress.
Updates StudentLearningState ORM entity.
"""

import uuid
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.database.models.student_profile import StudentLearningState


class LearningStateEngine:
    """Manages active student learning state and focus parameters."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_state(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Fetches current student learning state."""
        res = await self.session.execute(
            select(StudentLearningState).where(StudentLearningState.user_id == user_id)
        )
        state = res.scalars().first()

        return {
            "user_id": str(user_id),
            "current_focus_topic": state.current_focus_topic if state else "General Computer Science",
            "ability_theta": state.ability_theta if state else 0.0,
            "cognitive_load_capacity": state.cognitive_load_capacity if state else 1.0,
        }

    async def update_focus_topic(self, user_id: uuid.UUID, focus_topic: str) -> Dict[str, Any]:
        """Updates student current focus topic."""
        res = await self.session.execute(
            select(StudentLearningState).where(StudentLearningState.user_id == user_id)
        )
        state = res.scalars().first()

        if not state:
            state = StudentLearningState(user_id=user_id, current_focus_topic=focus_topic)
            self.session.add(state)
        else:
            state.current_focus_topic = focus_topic

        await self.session.commit()
        logger.info("Updated student focus topic: user_id={uid} topic='{t}'", uid=user_id, t=focus_topic)
        return {"user_id": str(user_id), "current_focus_topic": focus_topic}
