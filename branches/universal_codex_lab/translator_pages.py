from __future__ import annotations

import ast as py_ast
import re
from typing import Any

from runtime.src.codex.models import CodexDiagnostic, CodexPageProbe, CodexResult
from runtime.src.codex.page import CodexPage


def _brace_reindent(lines: list[str]) -> str:
    emitted: list[str] = []
    indent = 0
    for raw_line in lines:
        original_indent = len(raw_line) - len(raw_line.lstrip())
        line = raw_line.strip()
        if not line:
            emitted.append("")
            continue
        while line.startswith("}"):
            indent = max(0, indent - 1)
            line = line[1:].strip()
        if not line:
            continue
        opens_block = line.endswith("{")
        if opens_block:
            line = line[:-1].rstrip()
        effective_indent = max(indent * 4, original_indent)
        suffix = ":" if opens_block and not line.endswith(":") else ""
        emitted.append(" " * effective_indent + line + suffix)
        if opens_block:
            indent += 1
    return "\n".join(emitted).strip()


class PythonToVakExperimentalCodexPage(CodexPage):
    name = "python_to_vak_experimental"
    description = "Experimental AST-based Python to Vak translator"
    priority = 72
    kind = "branch_python"
    chapter = "experimental_language"
    chapter_title = "Experimental Language"
    chapter_order = 90
    capabilities = ("experimental", "python", "translate", "ast")
    emits_vak = True
    extensions = ("py",)
    experimental = True
    max_fixpoint_passes = 2
    max_source_length = 500_000

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._diagnostics: list[CodexDiagnostic] = []
        self._detected_constructs: list[str] = []

    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        if filename and filename.endswith(".py"):
            return CodexPageProbe(self.name, 120, ".py source path")
        score = 0
        for pattern in (
            r"^\s*def\s+\w+",
            r"^\s*class\s+\w+",
            r"^\s*import\s+\w+",
            r"^\s*from\s+\w+\s+import",
            r"^\s*print\s*\(",
        ):
            if re.search(pattern, source, re.MULTILINE):
                score += 20
        return CodexPageProbe(self.name, min(score, 110), "Python-like source detected" if score else "not a Python source candidate")

    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        self._diagnostics = []
        self._detected_constructs = []
        if len(source) > self.max_source_length:
            self._diagnostics.append(
                CodexDiagnostic(
                    page=self.name,
                    level="error",
                    message=f"Source too large ({len(source)} bytes, max {self.max_source_length})",
                    confidence="do_not_touch",
                )
            )
            return CodexResult(
                page=self.name,
                original_source=source,
                source=source,
                transformed=False,
                confidence="do_not_touch",
                diagnostics=tuple(self._diagnostics),
                metadata={"source_kind": "python", "error": "source_too_large"},
            )
        try:
            tree = py_ast.parse(source)
            parts = [self._convert_node(node) for node in tree.body]
            translated = "\n".join(part for part in parts if part)
            transformed = translated != source
            if transformed:
                self._diagnostics.append(
                    CodexDiagnostic(
                        page=self.name,
                        level="info",
                        message="Python source translated to Vak",
                        confidence="safe_auto_fix",
                    )
                )
            confidence = "suggest_only" if any(item.level == "warning" for item in self._diagnostics) else "safe_auto_fix"
            return CodexResult(
                page=self.name,
                original_source=source,
                source=translated,
                transformed=transformed,
                confidence=confidence if transformed else "suggest_only",
                diagnostics=tuple(self._diagnostics),
                metadata={
                    "source_kind": "python",
                    "detected_constructs": list(self._detected_constructs),
                    "translation_method": "ast_based",
                },
            )
        except SyntaxError as exc:
            self._diagnostics.append(
                CodexDiagnostic(
                    page=self.name,
                    level="error",
                    message=f"Python syntax error: {exc}",
                    confidence="do_not_touch",
                    line=getattr(exc, "lineno", 0),
                )
            )
            return CodexResult(
                page=self.name,
                original_source=source,
                source=source,
                transformed=False,
                confidence="do_not_touch",
                diagnostics=tuple(self._diagnostics),
                metadata={"source_kind": "python", "error": str(exc)},
            )

    def _convert_node(self, node: py_ast.AST) -> str | None:
        if isinstance(node, py_ast.FunctionDef):
            self._detected_constructs.append("function")
            params = ", ".join(arg.arg for arg in node.args.args if arg.arg != "self")
            lines = [f"कर्म {node.name}({params}):"]
            if not node.body:
                lines.append("    कोई_कार्य_नहीं")
            for stmt in node.body:
                rendered = self._convert_node(stmt)
                if rendered:
                    for line in rendered.split("\n"):
                        lines.append(f"    {line}")
            return "\n".join(lines)
        if isinstance(node, py_ast.ClassDef):
            self._detected_constructs.append("class")
            lines = [f"वर्ग {node.name}:"]
            if not node.body:
                lines.append("    कोई_कार्य_नहीं")
            for stmt in node.body:
                rendered = self._convert_node(stmt)
                if rendered:
                    for line in rendered.split("\n"):
                        lines.append(f"    {line}")
            return "\n".join(lines)
        if isinstance(node, py_ast.Assign):
            targets = ", ".join(self._convert_expr(target) for target in node.targets)
            return f"चर {targets} = {self._convert_expr(node.value)}"
        if isinstance(node, py_ast.Return):
            return "प्रत्यागच्छ" if node.value is None else f"प्रत्यागच्छ {self._convert_expr(node.value)}"
        if isinstance(node, py_ast.If):
            lines = [f"यदि {self._convert_expr(node.test)}:"]
            for stmt in node.body:
                rendered = self._convert_node(stmt)
                if rendered:
                    for line in rendered.split("\n"):
                        lines.append(f"    {line}")
            if node.orelse:
                lines.append("अन्यथा:")
                for stmt in node.orelse:
                    rendered = self._convert_node(stmt)
                    if rendered:
                        for line in rendered.split("\n"):
                            lines.append(f"    {line}")
            return "\n".join(lines)
        if isinstance(node, py_ast.For):
            lines = [f"प्रत्येक {self._convert_expr(node.target)} अन्तर्गत {self._convert_expr(node.iter)}:"]
            for stmt in node.body:
                rendered = self._convert_node(stmt)
                if rendered:
                    for line in rendered.split("\n"):
                        lines.append(f"    {line}")
            return "\n".join(lines)
        if isinstance(node, py_ast.While):
            lines = [f"यावत् {self._convert_expr(node.test)}:"]
            for stmt in node.body:
                rendered = self._convert_node(stmt)
                if rendered:
                    for line in rendered.split("\n"):
                        lines.append(f"    {line}")
            return "\n".join(lines)
        if isinstance(node, py_ast.Expr):
            return self._convert_expr(node.value)
        if isinstance(node, py_ast.Import):
            return "\n".join(f'आयात "{alias.asname or alias.name}"' for alias in node.names)
        if isinstance(node, py_ast.ImportFrom):
            module = node.module or ""
            return "\n".join(f'आयात "{module}.{alias.asname or alias.name}"' for alias in node.names)
        if isinstance(node, py_ast.Pass):
            return "कोई_कार्य_नहीं"
        if isinstance(node, py_ast.Break):
            return "विराम"
        if isinstance(node, py_ast.Continue):
            return "अग्रे"
        self._diagnostics.append(
            CodexDiagnostic(
                page=self.name,
                level="warning",
                message=f"Unsupported Python construct: {node.__class__.__name__}",
                confidence="suggest_only",
                line=getattr(node, "lineno", 0),
            )
        )
        return None

    def _convert_expr(self, node: py_ast.AST | None) -> str:
        if node is None:
            return ""
        if isinstance(node, py_ast.Name):
            return "स्वयं" if node.id == "self" else node.id
        if isinstance(node, py_ast.Constant):
            if node.value is None:
                return "शून्य"
            if isinstance(node.value, bool):
                return "सत्य" if node.value else "असत्य"
            return repr(node.value) if isinstance(node.value, str) else str(node.value)
        if isinstance(node, py_ast.Call):
            func = self._convert_expr(node.func)
            args = ", ".join(self._convert_expr(arg) for arg in node.args)
            if func == "print":
                return f"मुद्रय({args})"
            return f"{func}({args})"
        if isinstance(node, py_ast.Attribute):
            return f"{self._convert_expr(node.value)}.{node.attr}"
        if isinstance(node, py_ast.BinOp):
            return f"({self._convert_expr(node.left)} {self._op(node.op)} {self._convert_expr(node.right)})"
        if isinstance(node, py_ast.Compare) and len(node.ops) == 1 and len(node.comparators) == 1:
            return f"({self._convert_expr(node.left)} {self._cmp(node.ops[0])} {self._convert_expr(node.comparators[0])})"
        if isinstance(node, py_ast.List):
            return "[" + ", ".join(self._convert_expr(item) for item in node.elts) + "]"
        return node.__class__.__name__

    @staticmethod
    def _op(node: py_ast.operator) -> str:
        return {
            py_ast.Add: "+",
            py_ast.Sub: "-",
            py_ast.Mult: "*",
            py_ast.Div: "/",
        }.get(type(node), "?")

    @staticmethod
    def _cmp(node: py_ast.cmpop) -> str:
        return {
            py_ast.Eq: "==",
            py_ast.NotEq: "!=",
            py_ast.Lt: "<",
            py_ast.LtE: "<=",
            py_ast.Gt: ">",
            py_ast.GtE: ">=",
        }.get(type(node), "?")


