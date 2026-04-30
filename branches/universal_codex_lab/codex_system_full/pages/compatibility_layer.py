"""
Pipeline Page: Compatibility Layer.

Provides old-language compatibility as a Codex page:
- Python → Vak bridge
- JavaScript → Vak bridge
- C/C++ → Vak bridge
- Type mapping between languages

*Visionary RM (Raj Mitra)* ⚡
"""
from __future__ import annotations

import ast
import re
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage


# Type mapping between languages
_TYPE_MAP: dict[str, dict[str, str]] = {
    "python_to_vak": {
        "int": "पूर्णांक",
        "float": "दशमलव",
        "str": "पाठ",
        "bool": "बूलियन",
        "list": "सूची",
        "dict": "मानचित्र",
        "set": "समूह",
        "None": "अपरिभाषित",
        "True": "सत्य",
        "False": "असत्य",
    },
    "javascript_to_vak": {
        "number": "पूर्णांक",
        "string": "पाठ",
        "boolean": "बूलियन",
        "array": "सूची",
        "object": "मानचित्र",
        "null": "अपरिभाषित",
        "undefined": "अपरिभाषित",
        "function": "कर्म",
    },
    "c_to_vak": {
        "int": "पूर्णांक",
        "float": "दशमलव",
        "double": "दशमलव",
        "char": "अक्षर",
        "void": "रिक्त",
        "struct": "श्रेणी",
        "enum": "गणना",
    },
}


