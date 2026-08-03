"""
AI Study Companion Session REST API v1 Router.
Exposes RESTful endpoints for executing stateful study companion turns and completing session summaries.
"""

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.authentication.deps import get_current_active_user
from backend.database.models.user import User
from backend.database.session import get_db
from backend.services.study_session_orchestrator import study_session_orchestrator

router = APIRouter(prefix="/study")


class StudyTurnRequest(BaseModel):
    """Study session turn payload schema."""

    session_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Study session UUID")
    concept_name: str = Field(..., min_length=2, description="Active concept to study")
    question: str = Field(..., min_length=2, description="Student query or prompt text")
    student_answer: Optional[str] = Field(default=None, description="Optional answer to previous mini quiz check")
    quiz_item: Optional[Dict[str, Any]] = Field(default=None, description="Optional previous mini quiz question item")


class CompleteSessionRequest(BaseModel):
    """Study session completion request payload schema."""

    session_id: uuid.UUID = Field(..., description="Study session UUID")
    concepts_studied: List[str] = Field(..., description="List of concepts studied in session")
    duration_seconds: int = Field(default=300, ge=1, description="Total session duration in seconds")


@router.post(
    "/session",
    status_code=status.HTTP_200_OK,
    summary="Execute AI Study Companion session turn (Teach + Modalities + Check Understanding)",
)
async def execute_study_session_turn(
    payload: StudyTurnRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Executes a turn in the AI Study Companion loop:
    1. Evaluates previous mini-quiz answer (if provided) and updates IRT/BKT psychometrics.
    2. Teaches concept from uploaded material using optimal presentation modalities (Text/Code/Table/Diagram).
    3. Generates an embedded mini quiz check item to verify understanding.
    """
    return await study_session_orchestrator.execute_study_turn(
        session=session,
        user_id=current_user.id,
        session_id=payload.session_id,
        question=payload.question,
        concept_name=payload.concept_name,
        student_answer=payload.student_answer,
        quiz_item=payload.quiz_item,
    )


@router.post(
    "/complete",
    status_code=status.HTTP_200_OK,
    summary="Complete study session summary and schedule SM-2 revision dates",
)
async def complete_study_session(
    payload: CompleteSessionRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Completes session summary, calculates retention decay, and schedules SM-2 spaced repetition dates.
    """
    return await study_session_orchestrator.complete_session_summary(
        session=session,
        user_id=current_user.id,
        session_id=payload.session_id,
        concepts_studied=payload.concepts_studied,
        duration_seconds=payload.duration_seconds,
    )
