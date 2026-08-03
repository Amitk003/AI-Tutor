"""
Rate Limiting Middleware Module.
Protects endpoints against excessive requests using a sliding window algorithm.
"""

from typing import Dict, Tuple
import time
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from backend.core.config import settings
from backend.core.exceptions import RateLimitException


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory / Redis sliding-window rate limiting middleware."""

    def __init__(self, app, requests_per_minute: int = settings.RATE_LIMIT_PER_MINUTE):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        # Simple sliding window tracker (IP -> list of timestamps)
        self.client_windows: Dict[str, list] = {}

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Exempt health check and documentation endpoints
        if request.url.path in ("/health", "/", f"{settings.API_V1_STR}/docs", f"{settings.API_V1_STR}/openapi.json"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60.0

        # Clean old requests from window
        timestamps = [ts for ts in self.client_windows.get(client_ip, []) if ts > window_start]
        
        if len(timestamps) >= self.requests_per_minute:
            raise RateLimitException(
                f"Rate limit of {self.requests_per_minute} requests/minute exceeded."
            )

        timestamps.append(now)
        self.client_windows[client_ip] = timestamps

        return await call_next(request)
