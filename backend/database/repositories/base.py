"""
Generic Async Base Repository.
Provides standard CRUD methods, pagination, soft deletion filtering, and multi-tenant user isolation scoping.
"""

import uuid
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic async repository supporting multi-tenant isolation and soft deletion."""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(
        self, id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Optional[ModelType]:
        """
        Fetches entity by primary key ID.
        Enforces tenant isolation if user_id is provided.
        Filters out soft-deleted records if is_deleted attribute exists.
        """
        query = select(self.model).where(self.model.id == id)  # type: ignore

        if user_id is not None and hasattr(self.model, "user_id"):
            query = query.where(self.model.user_id == user_id)  # type: ignore

        if hasattr(self.model, "is_deleted"):
            query = query.where(self.model.is_deleted == False)  # type: ignore

        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_multi(
        self,
        user_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> List[ModelType]:
        """
        Fetches multiple records with optional filtering, tenant scoping, and pagination.
        """
        query = select(self.model)

        if user_id is not None and hasattr(self.model, "user_id"):
            query = query.where(self.model.user_id == user_id)  # type: ignore

        if hasattr(self.model, "is_deleted"):
            query = query.where(self.model.is_deleted == False)  # type: ignore

        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.where(getattr(self.model, key) == value)

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, attributes: Dict[str, Any]) -> ModelType:
        """Creates and persists a new model instance."""
        instance = self.model(**attributes)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, instance: ModelType, attributes: Dict[str, Any]) -> ModelType:
        """Updates attributes on an existing model instance."""
        for key, value in attributes.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def soft_delete(self, id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> bool:
        """Soft-deletes a record if model supports soft delete."""
        instance = await self.get_by_id(id, user_id=user_id)
        if not instance:
            return False
        if hasattr(instance, "soft_delete"):
            instance.soft_delete()  # type: ignore
            self.session.add(instance)
            await self.session.flush()
            return True
        return await self.delete(id, user_id=user_id)

    async def delete(self, id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> bool:
        """Hard-deletes a record from the database."""
        instance = await self.get_by_id(id, user_id=user_id)
        if not instance:
            return False
        await self.session.delete(instance)
        await self.session.flush()
        return True
