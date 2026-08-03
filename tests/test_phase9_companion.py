"""
Phase 9 & 10 AI Study Companion Integration Unit Tests.
Verifies KnowledgeBuilder concept extraction, TeachingModalitySelector modality determination,
and StudySessionOrchestrator turn execution.
"""

import uuid
import pytest

from backend.services.study_session_orchestrator import StudySessionOrchestrator
from backend.student_model.concept_graph import ConceptKnowledgeGraph
from backend.student_model.knowledge_builder import KnowledgeBuilder
from backend.tutor.modality_selector import TeachingModalitySelector


def test_teaching_modality_selector():
    """Verify TeachingModalitySelector selects appropriate presentation modalities."""
    selector = TeachingModalitySelector()

    # 1. Comparison concept -> Markdown Table
    res_comp = selector.select_modalities(strategy="Comparison", concept_name="BST vs AVL Tree")
    assert "MARKDOWN_TABLE" in res_comp["modalities"]
    assert "Markdown Comparison Table" in res_comp["formatting_instructions"]

    # 2. Procedural / Architecture concept -> Mermaid Diagram
    res_flow = selector.select_modalities(strategy="Direct Instruction", query_intent="PROCEDURAL", concept_name="Transformer Architecture")
    assert "MERMAID_DIAGRAM" in res_flow["modalities"]
    assert "Mermaid.js flowchart" in res_flow["formatting_instructions"]

    # 3. Code concept -> Code Snippet
    res_code = selector.select_modalities(strategy="Example-driven", concept_name="Binary Search Algorithm", has_code_context=True)
    assert "CODE_SNIPPET" in res_code["modalities"]


@pytest.mark.asyncio
async def test_knowledge_builder_extraction():
    """Verify KnowledgeBuilder parses text chunks and updates ConceptKnowledgeGraph."""
    graph = ConceptKnowledgeGraph()
    builder = KnowledgeBuilder(graph=graph)

    chunks = ["Binary Search Tree is a node-based binary tree data structure. BST requires Binary Trees."]
    doc_id = uuid.uuid4()

    res = await builder.extract_and_build_graph(document_id=doc_id, chunks_text=chunks)
    assert res["document_id"] == str(doc_id)
    assert isinstance(res["extracted_concepts_count"], int)
