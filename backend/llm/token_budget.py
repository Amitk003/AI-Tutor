"""
Token Budget Manager.
Enforces model context window token limits (~4096 tokens), reserves output tokens (~1024 tokens),
and trims retrieved context while preserving top-ranked chunks.
"""

from typing import Any, Dict, List
from loguru import logger

from backend.core.config import settings


def count_tokens(text: str) -> int:
    """
    Approximates token count using standard 1 token ~= 4 characters ratio.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


class TokenBudgetManager:
    """Manages token allocation across system prompts, memory, context, and output reservations."""

    def __init__(
        self,
        max_context_tokens: int = settings.MAX_CONTEXT_TOKENS,
        max_output_tokens: int = settings.MAX_OUTPUT_TOKENS,
    ):
        self.max_context_tokens = max_context_tokens
        self.max_output_tokens = max_output_tokens

    @property
    def max_input_tokens(self) -> int:
        """Max tokens available for input prompt (Context Window - Output Reservation)."""
        return self.max_context_tokens - self.max_output_tokens

    def enforce_context_budget(
        self,
        system_prompt: str,
        user_question: str,
        memory_summary: str,
        sources: List[Dict[str, Any]],
        context_blocks: List[str],
    ) -> List[str]:
        """
        Trims context blocks if total input tokens exceed budget while preserving top-ranked blocks.

        Args:
            system_prompt: Base system prompt text.
            user_question: Current user question text.
            memory_summary: Summarized conversation memory.
            sources: List of citation source dicts.
            context_blocks: List of formatted markdown context blocks ordered by relevance.

        Returns:
            Trimmed list of context blocks that fit within token budget.
        """
        base_tokens = (
            count_tokens(system_prompt)
            + count_tokens(user_question)
            + count_tokens(memory_summary)
            + 100  # Safety buffer for XML tags & metadata headers
        )

        available_for_context = self.max_input_tokens - base_tokens
        logger.info(
            "Token Budget: max_input={inp} base_tokens={base} available_for_context={avail}",
            inp=self.max_input_tokens,
            base=base_tokens,
            avail=available_for_context,
        )

        fitted_blocks: List[str] = []
        accumulated_tokens = 0

        for block in context_blocks:
            block_toks = count_tokens(block)
            if accumulated_tokens + block_toks <= available_for_context:
                fitted_blocks.append(block)
                accumulated_tokens += block_toks
            else:
                logger.debug("Trimmed lower-ranked context block to fit within token budget.")

        return fitted_blocks


# Global token budget manager instance
token_budget_manager = TokenBudgetManager()
