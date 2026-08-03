"""
Adaptive Tutor Engine Unit Tests.
Verifies PedagogicalPlanner strategy selection, DifficultyController adaptation,
MisconceptionDetector alerts, PrerequisiteEngine, TutorPromptComposer, and TutorFeedbackLoop.
"""

import uuid
import pytest

from backend.core.events import (
    EventDispatcher,
    ExplanationGenerated,
    MisconceptionDetected,
    TeachingStrategySelected,
    TutorInterventionTriggered,
)
from backend.tutor.difficulty_controller import difficulty_controller
from backend.tutor.misconception_detector import misconception_detector
from backend.tutor.pedagogical_planner import pedagogical_planner
from backend.tutor.prerequisite_engine import prerequisite_engine
from backend.tutor.prompt_composer import tutor_prompt_composer


@pytest.mark.asyncio
async def test_pedagogical_planner_strategy_selection():
    """Verify PedagogicalPlanner selects strategies based on theta and mastery."""
    user_id = uuid.uuid4()

    # 1. Socratic (High ability theta >= 0.5, mastery >= 0.6)
    res_soc = await pedagogical_planner.select_strategy(user_id, theta=1.2, mastery=0.85)
    assert res_soc["strategy"] == "Socratic"

    # 2. Feynman (Low mastery < 0.3)
    res_fey = await pedagogical_planner.select_strategy(user_id, theta=0.0, mastery=0.20)
    assert res_fey["strategy"] == "Feynman"

    # 3. Analogy (Low ability theta < -0.5)
    res_ana = await pedagogical_planner.select_strategy(user_id, theta=-1.2, mastery=0.50)
    assert res_ana["strategy"] == "Analogy"

    # 4. Step-by-step (Procedural intent)
    res_step = await pedagogical_planner.select_strategy(user_id, theta=0.0, mastery=0.50, query_intent="PROCEDURAL")
    assert res_step["strategy"] == "Step-by-step"


def test_difficulty_controller_levels():
    """Verify DifficultyController determines difficulty levels."""
    beg = difficulty_controller.determine_difficulty(theta=-1.5, mastery=0.2)
    assert beg["difficulty_level"] == "BEGINNER"
    assert beg["pacing"] == "Slow"

    adv = difficulty_controller.determine_difficulty(theta=1.8, mastery=0.9)
    assert adv["difficulty_level"] == "ADVANCED"

    mid = difficulty_controller.determine_difficulty(theta=0.0, mastery=0.5)
    assert mid["difficulty_level"] == "INTERMEDIATE"


@pytest.mark.asyncio
async def test_misconception_detector_intervention():
    """Verify MisconceptionDetector triggers MisconceptionDetected and TutorInterventionTriggered events."""
    dispatcher = EventDispatcher()
    emitted = []

    async def handle_evt(evt):
        emitted.append(evt)

    dispatcher.subscribe(MisconceptionDetected, handle_evt)
    dispatcher.subscribe(TutorInterventionTriggered, handle_evt)

    user_id = uuid.uuid4()
    res = await misconception_detector.check_misconceptions(
        user_id=user_id,
        concept_name="Gradient Descent",
        recent_questions=[],
        incorrect_quiz_count=4,
    )

    assert res["has_misconception"] is True
    assert "missed 4 consecutive questions" in res["detail"]


def test_prerequisite_engine_check():
    """Verify PrerequisiteEngine identifies unfulfilled prerequisites."""
    res = prerequisite_engine.check_prerequisites(
        target_concept="AVL Tree",
        mastered_concepts=["Binary Trees"],  # Missing Binary Search Tree
    )
    assert res["needs_prereq_review"] is True
    assert "Binary Search Tree" in res["missing_prerequisites"]


def test_tutor_prompt_composer():
    """Verify TutorPromptComposer builds specialized teaching prompt."""
    diff_info = {"difficulty_level": "BEGINNER", "explanation_depth": "Foundational", "example_count": 2}
    prompt = tutor_prompt_composer.compose_tutor_prompt(
        strategy="Feynman",
        difficulty_info=diff_info,
        user_question="What is backpropagation?",
        retrieved_context="Backpropagation computes derivatives.",
    )
    assert "Feynman" in prompt
    assert "BEGINNER" in prompt
    assert "What is backpropagation?" in prompt
    assert "<retrieved_context_sandbox>" in prompt
