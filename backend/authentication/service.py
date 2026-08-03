"""
Authentication Service Layer.
Implements business rules for user registration, profile initialization, authentication, and token refresh.
Keeps business logic decoupled from API routes.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.authentication.schemas import UserCreate, UserLogin, TokenResponse
from backend.authentication.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from backend.database.models.user import User
from backend.database.models.student_profile import (
    StudentProfile,
    StudentPreferences,
    StudentStatistics,
    StudentLearningState,
)
from backend.database.repositories.user_repository import UserRepository
from backend.core.exceptions import DomainException, UnauthorizedException, NotFoundException


class AuthService:
    """Service handling user authentication and registration workflows."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def register_user(self, payload: UserCreate) -> User:
        """
        Registers a new user, hashes password, and initializes profile sub-entities.
        """
        existing = await self.user_repo.get_by_email(payload.email)
        if existing:
            raise DomainException(f"User with email '{payload.email}' already exists.")

        # Create User entity
        user = User(
            email=payload.email.lower().strip(),
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            role=payload.role or "student",
            is_active=True,
        )
        self.session.add(user)
        await self.session.flush()

        # Initialize student profile sub-entities
        profile = StudentProfile(user_id=user.id)
        preferences = StudentPreferences(user_id=user.id)
        statistics = StudentStatistics(user_id=user.id)
        learning_state = StudentLearningState(user_id=user.id)

        self.session.add_all([profile, preferences, statistics, learning_state])
        await self.session.commit()
        await self.session.refresh(user)

        logger.info("User registered successfully: id={id} email={email}", id=user.id, email=user.email)
        return user

    async def authenticate_user(self, payload: UserLogin) -> TokenResponse:
        """
        Authenticates user credentials and issues access & refresh tokens.
        """
        user = await self.user_repo.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.hashed_password):
            raise UnauthorizedException("Invalid email address or password.")

        if not user.is_active:
            raise UnauthorizedException("User account is inactive.")

        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))

        logger.info("User authenticated: id={id}", id=user.id)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=900,
        )

    async def refresh_tokens(self, refresh_token_str: str) -> TokenResponse:
        """
        Validates refresh token and issues fresh access and refresh tokens.
        """
        payload = decode_token(refresh_token_str, expected_type="refresh")
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid token payload.")

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active or user.is_deleted:
            raise UnauthorizedException("User no longer active.")

        new_access_token = create_access_token(subject=str(user.id))
        new_refresh_token = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=900,
        )
