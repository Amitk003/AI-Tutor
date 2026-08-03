"""Initial database schema migration creating all core tables, indexes, UUID PKs, soft-deletes, and FK constraints.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-03 17:15:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='student'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_is_deleted', 'users', ['is_deleted'])

    # 2. student_profiles table
    op.create_table(
        'student_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('bio', sa.Text(), nullable=False, server_default=''),
        sa.Column('grade_level', sa.String(length=100), nullable=False, server_default='Undergraduate'),
        sa.Column('avatar_url', sa.String(length=500), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_student_profiles_id', 'student_profiles', ['id'])
    op.create_index('ix_student_profiles_user_id', 'student_profiles', ['user_id'])

    # 3. student_preferences table
    op.create_table(
        'student_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('preferred_explanation_style', sa.String(length=50), nullable=False, server_default='Academic'),
        sa.Column('preferred_language', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('theme', sa.String(length=20), nullable=False, server_default='dark'),
        sa.Column('notifications_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_student_preferences_id', 'student_preferences', ['id'])
    op.create_index('ix_student_preferences_user_id', 'student_preferences', ['user_id'])

    # 4. student_statistics table
    op.create_table(
        'student_statistics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('total_study_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('documents_uploaded_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quizzes_completed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('questions_answered_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('overall_accuracy_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('learning_streak_days', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_student_statistics_id', 'student_statistics', ['id'])
    op.create_index('ix_student_statistics_user_id', 'student_statistics', ['user_id'])

    # 5. student_learning_state table
    op.create_table(
        'student_learning_state',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('ability_theta', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('cognitive_load_capacity', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('current_focus_topic', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_student_learning_state_id', 'student_learning_state', ['id'])
    op.create_index('ix_student_learning_state_user_id', 'student_learning_state', ['user_id'])

    # 6. documents table
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('chunk_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('embedding_model_name', sa.String(length=100), nullable=False, server_default='BAAI/bge-small-en-v1.5'),
        sa.Column('embedding_dimension', sa.Integer(), nullable=False, server_default='384'),
        sa.Column('chunking_strategy_version', sa.String(length=50), nullable=False, server_default='v1.0-parent-child'),
        sa.Column('indexed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_documents_id', 'documents', ['id'])
    op.create_index('ix_documents_user_id', 'documents', ['user_id'])
    op.create_index('ix_documents_status', 'documents', ['status'])

    # 7. document_chunks table
    op.create_table(
        'document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('child_content', sa.Text(), nullable=False),
        sa.Column('parent_content', sa.Text(), nullable=False),
        sa.Column('vector_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('page_label', sa.String(length=50), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_document_chunks_id', 'document_chunks', ['id'])
    op.create_index('ix_document_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('ix_document_chunks_user_id', 'document_chunks', ['user_id'])
    op.create_index('ix_document_chunks_vector_id', 'document_chunks', ['vector_id'])

    # 8. chat_sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False, server_default='New Learning Session'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_chat_sessions_id', 'chat_sessions', ['id'])
    op.create_index('ix_chat_sessions_user_id', 'chat_sessions', ['user_id'])

    # 9. conversation_memories table
    op.create_table(
        'conversation_memories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('summary_text', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_summarized_message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_conversation_memories_id', 'conversation_memories', ['id'])
    op.create_index('ix_conversation_memories_session_id', 'conversation_memories', ['session_id'])

    # 10. chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_chat_messages_id', 'chat_messages', ['id'])
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id'])

    # 11. citations table
    op.create_table(
        'citations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chat_messages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('document_chunks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('page_label', sa.String(length=50), nullable=False, server_default='1'),
        sa.Column('similarity_score', sa.Float(), nullable=False),
        sa.Column('snippet_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_citations_id', 'citations', ['id'])
    op.create_index('ix_citations_message_id', 'citations', ['message_id'])

    # 12. concept_mastery table
    op.create_table(
        'concept_mastery',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('concept_name', sa.String(length=255), nullable=False),
        sa.Column('mastery_prob', sa.Float(), nullable=False, server_default='0.1'),
        sa.Column('total_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('correct_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_practiced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_concept_mastery_id', 'concept_mastery', ['id'])
    op.create_index('ix_concept_mastery_user_id', 'concept_mastery', ['user_id'])
    op.create_index('ix_concept_mastery_concept_name', 'concept_mastery', ['concept_name'])

    # 13. quizzes table
    op.create_table(
        'quizzes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('total_questions', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_quizzes_id', 'quizzes', ['id'])
    op.create_index('ix_quizzes_user_id', 'quizzes', ['user_id'])

    # 14. quiz_questions table
    op.create_table(
        'quiz_questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('quiz_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(length=50), nullable=False, server_default='MCQ'),
        sa.Column('options_json', sa.JSON(), nullable=False),
        sa.Column('correct_option', sa.String(length=255), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('difficulty_b', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_quiz_questions_id', 'quiz_questions', ['id'])

    # 15. quiz_attempts table
    op.create_table(
        'quiz_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('quiz_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('score_percentage', sa.Float(), nullable=False),
        sa.Column('delta_theta', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_quiz_attempts_id', 'quiz_attempts', ['id'])

    # 16. user_answers table
    op.create_table(
        'user_answers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('attempt_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quiz_attempts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quiz_questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('selected_option', sa.String(length=255), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_user_answers_id', 'user_answers', ['id'])

    # 17. revision_schedule table
    op.create_table(
        'revision_schedule',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('concept_name', sa.String(length=255), nullable=False),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=False),
        sa.Column('interval_days', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('ease_factor', sa.Float(), nullable=False, server_default='2.5'),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_revision_schedule_id', 'revision_schedule', ['id'])
    op.create_index('ix_revision_schedule_user_id', 'revision_schedule', ['user_id'])

    # 18. audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=False, server_default='127.0.0.1'),
        sa.Column('user_agent', sa.String(length=500), nullable=False, server_default=''),
        sa.Column('status_code', sa.Integer(), nullable=False, server_default='200'),
        sa.Column('details_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_audit_logs_id', 'audit_logs', ['id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])

    # 19. llm_registry table
    op.create_table(
        'llm_registry',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False, unique=True),
        sa.Column('provider', sa.String(length=50), nullable=False, server_default='ollama'),
        sa.Column('context_window', sa.Integer(), nullable=False, server_default='32768'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('parameters_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_llm_registry_id', 'llm_registry', ['id'])
    op.create_index('ix_llm_registry_model_name', 'llm_registry', ['model_name'])

    # 20. prompt_logs table
    op.create_table(
        'prompt_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chat_sessions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('model_name', sa.Text(), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('user_prompt', sa.Text(), nullable=False),
        sa.Column('context_injected', sa.Text(), nullable=False),
        sa.Column('response_text', sa.Text(), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('output_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('latency_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_prompt_logs_id', 'prompt_logs', ['id'])

    # 21. retrieval_metrics table
    op.create_table(
        'retrieval_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('retrieved_candidate_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('top_rerank_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('confidence_threshold_met', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('retrieval_latency_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_retrieval_metrics_id', 'retrieval_metrics', ['id'])


def downgrade() -> None:
    op.drop_table('retrieval_metrics')
    op.drop_table('prompt_logs')
    op.drop_table('llm_registry')
    op.drop_table('audit_logs')
    op.drop_table('revision_schedule')
    op.drop_table('user_answers')
    op.drop_table('quiz_attempts')
    op.drop_table('quiz_questions')
    op.drop_table('quizzes')
    op.drop_table('concept_mastery')
    op.drop_table('citations')
    op.drop_table('chat_messages')
    op.drop_table('conversation_memories')
    op.drop_table('chat_sessions')
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('student_learning_state')
    op.drop_table('student_statistics')
    op.drop_table('student_preferences')
    op.drop_table('student_profiles')
    op.drop_table('users')
