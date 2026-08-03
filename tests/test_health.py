"""
Health Check & Environment Setup Unit Tests.
Verifies FastAPI app startup, versioned API router, middleware, and health endpoints.
"""

from fastapi.testclient import TestClient
from backend.app import app
from backend.core.config import settings

client = TestClient(app)


def test_root_health_check_endpoint():
    """Verify root health endpoint returns HTTP 200 and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == settings.APP_NAME


def test_api_v1_health_check_endpoint():
    """Verify versioned /api/v1/health endpoint returns HTTP 200 and api_prefix."""
    response = client.get(f"{settings.API_V1_STR}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["api_prefix"] == settings.API_V1_STR


def test_request_id_middleware_header():
    """Verify RequestIDMiddleware attaches X-Request-ID response header."""
    response = client.get("/health")
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) > 0


def test_root_endpoint():
    """Verify root endpoint returns welcome payload."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
