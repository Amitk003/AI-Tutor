"""
Student Modeling & Adaptive Learning Engine Unit Tests.
Verifies StudentMemory 4-tier separation, ConceptKnowledgeGraph DAG traversal,
Weak/Strong Topic Detectors, Recommendation Engine, and Domain Events.
"""

import uuid
import pytest

from backend.core.events import (
    ConceptMastered,
    EventDispatcher,
    RevisionRecommended,
    WeakTopicDetected,
)
from backend.student_model.concept_graph import ConceptKnowledgeGraph
from backend.student_model.recommendation_engine import RecommendationEngine
from backend.student_model.strong_topic_detector import StrongTopicDetector
from backend.student_model.student_memory import StudentMemory
from backend.student_model.weak_topic_detector import WeakTopicDetector


def test_student_memory_four_tiers():
    """Verify StudentMemory maintains 4 separated memory tiers."""
    user_id = uuid.uuid4()
    mem = StudentMemory(user_id=user_id)

    # 1. Recent Memory
    mem.add_recent_interaction("Gradient Descent", "Student asked about formula.")
    assert len(mem.recent_memory) == 1
    assert mem.recent_memory[0].concept == "Gradient Descent"

    # 2. Topic Memory
    mem.record_topic_snapshot("Gradient Descent", mastery=0.85, status="Mastered")
    assert "Gradient Descent" in mem.topic_memory
    assert mem.topic_memory["Gradient Descent"].metadata["mastery"] == 0.85

    # 3. Revision Memory
    mem.flag_for_revision("Backpropagation", reason="Quiz score < 0.40")
    assert len(mem.revision_memory) == 1
    assert mem.revision_memory[0].concept == "Backpropagation"

    summary = mem.get_summary()
    assert summary["recent_count"] == 1
    assert "Gradient Descent" in summary["tracked_topics"]
    assert "Backpropagation" in summary["revision_queue"]


def test_concept_knowledge_graph_traversal():
    """Verify ConceptKnowledgeGraph DAG prerequisite lookup and dependency traversal."""
    graph = ConceptKnowledgeGraph()

    # Add edges: Trees -> BST -> AVL -> Red-Black
    graph.add_prerequisite("BST", "Trees")
    graph.add_prerequisite("AVL", "BST")
    graph.add_prerequisite("Red-Black", "AVL")

    # Direct prerequisites
    assert graph.get_prerequisites("BST") == ["Trees"]
    assert graph.get_prerequisites("AVL") == ["BST"]

    # Ancestors
    ancestors = graph.get_all_ancestors("Red-Black")
    assert set(ancestors) == {"AVL", "BST", "Trees"}

    # Unlocked next concepts
    dependents = graph.get_next_dependent_concepts("Trees")
    assert dependents == ["BST"]


@pytest.mark.asyncio
async def test_weak_topic_detector_event_emission():
    """Verify WeakTopicDetector identifies weak concepts and emits WeakTopicDetected event."""
    dispatcher = EventDispatcher()
    emitted_events = []

    async def handle_weak(evt: WeakTopicDetected):
        emitted_events.append(evt)

    dispatcher.subscribe(WeakTopicDetected, handle_weak)

    detector = WeakTopicDetector(weakness_threshold=0.40)
    user_id = uuid.uuid4()

    # Low mastery score < 0.40 -> Weak
    res = await detector.analyze_topic(
        user_id=user_id,
        concept_name="Partial Derivatives",
        mastery_score=0.25,
        incorrect_quiz_attempts=4,
    )

    assert res["is_weak"] is True
    assert len(res["reasons"]) >= 1


@pytest.mark.asyncio
async def test_strong_topic_detector():
    """Verify StrongTopicDetector identifies mastered concepts (>= 0.80)."""
    detector = StrongTopicDetector(mastery_threshold=0.80)
    user_id = uuid.uuid4()

    res = await detector.analyze_topic(user_id=user_id, concept_name="Vectors", mastery_score=0.92)
    assert res["is_mastered"] is True


@pytest.mark.asyncio
async def test_recommendation_engine_explainability():
    """Verify RecommendationEngine returns explainable next topic and revision recommendations."""
    graph = ConceptKnowledgeGraph()
    graph.add_prerequisite("AVL Tree", "Binary Search Tree")
    graph.add_prerequisite("Red-Black Tree", "AVL Tree")

    engine = RecommendationEngine(graph=graph)
    user_id = uuid.uuid4()

    weak_topics = [{"concept_name": "Binary Search Tree", "reason": "Low quiz accuracy"}]

    recs = await engine.generate_recommendations(
        user_id=user_id,
        current_concept="AVL Tree",
        weak_topics=weak_topics,
    )

    # Should recommend reviewing prerequisite Binary Search Tree
    assert recs["prerequisite_recommendation"] == "Binary Search Tree"
    assert len(recs["explanations"]) >= 1
    assert "review prerequisite 'Binary Search Tree'" in recs["explanations"][0]
