"""
Phase 5: Knowledge Graph Codex Page.

Provides knowledge graph storage and querying:
- Store entities and relationships
- Query paths between entities
- Traverse graph for related knowledge
- Output valid Vak code representing the graph
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from ..engines.code_generator import CodeGenerator, GenerationContext
from .utils import _overall_confidence


@dataclass
class GraphNode:
    id: str
    label: str
    properties: dict[str, Any] = field(default_factory=dict)
    category: str = "general"


@dataclass
class GraphEdge:
    source: str
    target: str
    relation: str
    properties: dict[str, Any] = field(default_factory=dict)


class KnowledgeGraphCodexPage(CodexPage):
    """Knowledge graph storage, querying, and traversal."""
    name = "knowledge_graph"
    description = "Knowledge graph page (store/query relationships)"
    priority = 70
    kind = "python"
    chapter = "knowledge_engine"
    chapter_title = "Domain-Specific Knowledge Engine"
    chapter_order = 50
    capabilities = ("knowledge_graph", "relationships", "traversal", "query", "entity")
    emits_vak = True
    extensions = ("graph", "kg", "rdf", "owl")
    max_fixpoint_passes = 2

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._nodes: dict[str, GraphNode] = {}
        self._edges: list[GraphEdge] = []
        self._generator = CodeGenerator()
        self._diagnostics: list[CodexDiagnostic] = []
        self._detected_constructs: list[str] = []
        self._register_templates()
        self._load_default_knowledge()

    def _register_templates(self) -> None:
        self._generator.register_template("graph_node", """# Node: {node_id}
# Label: {label}
# Category: {category}
श्रेणी Node_{node_id} {{
    परिवर्तनी id = "{node_id}"
    परिवर्तनी label = "{label}"
{properties}
}}""")

        self._generator.register_template("graph_edge", """# Edge: {source} -[{relation}]-> {target}
