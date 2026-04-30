"""
Pipeline Page: Semantic Analyzer.

Provides deep semantic analysis as a Codex page:
- Symbol resolution and scoping
- Data flow analysis
- Control flow analysis
- Complexity scoring

*Visionary RM (Raj Mitra)* ⚡
"""
from __future__ import annotations

import ast
import re
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage


class SemanticAnalyzerCodexPage(CodexPage):
    """Performs deep semantic analysis on source code."""
    name = "semantic_analyzer"
    description = "Semantic analysis page — symbols, data flow, control flow"
    priority = 71
    kind = "semantic_analyzer"
    chapter = "analyzers"
    chapter_title = "Semantic/Code Analyzers"
    chapter_order = 20
    capabilities = ("analyze", "semantic", "dataflow", "controlflow", "complexity")
    emits_vak = False
    extensions = ("py", "js", "ts", "c", "cpp", "java", "go", "rs")
    max_fixpoint_passes = 1

    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        """Any non-empty source is a candidate for semantic analysis."""
        if not source.strip():
            return CodexPageProbe(self.name, 0, "empty source")

        # Score based on structural complexity
        score = 10
        if "def " in source or "function " in source or "class " in source:
            score += 20
        if "if " in source or "for " in source or "while " in source:
            score += 10
        if "return " in source or "yield " in source:
            score += 10

        return CodexPageProbe(self.name, min(score, 90), "Semantic analysis candidate")

    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        diagnostics: list[CodexDiagnostic] = []
        metadata: dict[str, Any] = {}

        # Python semantic analysis
        symbols = self._analyze_python_semantics(source, diagnostics)
        complexity = self._compute_complexity(source)
        data_flow = self._analyze_data_flow(source)

        metadata["symbols"] = symbols
        metadata["complexity"] = complexity
        metadata["data_flow"] = data_flow

        # Build report
        lines = [
            "# Semantic Analysis Report",
            "",
            f"## Symbols ({len(symbols)} found)",
            "",
        ]
        for sym in symbols:
            lines.append(f"- `{sym['name']}` ({sym['kind']}, line {sym['line']})")
        lines.append("")

        lines.append(f"## Complexity")
        lines.append(f"- Cyclomatic: {complexity['cyclomatic']}")
        lines.append(f"- Nesting depth: {complexity['max_nesting']}")
        lines.append(f"- Lines of code: {complexity['loc']}")
        lines.append("")

        lines.append(f"## Data Flow")
        lines.append(f"- Variables defined: {len(data_flow['defined'])}")
        lines.append(f"- Variables used: {len(data_flow['used'])}")
        if data_flow.get("unused"):
            lines.append(f"- **Potentially unused**: {', '.join(data_flow['unused'])}")
        lines.append("")

        output = "\n".join(lines)

        if complexity["cyclomatic"] > 10:
            diagnostics.append(CodexDiagnostic(
                page=self.name, level="warning",
                message=f"High cyclomatic complexity: {complexity['cyclomatic']}",
                confidence="safe_auto_fix",
            ))

        return CodexResult(
            page=self.name, original_source=source, source=output,
            transformed=True, confidence="verified",
            diagnostics=tuple(diagnostics), metadata=metadata,
        )

    def _analyze_python_semantics(
        self, source: str, diagnostics: list[CodexDiagnostic],
    ) -> list[dict[str, Any]]:
        """Extract symbols from Python source."""
        symbols: list[dict[str, Any]] = []
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            diagnostics.append(CodexDiagnostic(
                page=self.name, level="error",
                message=f"Syntax error: {e}",
                confidence="do_not_touch",
            ))
            return symbols

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                symbols.append({
                    "name": node.name, "kind": "function",
                    "line": node.lineno or 0,
                    "args": [a.arg for a in node.args.args],
                })
            elif isinstance(node, ast.ClassDef):
                symbols.append({
                    "name": node.name, "kind": "class",
                    "line": node.lineno or 0,
                })
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        symbols.append({
                            "name": target.id, "kind": "variable",
                            "line": node.lineno or 0,
                        })

        return symbols

    def _compute_complexity(self, source: str) -> dict[str, Any]:
        """Compute complexity metrics."""
        lines = source.split("\n")
        non_empty = [l for l in lines if l.strip() and not l.strip().startswith("#")]

        cyclomatic = 1
        for line in lines:
            if re.match(r"\s*(if|elif|for|while|except|and|or)\b", line):
                cyclomatic += 1

        max_nesting = 0
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_nesting = max(max_nesting, indent // 4)

        return {
            "cyclomatic": cyclomatic,
            "max_nesting": max_nesting,
            "loc": len(non_empty),
        }

    def _analyze_data_flow(self, source: str) -> dict[str, Any]:
        """Basic data flow analysis."""
        defined: list[str] = []
        used: list[str] = []

        for line in source.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Simple definition detection
            m = re.match(r"(\w+)\s*=", stripped)
            if m:
                name = m.group(1)
                if name not in ("if", "while", "for", "def", "class", "return", "import", "from"):
                    defined.append(name)

            # Simple usage detection
            for name in set(defined):
                if re.search(rf"\b{re.escape(name)}\b", stripped):
                    if name not in used:
                        used.append(name)

        unused = [d for d in defined if d not in used]

        return {
            "defined": defined,
            "used": used,
            "unused": unused,
        }
