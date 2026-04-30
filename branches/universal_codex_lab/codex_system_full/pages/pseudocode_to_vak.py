"""
Phase 1: Pseudocode → Vak Translator Codex Page.

Translates algorithmic pseudocode into executable VakyaLang code by:
1. Recognizing pseudocode patterns (algorithmic constructs)
2. Mapping pseudocode keywords to Vak equivalents
3. Structuring into proper Vak syntax
4. Handling multiple pseudocode conventions
"""
from __future__ import annotations

import re
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from .utils import _overall_confidence
from ..vak_surface import normalize_vak_surface


# Pseudocode keyword variants → Vak
_PSEUDO_VAK: dict[str, str] = {
    # Function/Procedure
    "function": "कर्म",
    "procedure": "कर्म",
    "method": "कर्म",
    "def": "कर्म",
    "subroutine": "कर्म",
    "func": "कर्म",
    # Variables
    "variable": "चर",
    "var": "चर",
    "let": "चर",
    "set": "चर",
    "constant": "स्थिर",
    "const": "स्थिर",
    # Conditionals
    "if": "यदि",
    "then": "तब",
    "else": "अन्यथा",
    "elseif": "अन्यथा_यदि",
    "elif": "अन्यथा_यदि",
    "otherwise": "अन्यथा",
    # Loops
    "for": "प्रत्येक",
    "while": "यावत्",
    "do": "करें",
    "repeat": "दोहराएं",
    "until": "जब_तक",
    "foreach": "प्रत्येक_प्रत्येक",
    "for each": "प्रत्येक_प्रत्येक",
    "loop": "लूप",
    # Control
    "return": "प्रत्यागच्छ",
    "break": "विराम",
    "continue": "अग्रे",
    "exit": "बाहर",
    "stop": "रुको",
    # Logic
    "and": "और",
    "or": "या",
    "not": "नहीं",
    "true": "सत्य",
    "false": "असत्य",
    "null": "शून्य",
    "nil": "शून्य",
    "none": "शून्य",
    "undefined": "शून्य",
    # I/O
    "print": "मुद्रय",
    "output": "मुद्रय",
    "display": "मुद्रय",
    "write": "लिखो",
    "read": "पढ़ो",
    "input": "इनपुट",
    # Data structures
    "array": "सूची",
    "list": "सूची",
    "dictionary": "मानचित्र",
    "map": "मानचित्र",
    "hash": "मानचित्र",
    "set": "संग्रह",
    "queue": "पंक्ति",
    "stack": "ढेर",
    # Operations
    "append": "जोड़ें",
    "add": "जोड़ें",
    "remove": "हटाएं",
    "delete": "हटाओ",
    "insert": "डालें",
    "push": "धक्का",
    "pop": "निकालें",
    "length": "लंबाई",
    "size": "लंबाई",
    "empty": "खाली",
    "contains": "शामिल",
    "sort": "क्रमबद्ध",
    "reverse": "उलटा",
    # Math
    "sqrt": "वर्गमूल",
    "abs": "निरपेक्ष",
    "max": "अधिकतम",
    "min": "न्यूनतम",
    "sum": "योग",
    "average": "औसत",
    "mean": "औसत",
    "floor": "फर्श",
    "ceil": "छत",
    "round": "गोल",
    "random": "यादृच्छिक",
    # Comparison
    "equals": "==",
    "not equals": "!=",
    "greater than": ">",
    "less than": "<",
    "greater than or equal": ">=",
    "less than or equal": "<=",
    # Algorithm keywords
    "algorithm": "एल्गोरिदम",
    "begin": "शुरू",
    "end": "समाप्त",
    "initialize": "प्रारंभ",
    "create": "बनाओ",
    "destroy": "नष्ट",
    "copy": "प्रति",
}