कर्म edge_{source}_{target}() {{
    # {relation} relationship
    लौटाओ {{source: "{source}", target: "{target}", relation: "{relation}"}}
}}""")

    def _load_default_knowledge(self) -> None:
        """Load some default knowledge into the graph."""
        # Programming concepts
        self._add_node("python", "Python", {"type": "language", "paradigm": "multi-paradigm"}, "language")
        self._add_node("vak", "VakyaLang", {"type": "language", "paradigm": "Sanskrit-based"}, "language")
        self._add_node("javascript", "JavaScript", {"type": "language", "paradigm": "multi-paradigm"}, "language")

        # Relationships
        self._add_edge("python", "vak", "translates_to", {"confidence": 0.9})
        self._add_edge("javascript", "vak", "translates_to", {"confidence": 0.85})
        self._add_node("oop", "Object-Oriented Programming", {"type": "paradigm"}, "concept")
        self._add_edge("python", "oop", "supports", {})
        self._add_edge("javascript", "oop", "supports", {})

    # ------------------------------------------------------------------
    # Graph operations
    # ------------------------------------------------------------------
    def _add_node(self, node_id: str, label: str, properties: dict, category: str = "general") -> None:
        if node_id not in self._nodes:
            self._nodes[node_id] = GraphNode(id=node_id, label=label, properties=properties, category=category)

    def _add_edge(self, source: str, target: str, relation: str, properties: dict) -> None:
        self._edges.append(GraphEdge(source=source, target=target, relation=relation, properties=properties))

    def _query_neighbors(self, node_id: str) -> list[GraphEdge]:
        return [e for e in self._edges if e.source == node_id or e.target == node_id]

    def _find_path(self, start: str, end: str, max_depth: int = 5) -> list[list[str]]:
        """BFS to find paths between two nodes."""
        from collections import deque
        queue = deque([(start, [start])])
        paths: list[list[str]] = []
        visited = {start}

        while queue:
            current, path = queue.popleft()
            if len(path) > max_depth:
                continue
            if current == end and len(path) > 1:
                paths.append(path)
                continue
            for edge in self._edges:
                next_node = None
                if edge.source == current and edge.target not in visited:
                    next_node = edge.target
                elif edge.target == current and edge.source not in visited:
                    next_node = edge.source
                if next_node:
                    new_path = path + [next_node]
                    queue.append((next_node, new_path))

        return paths

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------
    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        indicators = [
            "knowledge_graph", "relationship", "entity", "node", "edge",
            "graph", "traverse", "path", "query",
            "is_a", "has_a", "part_of", "related_to",
        ]
        score = 0
        for indicator in indicators:
            if indicator in source.lower():
                score += 10

        if score >= 10:
            return CodexPageProbe(self.name, min(score, 85), f"Knowledge graph query detected ({score} indicators)")
        return CodexPageProbe(self.name, 10, "Knowledge graph chapter (default)")

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------
    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        self._diagnostics = []
        self._detected_constructs = []

        # Parse query from source
        query_result = self._process_query(source)

        # Generate Vak output
        vak_output = self._generate_graph_output(query_result)

        transformed = vak_output != source

        return CodexResult(
            page=self.name,
            original_source=source,
            source=vak_output,
            transformed=transformed,
            confidence=_overall_confidence(self._diagnostics, transformed),
            diagnostics=tuple(self._diagnostics),
            manifest=self.manifest(),
            metadata={
                "source_kind": "knowledge_graph_query",
                "nodes_count": len(self._nodes),
                "edges_count": len(self._edges),
                "query_result": str(query_result),
            },
        )

    def _process_query(self, source: str) -> dict[str, Any]:
        """Process a knowledge graph query."""
        result: dict[str, Any] = {"type": "unknown", "data": {}}
        source_lower = source.lower().strip()

        # Query: what is X related to?
        import re
        m = re.search(r"(?:related|connected|linked)\s+to\s+(\w+)", source_lower)
        if m:
            node_id = m.group(1)
            neighbors = self._query_neighbors(node_id)
            result = {"type": "neighbors", "data": {"node": node_id, "edges": [e.relation for e in neighbors]}}
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="info",
                message=f"Found {len(neighbors)} relationships for '{node_id}'",
                confidence="safe_auto_fix",
            ))
            return result

        # Query: path from X to Y
        m = re.search(r"path\s+from\s+(\w+)\s+to\s+(\w+)", source_lower)
        if m:
            start, end = m.group(1), m.group(2)
            paths = self._find_path(start, end)
            result = {"type": "path", "data": {"start": start, "end": end, "paths": paths}}
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="info",
                message=f"Found {len(paths)} paths from '{start}' to '{end}'",
                confidence="safe_auto_fix",
            ))
            return result

        # Query: list all X
        if "list" in source_lower or "all" in source_lower:
            result = {"type": "list_all", "data": {
                "nodes": {k: v.label for k, v in self._nodes.items()},
                "edges": [(e.source, e.relation, e.target) for e in self._edges],
            }}
            return result

        # Default: add as knowledge
        result = {"type": "graph_snapshot", "data": {
            "nodes": len(self._nodes),
            "edges": len(self._edges),
        }}
        return result

    def _generate_graph_output(self, query_result: dict[str, Any]) -> str:
        """Generate Vak code representing the knowledge graph."""
        lines: list[str] = []

        # Output nodes
        for node_id, node in self._nodes.items():
            props = ""
            for k, v in node.properties.items():
                props += f'    परिवर्तनी {k} = {v!r}\n'
            vak = self._generator.generate(
                template_name="graph_node",
                node_id=node_id, label=node.label, category=node.category,
                properties=props,
            )
            lines.append(vak)

        # Output edges
        for edge in self._edges:
            vak = self._generator.generate(
                template_name="graph_edge",
                source=edge.source, target=edge.target, relation=edge.relation,
            )
            lines.append(vak)

        return "\n\n".join(lines)
