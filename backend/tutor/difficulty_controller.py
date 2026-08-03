"""
Difficulty Controller.
Adapts explanation complexity, vocabulary level, pacing, and example requirements using IRT ability (theta) and BKT mastery.
"""

from typing import Any, Dict
from loguru import logger


class DifficultyController:
    """Adapts pedagogical difficulty level and explanation parameters."""

    def determine_difficulty(self, theta: float, mastery: float) -> Dict[str, Any]:
        """
        Determines target difficulty level (BEGINNER, INTERMEDIATE, ADVANCED)
        and associated explanation parameters.
        """
        if theta < -1.0 or mastery < 0.3:
            level = "BEGINNER"
            depth = "Foundational"
            example_count = 2
            pacing = "Slow"
        elif theta > 1.0 and mastery >= 0.8:
            level = "ADVANCED"
            depth = "Deep Technical"
            example_count = 1
            pacing = "Fast"
        else:
            level = "INTERMEDIATE"
            depth = "Standard Academic"
            example_count = 1
            pacing = "Moderate"

        logger.debug("Determined difficulty: theta={t:.2f} mastery={m:.2f} -> level={lvl}", t=theta, m=mastery, lvl=level)

        return {
            "difficulty_level": level,
            "explanation_depth": depth,
            "example_count": example_count,
            "pacing": pacing,
        }


# Global difficulty controller instance
difficulty_controller = DifficultyController()
