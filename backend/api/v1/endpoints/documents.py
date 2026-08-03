"""
Document Management REST API v1 Router.
Provides RESTful endpoints for document file uploading, SHA-256 deduplication,
pipeline status tracking, listing user materials, and soft deletion.
"""

import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.authentication.deps import get_current_active_user
from backend.core.config import settings
from backend.core.exceptions import NotFoundException, ValidationException
from backend.database.models.document import Document
from backend.database.models.user import User
from backend.database.repositories.document_repository import DocumentRepository
from backend.database.session import get_db
from backend.services.ai_orchestrator import AIOrchestrator
from backend.utils.validators import validate_file_extension, validate_file_size
from backend.workers.tasks import process_document_task

router = APIRouter(prefix="/documents")


@router.post(
    "/upload",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload study material document or URL",
)
async def upload_document(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Accepts study material file upload (PDF, DOCX, PPTX, TXT) or web URL payload.
    Executes SHA-256 deduplication, registers document, and triggers pipeline.
    """
    if not file and not url:
        raise ValidationException("Either a file upload or a valid URL must be provided.")

    orchestrator = AIOrchestrator(session)

    if file:
        filename = file.filename or "uploaded_document"
        ext = validate_file_extension(filename)

        # Read file contents
        content = await file.read()
        validate_file_size(len(content))

        # Save to local upload directory
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4()}{ext}")
        with open(file_path, "wb") as f:
            f.write(content)

        doc = await orchestrator.register_uploaded_document(
            user_id=current_user.id,
            title=filename,
            file_type=ext.replace(".", "").upper(),
            file_path=file_path,
            file_size_bytes=len(content),
        )
    else:
        # URL payload
        target_url = url.strip()
        doc = await orchestrator.register_uploaded_document(
            user_id=current_user.id,
            title=target_url,
            file_type="URL",
            file_path=target_url,
            file_size_bytes=0,
        )

    # Queue the expensive ingestion pipeline. The status endpoint exposes each checkpoint.
    try:
        process_document_task.delay(str(doc.id), str(current_user.id))
    except Exception as exc:
        logger.exception("Could not queue document ingestion: document_id={id}", id=doc.id)
        raise ValidationException(
            "Document was stored but could not be queued for ingestion. Please retry shortly.",
            {"document_id": str(doc.id)},
        ) from exc

    return {
        "message": "Document uploaded and queued for indexing.",
        "document_id": doc.id,
        "title": doc.title,
        "status": doc.status,
        "chunk_count": doc.chunk_count,
        "embedding_model": doc.embedding_model_name,
    }


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List user documents",
)
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Lists uploaded study materials owned by the authenticated user.
    """
    repo = DocumentRepository(session)
    docs = await repo.get_user_documents(user_id=current_user.id, skip=skip, limit=limit)
    return [
        {
            "id": doc.id,
            "title": doc.title,
            "file_type": doc.file_type,
            "status": doc.status,
            "chunk_count": doc.chunk_count,
            "file_size_bytes": doc.file_size_bytes,
            "embedding_model": doc.embedding_model_name,
            "created_at": doc.created_at,
        }
        for doc in docs
    ]


@router.get(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Inspect document details and chunks status",
)
async def get_document_details(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Inspects document metadata and state machine processing status.
    """
    repo = DocumentRepository(session)
    doc = await repo.get_by_id(document_id, user_id=current_user.id)
    if not doc:
        raise NotFoundException("Document", document_id)

    return {
        "id": doc.id,
        "title": doc.title,
        "file_type": doc.file_type,
        "status": doc.status,
        "chunk_count": doc.chunk_count,
        "file_hash": doc.file_hash,
        "embedding_model": doc.embedding_model_name,
        "indexed_at": doc.indexed_at,
        "created_at": doc.created_at,
    }


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Soft-delete document and remove vectors",
)
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Soft-deletes a document and deletes vectors from Qdrant storage.
    """
    repo = DocumentRepository(session)
    doc = await repo.get_by_id(document_id, user_id=current_user.id)
    if not doc:
        raise NotFoundException("Document", document_id)

    await repo.soft_delete(document_id, user_id=current_user.id)
    await session.commit()

    # Delete vectors from Qdrant
    from backend.vector_store.qdrant_client import qdrant_store
    qdrant_store.delete_document_vectors(document_id, current_user.id)

    return {"message": f"Document '{doc.title}' deleted successfully.", "document_id": document_id}
