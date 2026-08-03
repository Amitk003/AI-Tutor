"""
Tutor Prompt Composer.
Assembles pedagogical teaching prompts dynamically incorporating strategy, difficulty level,
modality presentation instructions (Markdown tables, Mermaid diagrams), misconception history, and student psychometrics.
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from backend.llm.security import prompt_sanitizer


class TutorPromptComposer:
    """Composes specialized teaching prompts for LLM inference."""

    def compose_tutor_prompt(
        self,
        strategy: str,
        difficulty_info: Dict[str, Any],
        user_question: str,
        retrieved_context: str,
        misconception_detail: Optional[str] = None,
        missing_prereqs: Optional[List[str]] = None,
        modality_instructions: Optional[str] = None,
    ) -> str:
        """
        Composes specialized pedagogical prompt instruction payload.

        Args:
            strategy: Pedagogical strategy (Socratic, Feynman, Analogy, Step-by-step, Direct Instruction).
            difficulty_info: Dict containing difficulty_level, explanation_depth, example_count, pacing.
            user_question: Student question string.
            retrieved_context: Formatted context blocks from hybrid retrieval.
            misconception_detail: Optional misconception warning.
            missing_prereqs: Optional list of missing prerequisite concepts.
            modality_instructions: Optional Mermaid diagram or Markdown table formatting instructions.

        Returns:
            Fully composed teaching prompt string.
        """
        sandboxed_context = prompt_sanitizer.wrap_in_sandbox(retrieved_context)
        diff_level = difficulty_info.get("difficulty_level", "INTERMEDIATE")
        depth = difficulty_info.get("explanation_depth", "Standard Academic")
        example_count = difficulty_info.get("example_count", 1)

        misconception_block = ""
        if misconception_detail:
            misconception_block = f"\n=== MISCONCEPTION WARNING ===\nAddress student misunderstanding: {misconception_detail}\n"

        prereq_block = ""
        if missing_prereqs:
            prereq_block = f"\n=== MISSING PREREQUISITES ===\nRecommend reviewing prerequisite concepts: {', '.join(missing_prereqs)}\n"

        modality_block = ""
        if modality_instructions:
            modality_block = f"\n=== PRESENTATION FORMATTING INSTRUCTIONS ===\n{modality_instructions}\n"

        prompt = f"""
=== PEDAGOGICAL TUTOR DIRECTIVES ===
Teaching Strategy: {strategy}
Target Difficulty Level: {diff_level}
Explanation Depth: {depth}
Required Examples: {example_count}

{misconception_block}{prereq_block}{modality_block}
=== RETRIEVED COURSE MATERIALS ===
{sandboxed_context}

=== STUDENT QUESTION ===
{user_question}

=== TEACHING INSTRUCTIONS ===
1. Teach using the {strategy} pedagogical strategy.
2. Adapt explanation vocabulary for a {diff_level} student level.
3. Provide exactly {example_count} concrete example(s).
4. Cite source page labels inline using format [Page X, Section Title].
"""
        logger.info("Tutor prompt composed: strategy='{s}' level='{l}'", s=strategy, l=diff_level)
        return prompt.strip()


# Global tutor prompt composer instance
tutor_prompt_composer = TutorPromptComposer()
