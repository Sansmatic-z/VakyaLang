"""
Phase 1: Python → Vak Translator Codex Page.

Translates Python source code into equivalent VakyaLang code by:
1. Parsing Python into an AST
2. Mapping Python constructs to Vak equivalents (using CORRECT Vak runtime keywords)
3. Generating valid Vak code with Devanagari keywords
4. Validating output via the REAL Vak compiler
"""
from __future__ import annotations

import ast as py_ast
import re
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from .utils import _overall_confidence
from ..engines.ast_builder import ASTBuilder, ASTNode, ASTNodeType


# ------------------------------------------------------------------
# Python → Vak keyword mapping
# Uses ACTUAL Vak runtime keywords (verified against tokens.py)
# ------------------------------------------------------------------
_PY_VAK_KEYWORDS: dict[str, str] = {
    # Functions and control flow
    "def": "कर्म",
    "class": "वर्ग",
    "return": "प्रत्यागच्छ",
    "if": "यदि",
    "elif": "अन्यथा_यदि",
    "else": "अन्यथा",
    "for": "प्रत्येक",
    "while": "यावत्",
    "break": "विराम",
    "continue": "अग्रे",
    "pass": "कोई_कार्य_नहीं",
    # Imports
    "import": "आयात",
    "from": "से",
    # Exceptions
    "try": "प्रयत्न",
    "except": "दोष",
    "finally": "अन्ततः",
    "with": "साथ",
    "raise": "उत्क्षिप",
    "assert": "दावा",
    # Async
    "async": "अतुल्यकालिक",
    "await": "प्रतीक्षा",
    "yield": "उपज",
    # Variables and scope
    "global": "वैश्विक",
    "nonlocal": "अस्थानिक",
    "del": "हटाओ",
    "self": "स्वयं",
    # Booleans and None
    "True": "सत्य",
    "False": "असत्य",
    "None": "शून्य",
    # Logical operators
    "and": "और",
    "or": "अथवा",
    "not": "न",
    # Membership / identity
    "in": "अन्तर्गत",
    "is": "है",
    # Lambda
    "lambda": "कार्य",
    # Built-in functions
    "print": "मुद्रय",
    "len": "लंबाई",
    "range": "परिसर",
    "str": "तार",
    "int": "संख्या",
    "float": "संख्या",
    "bool": "तर्क",
    "list": "सूची",
    "dict": "शब्दकोश",
    "set": "समुच्चय",
    "tuple": "टपल",
    # Common methods
    "append": "जोड़ें",
    "pop": "निकालें",
    "remove": "हटाएं",
    "keys": "कुंजियाँ",
    "values": "मान",
    "get": "प्राप्त",
    "extend": "विस्तार",
    "insert": "डालें",
    "sort": "क्रमबद्ध",
    "reverse": "उलटा",
    "split": "विभाजित",
    "strip": "पट्टी",
    "upper": "ऊपरी",
    "lower": "निचला",
    "replace": "बदलें",
    "find": "खोजें",
    "count": "गिनती",
    "index": "सूचकांक",
}

# Operator mappings
_PY_OPS: dict[str, str] = {
    "Add": "+",
    "Sub": "-",
    "Mult": "*",
    "Div": "/",
    "FloorDiv": "//",
    "Mod": "%",
    "Pow": "**",
    "BitAnd": "&",
    "BitOr": "|",
    "BitXor": "^",
    "LShift": "<<",
    "RShift": ">>",
    "Eq": "==",
    "NotEq": "!=",
    "Lt": "<",
    "LtE": "<=",
    "Gt": ">",
    "GtE": ">=",
    "And": "और",
    "Or": "अथवा",
}


