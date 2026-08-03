"""
Item Response Theory (IRT) Psychometric Engine.
Implements 1PL (Rasch), 2PL, and 3PL item response probability functions
and updates student latent ability parameter (theta).
"""

import math
import uuid
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.core.config import settings
from backend.core.events import AbilityUpdated, event_dispatcher
from backend.database.models.student_profile import StudentLearningState


class IRTEngine:
    """Item Response Theory (IRT) estimation engine."""

    def __init__(self, learning_rate: float = settings.IRT_LEARNING_RATE):
        self.learning_rate = learning_rate

    def calculate_probability_1pl(self, theta: float, b: float) -> float:
        """
        1PL (Rasch) Model: P(u=1 | theta, b) = 1 / (1 + e^-(theta - b))
        """
        exponent = -(theta - b)
        # Avoid math overflow
        exponent = max(min(exponent, 50.0), -50.0)
        return 1.0 / (1.0 + math.exp(exponent))

    def calculate_probability_2pl(self, theta: float, a: float, b: float) -> float:
        """
        2PL Model: P(u=1 | theta, a, b) = 1 / (1 + e^-a(theta - b))
        """
        exponent = -a * (theta - b)
        exponent = max(min(exponent, 50.0), -50.0)
        return 1.0 / (1.0 + math.exp(exponent))

    def calculate_probability_3pl(self, theta: float, a: float, b: float, c: float) -> float:
        """
        3PL Model: P(u=1 | theta, a, b, c) = c + (1 - c) / (1 + e^-a(theta - b))
        """
        p2pl = self.calculate_probability_2pl(theta, a, b)
        return c + (1.0 - c) * p2pl

    def update_ability_theta(
        self,
        current_theta: float,
        is_correct: bool,
        item_difficulty: float = settings.IRT_DEFAULT_ITEM_DIFFICULTY,
        item_discrimination: float = settings.IRT_DEFAULT_ITEM_DISCRIMINATION,
        model_type: str = "2PL",
    ) -> float:
        """
        Updates student ability parameter theta using gradient step based on outcome error.
        Clamps resulting theta strictly to [-3.0, +3.0] standard psychometric range.
        """
        u = 1.0 if is_correct else 0.0

        if model_type == "1PL":
            p_correct = self.calculate_probability_1pl(current_theta, item_difficulty)
            a_weight = 1.0
        elif model_type == "3PL":
            p_correct = self.calculate_probability_3pl(current_theta, item_discrimination, item_difficulty, c=0.20)
            a_weight = item_discrimination
        else:  # Default 2PL
            p_correct = self.calculate_probability_2pl(current_theta, item_discrimination, item_difficulty)
            a_weight = item_discrimination

        delta = self.learning_rate * a_weight * (u - p_correct)
        new_theta = current_theta + delta

        # Clamp within [-3.0, +3.0] standard psychometric scale
        clamped_theta = max(-3.0, min(3.0, new_theta))
        logger.info(
            "IRT theta update ({model}): old={old:.3f} new={new:.3f} delta={d:.3f} p_correct={p:.3f}",
            model=model_type,
            old=current_theta,
            new=clamped_theta,
            d=delta,
            p=p_correct,
        )
        return round(clamped_theta, 4)

    async def update_student_ability(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        is_correct: bool,
        item_difficulty: float = 0.0,
        item_discrimination: float = 1.0,
    ) -> float:
        """
        Updates and persists student ability parameter in PostgreSQL StudentLearningState.
        Emits AbilityUpdated domain event.
        """
        res = await session.execute(
            select(StudentLearningState).where(StudentLearningState.user_id == user_id)
        )
        state = res.scalars().first()

        old_theta = state.ability_theta if state else 0.0
        new_theta = self.update_ability_theta(
            current_theta=old_theta,
            is_correct=is_correct,
            item_difficulty=item_difficulty,
            item_discrimination=item_discrimination,
        )

        if not state:
            state = StudentLearningState(user_id=user_id, ability_theta=new_theta)
            session.add(state)
        else:
            state.ability_theta = new_theta

        await session.commit()

        # Emit AbilityUpdated domain event
        await event_dispatcher.emit(
            AbilityUpdated(
                user_id=user_id,
                old_theta=old_theta,
                new_theta=new_theta,
                delta_theta=round(new_theta - old_theta, 4),
            )
        )
        return new_theta


# Global IRT engine instance
irt_engine = IRTEngine()
