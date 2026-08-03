"""
Adaptive Quiz Planner.
Determines assessment objectives, target difficulty, concepts to test, and question distribution
based on IRT ability (theta), BKT mastery, weak topics, and SM-2 revision schedule.
"""

import uuid
from typing import Any, Dict, List, Optional
from loguru import logger

from backend.core.config import settings


class QuizPlanner:
    """Plans adaptive assessment structure matching student cognitive state."""

    def plan_quiz(
        self,
        user_id: uuid.UUID,
        target_concept: str,
        student_theta: float = 0.0,
        student_mastery: float = 0.5,
        weak_topics: Optional[List[str]] = None,
        question_count: int = settings.QUIZ_DEFAULT_QUESTION_COUNT,
    ) -> Dict[str, Any]:
        """
        Plans quiz structure targeting student ability theta +- margin.
        """
        target_difficulty = round(student_theta, 2)
        difficulty_margin = settings.QUIZ_DIFFICULTY_MARGIN

        concepts_to_test = [target_concept]
        if weak_topics:
            concepts_to_test.extend(weak_topics[:2])

        logger.info(
            "Quiz planned: user_id={uid} concept='{c}' q_count={n} target_diff={d:.2f}",
            uid=user_id,
            c=target_concept,
            n=question_count,
            d=target_difficulty,
        )

        return {
            "user_id": str(user_id),
            "target_concept": target_concept,
            "concepts_to_test": concepts_to_test,
            "question_count": question_count,
            "target_difficulty": target_difficulty,
            "min_difficulty": max(-3.0, round(target_difficulty - difficulty_margin, 2)),
            "max_difficulty": min(3.0, round(target_difficulty + difficulty_margin, 2)),
            "assessment_objective": f"Assess mastery on '{target_concept}' at ability level theta={target_difficulty:.2f}.",
        }


# Global quiz planner instance
quiz_planner = QuizPlanner()
