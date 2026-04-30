from __future__ import annotations

from difflib import get_close_matches
from pathlib import Path
import re
from typing import Any

from sanskrit_coder.core.translator import SanskritTranslator

from .code_transformer import VakCodeTransformer
from .compiler import Compiler
from .errors import format_vak_error
from .lexer import Lexer, is_identifier_part, is_identifier_start
from .parser import Parser
from .runtime_catalog import build_builtin_catalog, builtin_alias_map
from .rupantar_models import (
    RupantarEdit,
    RupantarResult,
    RupantarSuggestion,
    ValidationEvent,
    _CallSignature,
    _ModuleMemberRepair,
    _TypedMemberRepair,
    _UnresolvedNameIssue,
    _ValidationReport,
)
from .stdlib_manifest import build_stdlib_manifest, module_alias_map
from .tokens import KEYWORDS
from .vm import VakVM


_SUBSCRIPT_DIGIT_MAP = str.maketrans({
    "₀": "०",
    "₁": "१",
    "₂": "२",
    "₃": "३",
    "₄": "४",
    "₅": "५",
    "₆": "६",
    "₇": "७",
    "₈": "८",
    "₉": "९",
})

_IDENT_START_RE = r"[A-Za-z_\u0900-\u097F]"
_IDENT_BODY_RE = r"[A-Za-z0-9_\u0900-\u097F]"
_IDENT_RE = rf"{_IDENT_START_RE}{_IDENT_BODY_RE}*"
_MODULE_RE = rf"{_IDENT_RE}(?:\.{_IDENT_RE})*"

_CANONICAL_TOKEN_MAP = {
    "जबतक": "यावत्",
    "while": "यावत्",
    "elif": "अन्यत्",
    "else_if": "अन्यत्",
    "except": "दोष",
    "catch": "दोष",
    "पकड़ो": "दोष",
    "try": "प्रयत्न",
    "प्रयास": "प्रयत्न",
    "raise": "उत्क्षिप",
    "throw": "उत्क्षिप",
    "फेंको": "उत्क्षिप",
    "with": "साथ",
    "सहित": "साथ",
    "as": "जैसे",
    "के_रूप_में": "जैसे",
    "match": "प्रत्यभिज्ञा",
    "मिलान": "प्रत्यभिज्ञा",
    "data": "डेटा",
    "आँकड़ा": "डेटा",
    "break": "विराम",
    "तोड़ो": "विराम",
    "continue": "अग्रे",
    "जारी": "अग्रे",
    "else": "अन्यथा",
    "otherwise": "अन्यथा",
    "या": "अथवा",
    "return": "प्रत्यागच्छ",
    "वापस": "प्रत्यागच्छ",
    "print": "मुद्रय",
    "बोलो": "मुद्रय",
    "global": "वैश्विक",
    "nonlocal": "अस्थानिक",
    "from": "से",
    "import": "आयात",
    "async": "अतुल्यकालिक",
    "await": "प्रतीक्षा",
    "True": "सत्य",
    "true": "सत्य",
    "False": "असत्य",
    "false": "असत्य",
    "None": "शून्य",
    "none": "शून्य",
}

_BUILTIN_ALIAS_MAP = {
    "print": "मुद्रय",
    "len": "दीर्घता",
    "range": "परास",
    "type": "प्रकार",
    "str": "पाठ_कर",
    "open": "खोलो",
    "sorted": "क्रमबद्ध",
    "sum": "योग",
    "max": "अधिकतम",
    "min": "न्यूनतम",
    "keys": "कुंजियाँ",
    "values": "मान",
}

_MEMBER_ALIAS_MAP = {
    "append": "जोड़ो",
    "keys": "कुंजियाँ",
    "values": "मान",
    "strip": "छाँटो",
    "split": "विभाजन",
    "join": "संयोग",
}

_TYPE_LITERAL_ALIASES = {
    "int": "संख्या",
    "float": "संख्या",
    "number": "संख्या",
    "संख्या": "संख्या",
    "str": "तार",
    "string": "तार",
    "text": "तार",
    "तार": "तार",
    "पाठ": "तार",
    "dict": "शब्दकोश",
    "dictionary": "शब्दकोश",
    "शब्दकोश": "शब्दकोश",
    "list": "सूची",
    "array": "सूची",
    "सूची": "सूची",
    "bool": "बूलियन",
    "boolean": "बूलियन",
    "बूलियन": "बूलियन",
    "none": "शून्य",
    "null": "शून्य",
    "शून्य": "शून्य",
}

_TYPE_PATTERN_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<head>यदि|अन्यत्|if|elif)\s+"
    rf"(?P<expr>.+?)\s+के\s+प्रकार\s*(?P<op>==|!=)\s*(?P<type>{_IDENT_RE})\s*:$"
)

_TYPE_CALL_PATTERN_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<head>यदि|अन्यत्|if|elif)\s+"
    rf"प्रकार\((?P<expr>.+?)\)\s*(?P<op>==|!=)\s*(?P<type>{_IDENT_RE})\s*:$"
)

_RESERVED_DECL_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<decl>चर|मान|स्थिर)\s+"
    rf"(?P<name>{_IDENT_RE})(?!{_IDENT_BODY_RE})"
)
_ASSIGN_TARGET_RE = rf"{_IDENT_RE}(?:\s*(?:\.\s*{_IDENT_RE}|\[[^\n\]]+\]))*"
_AUGMENTED_ASSIGN_RE = re.compile(
    rf"^(?P<indent>[ \t]*)(?P<target>{_ASSIGN_TARGET_RE})\s*"
    r"(?P<op>\+=|-=|\*=|/=|%=|\*\*=)\s*(?P<expr>.+?)\s*$"
)
_POSTFIX_INCREMENT_RE = re.compile(
    rf"^(?P<indent>[ \t]*)(?P<target>{_ASSIGN_TARGET_RE})\s*(?P<op>\+\+|--)\s*$"
)
_PREFIX_INCREMENT_RE = re.compile(
    rf"^(?P<indent>[ \t]*)(?P<op>\+\+|--)\s*(?P<target>{_ASSIGN_TARGET_RE})\s*$"
)

_PYTHON_FROM_IMPORT_RE = re.compile(
    rf"^(?P<indent>[ \t]*)(?:से|from)\s+(?P<module>{_MODULE_RE})\s+(?:आयात|import)\s+(?P<names>.+?)\s*$"
)

_GENERATOR_CLASS_DECL_RE = re.compile(
    rf"^(?P<indent>[ \t]*)(?:वर्ग|श्रेणी|class|क्लास)\s+"
    rf"(?P<name>{_IDENT_RE})(?:\((?P<super>{_IDENT_RE})\))?\s*\{{\s*;?\s*$"
)

_GENERATOR_FUNC_DECL_RE = re.compile(
    rf"^(?P<indent>[ \t]*)(?P<async>(?:अतुल्यकालिक|async)\s+)?"
    rf"(?:कर्म|कार्य|def|function|फंक्शन)\s+(?P<name>{_IDENT_RE})"
    r"\((?P<params>.*)\)(?P<rtype>\s*(?:→|->)\s*[^:{]+?)?\s*\{\s*;?\s*$"
)

_GENERATOR_VAR_DECL_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<decl>परिवर्तनी|let|var|const|स्थिरांक)\s+(?P<body>.+?)\s*;?\s*$"
)

_GENERATOR_RETURN_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?:लौटाओ|return)\b(?P<rest>.*?)(?:\s*;)?\s*$"
)

_GENERATOR_CLOSING_BRACE_RE = re.compile(r"^(?P<indent>[ \t]*)}\s*;?\s*$")
_GENERATOR_JOINED_ELSE_RE = re.compile(
    r"^(?P<indent>[ \t]*)}\s*(?:अन्यथा|else|otherwise)\s*\{\s*;?\s*$"
)

_GENERATOR_FOREACH_RE = re.compile(
    rf"^(?P<indent>[ \t]*)(?:foreach|for\s+each|for)\s+(?:(?:char|var|let|const)\s+)?"
    rf"(?P<vars>{_IDENT_RE}(?:\s*,\s*{_IDENT_RE})*)\s+in\s+(?P<iterable>.+?)\s*\{{?\s*;?\s*$"
)

_INSUFFICIENT_ARGS_RE = re.compile(
    r"\[Line (?P<line>\d+)\]\s+अपर्याप्त तर्क: कम से कम (?P<required>\d+), मिला (?P<provided>\d+)"
)
_UNKNOWN_KWARGS_RE = re.compile(
    r"\[Line (?P<line>\d+)\]\s+अज्ञात नामित तर्क: (?P<names>.+)"
)

_FUNC_HEADER_RE = re.compile(
    rf"^(?P<indent>[ \t]*)(?P<prefix>(?:अतुल्यकालिक\s+)?कर्म\s+{_IDENT_RE})"
    r"\((?P<params>.*)\)(?P<suffix>\s*(?:→.+?)?\s*:\s*)$"
)

_CROSS_SCRIPT_IDENTIFIER_ALIASES: dict[str, tuple[str, ...]] = {
    "र": ("r",),
    "ग": ("g",),
    "ब": ("b",),
    "आर": ("r",),
    "जी": ("g",),
    "बी": ("b",),
}

_TYPED_MEMBER_METHODS: dict[str, tuple[str, ...]] = {
    "list": ("append", "जोड़ो"),
    "dict": ("keys", "values", "कुंजियाँ", "मान"),
    "str": ("strip", "split", "join", "छाँटो", "विभाजन", "संयोग"),
}


class _Scope:
    def __init__(self, parent: "_Scope | None" = None):
        self.parent = parent
        self.names: set[str] = set()

    def declare(self, name: str | None) -> None:
        if name:
            self.names.add(name)

    def contains(self, name: str) -> bool:
        if name in self.names:
            return True
        if self.parent is not None:
            return self.parent.contains(name)
        return False

    def visible_names(self) -> set[str]:
        names = set(self.names)
        if self.parent is not None:
            names.update(self.parent.visible_names())
        return names


