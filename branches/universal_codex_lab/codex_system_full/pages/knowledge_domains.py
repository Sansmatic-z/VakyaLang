"""
Phase 2: Knowledge Domains Codex Page.

Encodes domain-specific knowledge as transformable knowledge:
- Mathematics (algebra, calculus, number theory, statistics, combinatorics)
- Logic (propositional, predicate, temporal, fuzzy)
- Computer Science (complexity, data structures, design, concurrency, networking, databases, testing)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from ..engines.knowledge_base import KnowledgeBase, KnowledgeQuery
from .utils import _overall_confidence


_KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"


class KnowledgeDomainsCodexPage(CodexPage):
    """Provides domain-specific knowledge encoding and querying."""
    name = "knowledge_domains"
    description = "Domain knowledge encoding (math, logic, CS concepts)"
    priority = 43
    kind = "python"
    chapter = "patterns"
    chapter_title = "Pattern & Knowledge Encoding"
    chapter_order = 23
    capabilities = ("knowledge", "domain", "query", "math", "logic", "cs")
    emits_vak = True
    extensions = ("md", "txt")
    max_fixpoint_passes = 1

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._kb = KnowledgeBase()
        self._diagnostics: list[CodexDiagnostic] = []
        self._detected_constructs: list[str] = []
        self._load_knowledge()

    def _load_knowledge(self) -> None:
        """Load all knowledge base JSON files."""
        if not _KNOWLEDGE_DIR.exists():
            return
        count = 0
        for json_file in _KNOWLEDGE_DIR.glob("*.json"):
            try:
                loaded = self._kb.load_from_json(json_file)
                count += loaded
                self._diagnostics.append(CodexDiagnostic(
                    page=self.name, level="info",
                    message=f"Loaded {loaded} entries from {json_file.name}",
                    confidence="safe_auto_fix",
                ))
            except Exception as exc:
                self._diagnostics.append(CodexDiagnostic(
                    page=self.name, level="warning",
                    message=f"Failed to load {json_file.name}: {exc}",
                    confidence="suggest_only",
                ))
        self._detected_constructs.append(f"knowledge_base_loaded:{count}")

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------
    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        indicators = [
            "quadratic", "derivative", "integral", "prime", "factorization",
            "propositional", "predicate", "inference", "temporal",
            "big-o", "complexity", "data structure", "hash", "tree",
            "SOLID", "concurrency", "thread", "CAP theorem", "normalization",
            "math", "logic", "algorithm", "statistics",
        ]
        score = 0
        for indicator in indicators:
            if indicator.lower() in source.lower():
                score += 8

        if score >= 8:
            return CodexPageProbe(self.name, min(score, 85), f"Domain knowledge query detected ({score} indicators)")
        return CodexPageProbe(self.name, 5, "Knowledge domains chapter (low confidence)")

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------
    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        self._diagnostics = []
        self._detected_constructs = []

        # Query the knowledge base
        query = KnowledgeQuery(
            text=source[:200],  # Use first 200 chars as query
            max_results=10,
            sort_by="relevance",
        )
        results = self._kb.query(query)

        if not results:
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="info",
                message="No relevant knowledge found for query",
                confidence="suggest_only",
            ))
            return CodexResult(
                page=self.name, original_source=source, source=source,
                transformed=False, confidence="suggest_only",
                diagnostics=tuple(self._diagnostics), manifest=self.manifest(),
                metadata={"source_kind": "knowledge_query", "results_count": 0},
            )

        # Generate Vak output from knowledge entries
        output_lines: list[str] = []
        knowledge_keys: list[str] = []

        for entry in results:
            knowledge_keys.append(entry.key)
            self._detected_constructs.append(entry.key)
            output_lines.append(f"# Knowledge: {entry.title}")
            output_lines.append(f"# Category: {entry.category}")
            if entry.tags:
                output_lines.append(f"# Tags: {', '.join(entry.tags)}")
            output_lines.append(f"# {entry.content}")
            if entry.metadata:
                for k, v in entry.metadata.items():
                    output_lines.append(f"#   {k}: {v}")
            output_lines.append("")

        vak_output = "\n".join(output_lines)

        for entry in results:
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="info",
                message=f"Knowledge retrieved: {entry.title} ({entry.key})",
                confidence="safe_auto_fix",
            ))

        return CodexResult(
            page=self.name,
            original_source=source,
            source=vak_output,
            transformed=True,
            confidence=_overall_confidence(self._diagnostics, True),
            diagnostics=tuple(self._diagnostics),
            manifest=self.manifest(),
            metadata={
                "source_kind": "knowledge_query",
                "results_count": len(results),
                "knowledge_keys": knowledge_keys,
                "categories": self._kb.list_categories(),
                "entry_count": self._kb.get_entry_count(),
            },
        )
