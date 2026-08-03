# CHANGELOG

All notable changes to the AI Study Companion project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-08-03

### Added
- **Phase 11 Complete: User Interface & Frontend Workflows**
  - Built complete React 18, TypeScript, TailwindCSS, and Zustand frontend single-page application adhering strictly to the Product Specification.
  - Implemented `AppLayout` ([frontend/src/components/layout/AppLayout.tsx](file:///c:/Users/AKSHAT%20SRIVASTAVA/OneDrive/Desktop/GBU%202.0/AI-Learning-Platform-Structure/AI-Learning-Platform/frontend/src/components/layout/AppLayout.tsx)) with responsive sidebar navigation, mobile drawer nav, and top header shell.
  - Implemented `MermaidRenderer` ([frontend/src/components/common/MermaidRenderer.tsx](file:///c:/Users/AKSHAT%20SRIVASTAVA/OneDrive/Desktop/GBU%202.0/AI-Learning-Platform-Structure/AI-Learning-Platform/frontend/src/components/common/MermaidRenderer.tsx)) rendering Mermaid.js flowcharts (`graph TD`), sequence diagrams, and process maps.
  - Implemented `MarkdownRenderer` ([frontend/src/components/common/MarkdownRenderer.tsx](file:///c:/Users/AKSHAT%20SRIVASTAVA/OneDrive/Desktop/GBU%202.0/AI-Learning-Platform-Structure/AI-Learning-Platform/frontend/src/components/common/MarkdownRenderer.tsx)) supporting GFM tables, KaTeX LaTeX math, and code syntax highlighting.
  - Implemented `AuthPage` ([frontend/src/pages/AuthPage.tsx](file:///c:/Users/AKSHAT%20SRIVASTAVA/OneDrive/Desktop/GBU%202.0/AI-Learning-Platform-Structure/AI-Learning-Platform/frontend/src/pages/AuthPage.tsx)) for login and registration.
  - Implemented `DashboardPage` ([frontend/src/pages/DashboardPage.tsx](file:///c:/Users/AKSHAT%20SRIVASTAVA/OneDrive/Desktop/GBU%202.0/AI-Learning-Platform-Structure/AI-Learning-Platform/frontend/src/pages/DashboardPage.tsx)) featuring streak counter, SM-2 revision alerts, quick-start launcher, and mastery metrics.
  - Implemented `SubjectsPage` ([frontend/src/pages/SubjectsPage.tsx](file:///c:/Users/AKSHAT%20SRIVASTAVA/OneDrive/Desktop/GBU%202.0/AI-Learning-Platform-Structure/AI-Learning-Platform/frontend/src/pages/SubjectsPage.tsx)) featuring multi-format file dropzone, document status table, and DAG concept knowledge map viewer.
  - Implemented `StudyStudioPage` ([frontend/src/pages/StudyStudioPage.tsx](file:///c:/Users/AKSHAT%20SRIVASTAVA/OneDrive/Desktop/GBU%202.0/AI-Learning-Platform-Structure/AI-Learning-Platform/frontend/src/pages/StudyStudioPage.tsx)) featuring the AI Study Companion Studio, SSE chat streaming feed, automatic rendered Mermaid diagrams and Markdown tables, inline citations, split-screen PDF viewer, and embedded Check-Understanding Mini-Quiz card with distractor feedback.
  - Implemented `AssessmentPage` ([frontend/src/pages/AssessmentPage.tsx](file:///c:/Users/AKSHAT%20SRIVASTAVA/OneDrive/Desktop/GBU%202.0/AI-Learning-Platform-Structure/AI-Learning-Platform/frontend/src/pages/AssessmentPage.tsx)) for IRT calibrated practice quizzes and distractor feedback.
  - Implemented `RevisionPage` ([frontend/src/pages/RevisionPage.tsx](file:///c:/Users/AKSHAT%20SRIVASTAVA/OneDrive/Desktop/GBU%202.0/AI-Learning-Platform-Structure/AI-Learning-Platform/frontend/src/pages/RevisionPage.tsx)) for SM-2 spaced repetition review with 0–5 quality grade buttons.
  - Implemented `SettingsPage` ([frontend/src/pages/SettingsPage.tsx](file:///c:/Users/AKSHAT%20SRIVASTAVA/OneDrive/Desktop/GBU%202.0/AI-Learning-Platform-Structure/AI-Learning-Platform/frontend/src/pages/SettingsPage.tsx)) for pedagogical strategy selection (Socratic, Feynman, Analogy, ELI5).

---

## [0.15.0] - 2026-08-03

### Added
- **Phase 9 & 10 Complete: Knowledge Construction, Teaching Modality Selector & Study Session Orchestrator**
  - KnowledgeBuilder, TeachingModalitySelector, StudySessionOrchestrator, and REST Study endpoints.
