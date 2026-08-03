"""
Conversation Memory Manager.
Manages rolling chat history, automatic memory compression, and conversation summarization.
Prevents context window overflow while preserving long-term conversational history.
"""

import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.database.models.chat import ChatMessage
from backend.database.models.conversation_memory import ConversationMemory
from backend.llm.token_budget import count_tokens


class MemoryManager:
    """Manages chat history windowing and memory summarization."""

    def __init__(self, session: AsyncSession, max_recent_messages: int = 6):
        self.session = session
        self.max_recent_messages = max_recent_messages

    async def get_or_create_summary(self, session_id: uuid.UUID, user_id: uuid.UUID) -> Optional[ConversationMemory]:
        """Fetches existing rolling memory summary for session."""
        query = (
            select(ConversationMemory)
            .where(ConversationMemory.session_id == session_id)
            .where(ConversationMemory.user_id == user_id)
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def build_memory_context(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> str:
        """
        Builds compressed memory string containing summarized past turns and recent chat messages.
        """
        # 1. Fetch recent messages
        query = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .where(ChatMessage.user_id == user_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(self.max_recent_messages)
        )
        result = await self.session.execute(query)
        recent_messages = list(reversed(result.scalars().all()))

        # 2. Fetch existing summary
        summary_record = await self.get_or_create_summary(session_id, user_id)
        summary_text = summary_record.summary_text if summary_record else ""

        # 3. Format chat history
        history_parts = []
        if summary_text:
            history_parts.append(f"**Long-term Conversation Summary:**\n{summary_text}")

        if recent_messages:
            history_parts.append("**Recent Dialogue:**")
            for msg in recent_messages:
                history_parts.append(f"- **{msg.role.capitalize()}**: {msg.content}")

        combined_memory = "\n".join(history_parts)
        logger.info(
            "Memory context built: session_id={sid} recent_msgs={count} summary_present={has_sum}",
            sid=session_id,
            count=len(recent_messages),
            has_sum=bool(summary_text),
        )
        return combined_memory

    async def summarize_older_messages(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> str:
        """
        Compresses and summarizes older chat messages when dialogue exceeds recent message limits.
        """
        query = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .where(ChatMessage.user_id == user_id)
            .order_by(ChatMessage.created_at.asc())
        )
        result = await self.session.execute(query)
        all_messages = result.scalars().all()

        if len(all_messages) <= self.max_recent_messages:
            return ""

        older_messages = all_messages[:-self.max_recent_messages]
        text_to_summarize = " ".join([f"{m.role}: {m.content}" for m in older_messages])

        # Rule-based fallback summary (or LLM call)
        summary_text = f"Student discussed: '{text_to_summarize[:150]}...'"

        summary_record = await self.get_or_create_summary(session_id, user_id)
        if not summary_record:
            summary_record = ConversationMemory(
                session_id=session_id,
                user_id=user_id,
                summary_text=summary_text,
                token_count=count_tokens(summary_text),
            )
            self.session.add(summary_record)
        else:
            summary_record.summary_text = summary_text
            summary_record.token_count = count_tokens(summary_text)

        await self.session.commit()
        return summary_text
