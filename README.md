# AI Study Companion

> An AI Study Companion that first learns a student's study material and then teaches that student using the most effective teaching method. Powered by an open-source 3B LLM, Retrieval-Augmented Generation (RAG), Item Response Theory (IRT), Bayesian Knowledge Tracing (BKT), and SuperMemo SM-2.

---

## 🌟 Key Capabilities
- **Strict Groundedness (RAG)**: Answers are generated *only* from uploaded student study materials (PDF, DOCX, PPTX, TXT, Web URLs).
- **Zero-Retraining Policy**: Uploaded documents are indexed strictly in vector space and never modify underlying model weights.
- **Universal Document Ingestion & Knowledge Construction Pipeline**: Resumable state machine (`UPLOADED` $\rightarrow$ `PARSING` $\rightarrow$ `OCR` $\rightarrow$ `CLEANING` $\rightarrow$ `CHUNKING` $\rightarrow$ `EMBEDDING` $\rightarrow$ `INDEXING` $\rightarrow$ `READY`) and automated `KnowledgeBuilder` populating the DAG concept graph.
- **Dynamic Teaching Modality Selector**: Automatically determines when to display plain text, code snippets, structured Markdown tables, or Mermaid.js diagrams (`graph TD`, sequence diagrams) whenever pedagogically beneficial without requiring explicit student requests.
- **Stateful AI Study Companion Loop**: Orchestrates `Teach` $\rightarrow$ `Check Understanding` $\rightarrow$ `Mini Quiz` $\rightarrow$ `Evaluate & Update Psychometrics` $\rightarrow$ `Adapt Explanation` $\rightarrow$ `Session Summary` $\rightarrow$ `Schedule Revision`.
- **Advanced Multi-Stage Retrieval & Reranking**: NLU Query Processor, Okapi BM25 keyword matching, Reciprocal Rank Fusion (RRF $k=60$), Cross-Encoder deep attention reranking (`BAAI/bge-reranker-large`), Redis semantic cache, parent context optimization, verified citation structuring, composite confidence scoring ($0.5 S_{\text{rerank}} + 0.3 S_{\text{dense}} + 0.2 S_{\text{sparse}}$), and refusal threshold guardrails ($\tau < 0.35$).
- **Open-Source 3B LLM Inference Engine & RAG Orchestration**: Complete pipeline supporting Ollama and vLLM providers, SSE token streaming (`POST /api/v1/chat/stream`), token budget management, modular prompt templates, and XML context sandboxing for prompt injection protection.
- **Adaptive Assessment & Quiz Engine**: `QuizPlanner` targeting student ability $\theta \pm 0.30$, schema-constrained `QuestionGenerator` (MCQ, Multiple Select, True/False, Fill Blank, Short Answer, Code Completion) with Pydantic JSON validation and retry logic, Distractor Generator attaching misconception representations, and `QuizEvaluator` synchronizing IRT theta, BKT mastery, and SM-2 schedules in PostgreSQL DB.
- **Psychometric Learning Engine**: Item Response Theory (1PL, 2PL, 3PL) theta ($\theta \in [-3.0, +3.0]$) gradient estimator, Bayesian Knowledge Tracing (BKT) posterior concept mastery $P(L_t)$, SuperMemo SM-2 Spaced Repetition scheduler, and Ebbinghaus Forgetting Curve $R(t) = e^{-t/S}$ analytics.
- **Event-Driven Architecture**: Async `EventDispatcher` emitting domain events across ingestion, indexing, student modeling, psychometrics, tutoring, and assessment.

---

