"""
Prerequisite Engine.
Uses ConceptKnowledgeGraph to recommend prerequisite concepts before introducing advanced topics.
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from backend.student_model.concept_graph import ConceptKnowledgeGraph, concept_graph


class PrerequisiteEngine:
    """Recommends prerequisite review based on knowledge graph dependencies."""

    def __init__(self, graph: Optional[ConceptKnowledgeGraph] = None):
        self.graph = graph or concept_graph

    def check_prerequisites(self, target_concept: str, mastered_concepts: List[str]) -> Dict[str, Any]:
        """
        Checks unfulfilled prerequisites for target concept against student mastered list.
        """
        prereqs = self.graph.get_prerequisites(target_concept)
        missing_prereqs = [p for p in prereqs if p not in mastered_concepts]

        needs_prereq_review = len(missing_prereqs) > 0

        logger.debug("Prerequisite check for '{c}': missing={m}", c=target_concept, m=missing_prereqs)

        return {
            "target_concept": target_concept,
            "needs_prereq_review": needs_prereq_review,
            "missing_prerequisites": missing_prereqs,
        }


# Global prerequisite engine instance
prerequisite_engine = PrerequisiteEngine()
