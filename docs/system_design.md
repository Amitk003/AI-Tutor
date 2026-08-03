# Enterprise System Architecture & DDD Blueprints
## AI Study Companion Platform

---

## 1. High-Level Domain Driven Design Topology

```
                  ┌─────────────────────────────────────────┐
                  │          FastAPI API Gateway            │
                  │   (/api/v1/auth, /documents, /study)   │
                  └────────────────────┬────────────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                          ▼
 ┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐
 │  Auth & Security   │     │ AI Orchestrator &  │     │  Study Session     │
 │   Bounded Context  │     │ Ingestion Engine   │     │  Orchestrator      │
 └──────────┬─────────┘     └──────────┬─────────┘     └──────────┬─────────┘
            │                          │                          │
            ▼                          ▼                          ▼
 ┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐
 │ PostgreSQL 16 DB   │     │ PyMuPDF / Parsers  │     │ Modality Selector, │
 │ (Users, Profiles)  │     │ (PDF, DOCX, PPTX)  │     │ IRT, BKT, SM-2     │
 └────────────────────┘     └────────────────────┘     └────────────────────┘
```

---

## 2. End-to-End AI Study Companion Loop

```
Student Uploads Material
   │
   ▼
[Universal Ingestion Pipeline] ──► Extracts text, layout, headings & chunks
   │
   ▼
[KnowledgeBuilder] ──► Auto-populates ConceptKnowledgeGraph DAG
   │
   ▼
Student Starts Study Session
   │
   ▼
[StudySessionOrchestrator]
   │
   ├──► 1. [Hybrid Retriever] ──► Fetches grounded document context
   ├──► 2. [PedagogicalPlanner] ──► Selects strategy (Socratic, Feynman, Analogy, etc.)
   ├──► 3. [TeachingModalitySelector] ──► Selects Text / Code / Markdown Table / Mermaid Diagram
   ├──► 4. [LLMGateway] ──► Generates grounded teaching explanation with diagrams/tables
   ├──► 5. [QuestionGenerator] ──► Generates Mini Quiz check item to verify understanding
   └──► 6. [QuizEvaluator] ──► Evaluates answer & updates IRT θ, BKT P(L), SM-2 in PostgreSQL
```
