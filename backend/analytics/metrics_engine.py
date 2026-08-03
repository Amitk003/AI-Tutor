"""
Learning Analytics & Telemetry Engine.
Computes Ebbinghaus Forgetting Curves, concept memory retention R(t),
learning velocity, concept stability, and historical ability progression snapshots.
"""

import math
import uuid
from typing import Any, Dict, List
from loguru import logger


class LearningAnalyticsEngine:
    """Computes psychometric analytics and memory retention metrics."""

    def calculate_memory_retention(self, elapsed_days: float, stability: float = 5.0) -> float:
        """
        Computes Ebbinghaus Forgetting Curve retention: R(t) = e^(-t / S)

        Args:
            elapsed_days: Days elapsed since last study session (t).
            stability: Concept memory stability factor (S, default: 5.0).

        Returns:
            Memory retention probability R(t) in [0.0, 1.0].
        """
        if elapsed_days <= 0:
            return 1.0

        exponent = -elapsed_days / max(stability, 0.1)
        retention = math.exp(exponent)
        return round(max(0.0, min(1.0, retention)), 4)

    def calculate_learning_velocity(
        self,
        initial_mastery: float,
        final_mastery: float,
        study_duration_hours: float,
    ) -> float:
        """
        Calculates learning velocity: Delta P(L) / Delta t (mastery gained per study hour).
        """
        if study_duration_hours <= 0:
            return 0.0

        delta_mastery = final_mastery - initial_mastery
        velocity = delta_mastery / study_duration_hours
        return round(velocity, 4)

    def calculate_concept_stability(self, ease_factor: float, repetition_count: int) -> float:
        """
        Calculates concept stability S = ease_factor * max(1, repetition_count).
        """
        return round(ease_factor * max(1, repetition_count), 2)


# Global learning analytics engine instance
analytics_engine = LearningAnalyticsEngine()