class _UndefinedNameAnalyzer:
    def __init__(
        self,
        builtins: set[str],
        *,
        suggestion_cutoff: float = 0.84,
        suggestion_limit: int = 3,
    ):
        self.builtins = set(builtins)
        self.suggestion_cutoff = suggestion_cutoff
        self.suggestion_limit = max(1, suggestion_limit)
        self.unresolved: list[_UnresolvedNameIssue] = []

    def analyze(self, program: Any) -> tuple[str, ...]:
        self.unresolved = []
        root = _Scope()
        for name in self.builtins:
            root.declare(name)
        self._analyze_block(getattr(program, "body", []), root)
        warnings: list[str] = []
        for issue in self.unresolved:
            if issue.suggestion:
                warnings.append(
                    f"Line {issue.line}: अपरिभाषित नाम '{issue.name}' (संभवतः '{issue.suggestion}')"
                )
            else:
                warnings.append(f"Line {issue.line}: अपरिभाषित नाम '{issue.name}'")
        return tuple(warnings)

    def _analyze_block(self, statements: list[Any], scope: _Scope) -> None:
        self._predeclare(statements, scope)
        for stmt in statements:
            self._visit_stmt(stmt, scope)

    def _predeclare(self, statements: list[Any], scope: _Scope) -> None:
        for stmt in statements:
            kind = type(stmt).__name__
            if kind == "VarDecl":
                for name in getattr(stmt, "names", []):
                    scope.declare(name)
            elif kind == "ConstDecl":
                scope.declare(getattr(stmt, "name", None))
            elif kind == "FuncDecl":
                scope.declare(getattr(stmt, "name", None))
            elif kind == "ClassDecl":
                scope.declare(getattr(stmt, "name", None))
            elif kind == "DataDecl":
                scope.declare(getattr(stmt, "name", None))
                for variant in getattr(stmt, "variants", []):
                    scope.declare(getattr(variant, "name", None))
            elif kind == "ImportStmt":
                names = getattr(stmt, "names", None)
                if names:
                    for name in names:
                        scope.declare(name)
                else:
                    module_name = getattr(stmt, "module", "")
                    scope.declare(module_name)
                    scope.declare(module_name.split(".", 1)[0])

    def _visit_stmt(self, stmt: Any, scope: _Scope) -> None:
        kind = type(stmt).__name__
        if kind == "VarDecl":
            self._visit_expr(getattr(stmt, "value", None), scope)
            return
        if kind == "ConstDecl":
            self._visit_expr(getattr(stmt, "value", None), scope)
            return
        if kind == "FuncDecl":
            for default in getattr(stmt, "defaults", []):
                self._visit_expr(default, scope)
            inner = _Scope(scope)
            for param in getattr(stmt, "params", []):
                if hasattr(param, "name"):
                    inner.declare(param.name)
                elif isinstance(param, tuple) and param:
                    inner.declare(param[0])
            inner.declare(getattr(stmt, "varargs", None))
            body = getattr(stmt, "body", None)
            self._analyze_block(getattr(body, "stmts", []), inner)
            return
        if kind == "ClassDecl":
            self._visit_expr(getattr(stmt, "superclass", None), scope)
            inner = _Scope(scope)
            body = getattr(stmt, "body", None)
            self._analyze_block(getattr(body, "stmts", []), inner)
            return
        if kind == "DataDecl":
            return
        if kind == "ReturnStmt":
            self._visit_expr(getattr(stmt, "value", None), scope)
            return
        if kind == "PrintStmt":
            for value in getattr(stmt, "values", []):
                self._visit_expr(value, scope)
            return
        if kind == "IfStmt":
            self._visit_expr(getattr(stmt, "condition", None), scope)
            self._analyze_block(getattr(getattr(stmt, "then_body", None), "stmts", []), _Scope(scope))
            for cond, body in getattr(stmt, "elif_clauses", []):
                self._visit_expr(cond, scope)
                self._analyze_block(getattr(body, "stmts", []), _Scope(scope))
            else_body = getattr(stmt, "else_body", None)
            if else_body is not None:
                self._analyze_block(getattr(else_body, "stmts", []), _Scope(scope))
            return
        if kind == "WhileStmt":
            self._visit_expr(getattr(stmt, "condition", None), scope)
            self._analyze_block(getattr(getattr(stmt, "body", None), "stmts", []), _Scope(scope))
            return
        if kind == "ForStmt":
            self._visit_expr(getattr(stmt, "iterable", None), scope)
            inner = _Scope(scope)
            for name in getattr(stmt, "var_names", []):
                inner.declare(name)
            self._analyze_block(getattr(getattr(stmt, "body", None), "stmts", []), inner)
            return
        if kind == "TryStmt":
            self._analyze_block(getattr(getattr(stmt, "try_body", None), "stmts", []), _Scope(scope))
            for handler in getattr(stmt, "handlers", []):
                inner = _Scope(scope)
                inner.declare(getattr(handler, "bind_name", None))
                inner.declare(getattr(handler, "match_name", None))
                self._analyze_block(getattr(getattr(handler, "body", None), "stmts", []), inner)
            finally_body = getattr(stmt, "finally_body", None)
            if finally_body is not None:
                self._analyze_block(getattr(finally_body, "stmts", []), _Scope(scope))
            return
        if kind == "WithStmt":
            self._visit_expr(getattr(stmt, "expr", None), scope)
            inner = _Scope(scope)
            inner.declare(getattr(stmt, "var_name", None))
            self._analyze_block(getattr(getattr(stmt, "body", None), "stmts", []), inner)
            return
        if kind == "AsyncWithStmt":
            self._visit_expr(getattr(stmt, "expr", None), scope)
            inner = _Scope(scope)
            inner.declare(getattr(stmt, "var_name", None))
            self._analyze_block(getattr(getattr(stmt, "body", None), "stmts", []), inner)
            return
        if kind == "ThrowStmt":
            self._visit_expr(getattr(stmt, "value", None), scope)
            return
        if kind == "ExprStmt":
            self._visit_expr(getattr(stmt, "expr", None), scope)
            return
        if kind == "MatchStmt":
            self._visit_expr(getattr(stmt, "subject", None), scope)
            for case in getattr(stmt, "cases", []):
                inner = _Scope(scope)
                self._visit_expr(getattr(case, "guard", None), inner)
                self._visit_pattern(getattr(case, "pattern", None), inner)
                self._analyze_block(getattr(getattr(case, "body", None), "stmts", []), inner)
            return
        if kind == "Block":
            self._analyze_block(getattr(stmt, "stmts", []), _Scope(scope))

    def _visit_expr(self, expr: Any, scope: _Scope) -> None:
        if expr is None:
            return
        kind = type(expr).__name__
        if kind == "IdentifierExpr":
            name = getattr(expr, "name", "")
            if name and not scope.contains(name):
                visible = scope.visible_names()
                candidates = self._suggest_names(name, visible)
                suggestion = candidates[0] if candidates else None
                self.unresolved.append(
                    _UnresolvedNameIssue(
                        name=name,
                        line=getattr(expr, "line", 0),
                        suggestion=suggestion,
                        candidates=tuple(candidates),
                    )
                )
            return
        if kind in {"NumberLiteral", "StringLiteral", "BoolLiteral", "NullLiteral", "WildcardPattern"}:
            return
        if kind == "BinaryExpr":
            self._visit_expr(expr.left, scope)
            self._visit_expr(expr.right, scope)
            return
        if kind == "UnaryExpr":
            self._visit_expr(expr.operand, scope)
            return
        if kind == "ConditionalExpr":
            self._visit_expr(expr.condition, scope)
            self._visit_expr(expr.then_expr, scope)
            self._visit_expr(expr.else_expr, scope)
            return
        if kind == "AssignExpr":
            self._visit_expr(expr.value, scope)
            self._declare_target(expr.target, scope)
            self._visit_assignment_target(expr.target, scope)
            return
        if kind == "CallExpr":
            self._visit_expr(expr.callee, scope)
            for arg in expr.args:
                self._visit_expr(arg, scope)
            for value in expr.kwargs.values():
                self._visit_expr(value, scope)
            return
        if kind == "MemberExpr":
            self._visit_expr(expr.obj, scope)
            return
        if kind == "IndexExpr":
            self._visit_expr(expr.obj, scope)
            self._visit_expr(expr.index, scope)
            return
        if kind == "SliceExpr":
            self._visit_expr(expr.obj, scope)
            self._visit_expr(expr.start, scope)
            self._visit_expr(expr.stop, scope)
            self._visit_expr(expr.step, scope)
            return
        if kind in {"ListLiteral", "TupleLiteral", "SetLiteral"}:
            for item in expr.elements:
                self._visit_expr(item, scope)
            return
        if kind == "DictLiteral":
            for key, value in expr.pairs:
                self._visit_expr(key, scope)
                self._visit_expr(value, scope)
            return
        if kind == "FStringExpr":
            for part in expr.parts:
                if hasattr(part, "__dict__"):
                    self._visit_expr(part, scope)
            return
        if kind == "LambdaExpr":
            inner = _Scope(scope)
            for name in getattr(expr, "params", []):
                inner.declare(name)
            inner.declare(getattr(expr, "varargs", None))
            self._visit_expr(expr.body, inner)
            return
        if kind == "AwaitExpr":
            self._visit_expr(expr.operand, scope)
            return
        if kind == "ListComp":
            inner = _Scope(scope)
            inner.declare(getattr(expr, "var_name", None))
            self._visit_expr(expr.iterable, scope)
            self._visit_expr(expr.filter_expr, inner)
            self._visit_expr(expr.expr, inner)
            return
        if kind == "DictComp":
            inner = _Scope(scope)
            inner.declare(getattr(expr, "var_name", None))
            self._visit_expr(expr.iterable, scope)
            self._visit_expr(expr.filter_expr, inner)
            self._visit_expr(expr.key_expr, inner)
            self._visit_expr(expr.value_expr, inner)
            return
        if kind == "GeneratorExpr":
            inner = _Scope(scope)
            inner.declare(getattr(expr, "var_name", None))
            self._visit_expr(expr.iterable, scope)
            self._visit_expr(expr.filter_expr, inner)
            self._visit_expr(expr.expr, inner)
            return

    def _visit_assignment_target(self, target: Any, scope: _Scope) -> None:
        if target is None:
            return
        kind = type(target).__name__
        if kind == "IdentifierExpr":
            return
        if kind == "MemberExpr":
            self._visit_expr(target.obj, scope)
            return
        if kind == "IndexExpr":
            self._visit_expr(target.obj, scope)
            self._visit_expr(target.index, scope)
            return
        if kind in {"ListLiteral", "TupleLiteral"}:
            for item in target.elements:
                self._visit_assignment_target(item, scope)

    def _declare_target(self, target: Any, scope: _Scope) -> None:
        if target is None:
            return
        kind = type(target).__name__
        if kind == "IdentifierExpr":
            scope.declare(getattr(target, "name", None))
            return
        if kind in {"ListLiteral", "TupleLiteral"}:
            for item in target.elements:
                self._declare_target(item, scope)

    def _visit_pattern(self, pattern: Any, scope: _Scope) -> None:
        if pattern is None:
            return
        kind = type(pattern).__name__
        if kind == "BindingPattern":
            scope.declare(getattr(pattern, "name", None))
            return
        if kind == "SequencePattern":
            scope.declare(getattr(pattern, "rest_name", None))
            for item in getattr(pattern, "elements", []):
                self._visit_pattern(item, scope)
            return
        if kind == "CallPattern":
            callee = getattr(pattern, "callee", None)
            if callee and not scope.contains(callee):
                self.unresolved.append(
                    _UnresolvedNameIssue(
                        name=callee,
                        line=getattr(pattern, "line", 0),
                        suggestion=None,
                        candidates=(),
                    )
                )
            for arg in getattr(pattern, "args", []):
                self._visit_pattern(arg, scope)

    def _suggest_names(self, name: str, visible: set[str]) -> tuple[str, ...]:
        matches = get_close_matches(
            name,
            sorted(visible),
            n=self.suggestion_limit,
            cutoff=self.suggestion_cutoff,
        )
        if not matches:
            relaxed_cutoff = max(0.7, self.suggestion_cutoff - 0.14)
            matches = get_close_matches(
                name,
                sorted(visible),
                n=self.suggestion_limit,
                cutoff=relaxed_cutoff,
            )
        results: list[str] = list(matches)
        for candidate in _CROSS_SCRIPT_IDENTIFIER_ALIASES.get(name, ()):
            if candidate in visible and candidate not in results:
                results.append(candidate)
        return tuple(results[: self.suggestion_limit])

    def _suggest_name(self, name: str, visible: set[str]) -> str | None:
        matches = self._suggest_names(name, visible)
        if matches:
            return matches[0]
        return None