class PseudocodeToVakCodexPage(CodexPage):
    """Translates algorithmic pseudocode to VakyaLang."""
    name = "pseudocode_to_vak"
    description = "Pseudocode to Vak translator page"
    priority = 32
    kind = "pseudocode"
    chapter = "translators"
    chapter_title = "Language Translators"
    chapter_order = 12
    capabilities = ("translate", "pseudocode", "algorithm", "generate")
    emits_vak = True
    extensions = ("txt", "pseudo", "algo")
    max_fixpoint_passes = 2
    max_source_length = 500_000

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._diagnostics: list[CodexDiagnostic] = []
        self._detected_constructs: list[str] = []

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------
    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        if filename and filename.endswith((".txt", ".pseudo", ".algo")):
            return CodexPageProbe(self.name, 80, f"{filename} source path")

        # Check if source looks like pseudocode
        pseudo_indicators = [
            r"(?i)\b(algorithm|procedure|function|method)\b",
            r"(?i)\b(begin|start|initialize)\b",
            r"(?i)\b(for each|foreach|for all)\b",
            r"(?i)\b(end if|end for|end while|end function|end procedure)\b",
            r"(?i)\b(repeat\s+until)\b",
            r"(?i)\b(input|output|display|print)\b",
            r"(?i)\b(set\s+\w+\s*←|set\s+\w+\s*=)",
            r"←",  # Assignment arrow common in pseudocode
            r"(?i)\breturn\b",
        ]
        score = 0
        for pattern in pseudo_indicators:
            if re.search(pattern, source):
                score += 15

        # Bonus if no programming language markers
        if not any("\u0900" <= ch <= "\u097f" for ch in source):
            has_code_markers = any(
                marker in source for marker in [
                    "def ", "class ", "import ", "function ", "const ", "let ",
                    "#include", "#define", "package ", "public ", "private ",
                ]
            )
            if not has_code_markers and score > 0:
                score += 10  # More likely to be pseudocode

        if score >= 15:
            return CodexPageProbe(self.name, min(score, 90), "Pseudocode detected")
        return CodexPageProbe(self.name, 0, "not a pseudocode candidate")

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
                metadata={"source_kind": "pseudocode", "error": "source_too_large"},
            )

        try:
            vak_code = self._translate_pseudocode(source)
            transformed = vak_code != source

            if transformed:
                self._diagnostics.append(CodexDiagnostic(
                    page=self.name, level="info",
                    message="Pseudocode translated to Vak",
                    confidence="safe_auto_fix",
                ))

            return CodexResult(
                page=self.name,
                original_source=source,
                source=vak_code,
                transformed=transformed,
                confidence=_overall_confidence(self._diagnostics, transformed),
                diagnostics=tuple(self._diagnostics),
                manifest=self.manifest(),
                metadata={
                    "source_kind": "pseudocode",
                    "detected_constructs": list(self._detected_constructs),
                    "translation_method": "keyword_mapping",
                },
            )
        except Exception as exc:
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="error",
                message=f"Translation error: {exc}",
                confidence="do_not_touch",
            ))
            return CodexResult(
                page=self.name, original_source=source, source=source,
                transformed=False, confidence="do_not_touch",
                diagnostics=tuple(self._diagnostics), manifest=self.manifest(),
                metadata={"source_kind": "pseudocode", "error": str(exc)},
            )

    # ------------------------------------------------------------------
    # Translation engine
    # ------------------------------------------------------------------
    def _translate_pseudocode(self, source: str) -> str:
        """Translate pseudocode line by line with structural awareness."""
        lines = source.split("\n")
        output: list[str] = []
        in_function = False
        in_class = False
        block_depth = 0

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("--"):
                # Comment passthrough
                if stripped.startswith("//") or stripped.startswith("--"):
                    output.append("# " + stripped[2:])
                else:
                    output.append(line)
                continue

            # Skip algorithm/procedure header lines
            if re.match(r"(?i)^(algorithm|procedure|method)\b", stripped):
                self._detected_constructs.append("header")
                # Extract name
                m = re.match(r"(?i)^(?:algorithm|procedure|method)\s+(\w+)", stripped)
                if m:
                    output.append(f"# Algorithm: {m.group(1)}")
                continue

            if re.match(r"(?i)^begin\b", stripped):
                self._detected_constructs.append("begin")
                continue  # Skip begin markers

            if re.match(r"(?i)^end\b", stripped):
                self._detected_constructs.append("end")
                continue  # Skip end markers

            # Function definition
            m = re.match(r"(?i)^(function|procedure|method|func)\s+(\w+)\s*(?:\(([^)]*)\))?", stripped)
            if m:
                self._detected_constructs.append("function")
                name = m.group(2)
                params = m.group(3) or ""
                params = ", ".join(p.strip() for p in params.split(",") if p.strip())
                in_function = True
                block_depth = 0
                output.append(f"कर्म {name}({params}) {{")
                continue

            # Variable assignment (SET x = ... or x ← ...)
            m = re.match(r"(?i)^set\s+(\w+)\s*[=←]\s*(.+)", stripped)
            if m:
                self._detected_constructs.append("variable")
                name = m.group(1)
                value = self._translate_expr(m.group(2))
                output.append(f"चर {name} = {value}")
                continue

            # Arrow assignment
            if "←" in stripped:
                parts = stripped.split("←", 1)
                name = parts[0].strip()
                value = self._translate_expr(parts[1].strip())
                output.append(f"चर {name} = {value}")
                continue

            # If/Else
            m = re.match(r"(?i)^if\s+(.+?)\s+(?:then\s*)?$", stripped)
            if m:
                self._detected_constructs.append("conditional")
                cond = self._translate_expr(m.group(1))
                output.append(f"यदि ({cond}) {{")
                block_depth += 1
                continue

            if re.match(r"(?i)^(else\s+if|elseif|elif)\b", stripped):
                m = re.match(r"(?i)^(?:else\s+if|elseif|elif)\s+(.+?)(?:\s+then\s*)?$", stripped)
                if m:
                    cond = self._translate_expr(m.group(1))
                    output.append(f"}} अन्यथा_यदि ({cond}) {{")
                continue

            if re.match(r"(?i)^else\b", stripped):
                output.append("} अन्यथा {")
                continue

            # For loops
            m = re.match(r"(?i)^for\s+(?:each\s+)?(\w+)\s+in\s+(.+)", stripped)
            if m:
                self._detected_constructs.append("loop")
                var = m.group(1)
                iterable = self._translate_expr(m.group(2))
                output.append(f"प्रत्येक {var} अन्तर्गत {iterable} {{")
                block_depth += 1
                continue

            m = re.match(r"(?i)^for\s+(\w+)\s*=\s*(.+?)\s+to\s+(.+?)(?:\s+step\s+(.+))?$", stripped)
            if m:
                self._detected_constructs.append("loop")
                var = m.group(1)
                start = self._translate_expr(m.group(2))
                end = self._translate_expr(m.group(3))
                step = m.group(4)
                if step:
                    output.append(f"प्रत्येक {var} अन्तर्गत परिसर({start}, {end}, {self._translate_expr(step)}) {{")
                else:
                    output.append(f"प्रत्येक {var} अन्तर्गत परिसर({start}, {end} + 1) {{")
                block_depth += 1
                continue

            # While
            m = re.match(r"(?i)^while\s+(.+)", stripped)
            if m:
                self._detected_constructs.append("loop")
                cond = self._translate_expr(m.group(1))
                output.append(f"यावत् ({cond}) {{")
                block_depth += 1
                continue

            # Repeat-Until
            if re.match(r"(?i)^repeat\b", stripped):
                self._detected_constructs.append("loop")
                output.append("करें {{")
                block_depth += 1
                continue

            m = re.match(r"(?i)^until\s+(.+)", stripped)
            if m:
                cond = self._translate_expr(m.group(1))
                output.append(f"}} जब_तक ({cond})")
                block_depth -= 1
                continue

            # Return
            m = re.match(r"(?i)^return\s+(.+)", stripped)
            if m:
                self._detected_constructs.append("return")
                value = self._translate_expr(m.group(1))
                output.append(f"प्रत्यागच्छ {value}")
                continue

            if re.match(r"(?i)^return\b", stripped):
                self._detected_constructs.append("return")
                output.append("प्रत्यागच्छ")
                continue

            # Break/Continue
            if re.match(r"(?i)^break\b", stripped):
                output.append("तोड़ें")
                continue
            if re.match(r"(?i)^continue\b", stripped):
                output.append("जारी")
                continue

            # Output/Print
            m = re.match(r"(?i)^(?:print|output|display|write)\s+(.+)", stripped)
            if m:
                self._detected_constructs.append("output")
                value = self._translate_expr(m.group(1))
                output.append(f"मुद्रय({value})")
                continue

            # End if/for/while/function
            if re.match(r"(?i)^end\s+(if|for|while|function|procedure|method|loop|repeat)", stripped):
                output.append("}")
                block_depth = max(0, block_depth - 1)
                continue

            # General line: translate keywords and treat as expression
            translated = self._translate_expr(stripped)
            output.append(translated)

        return normalize_vak_surface("\n".join(output))

    def _translate_expr(self, expr: str) -> str:
        """Translate pseudocode expression to Vak syntax."""
        result = expr

        # Replace keywords (longest match first to avoid partial replacements)
        for pseudo_kw in sorted(_PSEUDO_VAK.keys(), key=len, reverse=True):
            vak_kw = _PSEUDO_VAK[pseudo_kw]
            # Case-insensitive replacement
            pattern = re.compile(re.escape(pseudo_kw), re.IGNORECASE)
            result = pattern.sub(vak_kw, result)

        # Convert common math notation
        result = result.replace("×", "*")
        result = result.replace("÷", "/")
        result = result.replace("≠", "!=")
        result = result.replace("≤", "<=")
        result = result.replace("≥", ">=")
        result = result.replace("→", "->")
        result = result.replace("∧", "और")
        result = result.replace("∨", "या")
        result = result.replace("¬", "नहीं")

        # Convert "x is empty" → "खाली(x)"
        result = re.sub(r"(\w+)\s+is\s+empty", r"खाली(\1)", result, flags=re.IGNORECASE)

        return result
