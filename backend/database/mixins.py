"""
SQLAlchemy Model Mixins.
Provides reusable audit fields, soft deletion, and UUID primary keys across models.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column


def utc_now() -> datetime:
    """Returns current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


class UUIDPrimaryKeyMixin:
    """Provides a UUID v4 primary key column."""

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique UUID primary key",
    )


class TimestampMixin:
    """Provides created_at and updated_at audit columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        doc="Record creation timestamp in UTC",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
        doc="Record last update timestamp in UTC",
    )


class SoftDeleteMixin:
    """Provides soft deletion support with deleted_at and is_deleted columns."""

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Soft deletion flag",
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="Timestamp when record was soft-deleted",
    )

    def soft_delete(self) -> None:
        """Marks record as soft-deleted."""
        self.is_deleted = True
        self.deleted_at = utc_now()

    def restore(self) -> None:
        """Restores a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
