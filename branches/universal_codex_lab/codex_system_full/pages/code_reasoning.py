"""
Phase 5: Code Reasoning Codex Page.

Analyzes code to understand intent and suggest improvements:
- Structural analysis (complexity, patterns, anti-patterns)
- Intent inference from code structure
- Improvement suggestions with confidence scoring
- Outputs valid Vak code with embedded suggestions
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from ..engines.code_generator import CodeGenerator, GenerationContext
from .utils import _overall_confidence


@dataclass
class CodeInsight:
    """An insight about the code."""
    category: str  # "complexity", "pattern", "anti_pattern", "performance", "readability", "security"
    severity: str  # "info", "warning", "error"
    message: str
    line: int = 0
    suggestion: str = ""
    confidence: float = 0.5


class CodeReasoningCodexPage(CodexPage):
    """Code reasoning: understand intent and suggest improvements."""
    name = "code_reasoning"
    description = "Code reasoning page (understand code intent, suggest improvements)"
    priority = 72
    kind = "python"
    chapter = "knowledge_engine"
    chapter_title = "Domain-Specific Knowledge Engine"
    chapter_order = 52
    capabilities = ("reasoning", "analysis", "suggestions", "intent", "improvements")
    emits_vak = True
    extensions = ("py", "js", "java", "cpp")
    max_fixpoint_passes = 2

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._generator = CodeGenerator()
        self._diagnostics: list[CodexDiagnostic] = []
        self._detected_constructs: list[str] = []
        self._register_templates()

    def _register_templates(self) -> None:
        self._generator.register_template("code_suggestion", """# Suggestion: {category} ({severity})
# {message}
# Confidence: {confidence:.0%}
{original_code}
# → Suggested: {suggestion}""")

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------
    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        # Any code-like content should trigger this page
        if any(marker in source for marker in ["def ", "class ", "function", "if ", "for ", "while ", "return"]):
            return CodexPageProbe(self.name, 60, "Code detected — reasoning available")
        return CodexPageProbe(self.name, 0, "not a code reasoning candidate")

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------
    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        self._diagnostics = []
        self._detected_constructs = []

        # Analyze code
        insights = self._analyze_code(source)

        # Always transform, even if no insights found
        vak_output = self._generate_reasoning_output(source, insights)
        transformed = True  # Always transformed - we analyze and document findings

        return CodexResult(
            page=self.name,
            original_source=source,
            source=vak_output,
            transformed=transformed,
            confidence=_overall_confidence(self._diagnostics, transformed),
            diagnostics=tuple(self._diagnostics),
            manifest=self.manifest(),
            metadata={
                "source_kind": "code_reasoning",
                "insights_count": len(insights),
                "insights_by_category": self._categorize_insights(insights),
            },
        )

    # ------------------------------------------------------------------
    # Code analysis
    # ------------------------------------------------------------------
    def _analyze_code(self, source: str) -> list[CodeInsight]:
        """Analyze code and generate insights."""
        insights: list[CodeInsight] = []
        lines = source.split("\n")

        # 1. Complexity analysis
        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Deeply nested code
            indent = len(line) - len(line.lstrip())
            if indent >= 16:  # 4+ levels of nesting
                insights.append(CodeInsight(
                    category="complexity", severity="warning",
                    message="Deep nesting detected (4+ levels)",
                    line=i, suggestion="Consider extracting nested logic into separate functions",
                    confidence=0.8,
                ))

            # Long lines
            if len(stripped) > 120:
                insights.append(CodeInsight(
                    category="readability", severity="info",
                    message=f"Long line ({len(stripped)} chars)",
                    line=i, suggestion="Break long lines for readability",
                    confidence=0.9,
                ))

        # 2. Pattern detection
        # Function with many lines
        func_starts: list[int] = []
        for i, line in enumerate(lines):
            if re.match(r"^\s*(def |function |कर्म )", line):
                func_starts.append(i)

        for start in func_starts:
            # Find function end (simplified: next def or end of file)
            end = len(lines)
            for j in range(start + 1, len(lines)):
                if re.match(r"^\s*(def |function |कर्म |class |श्रेणी )", lines[j]):
                    end = j
                    break
            func_length = end - start
            if func_length > 50:
                insights.append(CodeInsight(
                    category="complexity", severity="warning",
                    message=f"Long function ({func_length} lines)",
                    line=start + 1, suggestion="Break into smaller functions",
                    confidence=0.7,
                ))

        # 3. Anti-pattern detection
        for i, line in enumerate(lines, 1):
            # Magic numbers
            if re.search(r"\b(?:if|while|==)\s+\d{4,}\b", line):
                insights.append(CodeInsight(
                    category="anti_pattern", severity="warning",
                    message="Magic number detected",
                    line=i, suggestion="Use named constants instead of literal numbers",
                    confidence=0.6,
                ))

            # Generic variable names
            if re.match(r"\s*(?:var|परिवर्तनी)\s+(?:x|y|z|temp|data|foo|bar)\b", line):
                insights.append(CodeInsight(
                    category="readability", severity="info",
                    message="Generic variable name",
                    line=i, suggestion="Use descriptive variable names",
                    confidence=0.7,
                ))

        # 4. Performance hints
        for i, line in enumerate(lines, 1):
            if re.search(r"\+\s*=.*\+", line) and "for" in source[:source.find(line)]:
                insights.append(CodeInsight(
                    category="performance", severity="warning",
                    message="String concatenation in loop",
                    line=i, suggestion="Use list join or string builder",
                    confidence=0.7,
                ))

        # 5. Security hints
        for i, line in enumerate(lines, 1):
            if re.search(r"(?:eval|exec|executemany)\s*\(", line):
                insights.append(CodeInsight(
                    category="security", severity="error",
                    message="Potentially dangerous function usage (eval/exec)",
                    line=i, suggestion="Avoid eval/exec — use safe alternatives",
                    confidence=0.8,
                ))

        # Record insights as diagnostics
        for insight in insights:
            self._detected_constructs.append(f"{insight.category}:{insight.severity}")
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level=insight.severity,
                message=f"[{insight.category}] {insight.message}",
                confidence="safe_auto_fix" if insight.confidence > 0.7 else "suggest_only",
                line=insight.line,
            ))

        return insights

    def _categorize_insights(self, insights: list[CodeInsight]) -> dict[str, int]:
        """Count insights by category."""
        counts: dict[str, int] = {}
        for insight in insights:
            counts[insight.category] = counts.get(insight.category, 0) + 1
        return counts

    def _generate_reasoning_output(self, source: str, insights: list[CodeInsight]) -> str:
        """Generate Vak code with embedded reasoning results."""
        lines: list[str] = []
        lines.append("# Code Reasoning Analysis")
        lines.append(f"# Insights: {len(insights)}")
        lines.append("")

        if insights:
            for insight in insights:
                vak = self._generator.generate(
                    template_name="code_suggestion",
                    category=insight.category,
                    severity=insight.severity,
                    message=insight.message,
                    confidence=insight.confidence,
                    original_code=f"# Line {insight.line}",
                    suggestion=insight.suggestion,
                )
                lines.append(vak)
                lines.append("")
        else:
            lines.append("# No issues found — code looks good!")
            lines.append("परिवर्तनी code_quality = \"उत्कृष्ट\"")

        return "\n".join(lines)
