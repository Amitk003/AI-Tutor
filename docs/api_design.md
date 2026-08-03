# REST API Design & Endpoints Specification
## Adaptive AI Learning Platform

---

## 1. Global API Standards
- **Base URL Prefix**: `/api/v1`
- **Authentication Header**: `Authorization: Bearer <JWT_ACCESS_TOKEN>`
- **Correlation Header**: `X-Request-ID: <UUID>`
- **Error Response Format (RFC 7807)**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR | UNAUTHORIZED | RESOURCE_NOT_FOUND | RAG_PIPELINE_ERROR",
    "message": "Human-readable description of error.",
    "details": {},
    "path": "/api/v1/documents/upload"
  }
}
```

---

## 2. Endpoint Definitions

### 2.1 Authentication (`/api/v1/auth`)
- `POST /api/v1/auth/signup`: Create student account.
- `POST /api/v1/auth/login`: Authenticate credentials, return access token (15 mins) and refresh token (7 days).
- `POST /api/v1/auth/refresh`: Issue new access token using valid refresh token.

### 2.2 Document Management (`/api/v1/documents`)
- `POST /api/v1/documents/upload`: Upload file (`PDF`, `DOCX`, `PPTX`, `TXT`) or URL payload. Triggers Celery background parsing worker. Returns `202 Accepted` with `document_id`.
- `GET /api/v1/documents`: List user uploaded study materials with chunk count and index status.
- `DELETE /api/v1/documents/{document_id}`: Delete document, database record, and associated vectors from Qdrant.

### 2.3 RAG Chat Streaming (`/api/v1/chat`)
- `POST /api/v1/chat/query`: Submit prompt with document selection. Returns `text/event-stream` SSE response with real-time streamed tokens and exact page/slide citations.

### 2.4 Student Profile & Analytics (`/api/v1/student`)
- `GET /api/v1/student/profile`: Retrieve cognitive ability $\theta$, mastery probabilities, and learning style preferences.
- `GET /api/v1/analytics/weak-topics`: Retrieve list of concepts where $P(L) < 0.60$.
- `GET /api/v1/analytics/revision-plan`: Retrieve SuperMemo SM-2 scheduled review items.

### 2.5 Quiz Assessment (`/api/v1/quizzes`)
- `POST /api/v1/quizzes/generate`: Generate logit-masked structured JSON quiz tailored to student ability.
- `POST /api/v1/quizzes/submit`: Submit quiz answers; auto-grades performance and updates IRT ability $\theta$ and BKT mastery state $P(L)$.
