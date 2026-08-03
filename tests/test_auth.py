"""
Authentication & Security Unit Tests.
Verifies password hashing, JWT access/refresh token creation, schema validation, and endpoint routing.
"""

import pytest
from pydantic import ValidationError

from backend.authentication.schemas import UserCreate
from backend.authentication.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from backend.core.exceptions import UnauthorizedException


def test_password_hashing():
    """Verify Bcrypt password hashing and verification."""
    password = "SecurePassword123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_access_token():
    """Verify JWT Access token encoding and decoding."""
    subject = "user-123-uuid"
    token = create_access_token(subject=subject)
    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == subject
    assert payload["type"] == "access"


def test_jwt_refresh_token():
    """Verify JWT Refresh token encoding and decoding."""
    subject = "user-456-uuid"
    token = create_refresh_token(subject=subject)
    payload = decode_token(token, expected_type="refresh")
    assert payload["sub"] == subject
    assert payload["type"] == "refresh"


def test_jwt_invalid_token():
    """Verify decode_token raises UnauthorizedException for invalid tokens."""
    with pytest.raises(UnauthorizedException):
        decode_token("invalid.jwt.token", expected_type="access")


def test_user_create_password_validation():
    """Verify password strength validation rules on UserCreate schema."""
    # Valid password
    user = UserCreate(
        email="valid@example.com",
        password="ValidPassword123",
        full_name="Valid User",
    )
    assert user.email == "valid@example.com"

    # Too short (< 8 chars)
    with pytest.raises(ValidationError):
        UserCreate(email="short@example.com", password="Short1", full_name="Short")

    # Missing uppercase
    with pytest.raises(ValidationError):
        UserCreate(email="no_upper@example.com", password="lowercase123", full_name="No Upper")

    # Missing digit
    with pytest.raises(ValidationError):
        UserCreate(email="no_digit@example.com", password="NoDigitsHere", full_name="No Digit")
