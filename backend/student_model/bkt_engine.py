"""
Bayesian Knowledge Tracing (BKT) Psychometric Engine.
Estimates concept-level student mastery P(L_t) after every problem response using Bayesian update rules.
"""

import uuid
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.core.config import settings
from backend.core.events import MasteryUpdated, event_dispatcher
from backend.database.models.concept_mastery import ConceptMastery


class BKTEngine:
    """Bayesian Knowledge Tracing (BKT) estimation engine."""

    def __init__(
        self,
        p_l0: float = settings.BKT_PRIOR_P_L0,
        p_t: float = settings.BKT_PROB_TRANSITION,
        p_g: float = settings.BKT_PROB_GUESS,
        p_s: float = settings.BKT_PROB_SLIP,
    ):
        self.p_l0 = p_l0
        self.p_t = p_t
        self.p_g = p_g
        self.p_s = p_s

    def update_mastery(self, current_p_l: float, is_correct: bool) -> float:
        """
        Updates concept mastery probability P(L_t) given observation outcome (correct/incorrect).

        Formulas:
        P(L_t|u=1) = [P(L_{t-1}) * (1 - P_S)] / [P(L_{t-1}) * (1 - P_S) + (1 - P(L_{t-1})) * P_G]
        P(L_t|u=0) = [P(L_{t-1}) * P_S]       / [P(L_{t-1}) * P_S       + (1 - P(L_{t-1})) * (1 - P_G)]
        P(L_t)     = P(L_t|u) + (1 - P(L_t|u)) * P_T
        """
        # Ensure prior probability within (0, 1) bounds
        p_l_prev = max(0.001, min(0.999, current_p_l))

        if is_correct:
            numerator = p_l_prev * (1.0 - self.p_s)
            denominator = numerator + (1.0 - p_l_prev) * self.p_g
        else:
            numerator = p_l_prev * self.p_s
            denominator = numerator + (1.0 - p_l_prev) * (1.0 - self.p_g)

        p_l_given_obs = numerator / max(denominator, 1e-9)

        # Transition update step
        p_l_next = p_l_given_obs + (1.0 - p_l_given_obs) * self.p_t

        # Clamp strictly within [0.0, 1.0] bounds
        clamped_next = max(0.0, min(1.0, p_l_next))
        logger.info(
            "BKT mastery update: prev={prev:.3f} correct={corr} next={next:.3f}",
            prev=p_l_prev,
            corr=is_correct,
            next=clamped_next,
        )
        return round(clamped_next, 4)

    async def update_concept_mastery(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        concept_name: str,
        is_correct: bool,
    ) -> float:
        """
        Updates and persists concept mastery in PostgreSQL ConceptMastery table.
        Emits MasteryUpdated domain event.
        """
        res = await session.execute(
            select(ConceptMastery)
            .where(ConceptMastery.user_id == user_id)
            .where(ConceptMastery.concept_name == concept_name)
        )
        record = res.scalars().first()

        old_mastery = record.mastery_score if record else self.p_l0
        new_mastery = self.update_mastery(old_mastery, is_correct)

        if not record:
            record = ConceptMastery(
                user_id=user_id,
                concept_name=concept_name,
                mastery_score=new_mastery,
            )
            session.add(record)
        else:
            record.mastery_score = new_mastery

        await session.commit()

        # Emit MasteryUpdated domain event
        await event_dispatcher.emit(
            MasteryUpdated(
                user_id=user_id,
                concept_name=concept_name,
                old_mastery=old_mastery,
                new_mastery=new_mastery,
            )
        )
        return new_mastery


# Global BKT engine instance
bkt_engine = BKTEngine()