class JavaScriptToVakExperimentalCodexPage(CodexPage):
    name = "javascript_to_vak_experimental"
    description = "Experimental JavaScript/TypeScript to Vak translator"
    priority = 73
    kind = "branch_python"
    chapter = "experimental_language"
    chapter_title = "Experimental Language"
    chapter_order = 90
    capabilities = ("experimental", "javascript", "translate", "regex")
    emits_vak = True
    extensions = ("js", "ts", "jsx", "tsx")
    experimental = True
    max_fixpoint_passes = 2

    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        if filename and filename.endswith((".js", ".ts", ".jsx", ".tsx")):
            return CodexPageProbe(self.name, 118, "JavaScript-like source path")
        score = 0
        for pattern in (r"^\s*(const|let|var)\s+\w+", r"^\s*function\s+\w+", r"^\s*class\s+\w+", r"console\.\w+"):
            if re.search(pattern, source, re.MULTILINE):
                score += 18
        return CodexPageProbe(self.name, min(score, 108), "JavaScript-like source detected" if score else "not a JavaScript candidate")

    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        diagnostics: list[CodexDiagnostic] = [
            CodexDiagnostic(
                page=self.name,
                level="info",
                message="regex-based JavaScript translation is experimental",
                confidence="suggest_only",
            )
        ]
        lines: list[str] = []
        for raw in source.splitlines():
            line = raw.strip()
            if not line:
                continue
            if line.startswith("//"):
                lines.append("# " + line[2:].strip())
                continue
            inline_function = re.match(r"(?:const|let|var)\s+(\w+)\s*=\s*\(([^)]*)\)\s*=>\s*(.+);?$", line)
            if inline_function:
                name, params, expr = inline_function.groups()
                lines.append(f"कर्म {name}({params}): {{")
                lines.append(f"    प्रत्यागच्छ {self._expr(expr)}")
                lines.append("}")
                continue
            function_match = re.match(r"(async\s+)?function\s+(\w+)\s*\(([^)]*)\)\s*\{\s*(.*?)\s*\}\s*;?$", line)
            if function_match:
                async_prefix, name, params, body = function_match.groups()
                prefix = "अतुल्यकालिक " if async_prefix else ""
                lines.append(f"{prefix}कर्म {name}({params}): {{")
                lines.append(f"    {self._stmt(body)}")
                lines.append("}")
                continue
            class_match = re.match(r"class\s+(\w+)", line)
            if class_match:
                lines.append(f"वर्ग {class_match.group(1)} {{")
                continue
            method_match = re.match(r"(\w+)\s*\(([^)]*)\)\s*\{\s*(.*?)\s*\}\s*;?$", line)
            if method_match and not line.startswith(("if", "for", "while", "catch")):
                name, params, body = method_match.groups()
                lines.append(f"कर्म {name}({params}) {{")
                lines.append(f"    {self._stmt(body)}")
                lines.append("}")
                continue
            var_match = re.match(r"(const|let|var)\s+(\w+)\s*=\s*(.+?);?$", line)
            if var_match:
                kw = "स्थिर" if var_match.group(1) == "const" else "चर"
                lines.append(f"{kw} {var_match.group(2)} = {self._expr(var_match.group(3))}")
                continue
            if_match = re.match(r"if\s*\((.+?)\)\s*\{?$", line)
            if if_match:
                lines.append(f"यदि ({self._expr(if_match.group(1))}) {{")
                continue
            while_match = re.match(r"while\s*\((.+?)\)\s*\{?$", line)
            if while_match:
                lines.append(f"यावत् ({self._expr(while_match.group(1))}) {{")
                continue
            for_of_match = re.match(r"for\s*\(\s*(?:const|let|var)\s+(\w+)\s+of\s+(.+?)\s*\)\s*\{?$", line)
            if for_of_match:
                lines.append(f"प्रत्येक {for_of_match.group(1)} अन्तर्गत {self._expr(for_of_match.group(2))} {{")
                continue
            if line in ("}", "};"):
                lines.append("}")
                continue
            lines.append(self._stmt(line.rstrip(";")))
        output = _brace_reindent(lines)
        return CodexResult(
            page=self.name,
            original_source=source,
            source=output,
            transformed=output != source,
            confidence="suggest_only",
            diagnostics=tuple(diagnostics),
            metadata={"source_kind": "javascript", "translation_method": "regex_based"},
        )

    def _stmt(self, body: str) -> str:
        body = body.strip().rstrip(";")
        if body.startswith("return "):
            return f"प्रत्यागच्छ {self._expr(body[len('return '):])}"
        if "console.log(" in body:
            inner = body[body.find("(") + 1: body.rfind(")")]
            return f"मुद्रय({self._expr(inner)})"
        return self._expr(body)

    def _expr(self, expr: str) -> str:
        result = expr.strip()
        result = result.replace("this.", "स्वयं.")
        result = result.replace("true", "सत्य").replace("false", "असत्य").replace("null", "शून्य")
        result = re.sub(r'`([^`]*)`', lambda m: '"' + re.sub(r'\$\{([^}]*)\}', r'{\1}', m.group(1)) + '"', result)
        return result


