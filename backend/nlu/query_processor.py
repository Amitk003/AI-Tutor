"""
Query Processing Layer & Intent Classification Engine.
Provides query normalization, synonym expansion, query rewriting,
intent classification, and adaptive Top-K estimation.
"""

import re
from dataclasses import dataclass, field
from typing import List, Set
from loguru import logger

# Domain term synonym dictionary for AI / Computer Science
DOMAIN_SYNONYMS = {
    "ml": ["machine learning", "pattern recognition"],
    "dl": ["deep learning", "neural networks"],
    "nn": ["neural network", "deep model"],
    "gradient descent": ["optimization", "loss minimization", "backpropagation"],
    "backprop": ["backpropagation", "chain rule", "gradient calculation"],
    "rag": ["retrieval augmented generation", "vector search"],
    "llm": ["large language model", "foundation model"],
    "irt": ["item response theory", "latent trait theory"],
}


@dataclass
class ProcessedQuery:
    """Encapsulates processed query variants, intent, and adaptive Top-K."""

    raw_query: str
    normalized_query: str
    expanded_terms: List[str] = field(default_factory=list)
    query_variations: List[str] = field(default_factory=list)
    intent: str = "CONCEPTUAL"
    adaptive_top_k: int = 20


class QueryProcessor:
    """NLU Query processing engine."""

    def normalize(self, query: str) -> str:
        """Normalizes query text: lowercasing, punctuation cleanup, space collapsing."""
        text = query.lower().strip()
        text = re.sub(r"[^\w\s\-]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def expand_synonyms(self, normalized_query: str) -> List[str]:
        """Expands domain-specific terms using synonym map."""
        expanded: Set[str] = set()
        words = normalized_query.split()

        for phrase, synonyms in DOMAIN_SYNONYMS.items():
            if phrase in normalized_query:
                for syn in synonyms:
                    expanded.add(syn)

        for word in words:
            if word in DOMAIN_SYNONYMS:
                for syn in DOMAIN_SYNONYMS[word]:
                    expanded.add(syn)

        return list(expanded)

    def classify_intent(self, normalized_query: str) -> str:
        """Classifies query intent into FACTUAL, DEFINITIONAL, PROCEDURAL, or CONCEPTUAL."""
        if any(w in normalized_query for w in ["what is", "define", "definition", "meaning of"]):
            return "DEFINITIONAL"
        elif any(w in normalized_query for w in ["how to", "steps", "algorithm", "procedure", "process"]):
            return "PROCEDURAL"
        elif any(w in normalized_query for w in ["who", "when", "where", "exact", "number", "formula"]):
            return "FACTUAL"
        else:
            return "CONCEPTUAL"

    def determine_adaptive_top_k(self, normalized_query: str, intent: str) -> int:
        """Estimates adaptive Top-K candidate count based on query complexity and intent."""
        length = len(normalized_query.split())

        if intent == "DEFINITIONAL":
            return 10
        elif intent == "FACTUAL":
            return 12
        elif intent == "PROCEDURAL":
            return 25
        elif length > 10:  # Complex long query
            return 30
        else:
            return 20

    def process(self, raw_query: str) -> ProcessedQuery:
        """
        Executes complete query processing pipeline.
        """
        norm_q = self.normalize(raw_query)
        synonyms = self.expand_synonyms(norm_q)
        intent = self.classify_intent(norm_q)
        top_k = self.determine_adaptive_top_k(norm_q, intent)

        # Build query variations including expanded terms
        variations = [norm_q]
        if synonyms:
            variations.append(f"{norm_q} {' '.join(synonyms[:3])}")

        logger.info(
            "Query processed: raw='{raw}' intent={intent} adaptive_k={k} synonyms={syn_count}",
            raw=raw_query[:30],
            intent=intent,
            k=top_k,
            syn_count=len(synonyms),
        )

        return ProcessedQuery(
            raw_query=raw_query,
            normalized_query=norm_q,
            expanded_terms=synonyms,
            query_variations=variations,
            intent=intent,
            adaptive_top_k=top_k,
        )


# Global query processor instance
query_processor = QueryProcessor()
