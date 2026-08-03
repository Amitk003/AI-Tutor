"""
Student Profile & Concept Mastery Repositories.
Manages StudentProfile IRT parameters and ConceptMastery BKT state tracking.
"""

import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.concept_mastery import ConceptMastery
from backend.database.models.student_profile import StudentProfile
from backend.database.repositories.base import BaseRepository


class StudentProfileRepository(BaseRepository[StudentProfile]):
    """Student profile repository."""

    def __init__(self, session: AsyncSession):
        super().__init__(StudentProfile, session)

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[StudentProfile]:
        """Fetches student profile for a given user ID."""
        query = select(StudentProfile).where(StudentProfile.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalars().first()


class ConceptMasteryRepository(BaseRepository[ConceptMastery]):
    """Concept mastery repository."""

    def __init__(self, session: AsyncSession):
        super().__init__(ConceptMastery, session)

    async def get_user_mastery(self, user_id: uuid.UUID) -> List[ConceptMastery]:
        """Fetches all concept mastery states for user."""
        return await self.get_multi(user_id=user_id)

    async def get_weak_topics(self, user_id: uuid.UUID, threshold: float = 0.60) -> List[ConceptMastery]:
        """Fetches weak concepts where mastery probability P(L) is below threshold."""
        query = (
            select(ConceptMastery)
            .where(ConceptMastery.user_id == user_id)
            .where(ConceptMastery.mastery_prob < threshold)
            .order_by(ConceptMastery.mastery_prob.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
