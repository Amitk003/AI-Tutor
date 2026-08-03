"""
Concept Knowledge Graph Engine.
Maintains directed acyclic prerequisite relationships between concepts (e.g. Trees -> BST -> AVL).
Provides prerequisite lookup, dependency graph traversal, and learning pathway generation.
"""

from typing import Dict, List, Optional, Set
from loguru import logger


class ConceptNode:
    """Represents a concept in the domain Knowledge Graph."""

    def __init__(self, name: str, description: str = "", category: str = "General"):
        self.name = name
        self.description = description
        self.category = category
        self.prerequisites: Set[str] = set()  # Direct parent prerequisite concepts
        self.dependents: Set[str] = set()     # Direct child concepts depending on this


class ConceptKnowledgeGraph:
    """DAG Knowledge Graph representing subject domain concept dependencies."""

    def __init__(self):
        self.nodes: Dict[str, ConceptNode] = {}

    def add_concept(self, name: str, description: str = "", category: str = "General") -> ConceptNode:
        """Adds a new concept node to the knowledge graph."""
        if name not in self.nodes:
            self.nodes[name] = ConceptNode(name, description, category)
        return self.nodes[name]

    def add_prerequisite(self, concept_name: str, prerequisite_name: str) -> None:
        """
        Establishes a prerequisite edge: prerequisite_name -> concept_name.
        """
        c_node = self.add_concept(concept_name)
        p_node = self.add_concept(prerequisite_name)

        c_node.prerequisites.add(prerequisite_name)
        p_node.dependents.add(concept_name)
        logger.debug("Added prerequisite edge: {p} -> {c}", p=prerequisite_name, c=concept_name)

    def get_prerequisites(self, concept_name: str) -> List[str]:
        """Returns direct prerequisites for a concept."""
        node = self.nodes.get(concept_name)
        return list(node.prerequisites) if node else []

    def get_all_ancestors(self, concept_name: str) -> List[str]:
        """Traverses graph to return all recursive prerequisites (ancestors)."""
        ancestors: Set[str] = set()
        stack = self.get_prerequisites(concept_name)

        while stack:
            curr = stack.pop()
            if curr not in ancestors:
                ancestors.add(curr)
                stack.extend(self.get_prerequisites(curr))

        return list(ancestors)

    def get_next_dependent_concepts(self, concept_name: str) -> List[str]:
        """Returns concepts that depend on the given concept (unlocked next steps)."""
        node = self.nodes.get(concept_name)
        return list(node.dependents) if node else []


# Pre-populated Default Knowledge Graph for Computer Science & Machine Learning
def build_default_cs_knowledge_graph() -> ConceptKnowledgeGraph:
    graph = ConceptKnowledgeGraph()

    # Data Structures
    graph.add_prerequisite("Binary Search Tree", "Binary Trees")
    graph.add_prerequisite("AVL Tree", "Binary Search Tree")
    graph.add_prerequisite("Red-Black Tree", "AVL Tree")

    # Machine Learning
    graph.add_prerequisite("Gradient Descent", "Calculus Partial Derivatives")
    graph.add_prerequisite("Backpropagation", "Gradient Descent")
    graph.add_prerequisite("Neural Networks", "Backpropagation")
    graph.add_prerequisite("Transformers", "Neural Networks")

    return graph


# Global concept graph singleton
concept_graph = build_default_cs_knowledge_graph()