class PseudocodeToVakExperimentalCodexPage(CodexPage):
    name = "pseudocode_to_vak_experimental"
    description = "Experimental pseudocode to Vak translator"
    priority = 74
    kind = "branch_python"
    chapter = "experimental_language"
    chapter_title = "Experimental Language"
    chapter_order = 90
    capabilities = ("experimental", "pseudocode", "translate")
    emits_vak = True
    extensions = ("pseudo", "algo")
    experimental = True
    max_fixpoint_passes = 2

    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        if filename and filename.endswith((".pseudo", ".algo")):
            return CodexPageProbe(self.name, 115, "pseudocode source path")
        score = 0
        for pattern in (r"(?i)\bfunction\b", r"(?i)\bset\b", r"(?i)\bfor each\b", r"(?i)\breturn\b", r"←"):
            if re.search(pattern, source):
                score += 15
        return CodexPageProbe(self.name, min(score, 95), "pseudocode detected" if score else "not a pseudocode candidate")

    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        diagnostics: list[CodexDiagnostic] = []
        lines: list[str] = []
        for raw in source.splitlines():
            line = raw.strip()
            if not line:
                continue
            if re.match(r"(?i)^(algorithm|begin|end)\b", line):
                continue
            fn_match = re.match(r"(?i)^function\s+(\w+)\s*(?:\(([^)]*)\))?", line)
            if fn_match:
                params = ", ".join(part.strip() for part in (fn_match.group(2) or "").split(",") if part.strip())
                lines.append(f"कर्म {fn_match.group(1)}({params}) {{")
                continue
            set_match = re.match(r"(?i)^set\s+(\w+)\s*[=←]\s*(.+)$", line)
            if set_match:
                lines.append(f"चर {set_match.group(1)} = {set_match.group(2)}")
                continue
            arrow_assign = re.match(r"^(\w+)\s*←\s*(.+)$", line)
            if arrow_assign:
                lines.append(f"चर {arrow_assign.group(1)} = {arrow_assign.group(2)}")
                continue
            if_match = re.match(r"(?i)^if\s+(.+?)(?:\s+then)?$", line)
            if if_match:
                lines.append(f"यदि ({if_match.group(1)}) {{")
                continue
            else_match = re.match(r"(?i)^else$", line)
            if else_match:
                lines.append("} अन्यथा {")
                continue
            for_match = re.match(r"(?i)^for\s+(?:each\s+)?(\w+)\s+in\s+(.+)$", line)
            if for_match:
                lines.append(f"प्रत्येक {for_match.group(1)} अन्तर्गत {for_match.group(2)} {{")
                continue
            while_match = re.match(r"(?i)^while\s+(.+)$", line)
            if while_match:
                lines.append(f"यावत् ({while_match.group(1)}) {{")
                continue
            return_match = re.match(r"(?i)^return(?:\s+(.+))?$", line)
            if return_match:
                value = return_match.group(1)
                lines.append("प्रत्यागच्छ" if value is None else f"प्रत्यागच्छ {value}")
                continue
            print_match = re.match(r"(?i)^(?:print|output|display)\s+(.+)$", line)
            if print_match:
                lines.append(f"मुद्रय({print_match.group(1)})")
                continue
            if re.match(r"(?i)^end\s+(if|for|while|function)", line):
                lines.append("}")
                continue
            lines.append(line)
        output = _brace_reindent(lines)
        return CodexResult(
            page=self.name,
            original_source=source,
            source=output,
            transformed=output != source,
            confidence="suggest_only",
            diagnostics=tuple(diagnostics),
            metadata={"source_kind": "pseudocode", "translation_method": "keyword_mapping"},
        )
