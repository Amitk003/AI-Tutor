"""
Shared Helper Utilities.
Contains text sanitization, normalization, and UUID validation functions.
"""

import re
import uuid
from typing import Any


def sanitize_text(text: str) -> str:
    """
    Cleans raw extracted text by removing control characters, excess whitespace,
    and null bytes.
    """
    if not text:
        return ""
    # Remove null bytes
    text = text.replace("\x00", "")
    # Normalize unicode whitespace
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_valid_uuid(val: Any) -> bool:
    """Checks if a string or object is a valid UUID version 4."""
    try:
        uuid_obj = uuid.UUID(str(val))
        return str(uuid_obj) == str(val)
    except ValueError:
        return False
