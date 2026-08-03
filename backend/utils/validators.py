"""
Input Validation Utilities.
Provides file type, file size, and payload validation tools.
"""

from typing import Set
from backend.core.config import settings
from backend.core.exceptions import ValidationException

ALLOWED_EXTENSIONS = set(settings.ALLOWED_EXTENSIONS)


def validate_file_extension(filename: str, allowed_exts: Set[str] = ALLOWED_EXTENSIONS) -> str:
    """
    Validates that filename extension is supported.
    Raises ValidationException if invalid.
    """
    import os
    _, ext = os.path.splitext(filename.lower())
    if ext not in allowed_exts:
        raise ValidationException(
            f"Unsupported file format '{ext}'. Allowed formats: {', '.join(allowed_exts)}"
        )
    return ext


def validate_file_size(size_bytes: int, max_bytes: int = settings.MAX_UPLOAD_SIZE_BYTES) -> None:
    """
    Validates that file size does not exceed the configured byte limit.
    Raises ValidationException if exceeded.
    """
    if size_bytes > max_bytes:
        raise ValidationException(
            f"File size ({size_bytes / (1024*1024):.2f}MB) exceeds maximum limit of {max_bytes / (1024*1024):.0f}MB."
        )
