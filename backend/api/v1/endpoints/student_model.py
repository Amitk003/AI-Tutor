"""
Student Modeling REST API v1 Router.
Provides RESTful endpoints for student profile management, pedagogical preferences,
learning state tracking, and explainable learning recommendations.
"""

from typing import Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.authentication.deps import get_current_active_user
from backend.database.models.user import User
from backend.database.session import get_db
from backend.student_model.profile_manager import StudentProfileManager
from backend.student_model.recommendation_engine import recommendation_engine
from backend.student_model.state_engine import LearningStateEngine

router = APIRouter(prefix="/student")


class UpdatePreferencesRequest(BaseModel):
    """Student preference update payload schema."""

    preferred_explanation_style: Optional[str] = Field(default=None, description="Socratic, Analogical, Academic, or ELI5")
    preferred_language: Optional[str] = Field(default=None, description="ISO language code (e.g. en, es)")
    theme: Optional[str] = Field(default=None, description="UI theme: dark or light")


class FocusTopicRequest(BaseModel):
    """Focus topic update payload schema."""

    focus_topic: str = Field(..., min_length=2, description="Active topic name")


@router.get(
    "/profile",
    status_code=status.HTTP_200_OK,
    summary="Get combined student profile and preferences",
)
async def get_profile(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """Returns combined student profile options, preferences, and session stats."""
    manager = StudentProfileManager(session)
    return await manager.get_student_profile(current_user.id)


@router.patch(
    "/preferences",
    status_code=status.HTTP_200_OK,
    summary="Update pedagogical preferences",
)
async def update_preferences(
    payload: UpdatePreferencesRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """Updates student explanation style, language, or UI theme."""
    manager = StudentProfileManager(session)
    await manager.update_preferences(
        user_id=current_user.id,
        explanation_style=payload.preferred_explanation_style,
        language=payload.preferred_language,
        theme=payload.theme,
    )
    return {"message": "Preferences updated successfully."}


@router.get(
    "/state",
    status_code=status.HTTP_200_OK,
    summary="Get active student learning state",
)
async def get_learning_state(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """Returns current active topic, ability parameter, and focus state."""
    engine = LearningStateEngine(session)
    return await engine.get_state(current_user.id)


@router.post(
    "/focus",
    status_code=status.HTTP_200_OK,
    summary="Update active focus topic",
)
async def update_focus(
    payload: FocusTopicRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """Updates current active focus topic."""
    engine = LearningStateEngine(session)
    return await engine.update_focus_topic(current_user.id, payload.focus_topic)


@router.get(
    "/recommendations",
    status_code=status.HTTP_200_OK,
    summary="Get explainable learning recommendations",
)
async def get_recommendations(
    current_topic: str = "Binary Search Tree",
    current_user: User = Depends(get_current_active_user),
):
    """Returns explainable prerequisite review and next topic recommendations."""
    return await recommendation_engine.generate_recommendations(
        user_id=current_user.id,
        current_concept=current_topic,
        weak_topics=[{"concept_name": "Binary Trees", "reason": "Low quiz score"}],
    )
