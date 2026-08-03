"""
Development Database Seed Script.
Populates initial development data including user, profile, preferences, statistics, learning state,
sample documents, chunks, concept mastery, quizzes, memory, citations, and LLM registry.
"""

import sys
import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import AsyncSessionLocal, engine
from backend.database.base import Base
from backend.database.models.user import User
from backend.database.models.student_profile import (
    StudentProfile,
    StudentPreferences,
    StudentStatistics,
    StudentLearningState,
)
from backend.database.models.document import Document
from backend.database.models.document_chunk import DocumentChunk
from backend.database.models.chat import ChatSession, ChatMessage
from backend.database.models.conversation_memory import ConversationMemory
from backend.database.models.citation import Citation
from backend.database.models.concept_mastery import ConceptMastery
from backend.database.models.quiz import Quiz, QuizQuestion, QuizAttempt, UserAnswer
from backend.database.models.revision_schedule import RevisionSchedule
from backend.database.models.llm_registry import LLMRegistry
from backend.database.models.audit_log import AuditLog

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_database():
    print("=" * 60)
    print("  Adaptive AI Learning Platform - Enhanced Database Seeding")
    print("=" * 60)

    async with engine.begin() as conn:
        print("[1/6] Creating enhanced database tables...")
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        print("[2/6] Checking existing seed data...")
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == "student@example.com"))
        existing_user = result.scalars().first()

        if existing_user:
            print("[INFO] Sample student user already exists. Skipping seed.")
            return

        print("[3/6] Seeding LLM Registry...")
        qwen_llm = LLMRegistry(
            model_name="qwen2.5:3b-instruct",
            provider="ollama",
            context_window=32768,
            is_active=True,
            is_default=True,
            parameters_json={"temperature": 0.2, "top_p": 0.9},
        )
        llama_llm = LLMRegistry(
            model_name="llama3.2:3b-instruct",
            provider="ollama",
            context_window=131072,
            is_active=True,
            is_default=False,
            parameters_json={"temperature": 0.2, "top_p": 0.9},
        )
        session.add_all([qwen_llm, llama_llm])

        print("[4/6] Creating sample user, profile, preferences, stats & learning state...")
        demo_user = User(
            id=uuid.uuid4(),
            email="student@example.com",
            hashed_password=pwd_context.hash("password123"),
            full_name="Demo Student",
            role="student",
            is_active=True,
        )
        session.add(demo_user)
        await session.flush()

        profile = StudentProfile(
            user_id=demo_user.id,
            bio="Passionate computer science student exploring AI and Machine Learning.",
            grade_level="Undergraduate",
        )
        preferences = StudentPreferences(
            user_id=demo_user.id,
            preferred_explanation_style="Academic",
            preferred_language="en",
            theme="dark",
            notifications_enabled=True,
        )
        statistics = StudentStatistics(
            user_id=demo_user.id,
            total_study_seconds=7200,
            documents_uploaded_count=1,
            quizzes_completed_count=1,
            questions_answered_count=2,
            overall_accuracy_rate=50.0,
            learning_streak_days=3,
        )
        learning_state = StudentLearningState(
            user_id=demo_user.id,
            ability_theta=0.0,
            cognitive_load_capacity=1.0,
            current_focus_topic="Optimization & Neural Networks",
        )
        session.add_all([profile, preferences, statistics, learning_state])

        print("[5/6] Creating sample document with embedding metadata versioning...")
        doc = Document(
            id=uuid.uuid4(),
            user_id=demo_user.id,
            title="Introduction to Machine Learning.pdf",
            file_type="PDF",
            file_path="/app/backend/uploads/sample_ml.pdf",
            file_size_bytes=1048576,
            chunk_count=2,
            status="COMPLETED",
            embedding_model_name="BAAI/bge-small-en-v1.5",
            embedding_dimension=384,
            chunking_strategy_version="v1.0-parent-child",
            indexed_at=datetime.now(timezone.utc),
        )
        session.add(doc)
        await session.flush()

        chunk1 = DocumentChunk(
            document_id=doc.id,
            user_id=demo_user.id,
            chunk_index=0,
            child_content="Gradient descent is an optimization algorithm used to minimize loss functions in machine learning models.",
            parent_content="Chapter 2: Optimization Techniques. Gradient descent is an optimization algorithm used to minimize loss functions in machine learning models. It calculates partial derivatives of the loss function with respect to weights.",
            vector_id=uuid.uuid4(),
            page_label="Page 12",
        )
        chunk2 = DocumentChunk(
            document_id=doc.id,
            user_id=demo_user.id,
            chunk_index=1,
            child_content="Backpropagation computes gradients of the loss function with respect to each weight using the chain rule.",
            parent_content="Chapter 3: Neural Networks. Backpropagation computes gradients of the loss function with respect to each weight using the chain rule. It enables efficient gradient computation across multi-layer networks.",
            vector_id=uuid.uuid4(),
            page_label="Page 25",
        )
        session.add_all([chunk1, chunk2])
        await session.flush()

        print("[6/6] Creating chat memory, citations, concept mastery & audit logs...")
        chat_sess = ChatSession(
            id=uuid.uuid4(),
            user_id=demo_user.id,
            title="Machine Learning Optimization Q&A",
        )
        session.add(chat_sess)
        await session.flush()

        chat_mem = ConversationMemory(
            session_id=chat_sess.id,
            user_id=demo_user.id,
            summary_text="Student inquired about gradient descent loss functions and backpropagation calculus rules.",
            token_count=24,
        )
        msg_user = ChatMessage(
            session_id=chat_sess.id,
            user_id=demo_user.id,
            role="user",
            content="What mathematical rule does backpropagation rely on?",
        )
        msg_assistant = ChatMessage(
            session_id=chat_sess.id,
            user_id=demo_user.id,
            role="assistant",
            content="Backpropagation relies on the Chain Rule of calculus to compute partial derivatives of loss with respect to multi-layer network weights.",
        )
        session.add_all([chat_mem, msg_user, msg_assistant])
        await session.flush()

        citation = Citation(
            message_id=msg_assistant.id,
            document_id=doc.id,
            chunk_id=chunk2.id,
            user_id=demo_user.id,
            page_label="Page 25",
            similarity_score=0.92,
            snippet_text="Backpropagation computes gradients of the loss function using the chain rule.",
        )
        audit = AuditLog(
            user_id=demo_user.id,
            action="DOCUMENT_UPLOAD",
            resource_type="Document",
            resource_id=str(doc.id),
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0 (Development Seed Script)",
            status_code=200,
        )
        session.add_all([citation, audit])

        await session.commit()
        print("=" * 60)
        print("  ENHANCED DATABASE SEED COMPLETED SUCCESSFULLY.")
        print("  Demo User Email:    student@example.com")
        print("  Demo User Password: password123")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_database())
