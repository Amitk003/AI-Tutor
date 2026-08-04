# API Reference

This page lists every endpoint the backend provides. All endpoints start with
`/api`. Requests and responses are JSON, except file upload.

## Documents

### Upload a file

```
POST /api/documents/upload
Content-Type: multipart/form-data
Field name: file
```

Supported types: PDF, DOCX, PPTX, TXT, Markdown.

Response:

```json
{
  "id": "abc-123",
  "filename": "notes.pdf",
  "created_at": "2026-08-04T12:00:00"
}
```

The file is parsed, chunked, embedded, and stored before the response returns.
Large files may take a few seconds.

### List documents

```
GET /api/documents
```

Response:

```json
{
  "documents": [
    {
      "id": "abc-123",
      "filename": "notes.pdf",
      "created_at": "2026-08-04T12:00:00"
    }
  ]
}
```

### Delete a document

```
DELETE /api/documents/{id}
```

Removes the file and all its chunks.

## Ask

### Ask a question

```
POST /api/ask
{
  "message": "What is a binary search tree?",
  "history": [
    {"role": "user", "content": "previous question"},
    {"role": "assistant", "content": "previous answer"}
  ]
}
```

`history` is optional. Send the last few messages so the answer can keep context.

Response:

```json
{
  "answer": "A binary search tree is ... [1]",
  "citations": [
    {
      "index": 1,
      "text": "the matching passage",
      "filename": "notes.pdf"
    }
  ]
}
```

The answer is grounded in the user's uploaded material only. If nothing matches,
the answer says so. If the AI service is down, the answer shows the closest
material directly instead of failing.

## Quiz

### Evaluate a quiz answer

```
POST /api/quiz/evaluate
{
  "question": "Which property defines a binary search tree?",
  "options": ["a", "b", "c", "d"],
  "selected_index": 2,
  "correct_index": 2,
  "topic": "Binary Search Tree"
}
```

Response:

```json
{
  "correct": true,
  "explanation": "Because ..."
}
```

If the answer is correct, the topic is added or updated in the revision schedule.

## Review

### Get due reviews

```
GET /api/revision
```

Response:

```json
{
  "revisions": [
    {
      "topic": "Binary Search Tree",
      "ease": 2.5,
      "interval_days": 1,
      "next_review": "2026-08-05"
    }
  ]
}
```

Only topics due today or earlier are returned.

### Grade a review

```
POST /api/revision/grade
{
  "topic": "Binary Search Tree",
  "quality": 4
}
```

`quality` is from 0 to 5. 5 means the answer came easily, 0 means total failure.
The SM-2 algorithm updates the schedule.

## Health

### Check the app

```
GET /api/health
```

Response:

```json
{
  "status": "ok",
  "llm_connected": true,
  "documents_count": 3
}
```

`llm_connected` is false if the LLM API cannot be reached or the key is wrong.

## Errors

Errors follow one shape:

```json
{
  "detail": "human readable message"
}
```

The status code tells you the kind of error:

- 400: bad request (for example unsupported file type).
- 404: not found (for example deleting an unknown document).
- 500: internal error.