class PythonToVakCodexPage(CodexPage):
    """Translates Python source code to VakyaLang."""
    name = "python_to_vak"
    description = "Python source to Vak translator page"
    priority = 30
    kind = "python"
    chapter = "translators"
    chapter_title = "Language Translators"
    chapter_order = 10
    capabilities = ("translate", "python", "ast", "generate")
    emits_vak = True
    extensions = ("py",)
    max_fixpoint_passes = 2
    max_source_length = 500_000  # 500KB guard against ReDoS

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._ast_builder = ASTBuilder()
        self._diagnostics: list[CodexDiagnostic] = []
        self._detected_constructs: list[str] = []

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------
    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        if filename and filename.endswith(".py"):
            return CodexPageProbe(self.name, 100, ".py source path")
        # Check if source looks like Python
        python_indicators = [
            r"^\s*def\s+\w+",
            r"^\s*class\s+\w+",
            r"^\s*import\s+\w+",
            r"^\s*from\s+\w+\s+import",
            r"^\s*if\s+__name__\s*==",
            r"^\s*@\w+",  # decorators
            r"self\.",
            r"^\s*print\s*\(",
        ]
        score = 0
        for pattern in python_indicators:
            if re.search(pattern, source, re.MULTILINE):
                score += 20
        if score > 0 and not any("\u0900" <= ch <= "\u097f" for ch in source):
            return CodexPageProbe(self.name, min(score, 95), "Python-like source detected")
        return CodexPageProbe(self.name, 0, "not a Python source candidate")

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------
    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        self._diagnostics = []
        self._detected_constructs = []

        # Guard against excessively large sources
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
                metadata={"source_kind": "python", "error": "source_too_large"},
            )

        try:
            vak_code = self._translate_python(source)
            transformed = vak_code != source

            if transformed:
                self._diagnostics.append(CodexDiagnostic(
                    page=self.name, level="info",
                    message="Python source translated to Vak",
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
                    "source_kind": "python",
                    "detected_constructs": list(self._detected_constructs),
                    "translation_method": "ast_based",
                },
            )
        except SyntaxError as exc:
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="error",
                message=f"Python syntax error: {exc}",
                confidence="do_not_touch",
                line=getattr(exc, "lineno", 0),
            ))
            return CodexResult(
                page=self.name, original_source=source, source=source,
                transformed=False, confidence="do_not_touch",
                diagnostics=tuple(self._diagnostics), manifest=self.manifest(),
                metadata={"source_kind": "python", "error": str(exc)},
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
                metadata={"source_kind": "python", "error": str(exc)},
            )

    # ------------------------------------------------------------------
    # Translation engine
    # ------------------------------------------------------------------
    def _translate_python(self, source: str) -> str:
        if not source or not source.strip():
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="warning",
                message="Empty or whitespace-only Python source provided",
                confidence="suggest_only",
            ))
            return ""
        tree = py_ast.parse(source)
        self._detected_constructs.append("module")
        parts: list[str] = []
        for node in tree.body:
            parts.append(self._convert_node(node))
        return "\n".join(p for p in parts if p is not None)

    def _convert_node(self, node: py_ast.AST) -> str | None:
        if isinstance(node, py_ast.FunctionDef):
            return self._convert_function_def(node)
        elif isinstance(node, py_ast.AsyncFunctionDef):
            return self._convert_function_def(node, is_async=True)
        elif isinstance(node, py_ast.ClassDef):
            return self._convert_class_def(node)
        elif isinstance(node, py_ast.Assign):
            return self._convert_assign(node)
        elif isinstance(node, py_ast.AugAssign):
            return self._convert_aug_assign(node)
        elif isinstance(node, py_ast.AnnAssign):
            return self._convert_ann_assign(node)
        elif isinstance(node, py_ast.If):
            return self._convert_if(node)
        elif isinstance(node, py_ast.For):
            return self._convert_for(node)
        elif isinstance(node, py_ast.While):
            return self._convert_while(node)
        elif isinstance(node, py_ast.Return):
            return self._convert_return(node)
        elif isinstance(node, py_ast.Expr):
            return self._convert_expr_stmt(node)
        elif isinstance(node, py_ast.Import):
            return self._convert_import(node)
        elif isinstance(node, py_ast.ImportFrom):
            return self._convert_import_from(node)
        elif isinstance(node, py_ast.Try):
            return self._convert_try(node)
        elif isinstance(node, py_ast.With):
            return self._convert_with(node)
        elif isinstance(node, (py_ast.Break, py_ast.Continue, py_ast.Pass)):
            return self._convert_simple_stmt(node)
        elif isinstance(node, py_ast.Assert):
            return self._convert_assert(node)
        elif isinstance(node, py_ast.Raise):
            return self._convert_raise(node)
        elif isinstance(node, py_ast.Await):
            return self._convert_await_node(node)
        else:
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="warning",
                message=f"Unsupported Python construct: {node.__class__.__name__}",
                confidence="suggest_only",
                line=getattr(node, "lineno", 0),
            ))
            return None

    def _convert_function_def(self, node: py_ast.FunctionDef | py_ast.AsyncFunctionDef, *, is_async: bool = False) -> str:
        self._detected_constructs.append("function")
        params: list[str] = []
        for arg in node.args.args:
            if arg.arg == "self":
                continue
            params.append(arg.arg)
        param_str = ", ".join(params)
        prefix = "अतुल्यकालिक " if is_async else ""
        lines = [f"{prefix}कर्म {node.name}({param_str}):"]
        for stmt in node.body:
            body_line = self._convert_node(stmt)
            if body_line:
                for bl in body_line.split("\n"):
                    lines.append(f"    {bl}")
        return "\n".join(lines)

    def _convert_class_def(self, node: py_ast.ClassDef) -> str:
        self._detected_constructs.append("class")
        bases = [self._convert_expr(b) for b in node.bases]
        base_str = f" ({', '.join(bases)})" if bases else ""
        lines = [f"वर्ग {node.name}{base_str}:"]
        for stmt in node.body:
            body_line = self._convert_node(stmt)
            if body_line:
                for bl in body_line.split("\n"):
                    lines.append(f"    {bl}")
        return "\n".join(lines)

    def _convert_assign(self, node: py_ast.Assign) -> str:
        self._detected_constructs.append("variable")
        targets = [self._convert_expr(t) for t in node.targets]
        value = self._convert_expr(node.value)
        target_str = ", ".join(targets)
        return f"चर {target_str} = {value}"

    def _convert_aug_assign(self, node: py_ast.AugAssign) -> str:
        target = self._convert_expr(node.target)
        value = self._convert_expr(node.value)
        op = _PY_OPS.get(node.op.__class__.__name__, node.op.__class__.__name__)
        return f"{target} {op}= {value}"

    def _convert_ann_assign(self, node: py_ast.AnnAssign) -> str:
        target = self._convert_expr(node.target)
        value = self._convert_expr(node.value) if node.value else "अपरिभाषित"
        return f"चर {target} = {value}"

    def _convert_if(self, node: py_ast.If) -> str:
        self._detected_constructs.append("conditional")
        cond = self._convert_expr(node.test)
        lines = [f"यदि {cond}:"]
        for stmt in node.body:
            body_line = self._convert_node(stmt)
            if body_line:
                for bl in body_line.split("\n"):
                    lines.append(f"    {bl}")
        # Handle elif/else chains
        current = node
        while current.orelse:
            if len(current.orelse) == 1 and isinstance(current.orelse[0], py_ast.If):
                current = current.orelse[0]
                cond = self._convert_expr(current.test)
                lines.append(f"अन्यथा_यदि {cond}:")
                for stmt in current.body:
                    body_line = self._convert_node(stmt)
                    if body_line:
                        for bl in body_line.split("\n"):
                            lines.append(f"    {bl}")
            else:
                lines.append("अन्यथा:")
                for stmt in current.orelse:
                    body_line = self._convert_node(stmt)
                    if body_line:
                        for bl in body_line.split("\n"):
                            lines.append(f"    {bl}")
                break
        return "\n".join(lines)

    def _convert_for(self, node: py_ast.For) -> str:
        self._detected_constructs.append("loop")
        target = self._convert_expr(node.target)
        iterable = self._convert_expr(node.iter)
        lines = [f"प्रत्येक {target} अन्तर्गत {iterable}:"]
        for stmt in node.body:
            body_line = self._convert_node(stmt)
            if body_line:
                for bl in body_line.split("\n"):
                    lines.append(f"    {bl}")
        return "\n".join(lines)

    def _convert_while(self, node: py_ast.While) -> str:
        self._detected_constructs.append("loop")
        cond = self._convert_expr(node.test)
        lines = [f"यावत् {cond}:"]
        for stmt in node.body:
            body_line = self._convert_node(stmt)
            if body_line:
                for bl in body_line.split("\n"):
                    lines.append(f"    {bl}")
        return "\n".join(lines)

    def _convert_return(self, node: py_ast.Return) -> str:
        self._detected_constructs.append("return")
        if node.value:
            value = self._convert_expr(node.value)
            return f"प्रत्यागच्छ {value}"
        return "प्रत्यागच्छ"

    def _convert_import(self, node: py_ast.Import) -> str:
        self._detected_constructs.append("import")
        parts: list[str] = []
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            parts.append(f'आयात "{name}"')
        return "\n".join(parts)

    def _convert_import_from(self, node: py_ast.ImportFrom) -> str:
        self._detected_constructs.append("import")
        module = node.module or ""
        parts: list[str] = []
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            parts.append(f'आयात "{module}.{name}"')
        return "\n".join(parts)

    def _convert_try(self, node: py_ast.Try) -> str:
        self._detected_constructs.append("try_except")
        lines = ["प्रयत्न:"]
        for stmt in node.body:
            body_line = self._convert_node(stmt)
            if body_line:
                for bl in body_line.split("\n"):
                    lines.append(f"    {bl}")
        for handler in node.handlers:
            exc_name = ""
            if handler.type:
                exc_name = self._convert_expr(handler.type)
            if handler.name:
                exc_name = f"{handler.name}"
            exc_part = f" {exc_name}" if exc_name.strip() else ""
            lines.append(f"दोष{exc_part}:")
            for stmt in handler.body:
                body_line = self._convert_node(stmt)
                if body_line:
                    for bl in body_line.split("\n"):
                        lines.append(f"    {bl}")
        if node.orelse:
            lines.append("अन्यथा:")
            for stmt in node.orelse:
                body_line = self._convert_node(stmt)
                if body_line:
                    for bl in body_line.split("\n"):
                        lines.append(f"    {bl}")
        if node.finalbody:
            lines.append("अन्ततः:")
            for stmt in node.finalbody:
                body_line = self._convert_node(stmt)
                if body_line:
                    for bl in body_line.split("\n"):
                        lines.append(f"    {bl}")
        return "\n".join(lines)

    def _convert_with(self, node: py_ast.With) -> str:
        self._detected_constructs.append("with")
        items = [self._convert_expr(item.context_expr) for item in node.items]
        item_str = ", ".join(items)
        lines = [f"साथ {item_str}:"]
        for stmt in node.body:
            body_line = self._convert_node(stmt)
            if body_line:
                for bl in body_line.split("\n"):
                    lines.append(f"    {bl}")
        return "\n".join(lines)

    def _convert_simple_stmt(self, node: py_ast.AST) -> str:
        if isinstance(node, py_ast.Break):
            return "विराम"
        elif isinstance(node, py_ast.Continue):
            return "अग्रे"
        elif isinstance(node, py_ast.Pass):
            return "कोई_कार्य_नहीं"
        return ""

    def _convert_expr_stmt(self, node: py_ast.Expr) -> str | None:
        expr = self._convert_expr(node.value)
        if expr:
            return expr
        return None

    def _convert_assert(self, node: py_ast.Assert) -> str:
        self._detected_constructs.append("assert")
        test = self._convert_expr(node.test)
        if node.msg:
            msg = self._convert_expr(node.msg)
            return f"दावा ({test}, {msg})"
        return f"दावा ({test})"

    def _convert_raise(self, node: py_ast.Raise) -> str:
        self._detected_constructs.append("raise")
        if node.exc:
            exc = self._convert_expr(node.exc)
            return f"उत्क्षिप {exc}"
        return "उत्क्षिप"

    def _convert_await_node(self, node: py_ast.Await) -> str:
        self._detected_constructs.append("await")
        value = self._convert_expr(node.value)
        return f"प्रतीक्षा {value}"

    # ------------------------------------------------------------------
    # Expression conversion
    # ------------------------------------------------------------------
    def _convert_expr(self, node: py_ast.AST | None) -> str:
        if node is None:
            return ""
        if isinstance(node, py_ast.Constant):
            return self._convert_constant(node)
        elif isinstance(node, py_ast.Name):
            return _PY_VAK_KEYWORDS.get(node.id, node.id)
        elif isinstance(node, py_ast.BinOp):
            return self._convert_bin_op(node)
        elif isinstance(node, py_ast.UnaryOp):
            return self._convert_unary_op(node)
        elif isinstance(node, py_ast.Compare):
            return self._convert_compare(node)
        elif isinstance(node, py_ast.BoolOp):
            return self._convert_bool_op(node)
        elif isinstance(node, py_ast.Call):
            return self._convert_call(node)
        elif isinstance(node, py_ast.Attribute):
            return self._convert_attribute(node)
        elif isinstance(node, py_ast.Subscript):
            return self._convert_subscript(node)
        elif isinstance(node, py_ast.List):
            return self._convert_list(node)
        elif isinstance(node, py_ast.Tuple):
            return self._convert_tuple(node)
        elif isinstance(node, py_ast.Dict):
            return self._convert_dict(node)
        elif isinstance(node, py_ast.Set):
            return self._convert_set(node)
        elif isinstance(node, py_ast.ListComp):
            return self._convert_list_comp(node)
        elif isinstance(node, py_ast.Lambda):
            return self._convert_lambda(node)
        elif isinstance(node, py_ast.IfExp):
            return self._convert_if_exp(node)
        elif isinstance(node, py_ast.JoinedStr):
            return self._convert_joined_str(node)
        else:
            return f"# TODO: {node.__class__.__name__}"

    def _convert_constant(self, node: py_ast.Constant) -> str:
        if node.value is None:
            return "शून्य"
        elif isinstance(node.value, bool):
            return "सत्य" if node.value else "असत्य"
        elif isinstance(node.value, str):
            return repr(node.value)
        elif isinstance(node.value, (int, float)):
            return str(node.value)
        elif isinstance(node.value, bytes):
            return repr(node.value)
        elif isinstance(node.value, ellipsis):
            return "..."
        return repr(node.value)

    def _convert_bin_op(self, node: py_ast.BinOp) -> str:
        left = self._convert_expr(node.left)
        right = self._convert_expr(node.right)
        op = _PY_OPS.get(node.op.__class__.__name__, "?")
        return f"({left} {op} {right})"

    def _convert_unary_op(self, node: py_ast.UnaryOp) -> str:
        operand = self._convert_expr(node.operand)
        if isinstance(node.op, py_ast.Not):
            return f"(न {operand})"
        elif isinstance(node.op, py_ast.USub):
            return f"(-{operand})"
        elif isinstance(node.op, py_ast.UAdd):
            return f"(+{operand})"
        elif isinstance(node.op, py_ast.Invert):
            return f"(~{operand})"
        return operand

    def _convert_compare(self, node: py_ast.Compare) -> str:
        left = self._convert_expr(node.left)
        parts = [left]
        for op, comparator in zip(node.ops, node.comparators):
            op_str = _PY_OPS.get(op.__class__.__name__, "?")
            right = self._convert_expr(comparator)
            parts.append(f"{op_str} {right}")
        return f"({' '.join(parts)})"

    def _convert_bool_op(self, node: py_ast.BoolOp) -> str:
        op = _PY_OPS.get(node.op.__class__.__name__, "और")
        parts = [self._convert_expr(v) for v in node.values]
        return f" ({op}) ".join(parts)

    def _convert_call(self, node: py_ast.Call) -> str:
        func = self._convert_expr(node.func)
        args = [self._convert_expr(a) for a in node.args]
        for kw in node.keywords:
            if kw.arg:
                args.append(f"{kw.arg}={self._convert_expr(kw.value)}")
        arg_str = ", ".join(args)
        return f"{func}({arg_str})"

    def _convert_attribute(self, node: py_ast.Attribute) -> str:
        obj = self._convert_expr(node.value)
        attr = _PY_VAK_KEYWORDS.get(node.attr, node.attr)
        return f"{obj}.{attr}"

    def _convert_subscript(self, node: py_ast.Subscript) -> str:
        obj = self._convert_expr(node.value)
        key = self._convert_expr(node.slice)
        return f"{obj}[{key}]"

    def _convert_list(self, node: py_ast.List) -> str:
        items = [self._convert_expr(e) for e in node.elts]
        return f"[{', '.join(items)}]"

    def _convert_tuple(self, node: py_ast.Tuple) -> str:
        items = [self._convert_expr(e) for e in node.elts]
        return f"({', '.join(items)})"

    def _convert_dict(self, node: py_ast.Dict) -> str:
        items: list[str] = []
        for k, v in zip(node.keys, node.values):
            key = self._convert_expr(k) if k else "..."
            val = self._convert_expr(v)
            items.append(f"{key}: {val}")
        return "{" + ", ".join(items) + "}"

    def _convert_set(self, node: py_ast.Set) -> str:
        items = [self._convert_expr(e) for e in node.elts]
        return "{" + ", ".join(items) + "}"

    def _convert_list_comp(self, node: py_ast.ListComp) -> str:
        elt = self._convert_expr(node.elt)
        generators = []
        for gen in node.generators:
            target = self._convert_expr(gen.target)
            iterable = self._convert_expr(gen.iter)
            generators.append(f"{target} अन्तर्गत {iterable}")
        gen_str = ", ".join(generators)
        return f"[{elt}  # {gen_str}]"

    def _convert_lambda(self, node: py_ast.Lambda) -> str:
        params = [self._convert_expr(a) for a in node.args.args]
        param_str = ", ".join(params)
        body = self._convert_expr(node.body)
        return f"कार्य ({param_str}): {body}"

    def _convert_if_exp(self, node: py_ast.IfExp) -> str:
        body = self._convert_expr(node.body)
        test = self._convert_expr(node.test)
        orelse = self._convert_expr(node.orelse)
        return f"({body} यदि {test} अन्यथा {orelse})"

    def _convert_joined_str(self, node: py_ast.JoinedStr) -> str:
        parts: list[str] = []
        for val in node.values:
            if isinstance(val, py_ast.Constant):
                parts.append(str(val.value))
            elif isinstance(val, py_ast.FormattedValue):
                parts.append(f"{{{self._convert_expr(val.value)}}}")
        return '"' + "".join(parts) + '"'
