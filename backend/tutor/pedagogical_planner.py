"""
Pedagogical Planner.
Selects optimal teaching strategy based on student ability (theta), BKT mastery (P(L)),
query intent, and cognitive load state.
Emits TeachingStrategySelected domain event.
"""

import uuid
from typing import Any, Dict
from loguru import logger

from backend.core.config import settings
from backend.core.events import TeachingStrategySelected, event_dispatcher


class PedagogicalPlanner:
    """Selects pedagogical strategy based on psychometric parameters."""

    async def select_strategy(
        self,
        user_id: uuid.UUID,
        theta: float,
        mastery: float,
        query_intent: str = "CONCEPTUAL",
        explanation_preference: str = "Academic",
    ) -> Dict[str, Any]:
        """
        Selects teaching strategy matching student state.

        Supported strategies:
        - Socratic: Guided questions (theta >= 0.5 and mastery >= 0.6)
        - Feynman: ELI5 plain language (mastery < 0.3)
        - Analogy: Real-world analogies (theta < -0.5)
        - Step-by-step: Procedural breakdown (intent == 'PROCEDURAL')
        - Example-driven: Concrete code/numerical examples
        - Direct Instruction: Clear, authoritative explanation (Default)
        """
        strategy = "Direct Instruction"
        rationale = "Default authoritative explanation for general inquiries."

        if query_intent == "PROCEDURAL":
            strategy = "Step-by-step"
            rationale = "Procedural query detected; breaking down algorithmic steps sequentially."

        elif mastery < settings.PEDAGOGY_FEYNMAN_MASTERY_MAX:
            strategy = "Feynman"
            rationale = f"Low concept mastery ({mastery:.2f} < {settings.PEDAGOGY_FEYNMAN_MASTERY_MAX}); simplifying terminology using ELI5 principles."

        elif theta < settings.PEDAGOGY_ANALOGY_THETA_MAX:
            strategy = "Analogy"
            rationale = f"Low student ability theta ({theta:.2f} < {settings.PEDAGOGY_ANALOGY_THETA_MAX}); grounding concept in relatable real-world analogies."

        elif theta >= settings.PEDAGOGY_SOCRATIC_THETA_MIN and mastery >= settings.PEDAGOGY_SOCRATIC_MASTERY_MIN:
            strategy = "Socratic"
            rationale = f"High student ability ({theta:.2f}) and mastery ({mastery:.2f}); guiding student with reflective questions."

        elif explanation_preference == "Socratic":
            strategy = "Socratic"
            rationale = "Student explicit preference for Socratic method."

        elif explanation_preference == "ELI5":
            strategy = "Feynman"
            rationale = "Student explicit preference for ELI5 explanations."

        logger.info("Selected teaching strategy: user_id={uid} strategy='{s}'", uid=user_id, s=strategy)

        # Emit TeachingStrategySelected domain event
        await event_dispatcher.emit(
            TeachingStrategySelected(
                user_id=user_id,
                strategy_name=strategy,
                rationale=rationale,
            )
        )

        return {
            "strategy": strategy,
            "rationale": rationale,
        }


# Global pedagogical planner instance
pedagogical_planner = PedagogicalPlanner()
