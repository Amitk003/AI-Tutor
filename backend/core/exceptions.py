"""
Centralized Exception Definitions.
Defines domain, business, and system exceptions with standard error codes.
"""

from typing import Any, Dict, Optional


class BaseAppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class DomainException(BaseAppException):
    """Raised when a business domain rule is violated."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="DOMAIN_RULE_VIOLATION",
            status_code=400,
            details=details,
        )


class NotFoundException(BaseAppException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} with identifier '{identifier}' was not found.",
            code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource": resource, "identifier": identifier},
        )


class UnauthorizedException(BaseAppException):
    """Raised when authentication fails or token is invalid."""

    def __init__(self, message: str = "Invalid or expired authentication credentials."):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401,
        )


class ForbiddenException(BaseAppException):
    """Raised when user lacks permission for a resource."""

    def __init__(self, message: str = "Permission denied for this operation."):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
        )


class ValidationException(BaseAppException):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class RAGException(BaseAppException):
    """Raised when an error occurs during vector search or retrieval."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="RAG_PIPELINE_ERROR",
            status_code=500,
            details=details,
        )


class LLMServiceException(BaseAppException):
    """Raised when the configured inference provider cannot complete a request."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="LLM_SERVICE_UNAVAILABLE",
            status_code=503,
            details=details,
        )


class RateLimitException(BaseAppException):
    """Raised when rate limits are exceeded."""

    def __init__(self, message: str = "Rate limit exceeded. Please try again later."):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
        )