class VakyaRupantar:
    """Vak-native source transformer and normalization engine."""

    _from_import_re = re.compile(
        rf"^(?P<indent>[ \t]*)आयात\s+(?P<names>.+?)\s+से\s+(?P<module>{_MODULE_RE})\s*$"
    )
    _import_re = re.compile(
        rf"^(?P<indent>[ \t]*)आयात\s+(?P<module>{_MODULE_RE})\s*$"
    )

    def __init__(
        self,
        *,
        active_branches: list[str] | None = None,
        branch_registry: Any = None,
    ) -> None:
        if branch_registry is None:
            from branches.registry import create_default_registry

            branch_registry = create_default_registry()
        self.branch_registry = branch_registry
        self.branch_runtime = self.branch_registry.create_runtime(
            list(active_branches or []),
            include_defaults=True,
        )
        self.active_branches = tuple(self.branch_runtime.active_names())
        self.code_transformer = VakCodeTransformer()
        self.translator = SanskritTranslator()
        self.vm = VakVM(
            enable_jit=False,
            branch_runtime=self.branch_runtime,
            branch_registry=self.branch_registry,
        )
        self.builtin_catalog = build_builtin_catalog(
            self.vm.builtins,
            active_branches=self.active_branches,
        )
        self.builtin_names = set(self.builtin_catalog.keys())
        self.builtin_signatures = self._build_builtin_signatures()
        self._stdlib_root = Path(__file__).resolve().parent.parent / "stdlib"
        self.stdlib_manifest = build_stdlib_manifest(self._stdlib_root)
        self._module_exports_cache: dict[tuple[str | None, str], tuple[str, ...] | None] = {}
        self.canonical_token_map = dict(_CANONICAL_TOKEN_MAP)
        self.builtin_alias_map = builtin_alias_map(
            self.vm.builtins,
            active_branches=self.active_branches,
        )
        self.builtin_alias_map.update(_BUILTIN_ALIAS_MAP)
        self.member_alias_map = dict(_MEMBER_ALIAS_MAP)
        self.branch_member_aliases: dict[str, dict[str, dict[str, str]]] = {}
        self.module_aliases: dict[str, str] = module_alias_map(self._stdlib_root)
        self.max_fixpoint_passes = 3
        self.module_match_cutoff = 0.74
        self.module_export_match_cutoff = 0.72
        self.unresolved_name_cutoff = 0.84
        self.unresolved_suggestion_limit = 3
        self.candidate_search_width = 1
        self.fuzzy_builtin_cutoff: float | None = None
        self.fuzzy_member_cutoff: float | None = None
        self.auto_fix_unresolved_names = False
        self.promote_null_guard_defaults = False
        self.infer_missing_optional_params = False
        self._load_branch_rupantar_rules()

    def transform_source(
        self,
        source: str,
        *,
        source_path: str | None = None,
    ) -> RupantarResult:
        original_source = source
        edits: list[RupantarEdit] = []
        rejected_fixes: list[RupantarSuggestion] = []
        suggestions: list[RupantarSuggestion] = []
        warnings: list[str] = []
        translation_used = False
        translation_blocked_reason: str | None = None
        validation_events: list[ValidationEvent] = []

        translated = self.code_transformer.transform(source)
        if translated.transformed:
            translation_used = True
            source = translated.source
            edits.append(
                RupantarEdit(
                    line=0,
                    layer="translation",
                    before="<english-like source>",
                    after="<vak source>",
                    reason="existing वाक्य-अनुवादक applied before रूपान्तर",
                )
            )
        elif translated.blocked_reason:
            translation_blocked_reason = translated.blocked_reason
            warnings.append(translated.blocked_reason)
            suggestions.append(
                RupantarSuggestion(
                    line=translated.blocked_line or 0,
                    layer="translation",
                    message=translated.blocked_reason,
                    confidence="do_not_touch",
                )
            )

        source, line_edits = self._normalize_textual_layers(source, source_path=source_path)
        edits.extend(line_edits)

        validation = self._validate_source(
            source,
            source_path=source_path,
            stage="initial",
            validation_events=validation_events,
        )
        warnings.extend(validation.warnings)
        suggestions.extend(validation.suggestions)

        source, import_binding_edits, validation = self._apply_import_binding_repairs(
            source,
            validation,
            normalization_edits=line_edits,
            source_path=source_path,
            validation_events=validation_events,
            rejected_fixes=rejected_fixes,
        )
        if import_binding_edits:
            edits.extend(import_binding_edits)
            warnings = list(validation.warnings)
            suggestions = list(validation.suggestions)
            if translation_blocked_reason:
                warnings.insert(0, translation_blocked_reason)
                suggestions.insert(
                    0,
                    RupantarSuggestion(
                        line=translated.blocked_line or 0,
                        layer="translation",
                        message=translation_blocked_reason,
                        confidence="do_not_touch",
                    ),
                )

        source, ast_edits, validation = self._apply_ast_normalizations(
            source,
            validation,
            source_path=source_path,
            validation_events=validation_events,
            rejected_fixes=rejected_fixes,
        )
        if ast_edits:
            edits.extend(ast_edits)
            warnings = list(validation.warnings)
            suggestions = list(validation.suggestions)
            if translation_blocked_reason:
                warnings.insert(0, translation_blocked_reason)
                suggestions.insert(
                    0,
                    RupantarSuggestion(
                        line=translated.blocked_line or 0,
                        layer="translation",
                        message=translation_blocked_reason,
                        confidence="do_not_touch",
                    ),
                )

        source, unresolved_edits, validation = self._apply_unambiguous_unresolved_repairs(
            source,
            validation,
            source_path=source_path,
            validation_events=validation_events,
            rejected_fixes=rejected_fixes,
        )
        if unresolved_edits:
            edits.extend(unresolved_edits)
            warnings = list(validation.warnings)
            suggestions = list(validation.suggestions)
            if translation_blocked_reason:
                warnings.insert(0, translation_blocked_reason)
                suggestions.insert(
                    0,
                    RupantarSuggestion(
                        line=translated.blocked_line or 0,
                        layer="translation",
                        message=translation_blocked_reason,
                        confidence="do_not_touch",
                    ),
                )

        source, error_edits, validation = self._apply_error_driven_repairs(
            source,
            validation,
            source_path=source_path,
            validation_events=validation_events,
            rejected_fixes=rejected_fixes,
        )
        if error_edits:
            edits.extend(error_edits)
            warnings = list(validation.warnings)
            suggestions = list(validation.suggestions)
            if translation_blocked_reason:
                warnings.insert(0, translation_blocked_reason)
                suggestions.insert(
                    0,
                    RupantarSuggestion(
                        line=translated.blocked_line or 0,
                        layer="translation",
                        message=translation_blocked_reason,
                        confidence="do_not_touch",
                    ),
                )

        if self.auto_fix_unresolved_names:
            improved_source, adaptive_edits, improved_validation = self._apply_adaptive_repairs(
                source,
                validation,
                source_path=source_path,
                validation_events=validation_events,
                rejected_fixes=rejected_fixes,
            )
            if improved_source != source:
                source = improved_source
                edits.extend(adaptive_edits)
                validation = improved_validation
                warnings = list(validation.warnings)
                suggestions = list(validation.suggestions)
                if translation_blocked_reason:
                    warnings.insert(0, translation_blocked_reason)
                    suggestions.insert(
                        0,
                        RupantarSuggestion(
                            line=translated.blocked_line or 0,
                            layer="translation",
                            message=translation_blocked_reason,
                            confidence="do_not_touch",
                        ),
                    )

        transformed = source != original_source
        deduped_warnings = tuple(dict.fromkeys(warnings))
        return RupantarResult(
            original_source=original_source,
            source=source,
            transformed=transformed,
            edits=tuple(edits),
            rejected_fixes=tuple(self._dedupe_suggestions(rejected_fixes)),
            suggestions=tuple(self._dedupe_suggestions(suggestions)),
            warnings=deduped_warnings,
            active_branches=self.active_branches,
            translation_used=translation_used,
            translation_blocked_reason=translation_blocked_reason,
            syntax_valid=validation.syntax_valid,
            compiled=validation.compiled,
            validation_events=tuple(validation_events),
        )

    def _load_branch_rupantar_rules(self) -> None:
        rules: dict[str, Any] = {
            "canonical_tokens": self.canonical_token_map,
            "builtin_aliases": self.builtin_alias_map,
            "member_aliases": self.member_alias_map,
            "branch_member_aliases": self.branch_member_aliases,
            "module_aliases": self.module_aliases,
            "max_fixpoint_passes": self.max_fixpoint_passes,
            "module_match_cutoff": self.module_match_cutoff,
            "module_export_match_cutoff": self.module_export_match_cutoff,
            "unresolved_name_cutoff": self.unresolved_name_cutoff,
            "unresolved_suggestion_limit": self.unresolved_suggestion_limit,
            "candidate_search_width": self.candidate_search_width,
            "fuzzy_builtin_cutoff": self.fuzzy_builtin_cutoff,
            "fuzzy_member_cutoff": self.fuzzy_member_cutoff,
            "auto_fix_unresolved_names": self.auto_fix_unresolved_names,
            "promote_null_guard_defaults": self.promote_null_guard_defaults,
            "infer_missing_optional_params": self.infer_missing_optional_params,
        }
        self.branch_runtime.extend_rupantar_rules(rules)
        self.max_fixpoint_passes = max(1, int(rules.get("max_fixpoint_passes", 3)))
        self.module_match_cutoff = float(rules.get("module_match_cutoff", 0.74))
        self.module_export_match_cutoff = float(rules.get("module_export_match_cutoff", 0.72))
        self.unresolved_name_cutoff = float(rules.get("unresolved_name_cutoff", 0.84))
        self.unresolved_suggestion_limit = max(1, int(rules.get("unresolved_suggestion_limit", 3)))
        self.candidate_search_width = max(1, int(rules.get("candidate_search_width", 1)))
        self.fuzzy_builtin_cutoff = rules.get("fuzzy_builtin_cutoff")
        self.fuzzy_member_cutoff = rules.get("fuzzy_member_cutoff")
        self.auto_fix_unresolved_names = bool(rules.get("auto_fix_unresolved_names", False))
        self.promote_null_guard_defaults = bool(rules.get("promote_null_guard_defaults", False))
        self.infer_missing_optional_params = bool(rules.get("infer_missing_optional_params", False))

    def transform_file(self, input_path: str | Path, output_path: str | Path) -> RupantarResult:
        input_path = Path(input_path)
        output_path = Path(output_path)
        source = input_path.read_text(encoding="utf-8")
        result = self.transform_source(source, source_path=str(input_path))
        output_path.write_text(result.source, encoding="utf-8")
        return result

    def _build_builtin_signatures(self) -> dict[str, _CallSignature]:
        return {
            name: _CallSignature(
                name=spec.name,
                required_args=spec.required_args,
                max_args=spec.max_args,
                keyword_names=spec.keyword_names,
                accepts_varargs=spec.accepts_varargs,
                accepts_kwargs=spec.accepts_kwargs,
                source=spec.source,
            )
            for name, spec in self.builtin_catalog.items()
        }

    def _validate_source(
        self,
        source: str,
        *,
        source_path: str | None,
        stage: str = "validation",
        validation_events: list[ValidationEvent] | None = None,
    ) -> _ValidationReport:
        warnings: list[str] = []
        suggestions: list[RupantarSuggestion] = []
        unresolved: tuple[_UnresolvedNameIssue, ...] = ()
        syntax_valid = False
        compiled = False
        program = None
        caught_error: Exception | None = None
        error_kind: str | None = None
        error_line = 0
        error_message: str | None = None

        try:
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            program = parser.parse()
            syntax_valid = True

            analyzer = _UndefinedNameAnalyzer(
                self.builtin_names,
                suggestion_cutoff=self.unresolved_name_cutoff,
                suggestion_limit=self.unresolved_suggestion_limit,
            )
            warnings.extend(analyzer.analyze(program))
            unresolved = tuple(analyzer.unresolved)
            suggestions.extend(self._build_unresolved_suggestions(unresolved))
            suggestions.extend(self._collect_call_suggestions(program))

            compiler = Compiler(
                branch_runtime=self.branch_runtime,
                source_path=source_path,
            )
            compiler.compile(program)
            compiled = True
        except Exception as exc:
            caught_error = exc
            error_kind = type(exc).__name__
            error_line = int(getattr(exc, "line", 0) or 0)
            error_message = format_vak_error(exc)
            warnings.append(error_message)

        event = ValidationEvent(
            stage=stage,
            syntax_valid=syntax_valid,
            compiled=compiled,
            warnings_count=len(dict.fromkeys(warnings)),
            unresolved_count=len(unresolved),
            error_kind=error_kind,
            error_line=error_line,
            error_message=error_message,
        )
        if validation_events is not None:
            validation_events.append(event)

        return _ValidationReport(
            syntax_valid=syntax_valid,
            compiled=compiled,
            warnings=tuple(dict.fromkeys(warnings)),
            unresolved=unresolved,
            suggestions=tuple(self._dedupe_suggestions(suggestions)),
            program=program,
            error=caught_error,
            error_kind=error_kind,
            error_line=error_line,
            error_message=error_message,
            event=event,
        )

    @staticmethod
    def _dedupe_suggestions(
        suggestions: list[RupantarSuggestion],
    ) -> tuple[RupantarSuggestion, ...]:
        deduped: list[RupantarSuggestion] = []
        seen: set[tuple[Any, ...]] = set()
        for item in suggestions:
            key = (
                item.line,
                item.layer,
                item.message,
                item.confidence,
                item.before,
                item.after,
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return tuple(deduped)

    def _build_unresolved_suggestions(
        self,
        unresolved: tuple[_UnresolvedNameIssue, ...],
    ) -> list[RupantarSuggestion]:
        suggestions: list[RupantarSuggestion] = []
        for issue in unresolved:
            if issue.candidates:
                suggestions.append(
                    RupantarSuggestion(
                        line=issue.line,
                        layer="logic",
                        message=(
                            f"अपरिभाषित नाम '{issue.name}' के लिए संभावित विकल्प: "
                            f"{', '.join(issue.candidates)}"
                        ),
                        confidence="suggest_only",
                        before=issue.name,
                        after=issue.candidates[0],
                    )
                )
            else:
                suggestions.append(
                    RupantarSuggestion(
                        line=issue.line,
                        layer="logic",
                        message=(
                            f"अपरिभाषित नाम '{issue.name}' के लिए सुरक्षित स्वतः-संशोधन नहीं मिला"
                        ),
                        confidence="do_not_touch",
                        before=issue.name,
                    )
                )
        return suggestions

    def _build_function_signatures(self, program: Any) -> dict[str, _CallSignature]:
        signatures: dict[str, _CallSignature] = {}
        for func in self._iter_function_decls(program):
            param_names = [
                name for name in (self._extract_param_name(param) for param in getattr(func, "params", []))
                if name is not None
            ]
            if not param_names:
                required = 0
            else:
                defaults = list(getattr(func, "defaults", []) or [])
                if len(defaults) < len(param_names):
                    defaults.extend([None] * (len(param_names) - len(defaults)))
                required = sum(1 for default in defaults[: len(param_names)] if default is None)
            signatures[getattr(func, "name", "")] = _CallSignature(
                name=getattr(func, "name", ""),
                required_args=required,
                max_args=None if getattr(func, "varargs", None) else len(param_names),
                keyword_names=tuple(param_names),
                accepts_varargs=bool(getattr(func, "varargs", None)),
                accepts_kwargs=False,
                source="function",
            )
        return signatures

    def _collect_call_suggestions(self, program: Any) -> list[RupantarSuggestion]:
        signatures = dict(self.builtin_signatures)
        signatures.update(self._build_function_signatures(program))
        suggestions: list[RupantarSuggestion] = []

        def visit(node: Any) -> None:
            if node is None:
                return
            if isinstance(node, list):
                for item in node:
                    visit(item)
                return
            if not hasattr(node, "__dict__"):
                return
            if type(node).__name__ == "CallExpr":
                call_suggestion = self._analyze_call_expr(node, signatures)
                if call_suggestion is not None:
                    suggestions.append(call_suggestion)
            for value in vars(node).values():
                visit(value)

        visit(program)
        return suggestions

    def _analyze_call_expr(
        self,
        expr: Any,
        signatures: dict[str, _CallSignature],
    ) -> RupantarSuggestion | None:
        callee = getattr(expr, "callee", None)
        if type(callee).__name__ != "IdentifierExpr":
            return None
        name = getattr(callee, "name", "")
        signature = signatures.get(name)
        if signature is None:
            return None

        positional_count = len(getattr(expr, "args", []) or [])
        keyword_args = dict(getattr(expr, "kwargs", {}) or {})
        total_supplied = positional_count + len(keyword_args)
        line = getattr(expr, "line", 0)

        if total_supplied < signature.required_args:
            missing = signature.required_args - total_supplied
            return RupantarSuggestion(
                line=line,
                layer="logic",
                message=(
                    f"'{name}' को कम से कम {signature.required_args} तर्क चाहिए; "
                    f"यहाँ {total_supplied} मिले हैं"
                ),
                confidence="suggest_only",
                before=name,
            )

        if signature.max_args is not None and positional_count > signature.max_args:
            return RupantarSuggestion(
                line=line,
                layer="logic",
                message=(
                    f"'{name}' के लिए अधिकतम {signature.max_args} positional तर्क मान्य हैं; "
                    f"यहाँ {positional_count} मिले हैं"
                ),
                confidence="suggest_only",
                before=name,
            )

        if keyword_args and not signature.accepts_kwargs:
            unknown = [
                key for key in keyword_args
                if key not in signature.keyword_names
            ]
            if unknown:
                return RupantarSuggestion(
                    line=line,
                    layer="logic",
                    message=(
                        f"'{name}' के लिए अमान्य keyword तर्क: {', '.join(sorted(unknown))}"
                    ),
                    confidence="suggest_only",
                    before=name,
                )

        return None

    def _apply_adaptive_repairs(
        self,
        source: str,
        validation: _ValidationReport,
        *,
        source_path: str | None,
        validation_events: list[ValidationEvent],
        rejected_fixes: list[RupantarSuggestion],
    ) -> tuple[str, list[RupantarEdit], _ValidationReport]:
        current_source = source
        current_validation = validation
        edits: list[RupantarEdit] = []

        for _ in range(self.max_fixpoint_passes):
            if self.promote_null_guard_defaults or self.infer_missing_optional_params:
                candidate_source, candidate_edits = self._repair_optional_parameter_signatures(
                    current_source,
                    current_validation,
                )
                accepted = self._accept_adaptive_candidate(
                    current_source,
                    current_validation,
                    candidate_source,
                    candidate_edits,
                    source_path=source_path,
                    stage="adaptive:signature",
                    validation_events=validation_events,
                    rejected_fixes=rejected_fixes,
                )
                if accepted is not None:
                    current_source, accepted_edits, current_validation = accepted
                    edits.extend(accepted_edits)
                    continue

            candidate_map = self._build_unresolved_replacement_map(current_validation.unresolved)
            candidate_maps = self._build_unresolved_replacement_maps(current_validation.unresolved)
            if not candidate_maps:
                break
            accepted = None
            for candidate_map in candidate_maps:
                candidate_source, candidate_edits = self._rewrite_identifiers_with_map(
                    current_source,
                    candidate_map,
                )
                accepted = self._accept_adaptive_candidate(
                    current_source,
                    current_validation,
                    candidate_source,
                    candidate_edits,
                    source_path=source_path,
                    stage="adaptive:unresolved-name",
                    validation_events=validation_events,
                    rejected_fixes=rejected_fixes,
                )
                if accepted is not None:
                    break
            if accepted is None:
                break
            current_source, accepted_edits, current_validation = accepted
            edits.extend(accepted_edits)

        return current_source, edits, current_validation

    def _apply_ast_normalizations(
        self,
        source: str,
        validation: _ValidationReport,
        *,
        source_path: str | None,
        validation_events: list[ValidationEvent],
        rejected_fixes: list[RupantarSuggestion],
    ) -> tuple[str, list[RupantarEdit], _ValidationReport]:
        if validation.program is None:
            return source, [], validation

        candidate_source, candidate_edits = self._rewrite_ast_member_repairs(
            source,
            validation.program,
            source_path=source_path,
            unresolved=validation.unresolved,
        )
        if not candidate_edits:
            return source, [], validation

        accepted = self._accept_ast_candidate(
            current_source=source,
            current_validation=validation,
            candidate_source=candidate_source,
            candidate_edits=candidate_edits,
            source_path=source_path,
            stage="ast-normalization:typed-members",
            validation_events=validation_events,
            rejected_fixes=rejected_fixes,
        )
        if accepted is None:
            return source, [], validation
        return accepted

    def _apply_unambiguous_unresolved_repairs(
        self,
        source: str,
        validation: _ValidationReport,
        *,
        source_path: str | None,
        validation_events: list[ValidationEvent],
        rejected_fixes: list[RupantarSuggestion],
    ) -> tuple[str, list[RupantarEdit], _ValidationReport]:
        protected_names = self._collect_missing_optional_parameter_names(
            validation.program,
            validation.unresolved,
        )
        replacements = self._build_unambiguous_unresolved_replacement_map(
            validation.unresolved,
            exclude_names=protected_names,
        )
        if not replacements:
            return source, [], validation
        candidate_source, candidate_edits = self._rewrite_identifiers_with_map(
            source,
            replacements,
        )
        accepted = self._accept_adaptive_candidate(
            source,
            validation,
            candidate_source,
            candidate_edits,
            source_path=source_path,
            stage="logic:unambiguous-name",
            validation_events=validation_events,
            rejected_fixes=rejected_fixes,
        )
        if accepted is None:
            return source, [], validation
        return accepted

    def _apply_import_binding_repairs(
        self,
        source: str,
        validation: _ValidationReport,
        *,
        normalization_edits: list[RupantarEdit],
        source_path: str | None,
        validation_events: list[ValidationEvent],
        rejected_fixes: list[RupantarSuggestion],
    ) -> tuple[str, list[RupantarEdit], _ValidationReport]:
        replacements = self._build_import_binding_replacement_map(
            normalization_edits,
            validation.unresolved,
        )
        if not replacements:
            return source, [], validation

        candidate_source, candidate_edits = self._rewrite_identifiers_with_map(
            source,
            replacements,
        )
        accepted = self._accept_adaptive_candidate(
            source,
            validation,
            candidate_source,
            candidate_edits,
            source_path=source_path,
            stage="import-binding:usage",
            validation_events=validation_events,
            rejected_fixes=rejected_fixes,
        )
        if accepted is None:
            return source, [], validation
        return accepted

    def _apply_error_driven_repairs(
        self,
        source: str,
        validation: _ValidationReport,
        *,
        source_path: str | None,
        validation_events: list[ValidationEvent],
        rejected_fixes: list[RupantarSuggestion],
    ) -> tuple[str, list[RupantarEdit], _ValidationReport]:
        current_source = source
        current_validation = validation
        edits: list[RupantarEdit] = []

        for attempt in range(1, self.max_fixpoint_passes + 1):
            candidate_source, candidate_edits = self._repair_from_validation_error(
                current_source,
                current_validation,
            )
            accepted = self._accept_adaptive_candidate(
                current_source,
                current_validation,
                candidate_source,
                candidate_edits,
                source_path=source_path,
                stage=f"error-driven:{attempt}",
                validation_events=validation_events,
                rejected_fixes=rejected_fixes,
            )
            if accepted is None:
                break
            current_source, accepted_edits, current_validation = accepted
            edits.extend(accepted_edits)
            if current_validation.compiled:
                break

        return current_source, edits, current_validation

    def _accept_ast_candidate(
        self,
        *,
        current_source: str,
        current_validation: _ValidationReport,
        candidate_source: str,
        candidate_edits: list[RupantarEdit],
        source_path: str | None,
        stage: str,
        validation_events: list[ValidationEvent],
        rejected_fixes: list[RupantarSuggestion],
    ) -> tuple[str, list[RupantarEdit], _ValidationReport] | None:
        if candidate_source == current_source:
            return None
        candidate_source, normalization_edits = self._normalize_textual_layers(
            candidate_source,
            source_path=source_path,
        )
        candidate_validation = self._validate_source(
            candidate_source,
            source_path=source_path,
            stage=stage,
            validation_events=validation_events,
        )
        if not candidate_validation.syntax_valid or not candidate_validation.compiled:
            self._record_rejected_candidate(
                rejected_fixes,
                candidate_edits + normalization_edits,
                stage=stage,
                reason="candidate rejected because validation failed",
            )
            return None
        if current_validation.compiled and current_validation.syntax_valid:
            return candidate_source, candidate_edits + normalization_edits, candidate_validation
        if self._validation_improved(current_validation, candidate_validation):
            return candidate_source, candidate_edits + normalization_edits, candidate_validation
        self._record_rejected_candidate(
            rejected_fixes,
            candidate_edits + normalization_edits,
            stage=stage,
            reason="candidate rejected because validation did not improve",
        )
        return None

    def _repair_from_validation_error(
        self,
        source: str,
        validation: _ValidationReport,
    ) -> tuple[str, list[RupantarEdit]]:
        if validation.program is None or validation.error_message is None:
            return source, []
        repaired_source, edits = self._repair_unknown_keyword_args_from_error(
            source,
            validation,
        )
        if edits:
            return repaired_source, edits
        repaired_source, edits = self._repair_missing_call_args_from_error(
            source,
            validation,
        )
        if edits:
            return repaired_source, edits
        repaired_source, edits = self._repair_unambiguous_unresolved_names(
            source,
            validation,
        )
        if edits:
            return repaired_source, edits
        return source, []

    def _repair_unambiguous_unresolved_names(
        self,
        source: str,
        validation: _ValidationReport,
    ) -> tuple[str, list[RupantarEdit]]:
        protected_names = self._collect_missing_optional_parameter_names(
            validation.program,
            validation.unresolved,
        )
        replacements = self._build_unambiguous_unresolved_replacement_map(
            validation.unresolved,
            exclude_names=protected_names,
        )
        if not replacements:
            return source, []
        return self._rewrite_identifiers_with_map(
            source,
            replacements,
        )

    def _repair_unknown_keyword_args_from_error(
        self,
        source: str,
        validation: _ValidationReport,
    ) -> tuple[str, list[RupantarEdit]]:
        match = _UNKNOWN_KWARGS_RE.search(validation.error_message or "")
        if match is None:
            return source, []

        line_no = int(match.group("line"))
        unknown_names = tuple(
            name.strip() for name in match.group("names").split(",") if name.strip()
        )
        if not unknown_names:
            return source, []

        program = validation.program
        if program is None:
            return source, []

        signatures = dict(self.builtin_signatures)
        signatures.update(self._build_function_signatures(program))
        call_exprs = self._find_call_exprs_on_line(program, line_no)
        if not call_exprs:
            return source, []

        for expr in call_exprs:
            callee = getattr(expr, "callee", None)
            if type(callee).__name__ != "IdentifierExpr":
                continue
            name = getattr(callee, "name", "")
            signature = signatures.get(name)
            if signature is None or not signature.keyword_names:
                continue

            replacements: dict[str, str] = {}
            for unknown in unknown_names:
                replacement = self._suggest_keyword_name(
                    unknown,
                    signature.keyword_names,
                )
                if replacement is None or replacement == unknown:
                    replacements = {}
                    break
                replacements[unknown] = replacement

            if not replacements:
                continue

            reason = (
                f"error-driven repair normalized keyword arguments for '{name}' "
                "after compile-time argument validation failure"
            )
            return self._rewrite_keyword_arguments_on_line(
                source,
                line_no,
                replacements,
                reason=reason,
            )

        return source, []

    def _rewrite_ast_member_repairs(
        self,
        source: str,
        program: Any,
        *,
        source_path: str | None,
        unresolved: tuple[_UnresolvedNameIssue, ...] = (),
    ) -> tuple[str, list[RupantarEdit]]:
        typed_repairs = self._collect_typed_member_repairs(program)
        module_repairs = self._collect_module_member_repairs(
            program,
            source_path=source_path,
        )
        call_repairs = self._collect_unresolved_call_repairs(program, unresolved)
        if not typed_repairs and not module_repairs and not call_repairs:
            return source, []

        source_lines = source.splitlines(keepends=True)
        edits: list[RupantarEdit] = []
        typed_grouped: dict[int, list[_TypedMemberRepair]] = {}
        for repair in typed_repairs:
            typed_grouped.setdefault(repair.line, []).append(repair)
        module_grouped: dict[int, list[_ModuleMemberRepair]] = {}
        for repair in module_repairs:
            module_grouped.setdefault(repair.line, []).append(repair)
        call_grouped: dict[int, dict[str, str]] = {}
        for line_no, before_name, after_name in call_repairs:
            call_grouped.setdefault(line_no, {})[before_name] = after_name

        all_lines = sorted(set(typed_grouped) | set(module_grouped) | set(call_grouped))
        for line_no in all_lines:
            line_index = line_no - 1
            if line_index < 0 or line_index >= len(source_lines):
                continue
            raw_line = source_lines[line_index]
            newline = "\n" if raw_line.endswith("\n") else ""
            line = raw_line[:-1] if newline else raw_line
            code, comment = self._split_comment(line)
            rewritten_code = code

            for repair in typed_grouped.get(line_no, []):
                pattern = re.compile(
                    rf"(?<!{_IDENT_BODY_RE})({re.escape(repair.receiver)}\s*\.\s*)"
                    rf"{re.escape(repair.before_attr)}(?!{_IDENT_BODY_RE})"
                )
                updated, count = pattern.subn(
                    rf"\1{repair.after_attr}",
                    rewritten_code,
                    count=1,
                )
                if count == 0:
                    continue
                rewritten_code = updated
                edits.append(
                    RupantarEdit(
                        line=line_no,
                        layer="member",
                        before=f"{repair.receiver}.{repair.before_attr}",
                        after=f"{repair.receiver}.{repair.after_attr}",
                        reason=(
                            f"AST-aware {repair.receiver_kind} method normalized to live Vak member"
                        ),
                        )
                    )

            for repair in module_grouped.get(line_no, []):
                pattern = re.compile(
                    rf"(?<!{_IDENT_BODY_RE})({re.escape(repair.module_alias)}\s*\.\s*)"
                    rf"{re.escape(repair.before_attr)}(?!{_IDENT_BODY_RE})"
                )
                updated, count = pattern.subn(
                    rf"\1{repair.after_attr}",
                    rewritten_code,
                    count=1,
                )
                if count == 0:
                    continue
                rewritten_code = updated
                edits.append(
                    RupantarEdit(
                        line=line_no,
                        layer="import",
                        before=f"{repair.module_alias}.{repair.before_attr}",
                        after=f"{repair.module_alias}.{repair.after_attr}",
                        reason=(
                            f"module member corrected against exports in '{repair.module_name}'"
                        ),
                    )
                )

            if call_grouped.get(line_no):
                reason = "AST-aware callable name normalized against a visible builtin/function candidate"
                before_code = rewritten_code
                updated, _ = self._replace_identifier_tokens(
                    rewritten_code,
                    call_grouped[line_no],
                    line_no=line_no,
                    layer="logic",
                    reason=reason,
                )
                rewritten_code = updated
                if rewritten_code != before_code:
                    for before_name, after_name in call_grouped[line_no].items():
                        if before_name == after_name:
                            continue
                        edits.append(
                            RupantarEdit(
                                line=line_no,
                                layer="logic",
                                before=f"{before_name}(",
                                after=f"{after_name}(",
                                reason=reason,
                            )
                        )

            source_lines[line_index] = f"{rewritten_code}{comment}{newline}"

        return "".join(source_lines), edits

    def _collect_unresolved_call_repairs(
        self,
        program: Any,
        unresolved: tuple[_UnresolvedNameIssue, ...],
    ) -> list[tuple[int, str, str]]:
        replacements = self._build_unambiguous_unresolved_replacement_map(unresolved)
        if not replacements:
            return []

        repairs: list[tuple[int, str, str]] = []
        seen: set[tuple[int, str, str]] = set()

        def visit(node: Any) -> None:
            if node is None:
                return
            if isinstance(node, list):
                for item in node:
                    visit(item)
                return
            if isinstance(node, tuple):
                for item in node:
                    visit(item)
                return
            if not hasattr(node, "__dict__"):
                return

            if type(node).__name__ == "CallExpr":
                callee = getattr(node, "callee", None)
                if type(callee).__name__ == "IdentifierExpr":
                    before_name = getattr(callee, "name", "")
                    after_name = replacements.get(before_name)
                    line_no = getattr(callee, "line", 0) or getattr(node, "line", 0)
                    if after_name and after_name != before_name and line_no:
                        key = (line_no, before_name, after_name)
                        if key not in seen:
                            seen.add(key)
                            repairs.append(key)
            for value in vars(node).values():
                visit(value)

        visit(program)
        return repairs

    def _collect_typed_member_repairs(self, program: Any) -> list[_TypedMemberRepair]:
        repairs: list[_TypedMemberRepair] = []

        def visit_block(statements: list[Any], scope: dict[str, str]) -> None:
            local_scope = dict(scope)
            for stmt in statements:
                kind = type(stmt).__name__
                if kind == "VarDecl":
                    value_kind = self._infer_simple_value_kind(getattr(stmt, "value", None))
                    names = list(getattr(stmt, "names", []) or [])
                    if value_kind is not None and len(names) == 1:
                        local_scope[names[0]] = value_kind
                    visit_expr(getattr(stmt, "value", None), local_scope)
                    continue
                if kind == "ConstDecl":
                    value_kind = self._infer_simple_value_kind(getattr(stmt, "value", None))
                    name = getattr(stmt, "name", None)
                    if value_kind is not None and name:
                        local_scope[name] = value_kind
                    visit_expr(getattr(stmt, "value", None), local_scope)
                    continue
                if kind == "ExprStmt":
                    expr = getattr(stmt, "expr", None)
                    visit_expr(expr, local_scope)
                    if type(expr).__name__ == "AssignExpr" and getattr(expr, "op", None) == "=":
                        target = getattr(expr, "target", None)
                        if type(target).__name__ == "IdentifierExpr":
                            value_kind = self._infer_simple_value_kind(getattr(expr, "value", None))
                            if value_kind is not None:
                                local_scope[getattr(target, "name", "")] = value_kind
                    continue
                if kind == "FuncDecl":
                    child_scope = dict(local_scope)
                    for param in getattr(stmt, "params", []) or []:
                        name = self._extract_param_name(param)
                        if name:
                            child_scope.pop(name, None)
                    body = getattr(getattr(stmt, "body", None), "stmts", []) or []
                    visit_block(body, child_scope)
                    continue
                if kind == "ClassDecl":
                    body = getattr(getattr(stmt, "body", None), "stmts", []) or []
                    visit_block(body, {})
                    continue
                if kind == "IfStmt":
                    visit_expr(getattr(stmt, "condition", None), local_scope)
                    visit_block(getattr(getattr(stmt, "then_body", None), "stmts", []) or [], dict(local_scope))
                    for cond, body in getattr(stmt, "elif_clauses", []) or []:
                        visit_expr(cond, local_scope)
                        visit_block(getattr(body, "stmts", []) or [], dict(local_scope))
                    else_body = getattr(stmt, "else_body", None)
                    if else_body is not None:
                        visit_block(getattr(else_body, "stmts", []) or [], dict(local_scope))
                    continue
                if kind == "WhileStmt":
                    visit_expr(getattr(stmt, "condition", None), local_scope)
                    visit_block(getattr(getattr(stmt, "body", None), "stmts", []) or [], dict(local_scope))
                    continue
                if kind == "ForStmt":
                    visit_expr(getattr(stmt, "iterable", None), local_scope)
                    child_scope = dict(local_scope)
                    for var_name in getattr(stmt, "var_names", []) or []:
                        child_scope.pop(var_name, None)
                    visit_block(getattr(getattr(stmt, "body", None), "stmts", []) or [], child_scope)
                    continue
                if kind == "WithStmt":
                    visit_expr(getattr(stmt, "expr", None), local_scope)
                    child_scope = dict(local_scope)
                    var_name = getattr(stmt, "var_name", None)
                    if var_name:
                        child_scope.pop(var_name, None)
                    visit_block(getattr(getattr(stmt, "body", None), "stmts", []) or [], child_scope)
                    continue
                if kind == "TryStmt":
                    visit_block(getattr(getattr(stmt, "try_body", None), "stmts", []) or [], dict(local_scope))
                    for handler in getattr(stmt, "handlers", []) or []:
                        child_scope = dict(local_scope)
                        bind_name = getattr(handler, "bind_name", None)
                        if bind_name:
                            child_scope.pop(bind_name, None)
                        visit_block(getattr(getattr(handler, "body", None), "stmts", []) or [], child_scope)
                    finally_body = getattr(stmt, "finally_body", None)
                    if finally_body is not None:
                        visit_block(getattr(finally_body, "stmts", []) or [], dict(local_scope))
                    continue
                if kind == "MatchStmt":
                    visit_expr(getattr(stmt, "subject", None), local_scope)
                    for case in getattr(stmt, "cases", []) or []:
                        visit_expr(getattr(case, "guard", None), local_scope)
                        visit_block(getattr(getattr(case, "body", None), "stmts", []) or [], dict(local_scope))
                    continue

                if hasattr(stmt, "__dict__"):
                    for value in vars(stmt).values():
                        visit_expr(value, local_scope)

        def visit_expr(node: Any, scope: dict[str, str]) -> None:
            if node is None:
                return
            if isinstance(node, list):
                for item in node:
                    visit_expr(item, scope)
                return
            if not hasattr(node, "__dict__"):
                return

            if type(node).__name__ == "CallExpr":
                callee = getattr(node, "callee", None)
                if type(callee).__name__ == "MemberExpr":
                    obj = getattr(callee, "obj", None)
                    attr = getattr(callee, "attr", "")
                    if type(obj).__name__ == "IdentifierExpr":
                        receiver = getattr(obj, "name", "")
                        receiver_kind = scope.get(receiver)
                        replacement = self._typed_member_target(attr, receiver_kind)
                        if replacement is not None and replacement != attr:
                            repairs.append(
                                _TypedMemberRepair(
                                    line=getattr(node, "line", 0),
                                    receiver=receiver,
                                    before_attr=attr,
                                    after_attr=replacement,
                                    receiver_kind=receiver_kind,
                                )
                            )

            for value in vars(node).values():
                visit_expr(value, scope)

        visit_block(getattr(program, "body", []) or [], {})
        deduped: list[_TypedMemberRepair] = []
        seen: set[tuple[Any, ...]] = set()
        for item in repairs:
            key = (item.line, item.receiver, item.before_attr, item.after_attr)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped

    def _collect_module_member_repairs(
        self,
        program: Any,
        *,
        source_path: str | None,
    ) -> list[_ModuleMemberRepair]:
        imported_modules = self._collect_imported_modules(program)
        if not imported_modules:
            return []

        repairs: list[_ModuleMemberRepair] = []

        def visit(node: Any) -> None:
            if node is None:
                return
            if isinstance(node, list):
                for item in node:
                    visit(item)
                return
            if not hasattr(node, "__dict__"):
                return
            if type(node).__name__ == "MemberExpr":
                obj = getattr(node, "obj", None)
                if type(obj).__name__ == "IdentifierExpr":
                    alias = getattr(obj, "name", "")
                    module_name = imported_modules.get(alias)
                    if module_name is not None:
                        attr = getattr(node, "attr", "")
                        replacement = self._resolve_module_export_attr(
                            module_name,
                            attr,
                            source_path=source_path,
                        )
                        if replacement is not None and replacement != attr:
                            repairs.append(
                                _ModuleMemberRepair(
                                    line=getattr(node, "line", 0),
                                    module_alias=alias,
                                    module_name=module_name,
                                    before_attr=attr,
                                    after_attr=replacement,
                                )
                            )
            for value in vars(node).values():
                visit(value)

        visit(program)
        deduped: list[_ModuleMemberRepair] = []
        seen: set[tuple[Any, ...]] = set()
        for item in repairs:
            key = (item.line, item.module_alias, item.before_attr, item.after_attr)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped

    def _collect_imported_modules(self, program: Any) -> dict[str, str]:
        modules: dict[str, str] = {}
        for stmt in getattr(program, "body", []) or []:
            if type(stmt).__name__ != "ImportStmt":
                continue
            names = getattr(stmt, "names", None)
            module_name = getattr(stmt, "module", "")
            if names:
                continue
            if module_name:
                modules[module_name.split(".", 1)[0]] = module_name
        return modules

    def _resolve_module_export_attr(
        self,
        module_name: str,
        attr: str,
        *,
        source_path: str | None,
    ) -> str | None:
        exports = self._module_exports(module_name, source_path=source_path)
        if not exports or attr in exports:
            return None
        matches = get_close_matches(
            attr,
            list(exports),
            n=2,
            cutoff=self.module_export_match_cutoff,
        )
        if len(matches) != 1:
            return None
        return matches[0]

    def _typed_member_target(self, attr: str, receiver_kind: str | None) -> str | None:
        if receiver_kind is None:
            return None
        candidates = _TYPED_MEMBER_METHODS.get(receiver_kind)
        if not candidates:
            return None
        if attr in candidates:
            normalized = self.member_alias_map.get(attr, attr)
            return normalized if normalized != attr else None
        matches = get_close_matches(attr, sorted(candidates), n=2, cutoff=0.78)
        if len(matches) != 1:
            return None
        candidate = matches[0]
        normalized = self.member_alias_map.get(candidate, candidate)
        if normalized == attr:
            return None
        return normalized

    @staticmethod
    def _infer_simple_value_kind(expr: Any) -> str | None:
        kind = type(expr).__name__
        if kind == "ListLiteral":
            return "list"
        if kind == "DictLiteral":
            return "dict"
        if kind == "StringLiteral":
            return "str"
        if kind == "SetLiteral":
            return "set"
        if kind == "CallExpr":
            callee = getattr(expr, "callee", None)
            if type(callee).__name__ == "IdentifierExpr":
                name = getattr(callee, "name", "")
                if name in {"सूची", "list"}:
                    return "list"
                if name in {"शब्दकोश", "dict"}:
                    return "dict"
                if name in {"पाठ_कर", "str"}:
                    return "str"
                if name in {"समुच्चय", "set"}:
                    return "set"
        return None

    def _repair_missing_call_args_from_error(
        self,
        source: str,
        validation: _ValidationReport,
    ) -> tuple[str, list[RupantarEdit]]:
        match = _INSUFFICIENT_ARGS_RE.search(validation.error_message or "")
        if match is None:
            return source, []

        line_no = int(match.group("line"))
        provided = int(match.group("provided"))
        program = validation.program
        if program is None:
            return source, []

        functions = {
            getattr(func, "name", ""): func
            for func in self._iter_function_decls(program)
            if getattr(func, "name", "")
        }
        call_exprs = self._find_call_exprs_on_line(program, line_no)
        if not call_exprs:
            return source, []

        for expr in call_exprs:
            callee = getattr(expr, "callee", None)
            if type(callee).__name__ != "IdentifierExpr":
                continue
            func = functions.get(getattr(callee, "name", ""))
            if func is None:
                continue
            candidate = self._repair_missing_function_args_for_call(
                source,
                func,
                expr,
                provided_total=provided,
            )
            if candidate[1]:
                return candidate
        return source, []

    def _repair_missing_function_args_for_call(
        self,
        source: str,
        func: Any,
        expr: Any,
        *,
        provided_total: int,
    ) -> tuple[str, list[RupantarEdit]]:
        param_names = [
            name
            for name in (
                self._extract_param_name(param)
                for param in getattr(func, "params", [])
            )
            if name is not None
        ]
        if not param_names:
            return source, []

        defaults = list(getattr(func, "defaults", []) or [])
        if len(defaults) < len(param_names):
            defaults.extend([None] * (len(param_names) - len(defaults)))
        required_indices = [
            index for index, default in enumerate(defaults[: len(param_names)])
            if default is None
        ]
        if len(required_indices) <= provided_total:
            return source, []

        optional_names = set(self._find_optional_parameter_candidates(func))
        if not optional_names:
            return source, []

        promote_indices: list[int] = []
        required_total = len(required_indices)
        for index in range(len(param_names) - 1, -1, -1):
            if required_total <= provided_total:
                break
            if defaults[index] is not None:
                continue
            if param_names[index] not in optional_names:
                break
            promote_indices.append(index)
            required_total -= 1

        if required_total > provided_total or not promote_indices:
            return source, []

        reason = (
            "error-driven repair promoted trailing null-guarded parameters "
            "to explicit defaults after insufficient-argument compile failure"
        )
        return self._rewrite_function_signature_defaults(
            source,
            func,
            param_indices=tuple(sorted(promote_indices)),
            reason=reason,
        )

    def _rewrite_function_signature_defaults(
        self,
        source: str,
        func: Any,
        *,
        param_indices: tuple[int, ...],
        reason: str,
    ) -> tuple[str, list[RupantarEdit]]:
        if not param_indices:
            return source, []

        source_lines = source.splitlines(keepends=True)
        line_index = getattr(func, "line", 0) - 1
        if line_index < 0 or line_index >= len(source_lines):
            return source, []

        raw_line = source_lines[line_index]
        newline = "\n" if raw_line.endswith("\n") else ""
        line = raw_line[:-1] if newline else raw_line
        code, comment = self._split_comment(line)
        match = _FUNC_HEADER_RE.match(code)
        if not match:
            return source, []

        param_segments = self._split_signature_params(match.group("params"))
        edits: list[RupantarEdit] = []
        changed = False
        for index in param_indices:
            if index >= len(param_segments):
                continue
            before_segment = param_segments[index]
            if "=" in before_segment:
                continue
            param_segments[index] = f"{before_segment.rstrip()} = शून्य"
            edits.append(
                RupantarEdit(
                    line=line_index + 1,
                    layer="logic",
                    before=before_segment.strip(),
                    after=param_segments[index].strip(),
                    reason=reason,
                )
            )
            changed = True

        if not changed:
            return source, []

        rewritten_code = (
            f"{match.group('indent')}{match.group('prefix')}"
            f"({', '.join(param_segments)}){match.group('suffix')}"
        )
        source_lines[line_index] = f"{rewritten_code}{comment}{newline}"
        return "".join(source_lines), edits

    def _rewrite_keyword_arguments_on_line(
        self,
        source: str,
        line_no: int,
        replacements: dict[str, str],
        *,
        reason: str,
    ) -> tuple[str, list[RupantarEdit]]:
        source_lines = source.splitlines(keepends=True)
        line_index = line_no - 1
        if line_index < 0 or line_index >= len(source_lines):
            return source, []

        raw_line = source_lines[line_index]
        newline = "\n" if raw_line.endswith("\n") else ""
        line = raw_line[:-1] if newline else raw_line
        code, comment = self._split_comment(line)
        rewritten_code, changed_pairs = self._replace_keyword_names_in_code(
            code,
            replacements,
        )
        if not changed_pairs:
            return source, []

        source_lines[line_index] = f"{rewritten_code}{comment}{newline}"
        edits = [
            RupantarEdit(
                line=line_no,
                layer="logic",
                before=before,
                after=after,
                reason=reason,
            )
            for before, after in changed_pairs
        ]
        return "".join(source_lines), edits

    def _accept_adaptive_candidate(
        self,
        current_source: str,
        current_validation: _ValidationReport,
        candidate_source: str,
        candidate_edits: list[RupantarEdit],
        *,
        source_path: str | None,
        stage: str,
        validation_events: list[ValidationEvent],
        rejected_fixes: list[RupantarSuggestion],
    ) -> tuple[str, list[RupantarEdit], _ValidationReport] | None:
        if candidate_source == current_source:
            return None
        candidate_source, normalization_edits = self._normalize_textual_layers(
            candidate_source,
            source_path=source_path,
        )
        candidate_validation = self._validate_source(
            candidate_source,
            source_path=source_path,
            stage=stage,
            validation_events=validation_events,
        )
        if not self._validation_improved(current_validation, candidate_validation):
            self._record_rejected_candidate(
                rejected_fixes,
                candidate_edits + normalization_edits,
                stage=stage,
                reason="candidate rejected because validation did not improve",
            )
            return None
        return candidate_source, candidate_edits + normalization_edits, candidate_validation

    @staticmethod
    def _record_rejected_candidate(
        rejected_fixes: list[RupantarSuggestion],
        edits: list[RupantarEdit],
        *,
        stage: str,
        reason: str,
    ) -> None:
        for edit in edits:
            rejected_fixes.append(
                RupantarSuggestion(
                    line=edit.line,
                    layer=edit.layer,
                    message=f"{reason} ({stage})",
                    confidence="do_not_touch",
                    before=edit.before,
                    after=edit.after,
                )
            )

    @staticmethod
    def _validation_improved(current: _ValidationReport, candidate: _ValidationReport) -> bool:
        current_score = (
            int(current.compiled),
            int(current.syntax_valid),
            -len(current.unresolved),
            -len(current.warnings),
        )
        candidate_score = (
            int(candidate.compiled),
            int(candidate.syntax_valid),
            -len(candidate.unresolved),
            -len(candidate.warnings),
        )
        return candidate_score > current_score

    @staticmethod
    def _build_import_binding_replacement_map(
        normalization_edits: list[RupantarEdit],
        unresolved: tuple[_UnresolvedNameIssue, ...],
    ) -> dict[str, str]:
        unresolved_names = {item.name for item in unresolved}
        replacements: dict[str, str] = {}
        for edit in normalization_edits:
            if edit.layer != "import":
                continue
            if not edit.reason.startswith("imported name corrected against declarations"):
                continue
            if edit.before in unresolved_names and edit.after != edit.before:
                replacements[edit.before] = edit.after
        return replacements

    @staticmethod
    def _build_unresolved_replacement_map(
        unresolved: tuple[_UnresolvedNameIssue, ...],
    ) -> dict[str, str]:
        candidates: dict[str, set[str]] = {}
        for issue in unresolved:
            if issue.suggestion is None or issue.suggestion == issue.name:
                continue
            candidates.setdefault(issue.name, set()).add(issue.suggestion)
        return {
            name: next(iter(suggestions))
            for name, suggestions in candidates.items()
            if len(suggestions) == 1
        }

    @staticmethod
    def _build_unambiguous_unresolved_replacement_map(
        unresolved: tuple[_UnresolvedNameIssue, ...],
        *,
        exclude_names: set[str] | None = None,
    ) -> dict[str, str]:
        replacements: dict[str, str] = {}
        blocked = exclude_names or set()
        for issue in unresolved:
            if issue.name in blocked:
                continue
            unique_candidates = tuple(dict.fromkeys(issue.candidates))
            if len(unique_candidates) != 1:
                continue
            candidate = unique_candidates[0]
            if candidate != issue.name:
                replacements[issue.name] = candidate
        return replacements

    def _build_unresolved_replacement_maps(
        self,
        unresolved: tuple[_UnresolvedNameIssue, ...],
    ) -> list[dict[str, str]]:
        ranked_maps: list[dict[str, str]] = []
        base_map = self._build_unresolved_replacement_map(unresolved)
        if base_map:
            ranked_maps.append(base_map)

        seen: set[tuple[tuple[str, str], ...]] = set()
        for issue in unresolved:
            for candidate in issue.candidates[: self.candidate_search_width]:
                if candidate == issue.name:
                    continue
                mapping = {issue.name: candidate}
                key = tuple(sorted(mapping.items()))
                if key in seen:
                    continue
                seen.add(key)
                ranked_maps.append(mapping)

        combined: dict[str, str] = {}
        for issue in unresolved:
            if issue.candidates:
                combined.setdefault(issue.name, issue.candidates[0])
        combined_key = tuple(sorted(combined.items()))
        if combined and combined_key not in seen:
            ranked_maps.append(combined)
        return ranked_maps

    def _repair_optional_parameter_signatures(
        self,
        source: str,
        validation: _ValidationReport,
    ) -> tuple[str, list[RupantarEdit]]:
        program = validation.program
        if program is None:
            return source, []

        source_lines = source.splitlines(keepends=True)
        if not source_lines:
            return source, []

        unresolved = tuple(validation.unresolved)
        edits: list[RupantarEdit] = []

        for func in self._iter_function_decls(program):
            line_index = getattr(func, "line", 0) - 1
            if line_index < 0 or line_index >= len(source_lines):
                continue

            raw_line = source_lines[line_index]
            newline = "\n" if raw_line.endswith("\n") else ""
            line = raw_line[:-1] if newline else raw_line
            code, comment = self._split_comment(line)
            match = _FUNC_HEADER_RE.match(code)
            if not match:
                continue

            param_segments = self._split_signature_params(match.group("params"))
            param_names = [self._extract_param_name(param) for param in getattr(func, "params", [])]
            defaults = list(getattr(func, "defaults", []) or [])
            if len(defaults) < len(param_names):
                defaults.extend([None] * (len(param_names) - len(defaults)))

            optional_names = self._find_optional_parameter_candidates(func)
            if not optional_names:
                continue

            changed = False
            for name in optional_names:
                if name in param_names:
                    param_index = param_names.index(name)
                    if param_index >= len(param_segments):
                        continue
                    if param_index < len(defaults) and defaults[param_index] is not None:
                        continue
                    if "=" in param_segments[param_index]:
                        continue
                    before_segment = param_segments[param_index]
                    param_segments[param_index] = f"{before_segment.rstrip()} = शून्य"
                    edits.append(
                        RupantarEdit(
                            line=line_index + 1,
                            layer="logic",
                            before=before_segment.strip(),
                            after=param_segments[param_index].strip(),
                            reason="null-guarded parameter promoted to explicit Vak default",
                        )
                    )
                    changed = True
                    continue

                if not self.infer_missing_optional_params:
                    continue
                if not self._function_has_unresolved_name(func, name, unresolved):
                    continue
                if any(segment.lstrip().startswith("*") for segment in param_segments):
                    continue
                addition = f"{name} = शून्य"
                param_segments.append(addition)
                edits.append(
                    RupantarEdit(
                        line=line_index + 1,
                        layer="logic",
                        before="<missing trailing optional parameter>",
                        after=addition,
                        reason="missing null-guarded optional parameter inferred into function signature",
                    )
                )
                changed = True

            if not changed:
                continue

            rewritten_code = (
                f"{match.group('indent')}{match.group('prefix')}"
                f"({', '.join(param_segments)}){match.group('suffix')}"
            )
            source_lines[line_index] = f"{rewritten_code}{comment}{newline}"

        return "".join(source_lines), edits

    def _collect_missing_optional_parameter_names(
        self,
        program: Any,
        unresolved: tuple[_UnresolvedNameIssue, ...],
    ) -> set[str]:
        if program is None:
            return set()

        protected: set[str] = set()
        for func in self._iter_function_decls(program):
            param_names = {
                name
                for name in (
                    self._extract_param_name(param)
                    for param in getattr(func, "params", []) or []
                )
                if name is not None
            }
            for name in self._find_optional_parameter_candidates(func):
                if name in param_names:
                    continue
                if self._function_has_unresolved_name(func, name, unresolved):
                    protected.add(name)
        return protected

    def _find_optional_parameter_candidates(self, func: Any) -> tuple[str, ...]:
        body = getattr(func, "body", None)
        statements = list(getattr(body, "stmts", []) or [])
        candidates: list[str] = []
        for stmt in statements[:6]:
            name = self._extract_null_guard_name(stmt)
            if name is None:
                continue
            if not self._block_assigns_name(getattr(stmt, "then_body", None), name):
                continue
            candidates.append(name)
        return tuple(dict.fromkeys(candidates))

    @staticmethod
    def _extract_null_guard_name(stmt: Any) -> str | None:
        if type(stmt).__name__ != "IfStmt":
            return None
        if getattr(stmt, "elif_clauses", None):
            return None
        if getattr(stmt, "else_body", None) is not None:
            return None
        condition = getattr(stmt, "condition", None)
        if type(condition).__name__ != "BinaryExpr":
            return None
        if getattr(condition, "op", None) != "==":
            return None
        left = getattr(condition, "left", None)
        right = getattr(condition, "right", None)
        if type(left).__name__ == "IdentifierExpr" and type(right).__name__ == "NullLiteral":
            return getattr(left, "name", None)
        if type(right).__name__ == "IdentifierExpr" and type(left).__name__ == "NullLiteral":
            return getattr(right, "name", None)
        return None

    def _block_assigns_name(self, block: Any, name: str) -> bool:
        for stmt in getattr(block, "stmts", []) or []:
            if self._stmt_assigns_name(stmt, name):
                return True
        return False

    def _stmt_assigns_name(self, stmt: Any, name: str) -> bool:
        kind = type(stmt).__name__
        if kind == "VarDecl":
            return name in getattr(stmt, "names", [])
        if kind == "ConstDecl":
            return getattr(stmt, "name", None) == name
        if kind != "ExprStmt":
            return False
        expr = getattr(stmt, "expr", None)
        if type(expr).__name__ != "AssignExpr":
            return False
        target = getattr(expr, "target", None)
        return type(target).__name__ == "IdentifierExpr" and getattr(target, "name", None) == name

    def _function_has_unresolved_name(
        self,
        func: Any,
        name: str,
        unresolved: tuple[_UnresolvedNameIssue, ...],
    ) -> bool:
        start = getattr(func, "line", 0)
        end = self._max_line(func)
        for issue in unresolved:
            if issue.name == name and start <= issue.line <= end:
                return True
        return False

    def _iter_function_decls(self, node: Any) -> list[Any]:
        functions: list[Any] = []
        self._collect_function_decls(node, functions)
        return functions

    def _find_call_exprs_on_line(self, node: Any, line: int) -> list[Any]:
        calls: list[Any] = []

        def visit(value: Any) -> None:
            if value is None:
                return
            if isinstance(value, list):
                for item in value:
                    visit(item)
                return
            if not hasattr(value, "__dict__"):
                return
            if type(value).__name__ == "CallExpr" and getattr(value, "line", 0) == line:
                calls.append(value)
            for child in vars(value).values():
                visit(child)

        visit(node)
        return calls

    def _collect_function_decls(self, node: Any, sink: list[Any]) -> None:
        if node is None:
            return
        if isinstance(node, list):
            for item in node:
                self._collect_function_decls(item, sink)
            return
        if not hasattr(node, "__dict__"):
            return
        if type(node).__name__ == "FuncDecl":
            sink.append(node)
        for value in vars(node).values():
            if isinstance(value, list):
                for item in value:
                    self._collect_function_decls(item, sink)
            elif hasattr(value, "__dict__"):
                self._collect_function_decls(value, sink)

    def _max_line(self, node: Any) -> int:
        max_line = 0

        def visit(value: Any) -> None:
            nonlocal max_line
            if value is None:
                return
            if isinstance(value, list):
                for item in value:
                    visit(item)
                return
            if not hasattr(value, "__dict__"):
                return
            max_line = max(max_line, int(getattr(value, "line", 0) or 0))
            for child in vars(value).values():
                visit(child)

        visit(node)
        return max_line

    @staticmethod
    def _extract_param_name(param: Any) -> str | None:
        if hasattr(param, "name"):
            return getattr(param, "name", None)
        if isinstance(param, tuple) and param:
            return param[0]
        return None

    @staticmethod
    def _split_signature_params(param_text: str) -> list[str]:
        if not param_text.strip():
            return []

        parts: list[str] = []
        current: list[str] = []
        depth = 0
        in_single = False
        in_double = False
        escaped = False

        for ch in param_text:
            if escaped:
                current.append(ch)
                escaped = False
                continue
            if ch == "\\":
                current.append(ch)
                escaped = True
                continue
            if ch == "'" and not in_double:
                in_single = not in_single
                current.append(ch)
                continue
            if ch == '"' and not in_single:
                in_double = not in_double
                current.append(ch)
                continue
            if not in_single and not in_double:
                if ch in "([{":
                    depth += 1
                elif ch in ")]}":
                    depth = max(0, depth - 1)
                elif ch == "," and depth == 0:
                    parts.append("".join(current).strip())
                    current = []
                    continue
            current.append(ch)

        tail = "".join(current).strip()
        if tail:
            parts.append(tail)
        return parts

    @staticmethod
    def _suggest_keyword_name(name: str, keyword_names: tuple[str, ...]) -> str | None:
        matches = get_close_matches(name, sorted(keyword_names), n=1, cutoff=0.72)
        if matches:
            return matches[0]
        return None

    def _normalize_textual_layers(
        self,
        source: str,
        *,
        source_path: str | None,
    ) -> tuple[str, list[RupantarEdit]]:
        current_source = source
        all_edits: list[RupantarEdit] = []
        for _ in range(self.max_fixpoint_passes):
            next_source, pass_edits = self._normalize_textual_layers_once(
                current_source,
                source_path=source_path,
            )
            all_edits.extend(pass_edits)
            if next_source == current_source:
                break
            current_source = next_source
        return current_source, all_edits

    def _normalize_textual_layers_once(
        self,
        source: str,
        *,
        source_path: str | None,
    ) -> tuple[str, list[RupantarEdit]]:
        source, reserved_edits = self._rewrite_reserved_identifier_declarations(source)
        transformed_lines: list[str] = []
        edits: list[RupantarEdit] = list(reserved_edits)
        in_multiline: str | None = None

        for line_no, raw_line in enumerate(source.splitlines(keepends=True), start=1):
            newline = "\n" if raw_line.endswith("\n") else ""
            line = raw_line[:-1] if newline else raw_line

            if in_multiline is not None:
                close_at = line.find(in_multiline)
                transformed_lines.append(raw_line)
                if close_at != -1:
                    in_multiline = None
                continue

            code, comment = self._split_comment(line)
            original_code = code

            code = self._rewrite_branch_member_calls(code, line_no, edits)
            code = self._rewrite_branch_import_line(code, line_no, edits)
            code = self._rewrite_import_line(code, line_no, source_path, edits)
            code = self._rewrite_generator_surface_line(code, line_no, edits)
            code = self._rewrite_type_patterns(code, line_no, edits)
            code = self._rewrite_augmented_assignment(code, line_no, edits)
            code, new_multiline = self._scan_and_rewrite_code(code, line_no, edits)
            code = self._rewrite_postscan_block_surface(code, line_no, edits)

            if original_code != code:
                transformed_lines.append(f"{code}{comment}{newline}")
            else:
                transformed_lines.append(raw_line)

            in_multiline = new_multiline

        return "".join(transformed_lines), edits

    def _rewrite_reserved_identifier_declarations(
        self,
        source: str,
    ) -> tuple[str, list[RupantarEdit]]:
        lines = source.splitlines(keepends=True)
        if not lines:
            return source, []

        transformed_lines: list[str] = []
        edits: list[RupantarEdit] = []
        active_renames: list[tuple[int, dict[str, str]]] = []
        in_multiline: str | None = None

        for line_no, raw_line in enumerate(lines, start=1):
            newline = "\n" if raw_line.endswith("\n") else ""
            line = raw_line[:-1] if newline else raw_line

            if in_multiline is not None:
                close_at = line.find(in_multiline)
                transformed_lines.append(raw_line)
                if close_at != -1:
                    in_multiline = None
                continue

            code, comment = self._split_comment(line)
            stripped = code.strip()
            indent = len(code) - len(code.lstrip(" \t"))

            if stripped:
                while active_renames and indent < active_renames[-1][0]:
                    active_renames.pop()

            active_map: dict[str, str] = {}
            for _scope_indent, rename_map in active_renames:
                active_map.update(rename_map)

            match = _RESERVED_DECL_RE.match(code)
            pending_rename: tuple[str, str] | None = None
            if match:
                declared_name = match.group("name")
                if declared_name in KEYWORDS:
                    replacement = self._safe_identifier_name(declared_name)
                    if replacement != declared_name:
                        active_map = dict(active_map)
                        active_map[declared_name] = replacement
                        pending_rename = (declared_name, replacement)

            rewritten_code, new_multiline = self._replace_identifier_tokens(
                code,
                active_map,
                line_no=line_no,
                layer="pattern",
                reason="reserved keyword identifier normalized to safe Vak name",
            )
            if rewritten_code != code:
                edits.append(
                    RupantarEdit(
                        line=line_no,
                        layer="pattern",
                        before=code.strip(),
                        after=rewritten_code.strip(),
                        reason="reserved keyword identifier normalized to safe Vak name",
                    )
                )

            transformed_lines.append(f"{rewritten_code}{comment}{newline}")

            if pending_rename is not None:
                scope_indent = indent
                active_renames.append((scope_indent, {pending_rename[0]: pending_rename[1]}))

            in_multiline = new_multiline

        return "".join(transformed_lines), edits

    def _scan_and_rewrite_code(
        self,
        line: str,
        line_no: int,
        edits: list[RupantarEdit],
    ) -> tuple[str, str | None]:
        result: list[str] = []
        pos = 0
        length = len(line)
        in_multiline: str | None = None

        while pos < length:
            ch = line[pos]

            if ch in ('"', "'"):
                if pos + 2 < length and line[pos] == line[pos + 1] == line[pos + 2]:
                    quote = line[pos:pos + 3]
                    end_pos = line.find(quote, pos + 3)
                    if end_pos == -1:
                        result.append(line[pos:])
                        return "".join(result), quote
                    result.append(line[pos:end_pos + 3])
                    pos = end_pos + 3
                    continue

                end_pos = pos + 1
                while end_pos < length:
                    if line[end_pos] == "\\":
                        end_pos += 2
                        continue
                    if line[end_pos] == ch:
                        end_pos += 1
                        break
                    end_pos += 1
                result.append(line[pos:end_pos])
                pos = end_pos
                continue

            if is_identifier_start(ch):
                start = pos
                pos += 1
                while pos < length and is_identifier_part(line[pos]):
                    pos += 1
                token = line[start:pos]
                member_context = self._previous_significant_char(result) == "."
                rewritten = self._rewrite_identifier_token(
                    token,
                    member_context=member_context,
                )
                if rewritten != token:
                    layer = "member" if member_context else "syntax"
                    reason = "Vak member normalization" if member_context else "Vak keyword/builtin normalization"
                    edits.append(
                        RupantarEdit(
                            line=line_no,
                            layer=layer,
                            before=token,
                            after=rewritten,
                            reason=reason,
                        )
                    )
                result.append(rewritten)
                continue

            result.append(ch)
            pos += 1

        return "".join(result), in_multiline

    def _rewrite_identifier_token(self, token: str, *, member_context: bool) -> str:
        normalized = token.translate(_SUBSCRIPT_DIGIT_MAP)
        if member_context:
            exact = self.member_alias_map.get(normalized)
            if exact is not None:
                return exact
            lowered = normalized.lower()
            exact = self.member_alias_map.get(lowered)
            if exact is not None:
                return exact
            if self.fuzzy_member_cutoff is not None:
                candidate = self._fuzzy_alias_target(
                    normalized,
                    self.member_alias_map,
                    cutoff=self.fuzzy_member_cutoff,
                )
                if candidate is not None:
                    return candidate
            return normalized

        if normalized in self.canonical_token_map:
            return self.canonical_token_map[normalized]
        lowered = normalized.lower()
        if lowered in self.canonical_token_map:
            return self.canonical_token_map[lowered]
        if normalized in self.builtin_alias_map:
            return self.builtin_alias_map[normalized]
        if lowered in self.builtin_alias_map:
            return self.builtin_alias_map[lowered]
        replacement = self.translator.english_code_to_sanskrit(normalized)
        if replacement is not None:
            return replacement
        if self.fuzzy_builtin_cutoff is not None:
            candidate = self._fuzzy_builtin_target(normalized)
            if candidate is not None:
                return candidate
        return normalized

    def _rewrite_type_patterns(
        self,
        line: str,
        line_no: int,
        edits: list[RupantarEdit],
    ) -> str:
        for pattern in (_TYPE_PATTERN_RE, _TYPE_CALL_PATTERN_RE):
            match = pattern.match(line)
            if not match:
                continue
            type_name = match.group("type")
            canonical_type = _TYPE_LITERAL_ALIASES.get(type_name.lower()) or _TYPE_LITERAL_ALIASES.get(type_name)
            if canonical_type is None:
                return line
            head = match.group("head")
            if head == "if":
                head = "यदि"
            elif head == "elif":
                head = "अन्यत्"
            rewritten = (
                f"{match.group('indent')}{head} प्रकार({match.group('expr').strip()}) "
                f"{match.group('op')} \"{canonical_type}\":"
            )
            edits.append(
                RupantarEdit(
                    line=line_no,
                    layer="pattern",
                    before=line.strip(),
                    after=rewritten.strip(),
                    reason="deprecated type-check pattern normalized to live प्रकार(...) form",
                )
            )
            return rewritten
        return line

    def _rewrite_augmented_assignment(
        self,
        line: str,
        line_no: int,
        edits: list[RupantarEdit],
    ) -> str:
        match = _AUGMENTED_ASSIGN_RE.match(line)
        if match:
            target = match.group("target").strip()
            expr = match.group("expr").strip()
            op = match.group("op")
            operator = {
                "+=": "+",
                "-=": "-",
                "*=": "*",
                "/=": "/",
                "%=": "%",
                "**=": "**",
            }[op]
            rewritten = f"{match.group('indent')}{target} = {target} {operator} {expr}"
            edits.append(
                RupantarEdit(
                    line=line_no,
                    layer="syntax",
                    before=line.strip(),
                    after=rewritten.strip(),
                    reason="augmented assignment normalized to explicit Vak assignment",
                )
            )
            return rewritten

        for pattern in (_POSTFIX_INCREMENT_RE, _PREFIX_INCREMENT_RE):
            match = pattern.match(line)
            if not match:
                continue
            target = match.group("target").strip()
            op = match.group("op")
            operator = "+" if op == "++" else "-"
            rewritten = f"{match.group('indent')}{target} = {target} {operator} १"
            edits.append(
                RupantarEdit(
                    line=line_no,
                    layer="syntax",
                    before=line.strip(),
                    after=rewritten.strip(),
                    reason="increment/decrement syntax normalized to explicit Vak assignment",
                )
            )
            return rewritten

        return line

    def _rewrite_generator_surface_line(
        self,
        line: str,
        line_no: int,
        edits: list[RupantarEdit],
    ) -> str:
        match = _GENERATOR_CLASS_DECL_RE.match(line)
        if match:
            superclass = match.group("super")
            rewritten = f"{match.group('indent')}वर्ग {match.group('name')}"
            if superclass:
                rewritten += f"({superclass})"
            rewritten += ":"
            edits.append(
                RupantarEdit(
                    line=line_no,
                    layer="pattern",
                    before=line.strip(),
                    after=rewritten.strip(),
                    reason="legacy/generated class surface normalized to live Vak class declaration",
                )
            )
            return rewritten

        match = _GENERATOR_FUNC_DECL_RE.match(line)
        if match:
            async_prefix = "अतुल्यकालिक " if match.group("async") else ""
            rewritten = (
                f"{match.group('indent')}{async_prefix}कर्म {match.group('name')}"
                f"({match.group('params')})"
            )
            return_hint = (match.group("rtype") or "").strip()
            if return_hint:
                return_hint = return_hint.replace("->", "→", 1)
                rewritten += f" {return_hint}"
            rewritten += ":"
            edits.append(
                RupantarEdit(
                    line=line_no,
                    layer="pattern",
                    before=line.strip(),
                    after=rewritten.strip(),
                    reason="legacy/generated function surface normalized to live Vak function declaration",
                )
            )
            return rewritten

        match = _GENERATOR_JOINED_ELSE_RE.match(line)
        if match:
            rewritten = f"{match.group('indent')}अन्यथा:"
            edits.append(
                RupantarEdit(
                    line=line_no,
                    layer="pattern",
                    before=line.strip(),
                    after=rewritten.strip(),
                    reason="joined brace-style else block normalized to live Vak अन्यथा form",
                )
            )
            return rewritten

        match = _GENERATOR_FOREACH_RE.match(line)
        if match:
            rewritten = (
                f"{match.group('indent')}प्रत्येक चर {match.group('vars').strip()} "
                f"अन्तर्गत {match.group('iterable').strip()}:"
            )
            edits.append(
                RupantarEdit(
                    line=line_no,
                    layer="pattern",
                    before=line.strip(),
                    after=rewritten.strip(),
                    reason="legacy/generated foreach loop normalized to live Vak loop declaration",
                )
            )
            return rewritten

        match = _GENERATOR_VAR_DECL_RE.match(line)
        if match:
            decl = match.group("decl")
            keyword = "स्थिर" if decl in {"const", "स्थिरांक"} else "चर"
            rewritten = f"{match.group('indent')}{keyword} {match.group('body').strip()}"
            edits.append(
                RupantarEdit(
                    line=line_no,
                    layer="pattern",
                    before=line.strip(),
                    after=rewritten.strip(),
                    reason="legacy/generated variable declaration normalized to live Vak declaration",
                )
            )
            return rewritten

        match = _GENERATOR_RETURN_RE.match(line)
        if match:
            rest = match.group("rest").strip()
            rewritten = f"{match.group('indent')}प्रत्यागच्छ"
            if rest:
                rewritten += f" {rest}"
            edits.append(
                RupantarEdit(
                    line=line_no,
                    layer="pattern",
                    before=line.strip(),
                    after=rewritten.strip(),
                    reason="legacy/generated return syntax normalized to live Vak प्रत्यागच्छ form",
                )
            )
            return rewritten

        if _GENERATOR_CLOSING_BRACE_RE.match(line):
            edits.append(
                RupantarEdit(
                    line=line_no,
                    layer="pattern",
                    before=line.strip(),
                    after="",
                    reason="brace-only block closer removed after legacy/generated block normalization",
                )
            )
            return ""

        return line

    def _rewrite_branch_import_line(
        self,
        line: str,
        line_no: int,
        edits: list[RupantarEdit],
    ) -> str:
        match = self._import_re.match(line)
        if not match:
            return line

        module = match.group("module")
        for branch_name in self.active_branches:
            modules = self.branch_member_aliases.get(branch_name, {})
            if module not in modules:
                continue
            edits.append(
                RupantarEdit(
                    line=line_no,
                    layer="branch",
                    before=line.strip(),
                    after="",
                    reason=f"{branch_name} branch pseudo-module import removed because builtins are provided directly",
                )
            )
            return ""
        return line

    def _rewrite_postscan_block_surface(
        self,
        line: str,
        line_no: int,
        edits: list[RupantarEdit],
    ) -> str:
        stripped = line.strip()
        if not stripped.endswith("{"):
            return line

        head = stripped[:-1].rstrip()
        block_headers = (
            "यदि ",
            "अन्यत् ",
            "अन्यथा",
            "अन्य",
            "यावत् ",
            "प्रत्येक ",
            "प्रयत्न",
            "दोष",
            "अन्ततः",
            "साथ ",
            "प्रत्यभिज्ञा ",
            "वर्ग ",
            "कर्म ",
            "डेटा ",
        )
        if not any(head == prefix.rstrip() or head.startswith(prefix) for prefix in block_headers):
            return line

        indent = line[: len(line) - len(line.lstrip(" \t"))]
        rewritten = f"{indent}{head}:"
        edits.append(
            RupantarEdit(
                line=line_no,
                layer="pattern",
                before=line.strip(),
                after=rewritten.strip(),
                reason="brace-style block opener normalized to live Vak colon form",
            )
        )
        return rewritten

    def _rewrite_import_line(
        self,
        line: str,
        line_no: int,
        source_path: str | None,
        edits: list[RupantarEdit],
    ) -> str:
        match = _PYTHON_FROM_IMPORT_RE.match(line)
        if match:
            names_text = match.group("names").strip()
            if " as " in names_text or " जैसे " in names_text:
                return line
            module = match.group("module")
            corrected = self._resolve_module_name(module, source_path=source_path)
            rewritten_names = names_text
            module_for_exports = corrected or module
            corrected_names, name_edits = self._rewrite_imported_names(
                names_text,
                module_for_exports,
                line_no=line_no,
                source_path=source_path,
            )
            if name_edits:
                edits.extend(name_edits)
                rewritten_names = corrected_names
            if corrected is not None and corrected != module:
                edits.append(
                    RupantarEdit(
                        line=line_no,
                        layer="import",
                        before=module,
                        after=corrected,
                        reason="python-order import module name corrected against live Vak module files",
                    )
                )
            rewritten = f"{match.group('indent')}आयात {rewritten_names} से {module_for_exports}"
            edits.append(
                RupantarEdit(
                    line=line_no,
                    layer="import",
                    before=line.strip(),
                    after=rewritten.strip(),
                    reason="python-order import syntax normalized to live Vak import form",
                )
            )
            return rewritten

        match = self._from_import_re.match(line)
        if match:
            module = match.group("module")
            corrected = self._resolve_module_name(module, source_path=source_path)
            names_text = match.group("names")
            rewritten_names = names_text
            module_for_exports = corrected or module
            corrected_names, name_edits = self._rewrite_imported_names(
                names_text,
                module_for_exports,
                line_no=line_no,
                source_path=source_path,
            )
            if name_edits:
                edits.extend(name_edits)
                rewritten_names = corrected_names
            if corrected is not None and corrected != module:
                edits.append(
                    RupantarEdit(
                        line=line_no,
                        layer="import",
                        before=module,
                        after=corrected,
                        reason="module name corrected against live Vak module files",
                    )
                )
            if rewritten_names != names_text or (corrected is not None and corrected != module):
                return f"{match.group('indent')}आयात {rewritten_names} से {module_for_exports}"
            return line

        match = self._import_re.match(line)
        if match:
            module = match.group("module")
            corrected = self._resolve_module_name(module, source_path=source_path)
            if corrected is not None and corrected != module:
                rewritten = f"{match.group('indent')}आयात {corrected}"
                edits.append(
                    RupantarEdit(
                        line=line_no,
                        layer="import",
                        before=module,
                        after=corrected,
                        reason="module name corrected against live Vak module files",
                    )
                )
                return rewritten
        return line

    def _rewrite_branch_member_calls(
        self,
        line: str,
        line_no: int,
        edits: list[RupantarEdit],
    ) -> str:
        rewritten = line
        for branch_name in self.active_branches:
            modules = self.branch_member_aliases.get(branch_name, {})
            for module_name, member_aliases in modules.items():
                pattern = re.compile(
                    rf"\b{re.escape(module_name)}\s*\.\s*(?P<member>{_IDENT_RE})"
                )

                def replace(match: re.Match[str]) -> str:
                    member = match.group("member")
                    replacement = member_aliases.get(member)
                    if replacement is None:
                        return match.group(0)
                    edits.append(
                        RupantarEdit(
                            line=line_no,
                            layer="branch",
                            before=f"{module_name}.{member}",
                            after=replacement,
                            reason=f"{branch_name} branch API normalized to live builtin",
                        )
                    )
                    return replacement

                rewritten = pattern.sub(replace, rewritten)
        return rewritten

    def _rewrite_imported_names(
        self,
        names_text: str,
        module_name: str,
        *,
        line_no: int,
        source_path: str | None,
    ) -> tuple[str, list[RupantarEdit]]:
        exported_names = self._module_exports(module_name, source_path=source_path)
        if not exported_names:
            return names_text, []

        parts = [name.strip() for name in names_text.split(",")]
        rewritten_parts = list(parts)
        edits: list[RupantarEdit] = []

        for index, name in enumerate(parts):
            if not name or name in exported_names:
                continue
            replacement = self._resolve_export_name(name, exported_names)
            if replacement is None or replacement == name:
                continue
            rewritten_parts[index] = replacement
            edits.append(
                RupantarEdit(
                    line=line_no,
                    layer="import",
                    before=name,
                    after=replacement,
                    reason=f"imported name corrected against declarations in module '{module_name}'",
                )
            )

        if not edits:
            return names_text, []
        return ", ".join(rewritten_parts), edits

    def _resolve_module_name(
        self,
        module_name: str,
        *,
        source_path: str | None,
    ) -> str | None:
        candidates = self._available_module_names(source_path=source_path)
        alias = self.module_aliases.get(module_name) or self.module_aliases.get(module_name.lower())
        if alias is not None:
            return alias
        if module_name in candidates:
            return module_name

        normalized = self._normalize_module_key(module_name)
        normalized_map = {self._normalize_module_key(name): name for name in candidates}
        if normalized in normalized_map:
            return normalized_map[normalized]

        close = get_close_matches(
            module_name,
            sorted(candidates),
            n=1,
            cutoff=self.module_match_cutoff,
        )
        if close:
            return close[0]
        close = get_close_matches(
            normalized,
            sorted(normalized_map),
            n=1,
            cutoff=self.module_match_cutoff,
        )
        if close:
            return normalized_map[close[0]]
        return None

    def _module_exports(
        self,
        module_name: str,
        *,
        source_path: str | None,
    ) -> tuple[str, ...] | None:
        cache_key = (source_path, module_name)
        if cache_key in self._module_exports_cache:
            return self._module_exports_cache[cache_key]

        module_paths = self._available_module_paths(source_path=source_path)
        path = module_paths.get(module_name)
        if path is None:
            self._module_exports_cache[cache_key] = None
            return None

        try:
            source = path.read_text(encoding="utf-8")
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            program = parser.parse()
        except Exception:
            self._module_exports_cache[cache_key] = None
            return None

        exports = tuple(sorted(self._collect_top_level_names(program)))
        self._module_exports_cache[cache_key] = exports
        return exports

    def _collect_top_level_names(self, program: Any) -> set[str]:
        exports: set[str] = set()
        for stmt in getattr(program, "body", []) or []:
            kind = type(stmt).__name__
            if kind == "VarDecl":
                exports.update(getattr(stmt, "names", []) or [])
            elif kind == "ConstDecl":
                name = getattr(stmt, "name", None)
                if name:
                    exports.add(name)
            elif kind in {"FuncDecl", "ClassDecl", "DataDecl", "ParinamaDecl", "SutraDecl"}:
                name = getattr(stmt, "name", None)
                if name:
                    exports.add(name)
                if kind == "DataDecl":
                    for variant in getattr(stmt, "variants", []) or []:
                        variant_name = getattr(variant, "name", None)
                        if variant_name:
                            exports.add(variant_name)
        return exports

    def _resolve_export_name(
        self,
        name: str,
        exported_names: tuple[str, ...],
    ) -> str | None:
        matches = get_close_matches(
            name,
            list(exported_names),
            n=1,
            cutoff=self.module_export_match_cutoff,
        )
        if matches:
            return matches[0]
        return None

    def _rewrite_identifiers_with_map(
        self,
        source: str,
        replacements: dict[str, str],
    ) -> tuple[str, list[RupantarEdit]]:
        transformed_lines: list[str] = []
        edits: list[RupantarEdit] = []
        in_multiline: str | None = None

        for line_no, raw_line in enumerate(source.splitlines(keepends=True), start=1):
            newline = "\n" if raw_line.endswith("\n") else ""
            line = raw_line[:-1] if newline else raw_line

            if in_multiline is not None:
                close_at = line.find(in_multiline)
                transformed_lines.append(raw_line)
                if close_at != -1:
                    in_multiline = None
                continue

            code, comment = self._split_comment(line)
            rewritten, new_multiline, line_edits = self._replace_tokens_in_code(
                code,
                line_no,
                replacements,
            )
            edits.extend(line_edits)
            if rewritten != code:
                transformed_lines.append(f"{rewritten}{comment}{newline}")
            else:
                transformed_lines.append(raw_line)
            in_multiline = new_multiline

        return "".join(transformed_lines), edits

    def _replace_identifier_tokens(
        self,
        line: str,
        replacements: dict[str, str],
        *,
        line_no: int,
        layer: str,
        reason: str,
    ) -> tuple[str, str | None]:
        rewritten, in_multiline, _edits = self._replace_tokens_in_code(
            line,
            line_no,
            replacements,
            layer=layer,
            reason=reason,
        )
        return rewritten, in_multiline

    def _replace_keyword_names_in_code(
        self,
        line: str,
        replacements: dict[str, str],
    ) -> tuple[str, list[tuple[str, str]]]:
        result: list[str] = []
        changes: list[tuple[str, str]] = []
        pos = 0
        length = len(line)

        while pos < length:
            ch = line[pos]

            if ch in ('"', "'"):
                if pos + 2 < length and line[pos] == line[pos + 1] == line[pos + 2]:
                    quote = line[pos:pos + 3]
                    end_pos = line.find(quote, pos + 3)
                    if end_pos == -1:
                        result.append(line[pos:])
                        break
                    result.append(line[pos:end_pos + 3])
                    pos = end_pos + 3
                    continue

                end_pos = pos + 1
                while end_pos < length:
                    if line[end_pos] == "\\":
                        end_pos += 2
                        continue
                    if line[end_pos] == ch:
                        end_pos += 1
                        break
                    end_pos += 1
                result.append(line[pos:end_pos])
                pos = end_pos
                continue

            if is_identifier_start(ch):
                start = pos
                pos += 1
                while pos < length and is_identifier_part(line[pos]):
                    pos += 1
                token = line[start:pos]
                replacement = replacements.get(token)
                next_pos = pos
                while next_pos < length and line[next_pos] in (" ", "\t"):
                    next_pos += 1
                if (
                    replacement is not None
                    and self._previous_significant_char(result) != "."
                    and next_pos < length
                    and line[next_pos] == "="
                    and (next_pos + 1 >= length or line[next_pos + 1] != "=")
                ):
                    changes.append((token, replacement))
                    result.append(replacement)
                    continue
                result.append(token)
                continue

            result.append(ch)
            pos += 1

        return "".join(result), changes

    def _replace_tokens_in_code(
        self,
        line: str,
        line_no: int,
        replacements: dict[str, str],
        *,
        layer: str = "logic",
        reason: str = "adaptive unresolved-name repair accepted after validation",
    ) -> tuple[str, str | None, list[RupantarEdit]]:
        result: list[str] = []
        edits: list[RupantarEdit] = []
        pos = 0
        length = len(line)
        in_multiline: str | None = None

        while pos < length:
            ch = line[pos]

            if ch in ('"', "'"):
                if pos + 2 < length and line[pos] == line[pos + 1] == line[pos + 2]:
                    quote = line[pos:pos + 3]
                    end_pos = line.find(quote, pos + 3)
                    if end_pos == -1:
                        result.append(line[pos:])
                        return "".join(result), quote, edits
                    result.append(line[pos:end_pos + 3])
                    pos = end_pos + 3
                    continue

                end_pos = pos + 1
                while end_pos < length:
                    if line[end_pos] == "\\":
                        end_pos += 2
                        continue
                    if line[end_pos] == ch:
                        end_pos += 1
                        break
                    end_pos += 1
                result.append(line[pos:end_pos])
                pos = end_pos
                continue

            if is_identifier_start(ch):
                start = pos
                pos += 1
                while pos < length and is_identifier_part(line[pos]):
                    pos += 1
                token = line[start:pos]
                if self._previous_significant_char(result) == ".":
                    result.append(token)
                    continue
                replacement = replacements.get(token)
                if replacement is None:
                    result.append(token)
                    continue
                edits.append(
                    RupantarEdit(
                        line=line_no,
                        layer=layer,
                        before=token,
                        after=replacement,
                        reason=reason,
                    )
                )
                result.append(replacement)
                continue

            result.append(ch)
            pos += 1

        return "".join(result), in_multiline, edits

    @staticmethod
    def _safe_identifier_name(name: str) -> str:
        candidate = f"{name}_मान"
        if candidate in KEYWORDS:
            candidate = f"{name}_चर"
        return candidate

    @staticmethod
    def _fuzzy_alias_target(
        token: str,
        alias_map: dict[str, str],
        *,
        cutoff: float,
    ) -> str | None:
        candidate_pool = set(alias_map.keys()) | set(alias_map.values())
        matches = get_close_matches(token, sorted(candidate_pool), n=1, cutoff=cutoff)
        if not matches:
            lowered = token.lower()
            matches = get_close_matches(lowered, sorted(candidate_pool), n=1, cutoff=cutoff)
            if not matches:
                return None
        match = matches[0]
        return alias_map.get(match, match)

    def _fuzzy_builtin_target(self, token: str) -> str | None:
        candidate_pool = (
            set(self.builtin_alias_map.keys())
            | set(self.builtin_alias_map.values())
            | self.builtin_names
        )
        matches = get_close_matches(
            token,
            sorted(candidate_pool),
            n=1,
            cutoff=self.fuzzy_builtin_cutoff or 1.0,
        )
        if not matches:
            lowered = token.lower()
            matches = get_close_matches(
                lowered,
                sorted(candidate_pool),
                n=1,
                cutoff=self.fuzzy_builtin_cutoff or 1.0,
            )
            if not matches:
                return None
        match = matches[0]
        return self.builtin_alias_map.get(match, match)

    def _available_module_names(self, *, source_path: str | None) -> set[str]:
        return set(self._available_module_paths(source_path=source_path).keys())

    def _available_module_paths(self, *, source_path: str | None) -> dict[str, Path]:
        module_paths: dict[str, Path] = {}

        search_roots = [self._stdlib_root]
        if source_path is not None:
            search_roots.append(Path(source_path).resolve().parent)

        for root in search_roots:
            if not root.exists():
                continue
            for path in root.rglob("*.vak"):
                relative = path.relative_to(root)
                if relative.name == "__init__.vak":
                    parts = relative.parts[:-1]
                else:
                    parts = relative.with_suffix("").parts
                if not parts:
                    continue
                module_paths[".".join(parts)] = path

        for name, spec in self.stdlib_manifest.items():
            if spec.path.exists():
                module_paths.setdefault(name, spec.path)
            canonical = spec.canonical or spec.name
            if spec.path.exists():
                module_paths.setdefault(canonical, spec.path)
            for alias in spec.aliases:
                if spec.path.exists():
                    module_paths.setdefault(alias, spec.path)

        return module_paths

    @staticmethod
    def _normalize_module_key(name: str) -> str:
        return name.replace("-", "_").replace(" ", "_").lower()

    @staticmethod
    def _split_comment(line: str) -> tuple[str, str]:
        in_single = False
        in_double = False
        escaped = False

        for index, ch in enumerate(line):
            if escaped:
                escaped = False
                continue
            if ch == "\\":
                escaped = True
                continue
            if ch == '"' and not in_single:
                in_double = not in_double
                continue
            if ch == "'" and not in_double:
                in_single = not in_single
                continue
            if ch == "#" and not in_single and not in_double:
                return line[:index], line[index:]
        return line, ""

    @staticmethod
    def _previous_significant_char(parts: list[str]) -> str | None:
        for part in reversed(parts):
            for ch in reversed(part):
                if ch not in (" ", "\t"):
                    return ch
        return None


def रूपान्तर_करो(
    source: str,
    *,
    source_path: str | None = None,
    active_branches: list[str] | None = None,
    branch_registry: Any = None,
) -> RupantarResult:
    engine = VakyaRupantar(
        active_branches=active_branches,
        branch_registry=branch_registry,
    )
    return engine.transform_source(source, source_path=source_path)
