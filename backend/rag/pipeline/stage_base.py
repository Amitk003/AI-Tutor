"""
Abstract Pipeline Stage Interface.
"""

from abc import ABC, abstractmethod
from backend.rag.pipeline.context import IngestionContext


class PipelineStage(ABC):
    """Abstract stage in the event-driven document ingestion pipeline."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of stage matching DocumentProcessingStatus constant."""
        pass

    @abstractmethod
    async def execute(self, ctx: IngestionContext) -> IngestionContext:
        """
        Executes stage logic and returns updated IngestionContext.

        Args:
            ctx: Current IngestionContext instance.

        Returns:
            Updated IngestionContext.
        """
        pass
