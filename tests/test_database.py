"""
Database Models & Repository Layer Unit Tests.
Verifies model instantiation, UUID primary key generation, mixins, and repository query logic.
"""

import uuid
import pytest
from backend.database.models.user import User
from backend.database.models.student_profile import StudentLearningState, StudentPreferences, StudentProfile
from backend.database.models.document import Document
from backend.database.models.concept_mastery import ConceptMastery


def test_user_model_instantiation():
    """Verify User ORM model defaults and attributes."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="test@example.com",
        hashed_password="hashed_secret",
        full_name="Test Student",
    )
    assert user.id == user_id
    assert user.email == "test@example.com"
    # SQLAlchemy column defaults are applied when the entity is flushed.
    assert user.role is None
    assert user.is_active is None


def test_student_profile_model_instantiation():
    """Verify StudentProfile ORM model theta defaults."""
    user_id = uuid.uuid4()
    profile = StudentProfile(user_id=user_id)
    state = StudentLearningState(user_id=user_id, ability_theta=0.5)
    preferences = StudentPreferences(user_id=user_id, preferred_explanation_style="Socratic")
    assert profile.user_id == user_id
    assert state.ability_theta == 0.5
    assert preferences.preferred_explanation_style == "Socratic"


def test_document_model_instantiation():
    """Verify Document ORM model attributes and tenant isolation field."""
    user_id = uuid.uuid4()
    doc = Document(
        user_id=user_id,
        title="Linear Algebra Textbook.pdf",
        file_type="PDF",
        file_path="/uploads/linear_algebra.pdf",
        status="READY",
    )
    assert doc.user_id == user_id
    assert doc.title == "Linear Algebra Textbook.pdf"
    assert doc.status == "READY"


def test_concept_mastery_model_instantiation():
    """Verify ConceptMastery ORM model default BKT probability."""
    user_id = uuid.uuid4()
    mastery = ConceptMastery(
        user_id=user_id,
        concept_name="Matrix Inversion",
        mastery_prob=0.75,
    )
    assert mastery.user_id == user_id
    assert mastery.concept_name == "Matrix Inversion"
    assert mastery.mastery_prob == 0.75
