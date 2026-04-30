"""
Phase 2: Design Patterns Codex Page.

Encodes Gang of Four design patterns as transformable knowledge:
- Detects design pattern usage in source code
- Translates patterns to Vak implementations
- Provides template-based code generation
- Supports: Factory, Observer, Singleton, Strategy, Decorator, Adapter, Builder, Command, Iterator, Proxy
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from ..engines.pattern_matcher import PatternMatcher, PatternRegistry
from ..engines.code_generator import CodeGenerator, GenerationContext
from .utils import _overall_confidence


_DESIGN_PATTERNS_PATH = Path(__file__).resolve().parent.parent / "patterns" / "design_patterns.json"


class DesignPatternsCodexPage(CodexPage):
    """Detects and translates design patterns to Vak implementations."""
    name = "design_patterns"
    description = "Design pattern detection and translation (GoF patterns)"
    priority = 40
    kind = "design_patterns"
    chapter = "patterns"
    chapter_title = "Pattern & Knowledge Encoding"
    chapter_order = 20
    capabilities = ("pattern_match", "design_patterns", "generate", "translate")
    emits_vak = True
    extensions = ("py", "js", "java", "cpp")
    max_fixpoint_passes = 2
    max_source_length = 500_000

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._registry = PatternRegistry()
        self._matcher = PatternMatcher(self._registry)
        self._generator = CodeGenerator()
        self._diagnostics: list[CodexDiagnostic] = []
        self._detected_constructs: list[str] = []
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load design patterns from JSON registry."""
        try:
            if _DESIGN_PATTERNS_PATH.exists():
                self._registry.load_from_json(_DESIGN_PATTERNS_PATH)
                # Also register with the generator
                for entry in self._registry.list_patterns():
                    if entry.template:
                        self._generator.register_template(entry.name, entry.template)
        except Exception as exc:
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="warning",
                message=f"Could not load design patterns: {exc}",
                confidence="suggest_only",
            ))

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------
    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        # Check for design pattern indicators
        indicators = [
            "Factory", "Observer", "Singleton", "Strategy", "Decorator",
            "Adapter", "Builder", "Command", "Iterator", "Proxy",
            "getInstance", "subscribe", "notify", "execute", "wrapper",
            "create", "make", "build", "strategy", "context",
        ]
        score = 0
        for indicator in indicators:
            if indicator in source:
                score += 10

        if score >= 10:
            return CodexPageProbe(self.name, min(score, 90), f"Design patterns detected ({score} indicators)")
        return CodexPageProbe(self.name, 5, "Design patterns chapter (low confidence)")

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------
    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        self._diagnostics = []
        self._detected_constructs = []

        if len(source) > getattr(self, "max_source_length", 500_000):
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="error",
                message=f"Source too large ({len(source)} bytes, max {getattr(self, 'max_source_length', 500_000)})",
                confidence="do_not_touch",
            ))
            return CodexResult(
                page=self.name, original_source=source, source=source,
                transformed=False, confidence="do_not_touch",
                diagnostics=tuple(self._diagnostics), manifest=self.manifest(),
                metadata={"source_kind": "design_patterns", "error": "source_too_large"},
            )

        # Match patterns in source
        matches = self._matcher.match(source, category="design")

        if not matches:
            # Try to detect patterns heuristically even without regex match
            matches = self._detect_patterns_heuristic(source)

        if not matches:
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="info",
                message="No design patterns detected",
                confidence="suggest_only",
            ))
            return CodexResult(
                page=self.name, original_source=source, source=source,
                transformed=False, confidence="suggest_only",
                diagnostics=tuple(self._diagnostics), manifest=self.manifest(),
                metadata={"source_kind": "design_patterns", "patterns_found": []},
            )

        # Generate Vak implementations for detected patterns
        constructs: list[dict[str, Any]] = []
        pattern_names: list[str] = []

        for match in matches:
            pattern_names.append(match.pattern_name)
            self._detected_constructs.append(match.pattern_name)

            entry = self._registry.get(match.pattern_name)
            if entry and entry.template:
                ctx = GenerationContext()
                # Populate template variables from captures
                for key, val in match.captures.items():
                    ctx.add_variable(key, val)

                # If no captures, use defaults from template
                vak_code = self._generator.generate(
                    template_text=entry.template,
                    context=ctx,
                )

                # Parse the generated code into constructs
                for line in vak_code.split("\n"):
                    line = line.strip()
                    if line.startswith("कर्म "):
                        func_name = line.split("कर्म ")[1].split("(")[0].strip()
                        constructs.append({"kind": "function", "name": func_name, "body": line})
                    elif line.startswith("श्रेणी "):
                        class_name = line.split("श्रेणी ")[1].split("{")[0].strip()
                        constructs.append({"kind": "class", "name": class_name, "body": line})

                self._diagnostics.append(CodexDiagnostic(
                    page=self.name, level="info",
                    message=f"Pattern '{match.pattern_name}' detected (score: {match.score:.2f})",
                    confidence="safe_auto_fix" if match.score > 0.7 else "suggest_only",
                    line=match.line,
                ))

        # Generate consolidated Vak code
        if constructs:
            vak_output = self._generator.generate_vak("design_pattern", constructs)
        else:
            # Fallback: use templates directly
            templates_output: list[str] = []
            for match in matches:
                entry = self._registry.get(match.pattern_name)
                if entry and entry.template:
                    ctx = GenerationContext()
                    for key, val in match.captures.items():
                        ctx.add_variable(key, val)
                    rendered = self._generator.generate(template_text=entry.template, context=ctx)
                    templates_output.append(rendered)
            vak_output = "\n\n".join(templates_output)

        return CodexResult(
            page=self.name,
            original_source=source,
            source=vak_output,
            transformed=True,
            confidence=_overall_confidence(self._diagnostics, True),
            diagnostics=tuple(self._diagnostics),
            manifest=self.manifest(),
            metadata={
                "source_kind": "design_patterns",
                "patterns_found": pattern_names,
                "patterns_count": len(pattern_names),
            },
        )

    # ------------------------------------------------------------------
    # Heuristic pattern detection
    # ------------------------------------------------------------------
    def _detect_patterns_heuristic(self, source: str) -> list:
        """Detect design patterns using heuristic analysis when regex doesn't match."""
        from ..engines.pattern_matcher import PatternMatch

        results: list[PatternMatch] = []

        # Factory detection
        if any(kw in source for kw in ["create", "make", "factory", "Factory"]) and "class" in source:
            results.append(PatternMatch("factory_method", 0.6, {}, metadata={"category": "design", "detection": "heuristic"}))

        # Singleton detection
        if any(kw in source for kw in ["getInstance", "_instance", "singleton", "Singleton"]):
            results.append(PatternMatch("singleton", 0.7, {}, metadata={"category": "design", "detection": "heuristic"}))

        # Observer detection
        if any(kw in source for kw in ["subscribe", "notify", "observer", "Observer", "on_", "emit"]):
            results.append(PatternMatch("observer", 0.6, {}, metadata={"category": "design", "detection": "heuristic"}))

        # Strategy detection
        if any(kw in source for kw in ["strategy", "Strategy", "context", "Context"]) and "execute" in source:
            results.append(PatternMatch("strategy", 0.5, {}, metadata={"category": "design", "detection": "heuristic"}))

        # Decorator detection
        if "@" in source and any(kw in source for kw in ["decorator", "Decorator", "wraps", "wrapper"]):
            results.append(PatternMatch("decorator", 0.6, {}, metadata={"category": "design", "detection": "heuristic"}))

        return results