## 📚 Technical Architecture Documentation
Comprehensive enterprise architecture blueprints are published in `docs/`:
- 📐 [System Design & DDD Architecture](file:///c:/Users/AKSHAT%20SRIVASTAVA/OneDrive/Desktop/GBU%202.0/AI-Learning-Platform-Structure/AI-Learning-Platform/docs/system_design.md)
- 🗄 [Database Schema & Table Specifications](file:///c:/Users/AKSHAT%20SRIVASTAVA/OneDrive/Desktop/GBU%202.0/AI-Learning-Platform-Structure/AI-Learning-Platform/docs/database_design.md)
- ⚡ [Universal RAG Ingestion & Hybrid Retrieval Pipeline](file:///c:/Users/AKSHAT%20SRIVASTAVA/OneDrive/Desktop/GBU%202.0/AI-Learning-Platform-Structure/AI-Learning-Platform/docs/rag_pipeline.md)
- 🧠 [Psychometric Student Cognitive Modeling (IRT / BKT / SM-2)](file:///c:/Users/AKSHAT%20SRIVASTAVA/OneDrive/Desktop/GBU%202.0/AI-Learning-Platform-Structure/AI-Learning-Platform/docs/student_model.md)
- 🔌 [REST API Design & Endpoint Contracts](file:///c:/Users/AKSHAT%20SRIVASTAVA/OneDrive/Desktop/GBU%202.0/AI-Learning-Platform-Structure/AI-Learning-Platform/docs/api_design.md)

---

## 🏗 Modular Architecture Overview

```
AI-Learning-Platform/
├── alembic/                  # Database Migration Scripts (Alembic Async)
├── backend/
│   ├── api/                  # Versioned API Routers (/api/v1/...)
│   │   └── v1/endpoints/
│   │       ├── auth.py       # REST Auth (signup, login, refresh, me)
│   │       ├── chat.py       # REST RAG Search, Query & SSE Stream Endpoints
│   │       ├── documents.py  # Upload, Deduplication, Status & Deletion
│   │       ├── quiz.py       # REST Adaptive Quiz Generate & Evaluate Endpoints
│   │       ├── student_model.py # Student Profile, State & Recommendations
│   │       ├── study.py      # REST Study Companion Session Endpoints
│   │       └── health.py     # System Health Endpoint
│   ├── authentication/       # JWT Security, Password Hashing, AuthService & Deps
│   ├── core/                 # Config (Dev/Test/Prod), Exceptions, Logging, Events
│   ├── llm/                  # Provider-Agnostic LLM Inference Engine
│   ├── student_model/        # Student Intelligence, KnowledgeBuilder & Psychometric Engine
│   │   ├── bkt_engine.py     # Bayesian Knowledge Tracing (BKT) Posterior Mastery Engine
│   │   ├── concept_graph.py  # DAG Concept Knowledge Graph & Prerequisite Traversal
│   │   ├── irt_engine.py     # Item Response Theory (1PL/2PL/3PL) Theta Estimator
│   │   ├── knowledge_builder.py # Automated Knowledge Construction Engine
│   │   ├── profile_manager.py# Student Profile Manager & Pedagogical Preferences
│   │   ├── recommendation_engine.py # Explainable Recommendation Engine
│   │   ├── state_engine.py   # Active Learning Focus State Engine
│   │   ├── strong_topic_detector.py # Strong Topic & Mastery Detector
│   │   ├── student_memory.py # 4-Tier Student Memory (Recent, Long-term, Topic, Revision)
│   │   └── weak_topic_detector.py # Weak Topic & Remediation Detector
│   ├── tutor/                # Adaptive Tutor, Modality Selector & Quiz Engine
│   │   ├── decision_engine.py# Central TutorDecisionEngine Orchestrator
│   │   ├── difficulty_controller.py # Adaptive Difficulty & Pacing Controller
│   │   ├── distractor_generator.py # Distractor & Misconception Generator
│   │   ├── feedback_loop.py  # Tutor Feedback Loop (Theta & Mastery Updates)
│   │   ├── goal_tracker.py   # Learning Goal Tracker
│   │   ├── misconception_detector.py # Misconception Detector & Intervention Alerts
│   │   ├── modality_selector.py # Teaching Modality Selector (Text, Code, Tables, Diagrams)
│   │   ├── pedagogical_planner.py # Strategy Selection (Socratic, Feynman, Analogy, etc.)
│   │   ├── prerequisite_engine.py # Prerequisite Recommendation Engine
│   │   ├── prompt_composer.py# Dynamic Teaching Prompt Composer
│   │   ├── question_generator.py # Calibrated Schema-Valid Question Item Generator
│   │   ├── quiz_evaluator.py # Quiz Answer Evaluator & Psychometric Synchronizer
│   │   └── quiz_planner.py   # Adaptive Quiz Structure Planner
│   ├── services/
│   │   ├── ai_orchestrator.py# Central AI Orchestrator Service
│   │   └── study_session_orchestrator.py # AI Study Companion Loop Orchestrator
│   ├── analytics/            # Spaced Repetition & Psychometric Analytics
│   ├── nlu/                  # Query Processing, Synonym Expansion & Intent Classifier
│   ├── vector_store/
│   │   └── qdrant_client.py  # Qdrant Client Store & Payload HNSW Indexes
│   ├── rag/                  # Universal Ingestion & Hybrid Retrieval Engine
│   ├── middleware/           # Request ID Correlation, HTTP Logging, Rate Limiting
│   ├── workers/              # Celery Background Processing Workers
│   ├── utils/                # Shared Helpers & File Validators
│   └── database/             # 21 ORM Models & Generic BaseRepository
├── frontend/                 # React 18, TypeScript, Vite, TailwindCSS, Zustand
├── .github/workflows/ci.yml  # GitHub Actions CI Pipeline (Pytest, Ruff, Black, Mypy)
├── docker/                   # Multi-service Docker Compose & Dockerfiles
├── docs/                     # System Architecture & API Specifications
├── tests/                    # pytest Backend Unit & Integration Tests
└── scripts/                  # Seed Script & Infrastructure Health Checkers
```

---

## 🚀 Quick Start & Local Setup

### 1. Infrastructure Setup via Docker Compose
Start PostgreSQL 16, Redis 7, Qdrant Vector DB, and Ollama:
```bash
docker-compose -f docker/docker-compose.yml up -d
```

### 2. Verify Services & Seed Database
```bash
python scripts/check_services.py
python scripts/seed_db.py
```

### 3. Backend Setup & Tests
```bash
# Install backend dependencies
pip install -r backend/requirements.txt

# Run unit tests
pytest tests/
```

Start backend development server:
```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation is available at [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs).

---

## 📄 License & Standards
Built following SOLID design principles, PEP8 formatting guidelines, Clean Architecture, and enterprise privacy standards.
