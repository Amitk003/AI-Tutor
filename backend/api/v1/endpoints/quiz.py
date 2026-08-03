"""
Adaptive Assessment & Quiz REST API v1 Router.
Exposes RESTful endpoints for starting adaptive quizzes, generating JSON schema-validated items,
submitting answers, and synchronizing psychometric updates.
"""

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.authentication.deps import get_current_active_user
from backend.core.events import QuizStarted, event_dispatcher
from backend.database.models.user import User
from backend.database.session import get_db
from backend.tutor.question_generator import question_generator
from backend.tutor.quiz_evaluator import quiz_evaluator
from backend.tutor.quiz_planner import quiz_planner

router = APIRouter(prefix="/quiz")


class GenerateQuizRequest(BaseModel):
    """Adaptive quiz generation request payload schema."""

    concept_name: str = Field(..., min_length=2, description="Target concept to assess")
    question_count: int = Field(default=3, ge=1, le=10, description="Number of questions")
    question_type: str = Field(default="MCQ", description="MCQ, MULTIPLE_SELECT, TRUE_FALSE, SHORT_ANSWER, CODE_COMPLETION")


class SubmitAnswerRequest(BaseModel):
    """Quiz answer submission payload schema."""

    quiz_id: uuid.UUID = Field(..., description="Quiz session UUID")
    question_id: str = Field(..., description="Question item ID")
    concept_name: str = Field(..., description="Target concept name")
    student_answer: str = Field(..., description="Student submitted answer string")
    correct_answer: str = Field(..., description="Correct answer string")
    distractors: List[Dict[str, Any]] = Field(default_factory=list, description="List of distractors")
    calibrated_difficulty: float = Field(default=0.0, description="IRT calibrated difficulty")
    time_spent_seconds: float = Field(default=10.0, description="Time spent answering in seconds")


@router.post(
    "/generate",
    status_code=status.HTTP_200_OK,
    summary="Generate adaptive schema-constrained quiz items",
)
async def generate_quiz(
    payload: GenerateQuizRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Plans and generates adaptive, calibrated quiz items with structured JSON schemas.
    """
    quiz_id = uuid.uuid4()

    # 1. Plan Assessment
    plan = quiz_planner.plan_quiz(
        user_id=current_user.id,
        target_concept=payload.concept_name,
        question_count=payload.question_count,
    )

    await event_dispatcher.emit(
        QuizStarted(
            user_id=current_user.id,
            quiz_id=quiz_id,
            concept_name=payload.concept_name,
            target_difficulty=plan["target_difficulty"],
        )
    )

    # 2. Generate Calibrated Items
    questions = []
    for _ in range(payload.question_count):
        q = await question_generator.generate_question(
            concept_name=payload.concept_name,
            retrieved_context=f"Study context for {payload.concept_name}.",
            question_type=payload.question_type,
            target_difficulty=plan["target_difficulty"],
            quiz_id=quiz_id,
        )
        questions.append(q)

    return {
        "quiz_id": str(quiz_id),
        "plan": plan,
        "questions": questions,
    }


@router.post(
    "/evaluate",
    status_code=status.HTTP_200_OK,
    summary="Evaluate quiz answer and update IRT/BKT/SM-2 models",
)
async def evaluate_answer(
    payload: SubmitAnswerRequest,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Evaluates answer submission, generates distractor feedback, and updates IRT ability and BKT mastery.
    """
    return await quiz_evaluator.evaluate_answer(
        session=session,
        user_id=current_user.id,
        quiz_id=payload.quiz_id,
        question_id=payload.question_id,
        concept_name=payload.concept_name,
        student_answer=payload.student_answer,
        correct_answer=payload.correct_answer,
        distractors=payload.distractors,
        calibrated_difficulty=payload.calibrated_difficulty,
        time_spent_seconds=payload.time_spent_seconds,
    )
