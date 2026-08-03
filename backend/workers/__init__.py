"""
Celery Workers Package.
Contains Celery application initialization and background task definitions.
"""

from backend.workers.celery_app import celery_app

__all__ = ["celery_app"]
