"""
API v1 Router Aggregator.
Combines all v1 endpoint routers under a single /api/v1 prefix.
"""

from fastapi import APIRouter
from backend.api.v1.endpoints import auth, chat, documents, health, quiz, student_model, study

api_v1_router = APIRouter()

# Include endpoint routers
api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(auth.router, tags=["Authentication"])
api_v1_router.include_router(documents.router, tags=["Document Management"])
api_v1_router.include_router(chat.router, tags=["RAG Retrieval & Chat"])
api_v1_router.include_router(student_model.router, tags=["Student Modeling Engine"])
api_v1_router.include_router(quiz.router, tags=["Adaptive Assessment & Quiz Engine"])
api_v1_router.include_router(study.router, tags=["AI Study Companion Session Engine"])
