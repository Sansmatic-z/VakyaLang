"""
Phase 2: Architecture Patterns Codex Page.

Encodes software architecture patterns as transformable knowledge:
- MVC (Model-View-Controller)
- Microservices
- Event-Driven Architecture
- Layered Architecture
- Repository Pattern
- CQRS (Command Query Responsibility Segregation)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from ..engines.pattern_matcher import PatternMatcher, PatternRegistry
from ..engines.code_generator import CodeGenerator, GenerationContext
from .utils import _overall_confidence


_ARCH_PATTERNS_PATH = Path(__file__).resolve().parent.parent / "patterns" / "architectures.json"


class ArchitecturePatternsCodexPage(CodexPage):
    """Detects and translates architecture patterns to Vak implementations."""
    name = "architecture_patterns"
    description = "Architecture pattern detection and translation (MVC, Microservices, etc.)"
    priority = 42
    kind = "python"
    chapter = "patterns"
    chapter_title = "Pattern & Knowledge Encoding"
    chapter_order = 22
    capabilities = ("pattern_match", "architecture", "generate", "translate")
    emits_vak = True
    extensions = ("py", "js", "java", "go")
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
            if _ARCH_PATTERNS_PATH.exists():
                self._registry.load_from_json(_ARCH_PATTERNS_PATH)
                for entry in self._registry.list_patterns():
                    if entry.template:
                        self._generator.register_template(entry.name, entry.template)
        except Exception as exc:
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="warning",
                message=f"Could not load architecture patterns: {exc}",
                confidence="suggest_only",
            ))

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------
    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        indicators = [
            "MVC", "Model", "View", "Controller",
            "microservice", "microservices", "service_mesh", "api_gateway",
            "Service", "Gateway",
            "event", "publisher", "subscriber", "EventBus",
            "layered", "presentation", "business", "data_access",
            "repository", "Repository",
            "CQRS", "command", "query", "event_store",
        ]
        score = 0
        for indicator in indicators:
            if indicator in source:
                score += 10

        if score >= 10:
            return CodexPageProbe(self.name, min(score, 90), f"Architecture patterns detected ({score} indicators)")
        return CodexPageProbe(self.name, 5, "Architecture patterns chapter (low confidence)")

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------
    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        self._diagnostics = []
        self._detected_constructs = []

        matches = self._matcher.match(source, category="architecture")
        if not matches:
            matches = self._detect_architecture_heuristic(source)

        if not matches:
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="info",
                message="No architecture patterns detected in source",
                confidence="suggest_only",
            ))
            return CodexResult(
                page=self.name, original_source=source, source=source,
                transformed=False, confidence="suggest_only",
                diagnostics=tuple(self._diagnostics), manifest=self.manifest(),
                metadata={"source_kind": "architecture_patterns", "patterns_found": []},
            )

        pattern_names: list[str] = []
        for match in matches:
            pattern_names.append(match.pattern_name)
            self._detected_constructs.append(match.pattern_name)

            entry = self._registry.get(match.pattern_name)
            if entry and entry.template:
                ctx = GenerationContext()
                for key, val in match.captures.items():
                    ctx.add_variable(key, val)

                use_case = entry.metadata.get("use_case", "general")
                complexity = entry.metadata.get("complexity", "unknown")
                self._diagnostics.append(CodexDiagnostic(
                    page=self.name, level="info",
                    message=f"Architecture '{match.pattern_name}' detected (use: {use_case})",
                    confidence="safe_auto_fix" if match.score > 0.7 else "suggest_only",
                    line=match.line,
                ))

        # Generate output
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
                "source_kind": "architecture_patterns",
                "patterns_found": pattern_names,
                "patterns_count": len(pattern_names),
            },
        )

    # ------------------------------------------------------------------
    # Heuristic detection
    # ------------------------------------------------------------------
    def _detect_architecture_heuristic(self, source: str) -> list:
        from ..engines.pattern_matcher import PatternMatch
        results: list[PatternMatch] = []

        arch_map = {
            ("MVC", "Model-View-Controller", "model", "view", "controller"): "mvc",
            ("microservice", "MicroService", "api_gateway"): "microservices",
            ("event_driven", "EventBus", "publisher", "subscriber"): "event_driven",
            ("layered", "n-tier", "presentation", "business", "data_access"): "layered",
            ("Repository", "repository", "data_access"): "repository",
            ("CQRS", "command_query", "read_model", "write_model"): "cqrs",
        }

        for keywords, name in arch_map.items():
            if any(kw in source for kw in keywords):
                results.append(PatternMatch(name, 0.5, {}, metadata={"category": "architecture", "detection": "heuristic"}))

        return results
