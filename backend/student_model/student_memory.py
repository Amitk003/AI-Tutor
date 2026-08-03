"""
Student Memory Module.
Maintains separated memory tiers: Recent Memory, Long-Term Memory, Topic Memory, and Revision Memory.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from loguru import logger


@dataclass
class MemoryItem:
    concept: str
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


class StudentMemory:
    """Multi-tiered memory store for a student."""

    def __init__(self, user_id: uuid.UUID):
        self.user_id = user_id
        self.recent_memory: List[MemoryItem] = []      # Last 10 interactions
        self.long_term_memory: List[MemoryItem] = []   # Enduring facts & preferences
        self.topic_memory: Dict[str, MemoryItem] = {}  # Map of topic -> latest mastery snapshot
        self.revision_memory: List[MemoryItem] = []    # Queue of concepts needing review

    def add_recent_interaction(self, concept: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Appends item to recent memory window (max 10 items)."""
        item = MemoryItem(concept=concept, content=content, metadata=metadata or {})
        self.recent_memory.append(item)
        if len(self.recent_memory) > 10:
            self.recent_memory.pop(0)

    def record_topic_snapshot(self, concept: str, mastery: float, status: str) -> None:
        """Records or updates topic memory snapshot."""
        item = MemoryItem(
            concept=concept,
            content=f"Mastery: {mastery:.2f} ({status})",
            metadata={"mastery": mastery, "status": status},
        )
        self.topic_memory[concept] = item

    def flag_for_revision(self, concept: str, reason: str) -> None:
        """Appends a weak topic to the revision memory queue."""
        item = MemoryItem(concept=concept, content=reason)
        # Avoid duplicate queued items
        if not any(m.concept == concept for m in self.revision_memory):
            self.revision_memory.append(item)
            logger.info("Flagged concept '{concept}' for revision memory.", concept=concept)

    def get_summary(self) -> Dict[str, Any]:
        """Returns structured summary across all 4 memory tiers."""
        return {
            "recent_count": len(self.recent_memory),
            "long_term_count": len(self.long_term_memory),
            "tracked_topics": list(self.topic_memory.keys()),
            "revision_queue": [m.concept for m in self.revision_memory],
        }
