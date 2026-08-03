"""
Health Check API v1 Endpoint.
"""

from fastapi import APIRouter, status
from backend.core.config import settings
from backend.core.logging import logger

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK, summary="Health Check")
async def health_check():
    """
    Returns operational status, app metadata, and environment details.
    """
    logger.debug("API v1 Health Check Endpoint Called")
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "1.0.0",
        "api_prefix": settings.API_V1_STR,
    }
