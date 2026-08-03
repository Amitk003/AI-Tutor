"""
Teaching Modality Selector.
Determines optimal pedagogical presentation modalities (Text, Code Snippet, Markdown Table, Mermaid Diagram, Worked Example)
without requiring explicit student request.
"""

from typing import Any, Dict, List
from loguru import logger


class TeachingModalitySelector:
    """Selects dynamic presentation modalities for teaching explanations."""

    def select_modalities(
        self,
        strategy: str,
        query_intent: str = "CONCEPTUAL",
        concept_name: str = "",
        has_code_context: bool = False,
    ) -> Dict[str, Any]:
        """
        Determines presentation modalities and LLM formatting instructions.

        Modalities supported:
        - TEXT_EXPLANATION
        - CODE_SNIPPET
        - MARKDOWN_TABLE
        - MERMAID_DIAGRAM (Flowcharts, Sequence Diagrams)
        - WORKED_EXAMPLE
        """
        modalities: List[str] = ["TEXT_EXPLANATION"]
        formatting_instructions: List[str] = []

        concept_lower = concept_name.lower()

        # 1. Check if comparison / structural concept -> Markdown Table
        if strategy == "Comparison" or "vs" in concept_lower or "compare" in concept_lower:
            modalities.append("MARKDOWN_TABLE")
            formatting_instructions.append(
                "Include a structured Markdown Comparison Table contrasting key properties."
            )

        # 2. Check if procedural / architectural / flow concept -> Mermaid Diagram
        if (
            query_intent == "PROCEDURAL"
            or "flow" in concept_lower
            or "architecture" in concept_lower
            or "process" in concept_lower
            or "tree" in concept_lower
            or "graph" in concept_lower
            or "pipeline" in concept_lower
            or strategy in ["Step-by-step", "Socratic"]
        ):
            modalities.append("MERMAID_DIAGRAM")
            formatting_instructions.append(
                "Render a clean Mermaid.js flowchart (```mermaid\\ngraph TD\\n...\\n```) illustrating the process flow or hierarchy."
            )

        # 3. Check if algorithm / code implementation -> Code Snippet
        if has_code_context or "code" in concept_lower or "algorithm" in concept_lower or strategy == "Example-driven":
            modalities.append("CODE_SNIPPET")
            formatting_instructions.append(
                "Provide a clean, commented Python/pseudocode code snippet demonstrating the concept."
            )

        logger.info("Selected teaching modalities for concept='{c}': {m}", c=concept_name, m=modalities)

        return {
            "modalities": modalities,
            "formatting_instructions": "\n".join(formatting_instructions),
        }


# Global teaching modality selector instance
modality_selector = TeachingModalitySelector()
