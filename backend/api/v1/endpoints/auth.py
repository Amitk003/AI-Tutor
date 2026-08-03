"""
Authentication API v1 Router.
Provides RESTful endpoints for user signup, login, token refresh, and profile inspection.
Delegates business logic strictly to AuthService following Clean Architecture.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.authentication.deps import get_current_active_user
from backend.authentication.schemas import (
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from backend.authentication.service import AuthService
from backend.database.models.user import User
from backend.database.session import get_db

router = APIRouter(prefix="/auth")


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user account",
)
async def signup(
    payload: UserCreate,
    session: AsyncSession = Depends(get_db),
):
    """
    Registers a new student user account and initializes default profile sub-entities.
    """
    service = AuthService(session)
    user = await service.register_user(payload)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user & issue tokens",
)
async def login(
    payload: UserLogin,
    session: AsyncSession = Depends(get_db),
):
    """
    Authenticates user email and password, returning JWT access and refresh tokens.
    """
    service = AuthService(session)
    return await service.authenticate_user(payload)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
)
async def refresh_token(
    payload: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    Issues a fresh access token using a valid refresh token.
    """
    service = AuthService(session)
    return await service.refresh_tokens(payload.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns the authenticated user's profile information.
    """
    return current_user
