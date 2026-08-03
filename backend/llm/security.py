"""
Prompt Injection Protection & Security Sanitizer.
Sanitizes retrieved document context, strips special LLM control tags,
and wraps context in sandbox tags to prevent instruction override attacks.
"""

import re
from loguru import logger

# Regex patterns matching prompt injection keywords and LLM chat control tags
SPECIAL_CONTROL_TAGS = re.compile(
    r"(<\|im_start\|>|<\|im_end\|>|\[INST\]|\[/INST\]|<\|endoftext\|>|<s>|</s>|<\|system\|>|<\|user\|>|<\|assistant\|>)",
    re.IGNORECASE,
)

MALICIOUS_INSTRUCTION_PATTERNS = re.compile(
    r"(ignore\s+(all\s+)?(previous|above)\s+instructions|system\s+prompt\s*:|override\s+system\s+directives|you\s+are\s+now\s+a\s+|disregard\s+all\s+prior)",
    re.IGNORECASE,
)


class PromptSecuritySanitizer:
    """Sanitizes context inputs to mitigate prompt injection and template breakout attacks."""

    def sanitize_context_text(self, text: str) -> str:
        """
        Strips dangerous chat control tags and neutralizes embedded instruction overrides.

        Mitigation Strategy:
        1. Strips LLM special chat syntax (<|im_start|>, [INST], etc.).
        2. Neutralizes prompt injection phrases by escaping colons and wrapping in quotes.
        3. Encloses sanitized text inside <retrieved_context_sandbox> XML tags.
        """
        if not text:
            return ""

        # 1. Strip special control tokens
        sanitized = SPECIAL_CONTROL_TAGS.sub("", text)

        # 2. Defuse malicious instruction phrases
        def _defuse(match):
            matched_str = match.group(0)
            logger.warning("Prompt injection pattern detected and defused: '{match}'", match=matched_str)
            return f"[DEFUSED_TEXT: '{matched_str}']"

        sanitized = MALICIOUS_INSTRUCTION_PATTERNS.sub(_defuse, sanitized)
        return sanitized.strip()

    def wrap_in_sandbox(self, context_text: str) -> str:
        """Wraps context text in strict XML sandbox boundaries."""
        sanitized = self.sanitize_context_text(context_text)
        return (
            "<retrieved_context_sandbox>\n"
            f"{sanitized}\n"
            "</retrieved_context_sandbox>"
        )


# Global sanitizer singleton
prompt_sanitizer = PromptSecuritySanitizer()
