"""
Study Session Orchestrator.
Orchestrates the stateful end-to-end AI Study Companion learning experience loop:
Teach -> Check Understanding -> Mini Quiz -> Evaluate & Update -> Adapt Explanation -> Session Summary -> Schedule Revision.
"""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.analytics.sm2_scheduler import sm2_scheduler
from backend.core.events import LearningSessionCompleted, event_dispatcher
from backend.student_model.bkt_engine import bkt_engine
from backend.student_model.irt_engine import irt_engine
from backend.student_model.state_engine import LearningStateEngine
from backend.tutor.decision_engine import tutor_decision_engine
from backend.tutor.question_generator import question_generator
from backend.tutor.quiz_evaluator import quiz_evaluator
from backend.tutor.quiz_planner import quiz_planner


class StudySessionOrchestrator:
    """Orchestrates complete turn-by-turn AI Study Companion sessions."""

    async def execute_study_turn(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        question: str,
        concept_name: str = "General Topic",
        student_answer: Optional[str] = None,
        quiz_item: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes a turn in the study loop.
        1. Reads student ability (theta) and mastery (P(L)).
        2. If student_answer is provided -> Evaluates answer, updates IRT theta & BKT mastery.
        3. Generates adaptive teaching explanation with dynamic modalities (text/code/table/diagram).
        4. Generates an embedded mini quiz check item to verify understanding.
        """
        state_engine = LearningStateEngine(session)
        state_data = await state_engine.get_state(user_id)
        current_theta = state_data.get("ability_theta", 0.0)

        quiz_eval_result = None

        # Step 1: If evaluating previous quiz answer -> Evaluate & update psychometrics
        if student_answer and quiz_item:
            quiz_eval_result = await quiz_evaluator.evaluate_answer(
                session=session,
                user_id=user_id,
                quiz_id=session_id,
                question_id=quiz_item.get("question_id", str(uuid.uuid4())),
                concept_name=concept_name,
                student_answer=student_answer,
                correct_answer=quiz_item.get("correct_answer", ""),
                distractors=quiz_item.get("distractors", []),
                calibrated_difficulty=quiz_item.get("calibrated_difficulty", current_theta),
            )
            # Fetch updated theta after evaluation
            updated_state = await state_engine.get_state(user_id)
            current_theta = updated_state.get("ability_theta", 0.0)

        # Step 2: Teach from uploaded material using Adaptive Tutor Decision Engine
        tutor_result = await tutor_decision_engine.orchestrate_adaptive_explanation(
            session=session,
            user_id=user_id,
            question=question,
            concept_name=concept_name,
            student_theta=current_theta,
        )

        # Step 3: Check Understanding -> Generate Mini Quiz Item
        mini_quiz_item = await question_generator.generate_question(
            concept_name=concept_name,
            retrieved_context=question,
            question_type="MCQ",
            target_difficulty=current_theta,
            quiz_id=session_id,
        )

        logger.info(
            "Study session turn executed: user_id={uid} session_id={sid} concept='{c}'",
            uid=user_id,
            sid=session_id,
            c=concept_name,
        )

        return {
            "session_id": str(session_id),
            "concept_name": concept_name,
            "quiz_evaluation": quiz_eval_result,
            "teaching_explanation": tutor_result,
            "check_understanding_mini_quiz": mini_quiz_item,
        }

    async def complete_session_summary(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        concepts_studied: List[str],
        duration_seconds: int = 300,
    ) -> Dict[str, Any]:
        """
        Completes session summary and schedules SM-2 spaced repetition revision dates.
        """
        schedules = []
        for c in concepts_studied:
            sch = await sm2_scheduler.schedule_revision(
                session=session,
                user_id=user_id,
                concept_name=c,
                quality_grade=4,
            )
            schedules.append(sch)

        await event_dispatcher.emit(
            LearningSessionCompleted(
                user_id=user_id,
                session_id=session_id,
                duration_seconds=duration_seconds,
                concepts_studied_count=len(concepts_studied),
            )
        )

        return {
            "session_id": str(session_id),
            "duration_seconds": duration_seconds,
            "concepts_studied": concepts_studied,
            "revision_schedules": schedules,
        }


# Global study session orchestrator singleton
study_session_orchestrator = StudySessionOrchestrator()
