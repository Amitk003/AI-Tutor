"""
Explainable Learning Recommendation Engine.
Generates deterministic, explainable recommendations for next topic, prerequisite review, and weak concept revision.
Emits RevisionRecommended domain event.
"""

import uuid
from typing import Any, Dict, List, Optional
from loguru import logger

from backend.core.events import RevisionRecommended, event_dispatcher
from backend.student_model.concept_graph import ConceptKnowledgeGraph, concept_graph
from backend.student_model.student_memory import StudentMemory


class RecommendationEngine:
    """Deterministic, explainable learning recommendation engine."""

    def __init__(self, graph: Optional[ConceptKnowledgeGraph] = None):
        self.graph = graph or concept_graph

    async def generate_recommendations(
        self,
        user_id: uuid.UUID,
        current_concept: str,
        weak_topics: List[Dict[str, Any]],
        memory: Optional[StudentMemory] = None,
    ) -> Dict[str, Any]:
        """
        Generates explainable learning recommendations based on concept graph prerequisites and weak topics.

        Returns:
            Dict containing recommended_next_topic, prerequisite_recommendation, revision_recommendations, and rationale.
        """
        recommendations = {
            "recommended_next_topic": None,
            "prerequisite_recommendation": None,
            "revision_recommendations": [],
            "explanations": [],
        }

        # 1. Check if current concept has unfulfilled prerequisites
        prereqs = self.graph.get_prerequisites(current_concept)
        if prereqs:
            # Check if any prerequisite is in weak topics
            weak_prereq = next((wt["concept_name"] for wt in weak_topics if wt["concept_name"] in prereqs), None)
            if weak_prereq:
                recommendations["prerequisite_recommendation"] = weak_prereq
                explanation = f"You should review prerequisite '{weak_prereq}' before continuing with '{current_concept}' to build a solid foundation."
                recommendations["explanations"].append(explanation)

                await event_dispatcher.emit(
                    RevisionRecommended(
                        user_id=user_id,
                        concept_name=weak_prereq,
                        prerequisite=weak_prereq,
                        explanation=explanation,
                    )
                )

        # 2. Check weak topics needing revision
        for wt in weak_topics[:3]:
            concept = wt["concept_name"]
            reason = wt.get("reason", "Low mastery score")
            rec = {
                "concept_name": concept,
                "type": "REVISION",
                "explanation": f"Recommended for revision because: {reason}.",
            }
            recommendations["revision_recommendations"].append(rec)

        # 3. Unlocked next concepts
        dependents = self.graph.get_next_dependent_concepts(current_concept)
        if dependents:
            next_topic = dependents[0]
            recommendations["recommended_next_topic"] = next_topic
            recommendations["explanations"].append(
                f"Once you feel confident in '{current_concept}', move on to '{next_topic}'."
            )

        logger.info("Generated recommendations for user_id={uid} next='{n}'", uid=user_id, n=recommendations["recommended_next_topic"])
        return recommendations


# Global recommendation engine instance
recommendation_engine = RecommendationEngine()
