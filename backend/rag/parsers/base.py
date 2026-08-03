"""
Abstract Base Document Parser Interface.
Defines common contract for multi-format document parsers.
"""

from abc import ABC, abstractmethod
from typing import List
from backend.rag.schemas import ExtractedElement


class BaseDocumentParser(ABC):
    """Abstract interface for format-specific document layout extractors."""

    @abstractmethod
    async def parse(self, file_path: str) -> List[ExtractedElement]:
        """
        Parses document file and returns list of layout-preserved ExtractedElements.

        Args:
            file_path: Absolute filesystem path to document.

        Returns:
            List of ExtractedElement blocks with headings, paragraphs, and page numbers.
        """
        pass

    @abstractmethod
    def supports_extension(self, extension: str) -> bool:
        """Returns True if this parser supports the given file extension (e.g. '.pdf')."""
        pass
