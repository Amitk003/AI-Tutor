"""
Tutor Decision Engine.
Central pedagogical brain orchestrating strategy selection, difficulty adaptation,
modality selection (tables, diagrams, code), misconception detection, prerequisite checks, prompt composition, and LLM generation.
"""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.core.config import settings
from backend.core.events import ExplanationGenerated, event_dispatcher
from backend.llm.gateway import LLMGatewayFactory
from backend.rag.hybrid_retriever import hybrid_retriever
from backend.tutor.difficulty_controller import difficulty_controller
from backend.tutor.misconception_detector import misconception_detector
from backend.tutor.modality_selector import modality_selector
from backend.tutor.pedagogical_planner import pedagogical_planner
from backend.tutor.prerequisite_engine import prerequisite_engine
from backend.tutor.prompt_composer import tutor_prompt_composer


class TutorDecisionEngine:
    """Central pedagogical tutor decision engine."""

    async def orchestrate_adaptive_explanation(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        question: str,
        concept_name: str = "General Topic",
        student_theta: float = 0.0,
        student_mastery: float = 0.5,
        mastered_concepts: Optional[List[str]] = None,
        document_ids: Optional[List[uuid.UUID]] = None,
    ) -> Dict[str, Any]:
        """
        Orchestrates complete adaptive teaching workflow.
        """
        logger.info("Orchestrating adaptive explanation for user_id={uid} concept='{c}'", uid=user_id, c=concept_name)

        # 1. Retrieve Course Context
        retrieval = await hybrid_retriever.retrieve_hybrid(
            user_id=user_id,
            query_text=question,
            document_ids=document_ids,
            session=session,
        )

        # Refusal check
        if retrieval.get("is_refusal", False):
            return {
                "answer": retrieval["refusal_reason"],
                "is_refusal": True,
                "confidence_score": retrieval.get("confidence_score", 0.0),
                "strategy": "Refusal",
                "citations": [],
            }

        # 2. Select Pedagogical Strategy
        query_intent = retrieval.get("processed_query", {}).get("intent", "CONCEPTUAL")
        strategy_res = await pedagogical_planner.select_strategy(
            user_id=user_id,
            theta=student_theta,
            mastery=student_mastery,
            query_intent=query_intent,
        )

        # 3. Determine Difficulty & Pacing
        diff_info = difficulty_controller.determine_difficulty(
            theta=student_theta,
            mastery=student_mastery,
        )

        # 4. Select Presentation Modalities (Markdown tables, Mermaid diagrams, Code snippets)
        modality_res = modality_selector.select_modalities(
            strategy=strategy_res["strategy"],
            query_intent=query_intent,
            concept_name=concept_name,
        )

        # 5. Misconception Check
        misc_info = await misconception_detector.check_misconceptions(
            user_id=user_id,
            concept_name=concept_name,
            recent_questions=[question],
        )

        # 6. Prerequisite Check
        prereq_info = prerequisite_engine.check_prerequisites(
            target_concept=concept_name,
            mastered_concepts=mastered_concepts or [],
        )

        # 7. Compose Teaching Prompt with Modality Instructions
        prompt = tutor_prompt_composer.compose_tutor_prompt(
            strategy=strategy_res["strategy"],
            difficulty_info=diff_info,
            user_question=question,
            retrieved_context=retrieval["formatted_context"],
            misconception_detail=misc_info.get("detail"),
            missing_prereqs=prereq_info.get("missing_prerequisites"),
            modality_instructions=modality_res["formatting_instructions"],
        )

        # 8. Execute LLM Generation via Gateway
        gateway = LLMGatewayFactory.get_gateway()
        answer = await gateway.generate(prompt=prompt)

        # Emit ExplanationGenerated domain event
        await event_dispatcher.emit(
            ExplanationGenerated(
                user_id=user_id,
                concept_name=concept_name,
                strategy=strategy_res["strategy"],
                difficulty_level=diff_info["difficulty_level"],
            )
        )

        return {
            "answer": answer,
            "is_refusal": False,
            "pedagogy": {
                "strategy": strategy_res["strategy"],
                "rationale": strategy_res["rationale"],
                "difficulty_level": diff_info["difficulty_level"],
                "explanation_depth": diff_info["explanation_depth"],
                "pacing": diff_info["pacing"],
                "selected_modalities": modality_res["modalities"],
            },
            "misconception_detected": misc_info["has_misconception"],
            "missing_prerequisites": prereq_info["missing_prerequisites"],
            "citations": retrieval["citations"],
            "confidence_score": retrieval["confidence_score"],
        }


# Global tutor decision engine instance
tutor_decision_engine = TutorDecisionEngine()
