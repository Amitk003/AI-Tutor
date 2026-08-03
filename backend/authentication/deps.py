"""
Authentication FastAPI Security Dependencies.
Provides Bearer token extraction, user resolution, and role-based access control (RBAC).
"""

import uuid
from typing import AsyncGenerator
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.authentication.security import decode_token
from backend.core.config import settings
from backend.core.exceptions import ForbiddenException, UnauthorizedException
from backend.database.models.user import User
from backend.database.repositories.user_repository import UserRepository
from backend.database.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency resolving active user from JWT Bearer token.
    """
    payload = decode_token(token, expected_type="access")
    user_id_str: str = payload.get("sub", "")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException("Invalid user identifier in token.")

    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)

    if not user or user.is_deleted:
        raise UnauthorizedException("User associated with token not found.")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensures current user account is active."""
    if not current_user.is_active:
        raise ForbiddenException("Inactive user account.")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Ensures current active user possesses admin privileges."""
    if current_user.role != "admin":
        raise ForbiddenException("Operation requires administrative privileges.")
    return current_user
