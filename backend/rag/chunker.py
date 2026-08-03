"""
Hierarchical Parent-Child & Semantic Document Chunker.
Converts structured ExtractedElements into ~300 token child chunks linked to ~1200 token parent context.
Attaches rich metadata (heading path, section title, page labels, character bounds).
"""

from typing import Any, Dict, List, Tuple
from loguru import logger

from backend.rag.schemas import ElementType, ExtractedElement, StructuredChunk


class HierarchicalChunker:
    """Semantic Parent-Child document chunking engine."""

    def __init__(
        self,
        target_child_chars: int = 1200,   # ~300 words / tokens
        target_parent_chars: int = 4800,  # ~1200 words / tokens
        overlap_chars: int = 200,         # ~50 words overlap
    ):
        self.target_child_chars = target_child_chars
        self.target_parent_chars = target_parent_chars
        self.overlap_chars = overlap_chars

    def chunk_elements(self, elements: List[ExtractedElement]) -> List[StructuredChunk]:
        """
        Chunks extracted layout elements into structured Parent-Child chunks.

        Args:
            elements: List of layout ExtractedElement blocks.

        Returns:
            List of StructuredChunk models ready for database persistence.
        """
        if not elements:
            return []

        chunks: List[StructuredChunk] = []

        # 1. Group elements into text blocks while preserving heading breadcrumbs
        flat_blocks: List[Tuple[str, int, List[str], str]] = []
        for elem in elements:
            content = elem.content.strip()
            if not content:
                continue

            page_label = f"Page {elem.page_number}"
            heading_breadcrumb = elem.heading_path or []
            section_title = heading_breadcrumb[-1] if heading_breadcrumb else ""

            # Tables are treated as distinct atomic blocks
            if elem.element_type == ElementType.TABLE:
                table_content = f"**[TABLE]**\n{content}"
                flat_blocks.append((table_content, elem.page_number, heading_breadcrumb, section_title))
            else:
                flat_blocks.append((content, elem.page_number, heading_breadcrumb, section_title))

        # 2. Build combined full text sequence to generate parent sliding context
        full_text_parts = [block[0] for block in flat_blocks]
        full_text = "\n\n".join(full_text_parts)

        # 3. Slide child window across elements
        current_child_text = ""
        current_heading_path: List[str] = []
        current_section = ""
        start_page = 1
        end_page = 1
        chunk_idx = 0
        char_pos = 0

        for block_text, page_num, heading_path, section_title in flat_blocks:
            if not current_child_text:
                start_page = page_num
                current_heading_path = heading_path
                current_section = section_title

            current_child_text += block_text + "\n\n"
            end_page = page_num

            # Check if child window target size reached
            if len(current_child_text) >= self.target_child_chars:
                child_clean = current_child_text.strip()
                parent_context = self._extract_parent_context(
                    full_text, char_pos, len(child_clean)
                )

                page_label = f"Page {start_page}" if start_page == end_page else f"Pages {start_page}-{end_page}"

                chunk = StructuredChunk(
                    chunk_index=chunk_idx,
                    child_content=child_clean,
                    parent_content=parent_context,
                    page_label=page_label,
                    heading_path=current_heading_path,
                    section_title=current_section,
                    metadata={
                        "start_page": start_page,
                        "end_page": end_page,
                        "char_length": len(child_clean),
                        "heading_depth": len(current_heading_path),
                    },
                )
                chunks.append(chunk)

                char_pos += len(child_clean) - self.overlap_chars
                chunk_idx += 1

                # Retain overlap for next child window
                if len(child_clean) > self.overlap_chars:
                    current_child_text = child_clean[-self.overlap_chars :] + "\n\n"
                else:
                    current_child_text = ""

        # Flushes final residual chunk if any text remains
        if current_child_text.strip():
            child_clean = current_child_text.strip()
            parent_context = self._extract_parent_context(
                full_text, char_pos, len(child_clean)
            )

            page_label = f"Page {start_page}" if start_page == end_page else f"Pages {start_page}-{end_page}"

            chunk = StructuredChunk(
                chunk_index=chunk_idx,
                child_content=child_clean,
                parent_content=parent_context,
                page_label=page_label,
                heading_path=current_heading_path,
                section_title=current_section,
                metadata={
                    "start_page": start_page,
                    "end_page": end_page,
                    "char_length": len(child_clean),
                    "heading_depth": len(current_heading_path),
                },
            )
            chunks.append(chunk)

        logger.info(
            "Document chunked successfully: total_elements={elems} generated_chunks={chunks}",
            elems=len(elements),
            chunks=len(chunks),
        )
        return chunks

    def _extract_parent_context(self, full_text: str, child_start: int, child_len: int) -> str:
        """
        Extracts broader parent context (~1200 tokens / 4800 chars) surrounding the child window position.
        """
        half_parent = self.target_parent_chars // 2
        start_idx = max(0, child_start - half_parent)
        end_idx = min(len(full_text), child_start + child_len + half_parent)
        return full_text[start_idx:end_idx].strip()
