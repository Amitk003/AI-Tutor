"""
Document Repository.
Provides query operations for Document and DocumentChunk entities with multi-tenant user scoping
and SHA-256 duplicate document detection.
"""

import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.document import Document
from backend.database.models.document_chunk import DocumentChunk
from backend.database.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Document entity queries scoped to owning user."""

    def __init__(self, session: AsyncSession):
        super().__init__(Document, session)

    async def get_user_documents(self, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Document]:
        """Fetches active documents owned by a specific user."""
        return await self.get_multi(user_id=user_id, skip=skip, limit=limit)

    async def get_by_hash(self, user_id: uuid.UUID, file_hash: str) -> Optional[Document]:
        """
        Fetches existing active document owned by user with matching SHA-256 hash.
        Used for duplicate document detection.
        """
        query = (
            select(Document)
            .where(Document.user_id == user_id)
            .where(Document.file_hash == file_hash)
            .where(Document.is_deleted == False)
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_document_chunks(
        self, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[DocumentChunk]:
        """Fetches chunks belonging to a document, verifying user ownership."""
        query = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .where(DocumentChunk.user_id == user_id)
            .order_by(DocumentChunk.chunk_index.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
