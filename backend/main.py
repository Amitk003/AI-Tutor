"""StudyMate backend application.

One FastAPI server that serves both the API and the built frontend.
"""

import os
import shutil
import uuid

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend import config
from backend import db
from backend import rag
from backend import tutor
from backend.llm import llm

app = FastAPI(title="StudyMate", version="1.0.0")


class AskRequest(BaseModel):
    message: str
    history: list[dict] | None = None


@app.on_event("startup")
def startup() -> None:
    """Create data folders and database tables on start."""
    config.ensure_dirs()
    db.connect()


@app.get("/api/health")
def health() -> dict:
    """Check that the app, the database, and the LLM connection are ready."""
    try:
        doc_count = db.query("SELECT COUNT(*) AS n FROM documents")[0]["n"]
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail="database not ready") from exc
    return {
        "status": "ok",
        "documents_count": doc_count,
        "llm_connected": llm.ping(),
    }


@app.post("/api/ask")
def ask_question(payload: AskRequest) -> dict:
    """Answer a question grounded in the user's uploaded material."""
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message is empty.")
    result = tutor.answer_question(payload.message.strip(), payload.history)
    return result


@app.post("/api/documents/upload")
def upload_document(file: UploadFile) -> dict:
    """Save, parse, chunk, embed, and index an uploaded study file."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {sorted(config.ALLOWED_EXTENSIONS)}",
        )

    # Save the upload to disk first.
    config.ensure_dirs()
    temp_id = uuid.uuid4().hex
    saved_path = os.path.join(config.UPLOAD_DIR, f"{temp_id}{ext}")
    with open(saved_path, "wb") as out:
        shutil.copyfileobj(file.file, out)

    if os.path.getsize(saved_path) > config.MAX_UPLOAD_BYTES:
        os.remove(saved_path)
        raise HTTPException(status_code=400, detail="File is too large.")

    try:
        doc_id = rag.ingest_file(saved_path, file.filename or saved_path)
    except ValueError as exc:
        os.remove(saved_path)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        # Clean up the temporary upload; the text lives in the database now.
        if os.path.exists(saved_path):
            os.remove(saved_path)

    row = db.query("SELECT id, filename, created_at FROM documents WHERE id = ?", (doc_id,))[0]
    return {"id": row["id"], "filename": row["filename"], "created_at": row["created_at"]}


@app.get("/api/documents")
def list_documents() -> dict:
    """List all uploaded documents."""
    rows = db.query("SELECT id, filename, created_at FROM documents ORDER BY created_at DESC")
    return {"documents": rows}


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str) -> dict:
    """Delete a document and all its chunks."""
    exists = db.query("SELECT id FROM documents WHERE id = ?", (doc_id,))
    if not exists:
        raise HTTPException(status_code=404, detail="Document not found.")
    rag.delete_document(doc_id)
    return {"deleted": True}


# Serve the built frontend if it exists (after `npm run build`).
public_dir = os.path.join("frontend", "dist")
if os.path.isdir(public_dir):
    app.mount("/", StaticFiles(directory=public_dir, html=True), name="public")
else:
    @app.get("/")
    def root() -> dict:
        text = "StudyMate API is running. Build the frontend with npm run build to see the UI."
        return {"message": text, "docs": "/docs", "health": "/api/health"}
