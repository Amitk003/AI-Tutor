"""StudyMate backend application.

One FastAPI server that serves both the API and the built frontend.
"""

import os

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from backend import config
from backend import db
from backend.llm import llm

app = FastAPI(title="StudyMate", version="1.0.0")


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


# Serve the built frontend if it exists (after `npm run build`).
public_dir = os.path.join("frontend", "dist")
if os.path.isdir(public_dir):
    app.mount("/", StaticFiles(directory=public_dir, html=True), name="public")
else:
    @app.get("/")
    def root() -> dict:
        text = "StudyMate API is running. Build the frontend with npm run build to see the UI."
        return {"message": text, "docs": "/docs", "health": "/api/health"}
