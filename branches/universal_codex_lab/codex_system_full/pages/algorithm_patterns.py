"""
Phase 2: Algorithm Patterns Codex Page.

Encodes fundamental algorithm patterns as transformable knowledge:
- Sort algorithms (Bubble, Quick, Merge, etc.)
- Search algorithms (Binary, Linear, etc.)
- Graph algorithms (BFS, DFS, Dijkstra)
- Data structure patterns (Hash Table, etc.)
- Mathematical algorithms (Fibonacci, etc.)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from ..engines.pattern_matcher import PatternMatcher, PatternRegistry
from ..engines.code_generator import CodeGenerator, GenerationContext
from .utils import _overall_confidence


_ALGORITHM_PATTERNS_PATH = Path(__file__).resolve().parent.parent / "patterns" / "algorithms.json"


class AlgorithmPatternsCodexPage(CodexPage):
    """Detects and translates algorithm patterns to Vak implementations."""
    name = "algorithm_patterns"
    description = "Algorithm pattern detection and translation (sort, search, graph, etc.)"
    priority = 41
    kind = "python"
    chapter = "patterns"
    chapter_title = "Pattern & Knowledge Encoding"
    chapter_order = 21
    capabilities = ("pattern_match", "algorithms", "generate", "translate")
    emits_vak = True
    extensions = ("py", "js", "java", "cpp")
    max_fixpoint_passes = 2

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._registry = PatternRegistry()
        self._matcher = PatternMatcher(self._registry)
        self._generator = CodeGenerator()
        self._diagnostics: list[CodexDiagnostic] = []
        self._detected_constructs: list[str] = []
        self._load_patterns()

    def _load_patterns(self) -> None:
        try:
            if _ALGORITHM_PATTERNS_PATH.exists():
                self._registry.load_from_json(_ALGORITHM_PATTERNS_PATH)
                for entry in self._registry.list_patterns():
                    if entry.template:
                        self._generator.register_template(entry.name, entry.template)
        except Exception as exc:
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="warning",
                message=f"Could not load algorithm patterns: {exc}",
                confidence="suggest_only",
            ))

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------
    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        indicators = [
            "sort", "search", "binary", "bubble", "quick", "merge",
            "bfs", "dfs", "dijkstra", "fibonacci", "hash",
            "Sort", "Search", "Binary", "BFS", "DFS", "Dijkstra",
            "O(n", "O(log", "time_complexity", "space_complexity",
        ]
        score = 0
        for indicator in indicators:
            if indicator in source:
                score += 12

        if score >= 12:
            return CodexPageProbe(self.name, min(score, 90), f"Algorithm patterns detected ({score} indicators)")
        return CodexPageProbe(self.name, 5, "Algorithm patterns chapter (low confidence)")

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------
    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        self._diagnostics = []
        self._detected_constructs = []

        matches = self._matcher.match(source, category="algorithm")
        if not matches:
            matches = self._detect_algorithms_heuristic(source)

        if not matches:
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="info",
                message="No algorithm patterns detected in source",
                confidence="suggest_only",
            ))
            return CodexResult(
                page=self.name, original_source=source, source=source,
                transformed=False, confidence="suggest_only",
                diagnostics=tuple(self._diagnostics), manifest=self.manifest(),
                metadata={"source_kind": "algorithm_patterns", "algorithms_found": []},
            )

        constructs: list[dict[str, Any]] = []
        algo_names: list[str] = []

        for match in matches:
            algo_names.append(match.pattern_name)
            self._detected_constructs.append(match.pattern_name)

            entry = self._registry.get(match.pattern_name)
            if entry and entry.template:
                ctx = GenerationContext()
                for key, val in match.captures.items():
                    ctx.add_variable(key, val)

                vak_code = self._generator.generate(template_text=entry.template, context=ctx)

                complexity = entry.metadata.get("time_complexity", "unknown")
                self._diagnostics.append(CodexDiagnostic(
                    page=self.name, level="info",
                    message=f"Algorithm '{match.pattern_name}' detected (time: {complexity})",
                    confidence="safe_auto_fix" if match.score > 0.7 else "suggest_only",
                    line=match.line,
                ))

        # Generate consolidated Vak output
        templates_output: list[str] = []
        for match in matches:
            entry = self._registry.get(match.pattern_name)
            if entry and entry.template:
                ctx = GenerationContext()
                for key, val in match.captures.items():
                    ctx.add_variable(key, val)
                rendered = self._generator.generate(template_text=entry.template, context=ctx)
                templates_output.append(rendered)

        vak_output = "\n\n".join(templates_output) if templates_output else source

        return CodexResult(
            page=self.name,
            original_source=source,
            source=vak_output,
            transformed=True,
            confidence=_overall_confidence(self._diagnostics, True),
            diagnostics=tuple(self._diagnostics),
            manifest=self.manifest(),
            metadata={
                "source_kind": "algorithm_patterns",
                "algorithms_found": algo_names,
                "algorithms_count": len(algo_names),
            },
        )

    # ------------------------------------------------------------------
    # Heuristic detection
    # ------------------------------------------------------------------
    def _detect_algorithms_heuristic(self, source: str) -> list:
        from ..engines.pattern_matcher import PatternMatch
        results: list[PatternMatch] = []

        algo_map = {
            ("bubble_sort", "bubbleSort"): "bubble_sort",
            ("quick_sort", "quickSort"): "quick_sort",
            ("merge_sort", "mergeSort"): "merge_sort",
            ("binary_search", "binarySearch"): "binary_search",
            ("linear_search", "linearSearch"): "linear_search",
            ("bfs", "breadth_first"): "bfs",
            ("dfs", "depth_first"): "dfs",
            ("dijkstra", "shortest_path"): "dijkstra",
            ("fibonacci", "fib"): "fibonacci",
            ("hash_table", "hashTable", "HashMap"): "hash_table",
        }

        for keywords, name in algo_map.items():
            if any(kw in source for kw in keywords):
                results.append(PatternMatch(name, 0.6, {}, metadata={"category": "algorithm", "detection": "heuristic"}))

        return results
