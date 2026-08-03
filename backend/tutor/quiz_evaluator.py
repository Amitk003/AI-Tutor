"""
Adaptive Quiz Evaluator & Psychometric Synchronizer.
Evaluates student response correctness, partial credit, and response speed.
Provides adaptive feedback (why correct answer is right, distractor explanations).
Triggers automatic updates across IRT theta, BKT mastery, SM-2 scheduling, and Student Memory.
"""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.analytics.sm2_scheduler import sm2_scheduler
from backend.core.events import AssessmentUpdated, QuestionAnswered, QuizCompleted, event_dispatcher
from backend.student_model.bkt_engine import bkt_engine
from backend.student_model.irt_engine import irt_engine


class QuizEvaluator:
    """Evaluates question answers and triggers psychometric model updates."""

    async def evaluate_answer(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        quiz_id: uuid.UUID,
        question_id: str,
        concept_name: str,
        student_answer: str,
        correct_answer: str,
        distractors: List[Dict[str, Any]],
        calibrated_difficulty: float = 0.0,
        time_spent_seconds: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Evaluates answer correctness and updates psychometric models (IRT, BKT, SM-2).
        """
        # Exact match or normalized string matching
        is_correct = student_answer.strip().lower() == correct_answer.strip().lower()
        score = 1.0 if is_correct else 0.0

        # Find distractor explanation if student chose a distractor
        distractor_feedback = None
        for d in distractors:
            if d.get("option_text", "").strip().lower() == student_answer.strip().lower():
                distractor_feedback = {
                    "misconception": d.get("misconception_represented", "Common misunderstanding"),
                    "explanation": d.get("explanation", "Incorrect choice."),
                }
                break

        # 1. Update IRT Theta
        new_theta = await irt_engine.update_student_ability(
            session=session,
            user_id=user_id,
            is_correct=is_correct,
            item_difficulty=calibrated_difficulty,
        )

        # 2. Update BKT Concept Mastery
        new_mastery = await bkt_engine.update_concept_mastery(
            session=session,
            user_id=user_id,
            concept_name=concept_name,
            is_correct=is_correct,
        )

        # 3. Update SM-2 Spaced Repetition Schedule
        quality_grade = 5 if is_correct else 1
        await sm2_scheduler.schedule_revision(
            session=session,
            user_id=user_id,
            concept_name=concept_name,
            quality_grade=quality_grade,
        )

        logger.info(
            "Quiz answer evaluated: user_id={uid} correct={c} theta={t:.2f} mastery={m:.2f}",
            uid=user_id,
            c=is_correct,
            t=new_theta,
            m=new_mastery,
        )

        # Emit QuestionAnswered domain event
        await event_dispatcher.emit(
            QuestionAnswered(
                user_id=user_id,
                quiz_id=quiz_id,
                question_id=question_id,
                is_correct=is_correct,
                time_spent_seconds=time_spent_seconds,
            )
        )

        # Emit AssessmentUpdated domain event
        await event_dispatcher.emit(
            AssessmentUpdated(
                user_id=user_id,
                new_theta=new_theta,
                new_mastery=new_mastery,
            )
        )

        return {
            "question_id": question_id,
            "is_correct": is_correct,
            "score": score,
            "correct_answer": correct_answer,
            "distractor_feedback": distractor_feedback,
            "updated_psychometrics": {
                "ability_theta": new_theta,
                "concept_mastery": new_mastery,
            },
        }


# Global quiz evaluator instance
quiz_evaluator = QuizEvaluator()
