"""
Dedicated Modular Prompt Builder.
Assembles deterministic, modular, and sandboxed prompts from templates without polluting API routes.
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from backend.llm.security import prompt_sanitizer
from backend.llm.templates import BASE_SYSTEM_PROMPT, TEMPLATES_MAP
from backend.llm.token_budget import token_budget_manager


class PromptBuilder:
    """Assembles modular prompts for RAG LLM inference."""

    def build_prompt(
        self,
        template_type: str = "explain",
        user_question: str = "",
        retrieved_context: str = "",
        conversation_memory: str = "",
        grade_level: str = "Undergraduate",
        explanation_style: str = "Academic",
        system_prompt_override: Optional[str] = None,
    ) -> str:
        """
        Assembles complete deterministic prompt payload.

        Args:
            template_type: One of 'explain', 'summary', 'quiz', 'flashcards', 'code_explanation', 'comparison', 'revision'.
            user_question: Student question string.
            retrieved_context: Formatted context blocks from hybrid retrieval.
            conversation_memory: Compressed history string.
            grade_level: Student academic grade level.
            explanation_style: Socratic, Analogical, Academic, or ELI5.
            system_prompt_override: Custom system prompt if specified.

        Returns:
            Fully assembled, sanitized, and sandboxed prompt string.
        """
        template = TEMPLATES_MAP.get(template_type.lower(), TEMPLATES_MAP["explain"])
        system_prompt = system_prompt_override or BASE_SYSTEM_PROMPT

        # Sanitize and wrap retrieved context in XML sandbox
        sandboxed_context = prompt_sanitizer.wrap_in_sandbox(retrieved_context)

        # Format prompt payload
        assembled_prompt = template.format(
            system_prompt=system_prompt.strip(),
            grade_level=grade_level,
            explanation_style=explanation_style,
            conversation_memory=conversation_memory.strip() or "None",
            sandboxed_context=sandboxed_context,
            user_question=user_question.strip(),
        )

        logger.info(
            "Prompt assembled: template={tpl} total_chars={chars}",
            tpl=template_type,
            chars=len(assembled_prompt),
        )
        return assembled_prompt


# Global prompt builder singleton
prompt_builder = PromptBuilder()
