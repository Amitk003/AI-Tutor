"""
FastAPI Main Application Entrypoint.
Initializes structured logging, middleware pipeline, centralized exception handlers,
and mounts API v1 routers following Clean Architecture principles.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.core.config import settings
from backend.core.logging import logger, setup_logging
from backend.core.exception_handlers import register_exception_handlers
from backend.middleware.request_id import RequestIDMiddleware
from backend.middleware.logging import LoggingMiddleware
from backend.middleware.rate_limit import RateLimitMiddleware
from backend.api.v1.router import api_v1_router
from backend.database.base import Base
from backend.database.session import engine
import backend.database.models  # Import all ORM models to populate Base.metadata

# Initialize structured logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes database schema tables on startup."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")
    except Exception as exc:
        logger.warning("Database schema initialization warning: {err}", err=str(exc))
    yield


# Instantiate FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Production-Grade Adaptive AI Learning Platform API",
    version="1.0.0",
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# 1. Custom Middleware Pipeline (Order: Correlation ID -> HTTP Logging -> Rate Limit -> CORS)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 2. Centralized Exception Handlers
register_exception_handlers(app)

# 3. Mount API v1 Router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def root_health_check():
    """Root health check alias."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "1.0.0",
    }


@app.get("/", status_code=status.HTTP_200_OK, include_in_schema=False)
async def root():
    """Root status endpoint."""
    return JSONResponse(
        content={
            "message": f"Welcome to {settings.APP_NAME} API",
            "docs": f"{settings.API_V1_STR}/docs",
            "api_v1": f"{settings.API_V1_STR}/health",
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
