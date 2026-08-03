"""
Automated Knowledge Construction Engine.
Parses ingested study material document chunks to extract concept nodes, descriptions,
and prerequisite dependency edges, populating the ConceptKnowledgeGraph automatically.
"""

import json
import uuid
from typing import Any, Dict, List, Optional
from loguru import logger

from backend.llm.gateway import LLMGatewayFactory
from backend.student_model.concept_graph import ConceptKnowledgeGraph, concept_graph


class KnowledgeBuilder:
    """Extracts concept nodes and prerequisite dependency edges from study material."""

    def __init__(self, graph: Optional[ConceptKnowledgeGraph] = None):
        self.graph = graph or concept_graph

    async def extract_and_build_graph(
        self,
        document_id: uuid.UUID,
        chunks_text: List[str],
    ) -> Dict[str, Any]:
        """
        Parses document chunks and populates ConceptKnowledgeGraph.
        """
        combined_sample = "\n---\n".join(chunks_text[:5])
        prompt = f"""
=== CONCEPT EXTRACTOR & DEPENDENCY MAPPER ===
Study Material Text Sample:
{combined_sample[:2500]}

=== INSTRUCTIONS ===
Extract the core academic/technical concepts and prerequisite dependencies from the text sample.
Output ONLY a raw JSON object strictly adhering to this format:
{{
  "concepts": [
    {{
      "name": "Concept Name",
      "description": "Brief 1-sentence definition",
      "prerequisites": ["Prerequisite Concept Name"]
    }}
  ]
}}
Do NOT wrap JSON in markdown blocks.
"""
        gateway = LLMGatewayFactory.get_gateway()
        extracted_count = 0

        try:
            raw_response = await gateway.generate(prompt=prompt)
            clean_json = raw_response.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]
            clean_json = clean_json.strip()

            parsed = json.loads(clean_json)
            concepts_list = parsed.get("concepts", [])

            for item in concepts_list:
                c_name = item.get("name", "").strip()
                c_desc = item.get("description", "").strip()
                prereqs = item.get("prerequisites", [])

                if c_name:
                    self.graph.add_concept(name=c_name, description=c_desc)
                    extracted_count += 1

                    for p in prereqs:
                        p_name = str(p).strip()
                        if p_name:
                            self.graph.add_prerequisite(concept_name=c_name, prerequisite_name=p_name)

            logger.info("Extracted {n} concept nodes for document_id={did}", n=extracted_count, did=document_id)

        except Exception as err:
            logger.warning("Knowledge construction fallback for doc_id={did}: {e}", did=document_id, e=str(err))

        return {
            "document_id": str(document_id),
            "extracted_concepts_count": extracted_count,
            "total_graph_nodes": len(self.graph.nodes),
        }


# Global knowledge builder instance
knowledge_builder = KnowledgeBuilder()
