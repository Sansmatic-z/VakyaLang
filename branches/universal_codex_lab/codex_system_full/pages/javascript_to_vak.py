"""
Phase 1: JavaScript → Vak Translator Codex Page.

Translates JavaScript/TypeScript source code into equivalent VakyaLang code by:
1. Parsing JS constructs via regex-based analysis
2. Mapping JS patterns to Vak equivalents
3. Generating valid Vak code with Devanagari keywords
4. Handling common JS idioms (callbacks, promises, arrow functions)
"""
from __future__ import annotations

import re
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from .utils import _overall_confidence
from ..vak_surface import normalize_vak_surface


# ------------------------------------------------------------------
# JavaScript → Vak keyword mapping
# ------------------------------------------------------------------
_JS_VAK_KEYWORDS: dict[str, str] = {
    "function": "कर्म",
    "const": "स्थिर",
    "let": "चर",
    "var": "चर",
    "class": "वर्ग",
    "if": "यदि",
    "else": "अन्यथा",
    "for": "प्रत्येक",
    "while": "यावत्",
    "do": "करें",
    "return": "प्रत्यागच्छ",
    "import": "आयात",
    "export": "निर्यात",
    "default": "डिफ़ॉल्ट",
    "from": "से",
    "try": "प्रयत्न",
    "catch": "दोष",
    "finally": "अन्ततः",
    "throw": "उत्क्षिप",
    "new": "नया",
    "this": "स्वयं",
    "true": "सत्य",
    "false": "असत्य",
    "null": "शून्य",
    "undefined": "शून्य",
    "typeof": "प्रकार",
    "instanceof": "का_उदाहरण",
    "switch": "चयन",
    "case": "स्थिति",
    "break": "विराम",
    "continue": "अग्रे",
    "async": "अतुल्यकालिक",
    "await": "प्रतीक्षा",
    "yield": "उपज",
    "of": "में",
    "in": "में",
    "&&": "और",
    "||": "या",
    "!": "नहीं",
    "console.log": "मुद्रय",
    "console.error": "त्रुटि_मुद्रय",
    "console.warn": "चेतावनी_मुद्रय",
    "push": "जोड़ें",
    "pop": "निकालें",
    "length": "लंबाई",
    "map": "मानचित्र",
    "filter": "फ़िल्टर",
    "reduce": "कम_करें",
    "forEach": "प्रत्येक_प्रत्येक",
    "find": "खोजें",
    "includes": "शामिल",
    "concat": "जोड़ें",
    "slice": "टुकड़ा",
    "splice": "काटें",
    "join": "जोड़ें",
    "split": "विभाजित",
    "toString": "पाठ_बनाएं",
    "parseInt": "पूर्णांक",
    "parseFloat": "दशमलव",
}