class CompatibilityLayerCodexPage(CodexPage):
    """Translates old-language code to Vak with compatibility layers."""
    name = "compatibility_layer"
    description = "Old-language compatibility page"
    priority = 74
    kind = "compatibility_layer"
    chapter = "compatibility"
    chapter_title = "Old-Language Compatibility Layers"
    chapter_order = 70
    capabilities = ("bridge", "translate", "python_to_vak", "js_to_vak", "c_to_vak")
    emits_vak = True
    extensions = ("py", "js", "ts", "c", "cpp", "h")
    max_fixpoint_passes = 2

    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        """Check if source is a bridge spec or old-language code."""
        indicators = [
            "bridge", "map", "to vak", "python to", "javascript to",
            "c to", "def ", "function ", "int ", "class ",
        ]
        score = 0
        for indicator in indicators:
            if indicator.lower() in source.lower():
                score += 10

        if filename:
            ext_bonus = {".py": 20, ".js": 20, ".c": 20, ".cpp": 20, ".h": 20}
            score += ext_bonus.get(filename, 0)

        if score >= 10:
            return CodexPageProbe(self.name, min(score, 90), "Old-language code detected")
        return CodexPageProbe(self.name, 0, "not old-language code")

    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        diagnostics: list[CodexDiagnostic] = []
        metadata: dict[str, Any] = {}

        # Check for bridge specification
        if "bridge" in source.lower() and "to vak" in source.lower():
            return self._transform_bridge_spec(source, diagnostics, metadata)

        # Auto-detect language and translate
        language = self._detect_language(source, filename)
        metadata["detected_language"] = language

        if language == "python":
            output = self._translate_python(source)
        elif language == "javascript":
            output = self._translate_javascript(source)
        elif language in ("c", "cpp"):
            output = self._translate_c(source)
        else:
            output = self._translate_generic(source)
            diagnostics.append(CodexDiagnostic(
                page=self.name, level="info",
                message=f"Generic translation for '{language}'",
                confidence="suggest_only",
            ))

        metadata["translation_type"] = f"{language}_to_vak"

        return CodexResult(
            page=self.name, original_source=source, source=output,
            transformed=True, confidence="safe_auto_fix",
            diagnostics=tuple(diagnostics), metadata=metadata,
        )

    def _transform_bridge_spec(
        self, source: str, diagnostics: list[CodexDiagnostic], metadata: dict[str, Any],
    ) -> CodexResult:
        """Parse and apply a bridge specification."""
        lines: list[str] = ["# Vak Bridge Translation", ""]
        type_mappings: dict[str, str] = {}
        functions: list[dict[str, Any]] = []

        for line in source.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Parse type mapping: map int to पूर्णांक
            m = re.match(r"map\s+(\w+)\s+to\s+(\S+)", stripped, re.IGNORECASE)
            if m:
                type_mappings[m.group(1)] = m.group(2)
                continue

            # Parse function declaration: fn name(args)
            m = re.match(r"fn\s+(\w+)\s*\(([^)]*)\)", stripped)
            if m:
                functions.append({
                    "name": m.group(1),
                    "args": [a.strip() for a in m.group(2).split(",") if a.strip()],
                })
                continue

        # Generate Vak code
        if type_mappings:
            lines.append("# Type Mappings")
            for src, dst in type_mappings.items():
                lines.append(f"# {src} → {dst}")
            lines.append("")

        for func in functions:
            args = ", ".join(func["args"])
            lines.append(f"कर्म {func['name']}({args}) {{")
            lines.append(f"    # Translated via bridge")
            lines.append(f"    लौटाओ अपरिभाषित")
            lines.append("}")
            lines.append("")

        metadata["type_mappings"] = type_mappings
        metadata["functions_mapped"] = len(functions)

        return CodexResult(
            page=self.name,
            original_source=source,
            source="\n".join(lines),
            transformed=True,
            confidence="safe_auto_fix",
            diagnostics=tuple(diagnostics),
            metadata=metadata,
        )

    def _detect_language(self, source: str, filename: str | None) -> str:
        """Detect the source language."""
        if filename:
            ext_map = {".py": "python", ".js": "javascript", ".c": "c", ".cpp": "cpp"}
            for ext, lang in ext_map.items():
                if filename.endswith(ext):
                    return lang

        if "def " in source or "import " in source:
            return "python"
        if "function " in source or "const " in source or "let " in source:
            return "javascript"
        if "#include" in source or "int main" in source:
            return "c"

        return "unknown"

    def _translate_python(self, source: str) -> str:
        """Translate Python to Vak."""
        type_map = _TYPE_MAP["python_to_vak"]
        lines: list[str] = ["# Python → Vak Translation", ""]

        try:
            tree = ast.parse(source)
        except SyntaxError:
            lines.append("# Syntax error in Python source — wrapping as-is")
            lines.append(source)
            return "\n".join(lines)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = ", ".join(a.arg for a in node.args.args)
                lines.append(f"कर्म {node.name}({args}) {{")
                lines.append(f"    # Python function translated to Vak")
                lines.append(f"    लौटाओ अपरिभाषित")
                lines.append("}")
                lines.append("")
            elif isinstance(node, ast.ClassDef):
                lines.append(f"श्रेणी {node.name} {{")
                lines.append(f"    # Python class translated to Vak")
                lines.append("}")
                lines.append("")

        if len(lines) <= 2:
            lines.append("# No top-level symbols found — wrapping source")
            lines.append(source)

        return "\n".join(lines)

    def _translate_javascript(self, source: str) -> str:
        """Translate JavaScript to Vak."""
        lines: list[str] = ["# JavaScript → Vak Translation", ""]

        for match in re.finditer(r"(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:function|\([^)]*\)\s*=>))", source):
            name = match.group(1) or match.group(2)
            lines.append(f"कर्म {name}() {{")
            lines.append(f"    # JS function translated to Vak")
            lines.append(f"    लौटाओ अपरिभाषित")
            lines.append("}")
            lines.append("")

        for match in re.finditer(r"class\s+(\w+)", source):
            name = match.group(1)
            lines.append(f"श्रेणी {name} {{")
            lines.append(f"    # JS class translated to Vak")
            lines.append("}")
            lines.append("")

        if len(lines) <= 2:
            lines.append("# No symbols found — wrapping source")
            lines.append(source)

        return "\n".join(lines)

    def _translate_c(self, source: str) -> str:
        """Translate C/C++ to Vak."""
        lines: list[str] = ["# C/C++ → Vak Translation", ""]

        # Function declarations
        for match in re.finditer(r"(?:int|void|float|double|char|struct\s+\w+)\s+(\w+)\s*\(([^)]*)\)", source):
            name, params = match.group(1), match.group(2)
            lines.append(f"कर्म {name}({params.strip()}) {{")
            lines.append(f"    # C function translated to Vak")
            lines.append(f"    लौटाओ अपरिभाषित")
            lines.append("}")
            lines.append("")

        # Struct declarations
        for match in re.finditer(r"struct\s+(\w+)\s*\{", source):
            name = match.group(1)
            lines.append(f"श्रेणी {name} {{")
            lines.append(f"    # C struct translated to Vak")
            lines.append("}")
            lines.append("")

        if len(lines) <= 2:
            lines.append("# No symbols found — wrapping source")
            lines.append(source)

        return "\n".join(lines)

    def _translate_generic(self, source: str) -> str:
        """Generic translation for unknown languages."""
        return f"# Generic Translation\n\n{source}"
