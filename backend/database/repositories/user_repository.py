"""
User Repository.
Provides queries for User entity operations.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.user import User
from backend.database.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """User-specific database operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetches active user by unique email address."""
        query = (
            select(User)
            .where(User.email == email.lower().strip())
            .where(User.is_deleted == False)
        )
        result = await self.session.execute(query)
        return result.scalars().first()
