"""
Learning Goal Tracker.
Tracks active learning objective, completed milestones, and remaining goals.
Emits LearningGoalCompleted domain event when a objective is accomplished.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List
from loguru import logger

from backend.core.events import LearningGoalCompleted, event_dispatcher


@dataclass
class Goal:
    goal_id: str
    title: str
    concept_name: str
    is_completed: bool = False


class LearningGoalTracker:
    """Tracks student learning goals and milestones."""

    def __init__(self, user_id: uuid.UUID):
        self.user_id = user_id
        self.active_goals: List[Goal] = []

    def set_goal(self, goal_id: str, title: str, concept_name: str) -> Goal:
        """Sets a new active learning goal."""
        goal = Goal(goal_id=goal_id, title=title, concept_name=concept_name)
        self.active_goals.append(goal)
        logger.info("Set learning goal for user_id={uid}: '{title}'", uid=self.user_id, title=title)
        return goal

    async def mark_goal_completed(self, goal_id: str) -> bool:
        """Marks goal completed and emits LearningGoalCompleted domain event."""
        for g in self.active_goals:
            if g.goal_id == goal_id and not g.is_completed:
                g.is_completed = True
                logger.info("Goal completed: user_id={uid} goal='{t}'", uid=self.user_id, t=g.title)

                await event_dispatcher.emit(
                    LearningGoalCompleted(user_id=self.user_id, goal_title=g.title)
                )
                return True
        return False

    def get_progress(self) -> Dict[str, Any]:
        """Returns objective progress stats."""
        total = len(self.active_goals)
        completed = sum(1 for g in self.active_goals if g.is_completed)
        return {
            "total_goals": total,
            "completed_goals": completed,
            "remaining_goals": total - completed,
            "progress_percent": round((completed / max(total, 1)) * 100.0, 1),
        }
