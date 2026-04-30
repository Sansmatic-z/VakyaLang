"""
Phase 4: DSL Builder Codex Page.

Provides domain-specific language toolkit creation:
- Parses DSL specifications
- Generates grammar, lexer, and parser components
- Creates complete DSL compiler infrastructure
- Outputs valid Vak code with proper DSL structure
"""
from __future__ import annotations

import re
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from ..engines.grammar_parser import GrammarParser
from ..engines.code_generator import CodeGenerator, GenerationContext
from .utils import _overall_confidence


class DSLBuilderCodexPage(CodexPage):
    """Domain-specific language compiler builder."""
    name = "dsl_builder"
    description = "DSL compiler builder page (domain-specific language toolkit)"
    priority = 62
    kind = "python"
    chapter = "language_tools"
    chapter_title = "Language Creation Tools"
    chapter_order = 42
    capabilities = ("dsl", "domain_specific", "compiler_builder", "toolkit")
    emits_vak = True
    extensions = ("dsl", "spec", "lang")
    max_fixpoint_passes = 2

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._grammar_parser = GrammarParser()
        self._generator = CodeGenerator()
        self._diagnostics: list[CodexDiagnostic] = []
        self._detected_constructs: list[str] = []
        self._register_templates()

    def _register_templates(self) -> None:
        self._generator.register_template("dsl_main", """# DSL Compiler: {dsl_name}
# Domain: {domain}
# Description: {description}

श्रेणी {dsl_name}DSL {{
    परिवर्तनी lexer = अपरिभाषित
    परिवर्तनी parser = अपरिभाषित

    कर्म compile(source) {{
        tokens = lexer.tokenize(source)
        ast = parser.parse(tokens)
        लौटाओ ast
    }}

    कर्म validate(source) {{
        # Validate DSL source
        लौटाओ validation_result
    }}
}}""")

        self._generator.register_template("dsl_construct", """# DSL Construct: {construct_name}
# Type: {construct_type}
कर्म {construct_name}({params}) {{
    # {description}
    लौटाओ result
}}""")

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------
    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        indicators = [
            "dsl", "domain-specific", "domain specific", "language",
            "syntax", "semantics", "compiler", "interpreter",
            "construct", "expression", "statement", "block",
            "define", "name:", "domain:",
        ]
        score = 0
        for indicator in indicators:
            if indicator in source.lower():
                score += 10

        if filename and filename.endswith((".dsl", ".lang", ".spec")):
            score += 30

        # Check if it defines language constructs
        if re.search(r"(?i)(?:define|construct|syntax)\s+\w+", source):
            score += 20

        if score >= 20:
            return CodexPageProbe(self.name, min(score, 85), f"DSL specification detected ({score} indicators)")
        return CodexPageProbe(self.name, 0, "not a DSL spec candidate")

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------
    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        self._diagnostics = []
        self._detected_constructs = []

        try:
            spec = self._parse_dsl_spec(source)
            if spec is None:
                return self._no_transform(source, "Could not parse DSL specification")

            vak_code = self._generate_dsl(spec)

            return CodexResult(
                page=self.name,
                original_source=source,
                source=vak_code,
                transformed=True,
                confidence=_overall_confidence(self._diagnostics, True),
                diagnostics=tuple(self._diagnostics),
                manifest=self.manifest(),
                metadata={
                    "source_kind": "dsl_spec",
                    "dsl_name": spec.get("name", "unknown"),
                    "domain": spec.get("domain", "general"),
                    "constructs_count": len(spec.get("constructs", [])),
                },
            )
        except Exception as exc:
            return self._no_transform(source, str(exc))

    def _no_transform(self, source: str, reason: str) -> CodexResult:
        self._diagnostics.append(CodexDiagnostic(
            page=self.name, level="error", message=reason, confidence="do_not_touch",
        ))
        return CodexResult(
            page=self.name, original_source=source, source=source,
            transformed=False, confidence="do_not_touch",
            diagnostics=tuple(self._diagnostics), manifest=self.manifest(),
            metadata={"source_kind": "dsl_spec", "error": reason},
        )

    # ------------------------------------------------------------------
    # Spec parsing
    # ------------------------------------------------------------------
    def _parse_dsl_spec(self, source: str) -> dict[str, Any] | None:
        spec: dict[str, Any] = {
            "name": "DSL",
            "domain": "general",
            "description": "Domain-specific language",
            "constructs": [],
        }

        for line in source.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            m = re.match(r"(?:name|language)\s*:\s*(\w+)", stripped, re.IGNORECASE)
            if m:
                spec["name"] = m.group(1)

            m = re.match(r"(?:domain)\s*:\s*(.+)", stripped, re.IGNORECASE)
            if m:
                spec["domain"] = m.group(1).strip()

            m = re.match(r"(?:define|construct)\s+(\w+)\s*(?:as|:|=)?\s*(.*)", stripped, re.IGNORECASE)
            if m:
                spec["constructs"].append({
                    "name": m.group(1),
                    "description": m.group(2).strip(),
                    "type": "construct",
                })

        if spec["constructs"]:
            return spec
        return None

    # ------------------------------------------------------------------
    # Code generation
    # ------------------------------------------------------------------
    def _generate_dsl(self, spec: dict[str, Any]) -> str:
        lines: list[str] = []
        dsl_name = spec.get("name", "DSL")
        domain = spec.get("domain", "general")
        description = spec.get("description", "DSL")

        # Main compiler class
        lines.append(self._generator.generate(
            template_name="dsl_main",
            dsl_name=dsl_name, domain=domain, description=description,
        ))
        lines.append("")

        # Constructs
        for construct in spec.get("constructs", []):
            name = construct["name"]
            desc = construct.get("description", f"Handle {name}")
            self._detected_constructs.append(f"construct:{name}")
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="info",
                message=f"Generated DSL construct: {name}",
                confidence="safe_auto_fix",
            ))

            vak = self._generator.generate(
                template_name="dsl_construct",
                construct_name=name,
                construct_type=construct.get("type", "construct"),
                params="args",
                description=desc,
            )
            lines.append(vak)
            lines.append("")

        return "\n".join(lines)
