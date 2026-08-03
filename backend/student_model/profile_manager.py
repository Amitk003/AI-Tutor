"""
Student Profile Manager.
Manages student academic level, explanation style preferences, ISO language options,
content format choices, and session activity counters.
"""

import uuid
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.database.models.student_profile import (
    StudentProfile,
    StudentPreferences,
    StudentStatistics,
)


class StudentProfileManager:
    """Manages student profile options, pedagogical preferences, and statistics."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_student_profile(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Fetches combined student profile, preferences, and statistics.
        """
        prof_res = await self.session.execute(
            select(StudentProfile).where(StudentProfile.user_id == user_id)
        )
        profile = prof_res.scalars().first()

        pref_res = await self.session.execute(
            select(StudentPreferences).where(StudentPreferences.user_id == user_id)
        )
        preferences = pref_res.scalars().first()

        stat_res = await self.session.execute(
            select(StudentStatistics).where(StudentStatistics.user_id == user_id)
        )
        statistics = stat_res.scalars().first()

        return {
            "user_id": str(user_id),
            "grade_level": profile.grade_level if profile else "Undergraduate",
            "bio": profile.bio if profile else "",
            "preferred_language": preferences.preferred_language if preferences else "en",
            "preferred_explanation_style": preferences.preferred_explanation_style if preferences else "Academic",
            "theme": preferences.theme if preferences else "dark",
            "notifications_enabled": preferences.notifications_enabled if preferences else True,
            "total_study_seconds": statistics.total_study_seconds if statistics else 0,
            "documents_uploaded_count": statistics.documents_uploaded_count if statistics else 0,
            "quizzes_completed_count": statistics.quizzes_completed_count if statistics else 0,
            "overall_accuracy_rate": statistics.overall_accuracy_rate if statistics else 0.0,
            "learning_streak_days": statistics.learning_streak_days if statistics else 0,
        }

    async def update_preferences(
        self,
        user_id: uuid.UUID,
        explanation_style: Optional[str] = None,
        language: Optional[str] = None,
        theme: Optional[str] = None,
    ) -> bool:
        """Updates student pedagogical options."""
        res = await self.session.execute(
            select(StudentPreferences).where(StudentPreferences.user_id == user_id)
        )
        preferences = res.scalars().first()

        if not preferences:
            preferences = StudentPreferences(user_id=user_id)
            self.session.add(preferences)

        if explanation_style:
            preferences.preferred_explanation_style = explanation_style
        if language:
            preferences.preferred_language = language
        if theme:
            preferences.theme = theme

        await self.session.commit()
        logger.info("Updated student preferences for user_id={uid}", uid=user_id)
        return True
