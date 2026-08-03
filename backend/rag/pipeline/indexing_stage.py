"""
Qdrant Indexing Pipeline Stage.
Upserts vector points and rich payload metadata to Qdrant collection.
Emits DocumentIndexedEvent.
"""

import uuid

from loguru import logger
from backend.core.events import DocumentIndexedEvent, event_dispatcher
from backend.database.models.document import DocumentProcessingStatus
from backend.rag.pipeline.context import IngestionContext
from backend.rag.pipeline.stage_base import PipelineStage
from backend.vector_store.qdrant_client import QdrantVectorStore, qdrant_store


class IndexingStage(PipelineStage):
    """Executes Qdrant vector indexing stage."""

    def __init__(self, store: QdrantVectorStore = None):
        self.store = store or qdrant_store

    @property
    def name(self) -> str:
        return DocumentProcessingStatus.INDEXING

    async def execute(self, ctx: IngestionContext) -> IngestionContext:
        vectors = ctx.metadata.get("vectors", [])
        if not ctx.chunks or not vectors:
            logger.warning("No chunks or vectors to index for doc_id={id}", id=ctx.document_id)
            return ctx

        logger.info("Executing INDEXING stage for doc_id={id} vectors={count}", id=ctx.document_id, count=len(vectors))

        # Ensure collection exists
        vector_dim = len(vectors[0]) if vectors else 384
        self.store.ensure_collection_exists(vector_size=vector_dim)

        points = []
        for idx, (chunk, vector) in enumerate(zip(ctx.chunks, vectors)):
            # Persist the exact Qdrant point ID in the relational chunk record.
            vector_uuid = chunk.metadata.get("vector_id") or chunk.metadata.get("id")
            if not vector_uuid:
                vector_uuid = str(uuid.uuid4())
                chunk.metadata["vector_id"] = vector_uuid

            points.append({
                "id": str(vector_uuid),
                "vector": vector,
                "payload": {
                    "document_id": str(ctx.document_id),
                    "user_id": str(ctx.user_id),
                    "chunk_index": chunk.chunk_index,
                    "page_label": chunk.page_label,
                    "section_title": chunk.section_title,
                    "heading_path": chunk.heading_path,
                    "child_content": chunk.child_content,
                    "parent_content": chunk.parent_content,
                    "metadata": chunk.metadata,
                },
            })

        self.store.upsert_points(points)
        ctx.current_stage = self.name

        # Emit DocumentIndexedEvent
        await event_dispatcher.emit(
            DocumentIndexedEvent(
                document_id=ctx.document_id,
                collection_name=self.store.collection_name,
                point_count=len(points),
            )
        )

        return ctx
