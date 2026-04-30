"""
Phase 4: Language Bridge Codex Page.

Defines and manages bridges between programming languages:
- Parses language interoperability specifications
- Generates bridge code for calling between languages
- Maps types and constructs across language boundaries
- Outputs valid Vak code with proper bridging infrastructure
"""
from __future__ import annotations

import re
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from ..engines.code_generator import CodeGenerator, GenerationContext
from .utils import _overall_confidence


# Type mappings between common languages
_TYPE_MAP: dict[str, dict[str, str]] = {
    "python": {
        "int": "पूर्णांक", "float": "दशमलव", "str": "पाठ", "bool": "बूलियन",
        "list": "सूची", "dict": "मानचित्र", "set": "संग्रह", "tuple": "टपल",
        "None": "अपरिभाषित", "True": "सत्य", "False": "असत्य",
    },
    "javascript": {
        "number": "दशमलव", "string": "पाठ", "boolean": "बूलियन",
        "array": "सूची", "object": "मानचित्र", "null": "अपरिभाषित",
        "undefined": "अपरिभाषित", "true": "सत्य", "false": "असत्य",
    },
    "java": {
        "int": "पूर्णांक", "long": "दीर्घ", "double": "दशमलव", "float": "दशमलव",
        "String": "पाठ", "boolean": "बूलियन", "List": "सूची", "Map": "मानचित्र",
        "Set": "संग्रह", "null": "अपरिभाषित", "true": "सत्य", "false": "असत्य",
    },
    "c": {
        "int": "पूर्णांक", "long": "दीर्घ", "double": "दशमलव", "float": "दशमलव",
        "char*": "पाठ", "void": "शून्य", "NULL": "अपरिभाषित",
    },
}