class JavaScriptToVakCodexPage(CodexPage):
    """Translates JavaScript/TypeScript source code to VakyaLang."""
    name = "javascript_to_vak"
    description = "JavaScript/TypeScript source to Vak translator page"
    priority = 31
    kind = "javascript"
    chapter = "translators"
    chapter_title = "Language Translators"
    chapter_order = 11
    capabilities = ("translate", "javascript", "typescript", "ast", "generate")
    emits_vak = True
    extensions = ("js", "ts", "jsx", "tsx")
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
        if filename and filename.endswith((".js", ".ts", ".jsx", ".tsx")):
            return CodexPageProbe(self.name, 100, f"{filename} source path")
        # Check if source looks like JavaScript
        js_indicators = [
            r"^\s*(const|let|var)\s+\w+",
            r"^\s*function\s+\w+",
            r"^\s*class\s+\w+",
            r"^\s*import\s+.*\s+from\s+",
            r"^\s*export\s+(default\s+)?(function|class|const)",
            r"=>\s*{",  # arrow functions
            r"\.then\s*\(",  # promises
            r"\.catch\s*\(",
            r"console\.\w+",
            r"module\.exports",
            r"require\s*\(",
            r"use\s+(useState|useEffect|useRef|useMemo|useCallback)",  # React hooks
        ]
        score = 0
        for pattern in js_indicators:
            if re.search(pattern, source, re.MULTILINE):
                score += 15
        if score > 0 and not any("\u0900" <= ch <= "\u097f" for ch in source):
            return CodexPageProbe(self.name, min(score, 95), "JavaScript-like source detected")
        return CodexPageProbe(self.name, 0, "not a JavaScript source candidate")

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
                metadata={"source_kind": "javascript", "error": "source_too_large"},
            )

        try:
            vak_code = self._translate_javascript(source)
            transformed = vak_code != source

            if transformed:
                self._diagnostics.append(CodexDiagnostic(
                    page=self.name, level="info",
                    message="JavaScript source translated to Vak",
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
                    "source_kind": "javascript",
                    "detected_constructs": list(self._detected_constructs),
                    "translation_method": "regex_based",
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
                metadata={"source_kind": "javascript", "error": str(exc)},
            )

    # ------------------------------------------------------------------
    # Translation engine (regex-based transformation)
    # ------------------------------------------------------------------
    def _translate_javascript(self, source: str) -> str:
        if not source or not source.strip():
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="warning",
                message="Empty or whitespace-only JavaScript source provided",
                confidence="suggest_only",
            ))
            return ""
        result = source
        lines = result.split("\n")
        output: list[str] = []

        for line in lines:
            translated = self._translate_line(line)
            output.append(translated)

        return normalize_vak_surface("\n".join(output))

    def _translate_line(self, line: str) -> str:
        stripped = line.strip()
        if not stripped or stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            if stripped.startswith("//"):
                return "# " + stripped[2:]
            return line

        indent = line[:len(line) - len(line.lstrip())]

        # Function declaration with inline body
        m = re.match(r"(async\s+)?function\s+(\w+)\s*\(([^)]*)\)\s*\{\s*(.*?)\s*\}\s*;?\s*$", stripped)
        if m:
            self._detected_constructs.append("function")
            async_kw = "अतुल्यकालिक " if m.group(1) else ""
            name = m.group(2)
            params = self._translate_params(m.group(3))
            body = self._translate_inline_statement(m.group(4))
            return f"{indent}{async_kw}कर्म {name}({params}) {{\n{indent}    {body}\n{indent}}}"

        # Class definition
        m = re.match(r"(export\s+(default\s+)?)?class\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{?", stripped)
        if m:
            self._detected_constructs.append("class")
            name = m.group(3)
            parent = m.group(4)
            base = f" ({parent})" if parent else ""
            return f"{indent}वर्ग {name}{base} {{"

        # Function declaration
        m = re.match(r"(async\s+)?function\s+(\w+)\s*\(([^)]*)\)\s*\{?", stripped)
        if m:
            self._detected_constructs.append("function")
            async_kw = "अतुल्यकालिक " if m.group(1) else ""
            name = m.group(2)
            params = self._translate_params(m.group(3))
            return f"{indent}{async_kw}कर्म {name}({params}) {{"

        # Arrow function assigned to variable
        m = re.match(r"(const|let|var)\s+(\w+)\s*=\s*(async\s+)?\(([^)]*)\)\s*=>\s*\{?", stripped)
        if m:
            self._detected_constructs.append("function")
            kw = "स्थिर" if m.group(1) == "const" else "चर"
            async_kw = "अतुल्यकालिक " if m.group(3) else ""
            name = m.group(2)
            params = self._translate_params(m.group(4))
            return f"{indent}{kw} {name} = {async_kw}कर्म ({params}) {{"

        # Method definition in class
        m = re.match(r"(async\s+)?(\w+)\s*\(([^)]*)\)\s*\{\s*(.*?)\s*\}\s*;?\s*$", stripped)
        if m and not stripped.startswith(("if", "for", "while", "switch", "catch")):
            if not re.match(r"(console|Math|JSON|Object|Array|String|Number|Promise|process)\.", stripped):
                self._detected_constructs.append("function")
                async_kw = "अतुल्यकालिक " if m.group(1) else ""
                name = m.group(2)
                if name not in ("return", "throw", "delete", "typeof", "void"):
                    params = self._translate_params(m.group(3))
                    body = self._translate_inline_statement(m.group(4))
                    return f"{indent}{async_kw}कर्म {name}({params}) {{\n{indent}    {body}\n{indent}}}"

        m = re.match(r"(async\s+)?(\w+)\s*\(([^)]*)\)\s*\{?", stripped)
        if m and not stripped.startswith(("if", "for", "while", "switch", "catch")):
            # Check it's not a call expression
            if not re.match(r"(console|Math|JSON|Object|Array|String|Number|Promise|process)\.", stripped):
                self._detected_constructs.append("function")
                async_kw = "अतुल्यकालिक " if m.group(1) else ""
                name = m.group(2)
                if name not in ("return", "throw", "delete", "typeof", "void"):
                    params = self._translate_params(m.group(3))
                    return f"{indent}{async_kw}कर्म {name}({params}) {{"

        # Variable declarations
        m = re.match(r"(const|let|var)\s+(\w+)\s*=\s*(.+?);?\s*$", stripped)
        if m:
            self._detected_constructs.append("variable")
            kw = "स्थिर" if m.group(1) == "const" else "चर"
            name = m.group(2)
            value = self._translate_expr(m.group(3).rstrip(";"))
            return f"{indent}{kw} {name} = {value}"

        # if/else
        m = re.match(r"if\s*\((.+?)\)\s*\{?", stripped)
        if m:
            self._detected_constructs.append("conditional")
            cond = self._translate_expr(m.group(1))
            return f"{indent}यदि ({cond}) {{"

        m = re.match(r"\}\s*else\s+if\s*\((.+?)\)\s*\{?", stripped)
        if m:
            cond = self._translate_expr(m.group(1))
            return f"{indent}}} अन्यथा_यदि ({cond}) {{"

        m = re.match(r"\}\s*else\s*\{?", stripped)
        if m:
            return f"{indent}}} अन्यथा {{"

        m = re.match(r"else\s*\{?", stripped)
        if m:
            return f"{indent}अन्यथा {{"

        # for loops
        m = re.match(r"for\s*\(\s*(?:const|let|var)\s+(\w+)\s+of\s+(.+?)\s*\)\s*\{?", stripped)
        if m:
            self._detected_constructs.append("loop")
            var_name = m.group(1)
            iterable = self._translate_expr(m.group(2))
            return f"{indent}प्रत्येक {var_name} अन्तर्गत {iterable} {{"

        m = re.match(r"for\s*\(\s*(?:const|let|var)\s+(\w+)\s+in\s+(.+?)\s*\)\s*\{?", stripped)
        if m:
            self._detected_constructs.append("loop")
            var_name = m.group(1)
            iterable = self._translate_expr(m.group(2))
            return f"{indent}प्रत्येक {var_name} अन्तर्गत {iterable} {{"

        # Standard for loop
        m = re.match(r"for\s*\((.+?);(.+?);(.+?)\)\s*\{?", stripped)
        if m:
            self._detected_constructs.append("loop")
            init = self._translate_expr(m.group(1))
            cond = self._translate_expr(m.group(2))
            update = self._translate_expr(m.group(3))
            return f"{indent}{init}\n{indent}यावत् ({cond}) {{\n{indent}    # body\n{indent}    {update}"

        # while
        m = re.match(r"while\s*\((.+?)\)\s*\{?", stripped)
        if m:
            self._detected_constructs.append("loop")
            cond = self._translate_expr(m.group(1))
            return f"{indent}यावत् ({cond}) {{"

        # return
        m = re.match(r"return\s+(.+?);?\s*$", stripped)
        if m:
            self._detected_constructs.append("return")
            value = self._translate_expr(m.group(1))
            return f"{indent}प्रत्यागच्छ {value}"

        m = re.match(r"return\s*;\s*$", stripped)
        if m:
            return f"{indent}प्रत्यागच्छ"

        # throw
        m = re.match(r"throw\s+(.+?);?\s*$", stripped)
        if m:
            value = self._translate_expr(m.group(1))
            return f"{indent}उठाओ {value}"

        # try/catch
        if stripped.startswith("try"):
            self._detected_constructs.append("try_except")
            return f"{indent}प्रयत्न {{"

        m = re.match(r"\}\s*catch\s*\(\s*(?:\w+\s+)?(\w+)\s*\)\s*\{?", stripped)
        if m:
            err_name = m.group(1)
            return f"{indent}}} दोष ({err_name}) {{"

        if stripped.startswith("finally"):
            return f"{indent}}} अन्ततः {{"

        # Import
        m = re.match(r"import\s+(?:(\w+)\s*,?\s*)?(?:\{([^}]*)\})?\s*from\s+['\"](.+?)['\"]", stripped)
        if m:
            self._detected_constructs.append("import")
            module = m.group(3)
            parts: list[str] = []
            if m.group(1):
                parts.append(f'आयात "{module}" से "{m.group(1)}"')
            if m.group(2):
                for item in m.group(2).split(","):
                    item = item.strip()
                    if item:
                        parts.append(f'से "{module}" आयात "{item}"')
            return f"{indent}" + f"\n{indent}".join(parts)

        # Export
        if stripped.startswith("export default"):
            rest = stripped[len("export default"):].strip()
            return f"{indent}निर्यात डिफ़ॉल्ट {rest}"
        elif stripped.startswith("export"):
            rest = stripped[len("export"):].strip()
            return f"{indent}निर्यात {rest}"

        # console.log
        if "console.log(" in stripped:
            expr = stripped.replace("console.log(", "मुद्रय(").rstrip(";")
            return f"{indent}{expr}"

        # .then() / .catch() promise chains
        m = re.match(r"\.then\s*\(\s*(\w+)\s*=>\s*(.+?)\s*\)", stripped)
        if m:
            param = m.group(1)
            body = self._translate_expr(m.group(2))
            return f"{indent}# promise.then: {param} => {body}"

        # Closing braces
        if stripped in ("}", "};"):
            return f"{indent}}}"

        # General expression statement - translate keywords
        translated = self._translate_expr(stripped.rstrip(";"))
        return f"{indent}{translated}" if translated != stripped.rstrip(";") else line

    def _translate_inline_statement(self, body: str) -> str:
        body = body.strip().rstrip(";").strip()
        if not body:
            return "कोई_कार्य_नहीं"
        if body.startswith("return "):
            value = self._translate_expr(body[len("return "):].rstrip(";"))
            return f"प्रत्यागच्छ {value}"
        if body.startswith("throw "):
            value = self._translate_expr(body[len("throw "):].rstrip(";"))
            return f"उत्क्षिप {value}"
        return self._translate_expr(body)

    def _translate_params(self, params_str: str) -> str:
        """Translate JS function parameters to Vak style."""
        if not params_str.strip():
            return ""
        params = [p.strip().split(":")[0].split("=")[0].strip() for p in params_str.split(",")]
        params = [p for p in params if p and p != "this"]
        return ", ".join(params)

    def _translate_expr(self, expr: str) -> str:
        """Translate a JavaScript expression to Vak syntax."""
        result = expr

        # Replace keywords
        for js_kw, vak_kw in _JS_VAK_KEYWORDS.items():
            # Use word boundary matching for safety
            result = re.sub(rf"\b{re.escape(js_kw)}\b", vak_kw, result)

        # Arrow function expressions
        result = re.sub(r"\(([^)]*)\)\s*=>\s*", lambda m: f"कर्म ({m.group(1)}) -> ", result)

        # Template literals
        def _replace_template(m: re.Match) -> str:
            inner = m.group(1)
            # Convert ${expr} to {expr}
            inner = re.sub(r'\$\{([^}]*)\}', r'{\1}', inner)
            return '"' + inner + '"'
        result = re.sub(r'`([^`]*)`', _replace_template, result)

        # Spread operator — mark for manual review
        if "..." in result:
            result = result.replace("...", "# spread:")

        # Null coalescing
        result = re.sub(r"(\w+)\s*\?\?\s*(\w+)", r"\1 या \2", result)

        # Ternary — handle with care to avoid catastrophic backtracking
        ternary_match = re.search(r'([^?:]+?)\s*\?\s*([^?:]+?)\s*:\s*([^?:]+)$', result)
        if ternary_match:
            result = f"{ternary_match.group(2).strip()} यदि {ternary_match.group(1).strip()} अन्यथा {ternary_match.group(3).strip()}"

        return result
