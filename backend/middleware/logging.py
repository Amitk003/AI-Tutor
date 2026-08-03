"""
HTTP Request Logging Middleware.
Logs method, path, status code, and execution duration for every HTTP transaction.
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from loguru import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP request lifecycle and execution timing."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.perf_counter()
        path = request.url.path
        method = request.method

        logger.debug("Incoming HTTP request: method={method} path={path}", method=method, path=path)

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            logger.info(
                "HTTP request complete: method={method} path={path} status={status} duration={duration:.2f}ms",
                method=method,
                path=path,
                status=response.status_code,
                duration=duration_ms,
            )
            return response
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(
                "HTTP request failed: method={method} path={path} duration={duration:.2f}ms error={error}",
                method=method,
                path=path,
                duration=duration_ms,
                error=str(exc),
            )
            raise
