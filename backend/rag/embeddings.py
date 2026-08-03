"""
Batch Embedding Service using Sentence Transformers.
Generates 384d / 1024d normalized vector embeddings for document chunks in batches.
Supports model caching and incremental processing.
"""

from typing import List, Optional
import numpy as np
from loguru import logger

from backend.core.config import settings


class BatchEmbeddingService:
    """Sentence Transformers batch embedding service."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self._model = None

    def _load_model(self):
        """Lazy loads SentenceTransformer model."""
        if self._model is None:
            logger.info("Loading SentenceTransformer embedding model: {name}", name=self.model_name)
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                logger.info("Embedding model loaded successfully.")
            except Exception as e:
                logger.error("Failed to load SentenceTransformer model '{name}': {err}", name=self.model_name, err=str(e))
                raise

    def embed_text(self, text: str) -> List[float]:
        """Generates a single normalized 384d/1024d vector embedding."""
        self._load_model()
        vector = self._model.encode(text, normalize_embeddings=True)
        return vector.tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generates normalized vector embeddings for a batch of text strings.

        Args:
            texts: List of text strings to embed.
            batch_size: Batch size for model execution (default: 32).

        Returns:
            List of float vector lists matching input text length.
        """
        if not texts:
            return []

        self._load_model()
        logger.info("Generating batch embeddings: count={count} batch_size={size}", count=len(texts), size=batch_size)

        vectors = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return vectors.tolist()


# Global embedding service singleton
embedding_service = BatchEmbeddingService()
