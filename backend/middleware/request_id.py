"""
Request ID Correlation Middleware.
Assigns a unique UUID to every incoming HTTP request and attaches X-Request-ID response header.
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from loguru import logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware for injecting request correlation IDs."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Extract existing X-Request-ID or generate new UUID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        # Bind request_id to loguru context
        with logger.contextualize(request_id=request_id):
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
