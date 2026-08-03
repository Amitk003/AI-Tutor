"""
Authentication Pydantic Validation Schemas.
Defines input payloads, password strength rules, and token response models.
"""

import re
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """User registration request schema."""

    email: EmailStr = Field(..., description="User unique email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    full_name: str = Field(..., min_length=2, max_length=255, description="Full display name")
    role: Optional[str] = Field(default="student", description="Role: student or educator")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit.")
        return v


class UserLogin(BaseModel):
    """User authentication login schema."""

    email: EmailStr = Field(..., description="User registered email")
    password: str = Field(..., description="User password")


class RefreshTokenRequest(BaseModel):
    """Token refresh request schema."""

    refresh_token: str = Field(..., description="JWT refresh token string")


class TokenResponse(BaseModel):
    """JWT token response schema."""

    access_token: str = Field(..., description="Short-lived JWT access token (15 mins)")
    refresh_token: str = Field(..., description="Long-lived JWT refresh token (7 days)")
    token_type: str = Field(default="bearer", description="Token authorization type")
    expires_in: int = Field(default=900, description="Access token expiry in seconds")


class UserResponse(BaseModel):
    """User public profile response schema."""

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
