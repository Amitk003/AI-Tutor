"""
Audit Log SQLAlchemy Model.
Tracks security events, user logins, document uploads/deletions, and system actions.
"""

import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.database.mixins import UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from backend.database.models.user import User


class AuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Audit log entry entity."""

    __tablename__ = "audit_logs"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Foreign Key to User (nullable for unauthenticated attempts)",
    )
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Action name (LOGIN_SUCCESS, LOGIN_FAILURE, DOCUMENT_UPLOAD, DOCUMENT_DELETE)",
    )
    resource_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Target resource type (User, Document, Quiz)",
    )
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Identifier of target resource",
    )
    ip_address: Mapped[str] = mapped_column(
        String(50),
        default="127.0.0.1",
        nullable=False,
        doc="Client IP address",
    )
    user_agent: Mapped[str] = mapped_column(
        String(500),
        default="",
        nullable=False,
        doc="Client User-Agent header",
    )
    status_code: Mapped[int] = mapped_column(
        Integer,
        default=200,
        nullable=False,
        doc="HTTP response status code",
    )
    details_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Additional event context details",
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="audit_logs",
    )

    def __repr__(self) -> str:
        return f"<AuditLog action='{self.action}' user_id={self.user_id} ip='{self.ip_address}'>"
