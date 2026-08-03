"""
Chat Repository.
Provides query operations for ChatSession and ChatMessage entities with tenant isolation.
"""

import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.chat import ChatMessage, ChatSession
from backend.database.repositories.base import BaseRepository


class ChatRepository(BaseRepository[ChatSession]):
    """Chat session and message queries scoped to owning user."""

    def __init__(self, session: AsyncSession):
        super().__init__(ChatSession, session)

    async def get_user_sessions(self, user_id: uuid.UUID) -> List[ChatSession]:
        """Fetches active chat sessions owned by user."""
        return await self.get_multi(user_id=user_id)

    async def get_session_messages(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[ChatMessage]:
        """Fetches messages for a chat session, verifying user ownership."""
        query = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .where(ChatMessage.user_id == user_id)
            .order_by(ChatMessage.created_at.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def add_message(
        self, session_id: uuid.UUID, user_id: uuid.UUID, role: str, content: str, sources_json: Optional[dict] = None
    ) -> ChatMessage:
        """Appends a new chat message to an active session."""
        msg = ChatMessage(
            session_id=session_id,
            user_id=user_id,
            role=role,
            content=content,
            sources_json=sources_json,
        )
        self.session.add(msg)
        await self.session.flush()
        await self.session.refresh(msg)
        return msg
