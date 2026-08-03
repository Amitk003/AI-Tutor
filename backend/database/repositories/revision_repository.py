"""
Revision Schedule Repository.
Manages SuperMemo SM-2 spaced repetition items and due review dates.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.revision_schedule import RevisionSchedule
from backend.database.repositories.base import BaseRepository


class RevisionRepository(BaseRepository[RevisionSchedule]):
    """SuperMemo SM-2 spaced repetition queries."""

    def __init__(self, session: AsyncSession):
        super().__init__(RevisionSchedule, session)

    async def get_due_revisions(
        self, user_id: uuid.UUID, current_time: Optional[datetime] = None
    ) -> List[RevisionSchedule]:
        """Fetches pending revision items due on or before current_time."""
        now = current_time or datetime.now(timezone.utc)
        query = (
            select(RevisionSchedule)
            .where(RevisionSchedule.user_id == user_id)
            .where(RevisionSchedule.is_completed == False)
            .where(RevisionSchedule.scheduled_for <= now)
            .order_by(RevisionSchedule.scheduled_for.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
