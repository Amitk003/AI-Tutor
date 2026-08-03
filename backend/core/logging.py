"""
Structured Logging Module using Loguru.
Configures JSON formatted logs for production and colorized output for development.
Intercepts standard logging messages from Uvicorn, FastAPI, and SQLAlchemy.
"""

import sys
import logging
from loguru import logger
from backend.core.config import settings


class InterceptHandler(logging.Handler):
    """
    Custom handler to intercept standard Python logging records
    and redirect them to Loguru.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    """
    Configures Loguru structured logger based on application settings.
    Replaces standard logging handlers for Uvicorn and FastAPI.
    """
    # Remove default loguru sinks
    logger.remove()

    # Determine format and sink settings
    if settings.APP_ENV == "production":
        # Structured JSON logging for production log aggregators (ELK, Datadog)
        logger.add(
            sys.stdout,
            enqueue=True,
            backtrace=False,
            diagnose=False,
            level="INFO",
            serialize=True,
        )
    else:
        # Human-readable colorized logging for development
        logger.add(
            sys.stdout,
            enqueue=True,
            backtrace=True,
            diagnose=True,
            level="DEBUG" if settings.DEBUG else "INFO",
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            ),
        )

    # Intercept standard library loggers
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for logger_name in ("uvicorn", "uvicorn.access", "fastapi", "sqlalchemy.engine"):
        mod_logger = logging.getLogger(logger_name)
        mod_logger.handlers = [InterceptHandler()]

    logger.info(
        "Structured logging initialized for environment: {env}",
        env=settings.APP_ENV,
    )


# Export logger instance
__all__ = ["logger", "setup_logging"]