class LanguageBridgeCodexPage(CodexPage):
    """Language interoperability bridge definition and generation."""
    name = "language_bridge"
    description = "Language interoperability page (define bridges between languages)"
    priority = 63
    kind = "python"
    chapter = "language_tools"
    chapter_title = "Language Creation Tools"
    chapter_order = 43
    capabilities = ("bridge", "interop", "ffi", "type_mapping", "cross_language")
    emits_vak = True
    extensions = ("bridge", "ffi", "interop", "spec")
    max_fixpoint_passes = 2

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._generator = CodeGenerator()
        self._diagnostics: list[CodexDiagnostic] = []
        self._detected_constructs: list[str] = []
        self._register_templates()

    def _register_templates(self) -> None:
        self._generator.register_template("bridge_module", """# Language Bridge: {source_lang} ↔ {target_lang}
# Module: {module_name}

श्रेणी {module_name}Bridge {{
    # Type mappings
{type_mappings}

    # Function bridges
{function_bridges}
}}""")

        self._generator.register_template("type_mapping", """    # {source_type} → {target_type}
    कर्म map_{source_type_lower}(value) {{
        लौटाओ value  # Direct mapping
    }}""")

        self._generator.register_template("function_bridge", """    # Bridge: {source_name} → {target_name}
    कर्म bridge_{func_name}({params}) {{
        # {source_lang} function: {source_signature}
        # {target_lang} function: {target_signature}
        लौटाओ result
    }}""")

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------
    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        indicators = [
            "bridge", "interop", "interopability", "FFI", "foreign",
            "Python", "JavaScript", "Java", "C", "Rust", "Go",
            "↔", "<->", "->", "map_type", "type_mapping",
        ]
        score = 0
        for indicator in indicators:
            if indicator in source:
                score += 10

        if filename and filename.endswith((".bridge", ".ffi", ".interop", ".spec")):
            score += 30

        # Check for language bridging patterns
        if re.search(r"(?i)(?:bridge|map|convert)\s+\w+\s+(?:to|→|->)\s+\w+", source):
            score += 25

        if score >= 20:
            return CodexPageProbe(self.name, min(score, 85), f"Language bridge detected ({score} indicators)")
        return CodexPageProbe(self.name, 0, "not a language bridge candidate")

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------
    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        self._diagnostics = []
        self._detected_constructs = []

        try:
            spec = self._parse_bridge_spec(source)
            if spec is None:
                return self._no_transform(source, "Could not parse language bridge specification")

            vak_code = self._generate_bridge(spec)

            return CodexResult(
                page=self.name,
                original_source=source,
                source=vak_code,
                transformed=True,
                confidence=_overall_confidence(self._diagnostics, True),
                diagnostics=tuple(self._diagnostics),
                manifest=self.manifest(),
                metadata={
                    "source_kind": "language_bridge",
                    "source_lang": spec.get("source_lang", "unknown"),
                    "target_lang": spec.get("target_lang", "unknown"),
                    "mappings_count": len(spec.get("type_mappings", [])),
                    "functions_count": len(spec.get("functions", [])),
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
            metadata={"source_kind": "language_bridge", "error": reason},
        )

    # ------------------------------------------------------------------
    # Spec parsing
    # ------------------------------------------------------------------
    def _parse_bridge_spec(self, source: str) -> dict[str, Any] | None:
        spec: dict[str, Any] = {
            "source_lang": "python",
            "target_lang": "vak",
            "module_name": "Bridge",
            "type_mappings": [],
            "functions": [],
        }

        for line in source.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Language declaration
            m = re.match(r"(?:bridge|from)\s+(\w+)\s+(?:to|→|->)\s+(\w+)", stripped, re.IGNORECASE)
            if m:
                spec["source_lang"] = m.group(1).lower()
                spec["target_lang"] = m.group(2).lower()
                spec["module_name"] = f"{spec['source_lang'].capitalize()}To{spec['target_lang'].capitalize()}"
                continue

            # Type mapping
            m = re.match(r"(?:map|type)\s+(\w+)\s+(?:to|→|->|as)\s+(\w+)", stripped, re.IGNORECASE)
            if m:
                spec["type_mappings"].append({
                    "source": m.group(1), "target": m.group(2),
                })
                continue

            # Function bridge
            m = re.match(r"(?:fn|function|def)\s+(\w+)\s*\(([^)]*)\)", stripped, re.IGNORECASE)
            if m:
                spec["functions"].append({
                    "name": m.group(1),
                    "params": m.group(2),
                })

        return spec

    # ------------------------------------------------------------------
    # Code generation
    # ------------------------------------------------------------------
    def _generate_bridge(self, spec: dict[str, Any]) -> str:
        source_lang = spec.get("source_lang", "python")
        target_lang = spec.get("target_lang", "vak")
        module_name = spec.get("module_name", "Bridge")

        # Generate type mappings
        type_mappings_lines: list[str] = []
        for mapping in spec.get("type_mappings", []):
            source_type = mapping["source"]
            target_type = mapping["target"]
            source_lower = source_type.lower()

            type_mappings_lines.append(self._generator.generate(
                template_name="type_mapping",
                source_type=source_type, target_type=target_type,
                source_type_lower=source_lower,
            ))

            self._detected_constructs.append(f"type_map:{source_type}->{target_type}")
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="info",
                message=f"Type mapping: {source_type} → {target_type}",
                confidence="safe_auto_fix",
            ))

        # Generate function bridges
        function_bridges_lines: list[str] = []
        for func in spec.get("functions", []):
            name = func["name"]
            params = func.get("params", "args")

            function_bridges_lines.append(self._generator.generate(
                template_name="function_bridge",
                func_name=name, params=params,
                source_lang=source_lang, target_lang=target_lang,
                source_signature=f"{name}({params})",
                target_signature=f"{name}({params})",
            ))

            self._detected_constructs.append(f"function_bridge:{name}")

        vak = self._generator.generate(
            template_name="bridge_module",
            source_lang=source_lang, target_lang=target_lang,
            module_name=module_name,
            type_mappings="\n\n".join(type_mappings_lines),
            function_bridges="\n\n".join(function_bridges_lines),
        )

        return vak
