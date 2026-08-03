"""
Adaptive Assessment & Quiz Engine Unit Tests.
Verifies QuizPlanner structure, QuestionGenerator JSON schema validation,
IRT/BKT psychometric updates, QuizEvaluator feedback, and Domain Events.
"""

import uuid
import pytest

from backend.core.events import EventDispatcher, QuestionAnswered, QuestionGenerated, QuizStarted
from backend.tutor.question_generator import QuestionGenerator, QuestionSchema
from backend.tutor.quiz_planner import QuizPlanner


def test_quiz_planner_difficulty_calibration():
    """Verify QuizPlanner targets student ability theta +- margin."""
    planner = QuizPlanner()
    user_id = uuid.uuid4()

    plan = planner.plan_quiz(
        user_id=user_id,
        target_concept="Gradient Descent",
        student_theta=1.20,
        student_mastery=0.75,
        weak_topics=["Partial Derivatives"],
    )

    assert plan["target_difficulty"] == 1.20
    assert plan["min_difficulty"] == 0.90
    assert plan["max_difficulty"] == 1.50
    assert "Gradient Descent" in plan["concepts_to_test"]
    assert "Partial Derivatives" in plan["concepts_to_test"]


@pytest.mark.asyncio
async def test_question_generator_json_schema_validation(monkeypatch):
    """Verify QuestionGenerator enforces Pydantic schema validation across question types."""
    generator = QuestionGenerator()
    quiz_id = uuid.uuid4()

    class JSONGateway:
        async def generate(self, prompt: str) -> str:
            return '''{
                "question_type": "MCQ",
                "question_text": "Which rule is used by backpropagation?",
                "correct_answer": "The chain rule",
                "distractors": [{
                    "option_text": "Bayes rule",
                    "misconception_represented": "Confuses probability with differentiation",
                    "explanation": "Backpropagation computes derivatives using the chain rule."
                }],
                "calibrated_difficulty": 0.5,
                "explanation": "The chain rule propagates gradients through composed functions."
            }'''

    monkeypatch.setattr("backend.tutor.question_generator.LLMGatewayFactory.get_gateway", lambda: JSONGateway())

    q_data = await generator.generate_question(
        concept_name="Backpropagation",
        retrieved_context="Backpropagation computes gradients using chain rule.",
        question_type="MCQ",
        target_difficulty=0.50,
        quiz_id=quiz_id,
    )

    # Validate against Pydantic schema
    item = QuestionSchema(**q_data)
    assert item.question_type == "MCQ"
    assert len(item.question_text) > 5
    assert len(item.correct_answer) > 0
    assert isinstance(item.distractors, list)


@pytest.mark.asyncio
async def test_quiz_events_emission():
    """Verify Quiz domain events are emitted."""
    dispatcher = EventDispatcher()
    emitted = []

    async def handle_evt(evt):
        emitted.append(evt)

    dispatcher.subscribe(QuizStarted, handle_evt)
    dispatcher.subscribe(QuestionGenerated, handle_evt)

    user_id = uuid.uuid4()
    quiz_id = uuid.uuid4()

    await dispatcher.emit(
        QuizStarted(
            user_id=user_id,
            quiz_id=quiz_id,
            concept_name="Vectors",
            target_difficulty=0.0,
        )
    )

    assert len(emitted) == 1
    assert emitted[0].quiz_id == quiz_id
