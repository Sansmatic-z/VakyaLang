from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sansmatic.src.config import SansmaticSettings
from sansmatic.src.engine import SansmaticEngine

from .ast_nodes import *
from .errors import CompileError
from .types import (
    ADTType,
    ANY,
    BOOL,
    FLOAT,
    INT,
    NEVER,
    NULL,
    OBJECT,
    RANGE,
    STR,
    ClassType,
    DictType,
    FunctionType,
    InstanceType,
    ListType,
    ModuleType,
    ResultType,
    RefinementType,
    SetType,
    TupleType,
    TypeVarType,
    UnionType,
    VakType,
    VariantValueType,
    bind_typevars,
    combine_types,
    instantiate_type,
    is_assignable,
    iterable_element_type,
    parse_type_hint,
    register_adt_type,
)

_NO_STATIC_VALUE = object()


@dataclass
class FunctionContext:
    name: str
    declared_return: VakType
    observed_return: VakType = NEVER
    owner_class: str | None = None


@dataclass
class DataVariantInfo:
    name: str
    field_types: tuple[VakType, ...]


@dataclass
class DataInfo:
    name: str
    type_params: tuple[str, ...]
    variants: dict[str, DataVariantInfo]


class TypeEnv:
    def __init__(self, parent: "TypeEnv | None" = None):
        self.parent = parent
        self.values: dict[str, VakType] = {}
        self.fixed_names: set[str] = set()
        self.static_values: dict[str, Any] = {}

    def define(
        self,
        name: str,
        value_type: VakType,
        *,
        fixed: bool = False,
        static_value: Any = _NO_STATIC_VALUE,
    ) -> None:
        self.values[name] = value_type
        if fixed:
            self.fixed_names.add(name)
        else:
            self.fixed_names.discard(name)
        if static_value is _NO_STATIC_VALUE:
            self.static_values.pop(name, None)
        else:
            self.static_values[name] = static_value

    def lookup(self, name: str) -> VakType | None:
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.lookup(name)
        return None

    def lookup_static(self, name: str) -> Any:
        if name in self.static_values:
            return self.static_values[name]
        if self.parent is not None:
            return self.parent.lookup_static(name)
        return _NO_STATIC_VALUE

    def assign(self, name: str, value_type: VakType, *, static_value: Any = _NO_STATIC_VALUE) -> None:
        if name in self.values:
            self.values[name] = value_type
            if static_value is _NO_STATIC_VALUE:
                self.static_values.pop(name, None)
            else:
                self.static_values[name] = static_value
            return
        if self.parent is not None and self.parent.lookup(name) is not None:
            self.parent.assign(name, value_type, static_value=static_value)
            return
        self.values[name] = value_type
        if static_value is not _NO_STATIC_VALUE:
            self.static_values[name] = static_value

    def is_fixed(self, name: str) -> bool:
        if name in self.values:
            return name in self.fixed_names
        if self.parent is not None:
            return self.parent.is_fixed(name)
        return False

    def child(self) -> "TypeEnv":
        return TypeEnv(parent=self)


class TypeChecker:
    def __init__(self):
        self.globals = TypeEnv()
        self.class_methods: dict[str, dict[str, FunctionType]] = {}
        self.class_fields: dict[str, dict[str, VakType]] = {}
        self.data_types: dict[str, DataInfo] = {}
        self.variant_constructors: dict[str, tuple[DataInfo, DataVariantInfo]] = {}
        self._function_stack: list[FunctionContext] = []
        self.sansmatic = SansmaticEngine(
            verbose=False,
            settings=SansmaticSettings.from_env(),
        )
        self._install_builtins()

    def check(self, node: Node) -> None:
        if not isinstance(node, Program):
            return
        self._predeclare_block(node.body, self.globals)
        self._check_block(node.body, self.globals, None)

    def _install_builtins(self) -> None:
        one_any = FunctionType((ANY,), ANY)
        one_str = FunctionType((ANY,), STR)
        one_bool = FunctionType((ANY,), BOOL)
        one_seq = FunctionType((ANY,), INT)
        one_report = DictType(STR, ANY)
        self.globals.define("पाठ_कर", one_str, fixed=True)
        self.globals.define("str", one_str, fixed=True)
        self.globals.define("दीर्घता", one_seq, fixed=True)
        self.globals.define("len", one_seq, fixed=True)
        self.globals.define("संख्या", FunctionType((ANY,), INT), fixed=True)
        self.globals.define("int", FunctionType((ANY,), INT), fixed=True)
        self.globals.define("दशमलव", FunctionType((ANY,), FLOAT), fixed=True)
        self.globals.define("float", FunctionType((ANY,), FLOAT), fixed=True)
        self.globals.define("bool", FunctionType((ANY,), BOOL), fixed=True)
        self.globals.define("type", one_str, fixed=True)
        self.globals.define("प्रकार", one_str, fixed=True)
        self.globals.define("मुद्रय", FunctionType((ANY,), NULL, varargs_name="args"), fixed=True)
        self.globals.define("print", FunctionType((ANY,), NULL, varargs_name="args"), fixed=True)
        self.globals.define("range", FunctionType((INT,), RANGE, defaults_count=0, varargs_name="rest"), fixed=True)
        self.globals.define("परास", FunctionType((INT,), RANGE, defaults_count=0, varargs_name="rest"), fixed=True)
        self.globals.define("list", FunctionType((ANY,), ListType(ANY)), fixed=True)
        self.globals.define("dict", FunctionType((ANY,), DictType(ANY, ANY)), fixed=True)
        self.globals.define("set", FunctionType((ANY,), SetType(ANY)), fixed=True)
        self.globals.define("enumerate", FunctionType((ANY, INT), ListType(TupleType((INT, ANY))), defaults_count=1), fixed=True)
        self.globals.define("zip", FunctionType((ANY,), ListType(TupleType((ANY,))), varargs_name="rest"), fixed=True)
        self.globals.define("map", FunctionType((ANY, ANY), ListType(ANY)), fixed=True)
        self.globals.define("filter", FunctionType((ANY, ANY), ListType(ANY)), fixed=True)
        self.globals.define("isinstance", FunctionType((ANY, ANY), BOOL), fixed=True)
        self.globals.define("hasattr", FunctionType((ANY, STR), BOOL), fixed=True)
        self.globals.define("all", one_bool, fixed=True)
        self.globals.define("any", one_bool, fixed=True)
        self.globals.define("sum", one_any, fixed=True)
        self.globals.define("योग", one_any, fixed=True)
        self.globals.define("min", one_any, fixed=True)
        self.globals.define("न्यूनतम", one_any, fixed=True)
        self.globals.define("max", one_any, fixed=True)
        self.globals.define("अधिकतम", one_any, fixed=True)
        self.globals.define("sorted", FunctionType((ANY,), ListType(ANY)), fixed=True)
        self.globals.define("क्रमबद्ध", FunctionType((ANY,), ListType(ANY)), fixed=True)
        self.globals.define("सिद्ध", FunctionType((ANY,), ResultType(ANY, ANY)), fixed=True)
        self.globals.define("असिद्ध", FunctionType((ANY,), ResultType(ANY, ANY)), fixed=True)
        self.globals.define("फल_सफल_है", FunctionType((ANY,), BOOL), fixed=True)
        self.globals.define("फल_विफल_है", FunctionType((ANY,), BOOL), fixed=True)
        self.globals.define("फल_खोलो", FunctionType((ANY,), ANY), fixed=True)
        self.globals.define("फल_त्रुटि", FunctionType((ANY,), ANY), fixed=True)
        self.globals.define("पद", FunctionType((ANY,), ANY), fixed=True)
        self.globals.define("term", FunctionType((ANY,), ANY), fixed=True)
        self.globals.define("धर्म_निर्माण", FunctionType((STR, STR), one_report, defaults_count=0, varargs_name="rest"), fixed=True)
        self.globals.define("धर्म_जाँच", FunctionType((ANY, ANY), one_report), fixed=True)
        self.globals.define("धर्म_मान्य_है", FunctionType((ANY, ANY), BOOL), fixed=True)
        self.globals.define("कारक_हस्ताक्षर", FunctionType((STR, ANY), one_report), fixed=True)
        self.globals.define("कारक_जाँच", FunctionType((ANY, DictType(STR, ANY)), one_report), fixed=True)
        self.globals.define("न्याय_सिद्धि_रिपोर्ट", FunctionType((STR, STR, STR, STR, STR), one_report), fixed=True)
        self.globals.define("न्याय_सिद्धि_मान्य_है", FunctionType((STR, STR, STR, STR, STR), BOOL), fixed=True)
        self.globals.define("पदार्थ_वर्गीकरण", FunctionType((ANY,), STR), fixed=True)

    def _predeclare_block(self, stmts: list[Any], env: TypeEnv) -> None:
        for stmt in stmts:
            if isinstance(stmt, DataDecl):
                self._register_data_decl(stmt, env)
        for stmt in stmts:
            if isinstance(stmt, FuncDecl):
                env.define(stmt.name, self._signature_from_func(stmt), fixed=True)
            elif isinstance(stmt, ClassDecl):
                env.define(stmt.name, ClassType(stmt.name), fixed=True)
                self.class_methods[stmt.name] = self._collect_class_methods(stmt)
            elif isinstance(stmt, DataDecl):
                continue
            elif isinstance(stmt, ParinamaDecl):
                env.define(
                    stmt.name,
                    FunctionType((ANY, ANY, ANY), ANY, ("term", "अधिकार", "scope"), defaults_count=2),
                    fixed=True,
                )
            elif isinstance(stmt, ImportStmt):
                if stmt.names:
                    for name in stmt.names:
                        env.define(name, ANY, fixed=True)
                else:
                    module_name = stmt.module.split(".")[-1]
                    env.define(module_name, ModuleType(stmt.module), fixed=True)

    def _register_data_decl(self, node: DataDecl, env: TypeEnv) -> None:
        register_adt_type(node.name, [variant.name for variant in node.variants], node.type_params)

        variants: dict[str, DataVariantInfo] = {}
        for variant in node.variants:
            field_types = tuple(parse_type_hint(field_type) for field_type in variant.field_types)
            info = DataVariantInfo(name=variant.name, field_types=field_types)
            variants[variant.name] = info

        data_info = DataInfo(name=node.name, type_params=tuple(node.type_params), variants=variants)
        self.data_types[node.name] = data_info

        adt_type = ADTType(node.name, tuple(TypeVarType(param) for param in node.type_params))
        env.define(node.name, adt_type, fixed=True)

        for variant_name, variant_info in variants.items():
            signature = FunctionType(
                variant_info.field_types,
                adt_type,
                tuple(f"value{i}" for i in range(len(variant_info.field_types))),
            )
            env.define(variant_name, signature, fixed=True)
            self.variant_constructors[variant_name] = (data_info, variant_info)

    def _collect_class_methods(self, node: ClassDecl) -> dict[str, FunctionType]:
        methods: dict[str, FunctionType] = {}
        if not isinstance(node.body, Block):
            return methods
        for stmt in node.body.stmts:
            if isinstance(stmt, FuncDecl):
                methods[stmt.name] = self._signature_from_func(stmt, class_name=node.name)
        return methods

    def _signature_from_func(self, node: FuncDecl, class_name: str | None = None) -> FunctionType:
        param_types: list[VakType] = []
        param_names: list[str] = []
        for param in node.params:
            if isinstance(param, VibhaktiParam):
                param_type = parse_type_hint(param.type_hint)
                param_name = param.name
            else:
                param_name, type_hint = param
                param_type = parse_type_hint(type_hint)
            if class_name and param_name in ("स्वयं", "self") and param_type == ANY:
                param_type = InstanceType(class_name)
            param_names.append(param_name)
            param_types.append(param_type)
        return FunctionType(
            tuple(param_types),
            parse_type_hint(node.return_type),
            tuple(param_names),
            defaults_count=sum(1 for d in node.defaults if d is not None),
            varargs_name=node.varargs,
            is_async=node.is_async,
        )

    def _check_block(self, stmts: list[Any], env: TypeEnv, fn_ctx: FunctionContext | None) -> None:
        self._predeclare_block(stmts, env)
        for stmt in stmts:
            self._check_stmt(stmt, env, fn_ctx)

    def _check_stmt(self, stmt: Node, env: TypeEnv, fn_ctx: FunctionContext | None) -> None:
        if isinstance(stmt, VarDecl):
            value_type = self._infer_expr(stmt.value, env) if stmt.value is not None else NULL
            declared_type = parse_type_hint(stmt.type_hint)
            if declared_type != ANY and not is_assignable(value_type, declared_type):
                raise CompileError(
                    f"चर '{stmt.names[0]}' को {declared_type} चाहिए, मिला {value_type}",
                    stmt.line,
                )
            self._require_refinement_constraint(
                stmt.value,
                value_type,
                declared_type,
                env,
                stmt.line,
                f"चर '{stmt.names[0]}'",
            )
            final_type = declared_type if declared_type != ANY else value_type
            static_value = self._static_value(stmt.value, env) if stmt.value is not None else None
            if len(stmt.names) == 1:
                env.define(
                    stmt.names[0],
                    final_type,
                    fixed=declared_type != ANY,
                    static_value=static_value,
                )
            else:
                element_types = self._destructure_types(final_type, len(stmt.names))
                if isinstance(static_value, (list, tuple)) and len(static_value) == len(stmt.names):
                    static_items = list(static_value)
                else:
                    static_items = [_NO_STATIC_VALUE] * len(stmt.names)
                for name, element_type, item_static in zip(stmt.names, element_types, static_items):
                    env.define(
                        name,
                        element_type,
                        fixed=declared_type != ANY,
                        static_value=item_static,
                    )
            return

        if isinstance(stmt, ConstDecl):
            value_type = self._infer_expr(stmt.value, env)
            declared_type = parse_type_hint(stmt.type_hint)
            if declared_type != ANY and not is_assignable(value_type, declared_type):
                raise CompileError(
                    f"स्थिर '{stmt.name}' को {declared_type} चाहिए, मिला {value_type}",
                    stmt.line,
                )
            self._require_refinement_constraint(
                stmt.value,
                value_type,
                declared_type,
                env,
                stmt.line,
                f"स्थिर '{stmt.name}'",
            )
            env.define(
                stmt.name,
                declared_type if declared_type != ANY else value_type,
                fixed=True,
                static_value=self._static_value(stmt.value, env),
            )
            return

        if isinstance(stmt, ExprStmt):
            self._infer_expr(stmt.expr, env)
            return

        if isinstance(stmt, PrintStmt):
            for value in stmt.values:
                self._infer_expr(value, env)
            return

        if isinstance(stmt, ReturnStmt):
            if fn_ctx is None:
                return
            value_type = NULL if stmt.value is None else self._infer_expr(stmt.value, env)
            if fn_ctx.declared_return != ANY and not is_assignable(value_type, fn_ctx.declared_return):
                raise CompileError(
                    f"कर्म '{fn_ctx.name}' को {fn_ctx.declared_return} लौटाना था, मिला {value_type}",
                    stmt.line,
                )
            self._require_refinement_constraint(
                stmt.value,
                value_type,
                fn_ctx.declared_return,
                env,
                stmt.line,
                f"कर्म '{fn_ctx.name}' का return",
            )
            fn_ctx.observed_return = combine_types(fn_ctx.observed_return, value_type)
            return

        if isinstance(stmt, IfStmt):
            self._require_bool(
                self._infer_expr(stmt.condition, env),
                stmt.line,
                "यदि की शर्त",
            )
            self._check_block(stmt.then_body.stmts, env.child(), fn_ctx)
            for cond, body in stmt.elif_clauses:
                self._require_bool(
                    self._infer_expr(cond, env),
                    getattr(cond, "line", stmt.line),
                    "अन्ययदि की शर्त",
                )
                self._check_block(body.stmts, env.child(), fn_ctx)
            if stmt.else_body:
                self._check_block(stmt.else_body.stmts, env.child(), fn_ctx)
            return

        if isinstance(stmt, WhileStmt):
            self._require_bool(
                self._infer_expr(stmt.condition, env),
                stmt.line,
                "यावत् की शर्त",
            )
            self._check_block(stmt.body.stmts, env.child(), fn_ctx)
            return

        if isinstance(stmt, ForStmt):
            iterable_type = self._infer_expr(stmt.iterable, env)
            loop_env = env.child()
            element_type = iterable_element_type(iterable_type)
            if len(stmt.var_names) == 1:
                loop_env.define(stmt.var_names[0], element_type)
            else:
                element_types = self._destructure_types(element_type, len(stmt.var_names))
                for name, item_type in zip(stmt.var_names, element_types):
                    loop_env.define(name, item_type)
            self._check_block(stmt.body.stmts, loop_env, fn_ctx)
            return

        if isinstance(stmt, Block):
            self._check_block(stmt.stmts, env.child(), fn_ctx)
            return

        if isinstance(stmt, MatchStmt):
            subject_type = self._infer_expr(stmt.subject, env)
            covered_keys: set[str] = set()
            has_catchall = False
            for case in stmt.cases:
                case_env = env.child()
                for name, binding_type in self._pattern_bindings(case.pattern, subject_type).items():
                    case_env.define(name, binding_type)
                if case.guard is not None:
                    self._require_bool(
                        self._infer_expr(case.guard, case_env),
                        getattr(case.guard, "line", stmt.line),
                        "प्रत्यभिज्ञा guard",
                    )
                self._check_block(case.body.stmts, case_env, fn_ctx)
                if case.guard is None:
                    coverage = self._pattern_coverage(case.pattern, subject_type)
                    if coverage == "__all__":
                        has_catchall = True
                    elif coverage is not None:
                        covered_keys.add(coverage)

            exhaustive = has_catchall
            if not exhaustive:
                possible = self._possible_match_coverage(subject_type)
                if possible is not None and possible.issubset(covered_keys):
                    exhaustive = True
                elif possible is not None and not has_catchall:
                    raise CompileError("अपूर्ण प्रत्यभिज्ञा: सभी रूपों को कवर करना आवश्यक है", stmt.line)
            setattr(stmt, "exhaustive", exhaustive)
            return

        if isinstance(stmt, TryStmt):
            self._check_block(stmt.try_body.stmts, env.child(), fn_ctx)
            for handler in stmt.handlers:
                catch_env = env.child()
                if handler.bind_name:
                    catch_env.define(handler.bind_name, ANY)
                self._check_block(handler.body.stmts, catch_env, fn_ctx)
            if stmt.finally_body:
                self._check_block(stmt.finally_body.stmts, env.child(), fn_ctx)
            return

        if isinstance(stmt, WithStmt):
            expr_type = self._infer_expr(stmt.expr, env)
            with_env = env.child()
            if stmt.var_name:
                with_env.define(
                    stmt.var_name,
                    expr_type,
                    static_value=self._static_value(stmt.expr, env),
                )
            self._check_block(stmt.body.stmts, with_env, fn_ctx)
            return

        if isinstance(stmt, ThrowStmt):
            self._infer_expr(stmt.value, env)
            return

        if isinstance(stmt, ImportStmt):
            return

        if isinstance(stmt, DataDecl):
            return

        if isinstance(stmt, GlobalStmt | NonlocalStmt | BreakStmt | ContinueStmt):
            return

        if isinstance(stmt, ClassDecl):
            self._check_class(stmt, env)
            return

        if isinstance(stmt, FuncDecl):
            self._check_function(stmt, env)
            return

    def _check_class(self, node: ClassDecl, env: TypeEnv) -> None:
        if not isinstance(node.body, Block):
            return
        class_env = env.child()
        class_env.define(node.name, ClassType(node.name), fixed=True)
        self.class_fields.setdefault(node.name, {})
        for stmt in node.body.stmts:
            if isinstance(stmt, FuncDecl):
                self._check_function(stmt, class_env, class_name=node.name)

    def _check_function(self, node: FuncDecl, env: TypeEnv, class_name: str | None = None) -> None:
        signature = self._signature_from_func(node, class_name=class_name)
        for name, default_expr, expected_type in zip(signature.param_names, node.defaults, signature.param_types):
            if default_expr is None:
                continue
            default_type = self._infer_expr(default_expr, env)
            if expected_type != ANY and not is_assignable(default_type, expected_type):
                raise CompileError(
                    f"परिमाण '{name}' का डिफ़ॉल्ट मान {expected_type} चाहिए, मिला {default_type}",
                    getattr(default_expr, "line", node.line),
                )
            self._require_refinement_constraint(
                default_expr,
                default_type,
                expected_type,
                env,
                getattr(default_expr, "line", node.line),
                f"परिमाण '{name}'",
            )
        fn_env = env.child()
        for name, value_type in zip(signature.param_names, signature.param_types):
            fn_env.define(name, value_type, fixed=True)
        if node.varargs:
            fn_env.define(node.varargs, ListType(ANY), fixed=True)
        fn_ctx = FunctionContext(
            name=node.name,
            declared_return=signature.return_type,
            owner_class=class_name,
        )
        self._function_stack.append(fn_ctx)
        try:
            self._check_block(node.body.stmts, fn_env, fn_ctx)
        finally:
            self._function_stack.pop()
        final_return = signature.return_type if signature.return_type != ANY else (
            fn_ctx.observed_return if fn_ctx.observed_return != NEVER else NULL
        )
        if (
            signature.return_type not in (ANY, NULL)
            and not self._block_guarantees_exit(node.body.stmts)
        ):
            raise CompileError(
                f"कर्म '{node.name}' को सभी मार्गों में {signature.return_type} लौटाना आवश्यक है",
                node.line,
            )
        env.assign(
            node.name,
            FunctionType(
                signature.param_types,
                final_return,
                signature.param_names,
                signature.defaults_count,
                signature.varargs_name,
                signature.is_async,
            ),
        )

    def _require_refinement_constraint(
        self,
        expr: Any,
        actual_type: VakType,
        expected_type: VakType,
        env: TypeEnv,
        line: int,
        context: str,
    ) -> None:
        if not isinstance(expected_type, RefinementType):
            return
        if isinstance(actual_type, RefinementType):
            if (
                actual_type.predicate == expected_type.predicate
                and is_assignable(actual_type.base_type, expected_type.base_type)
            ):
                return
        static_value = self._static_value(expr, env)
        if static_value is _NO_STATIC_VALUE:
            raise CompileError(
                f"{context} के refinement '{expected_type.predicate}' को compile-time सिद्ध करना आवश्यक है",
                line,
            )
        if not self._prove_refinement(expected_type, static_value):
            raise CompileError(
                f"{context} refinement '{expected_type.predicate}' को संतुष्ट नहीं करता",
                line,
            )

    def _prove_refinement(self, refinement: RefinementType, value: Any) -> bool:
        statement = f"{refinement.predicate}({self._serialize_refinement_value(value)})"
        probe = self.sansmatic.clone(verbose=False)
        return probe.verify_statement(statement)

    def _serialize_refinement_value(self, value: Any) -> str:
        if value is True:
            return "सत्य"
        if value is False:
            return "असत्य"
        if value is None:
            return "शून्य"
        if isinstance(value, str):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        if isinstance(value, tuple):
            inner = ", ".join(self._serialize_refinement_value(item) for item in value)
            return f"({inner})"
        if isinstance(value, list):
            inner = ", ".join(self._serialize_refinement_value(item) for item in value)
            return f"[{inner}]"
        if isinstance(value, set):
            inner = ", ".join(self._serialize_refinement_value(item) for item in sorted(value, key=repr))
            return f"{{{inner}}}"
        if isinstance(value, dict):
            parts = [
                f"{self._serialize_refinement_value(key)}: {self._serialize_refinement_value(val)}"
                for key, val in value.items()
            ]
            return f"{{{', '.join(parts)}}}"
        return str(value)

    def _static_value(self, expr: Any, env: TypeEnv) -> Any:
        if expr is None:
            return None
        method = getattr(self, f"_static_{type(expr).__name__}", None)
        if method is None:
            return _NO_STATIC_VALUE
        return method(expr, env)

    def _static_NumberLiteral(self, expr: NumberLiteral, env: TypeEnv) -> Any:
        return expr.value

    def _static_StringLiteral(self, expr: StringLiteral, env: TypeEnv) -> Any:
        return expr.value

    def _static_FStringExpr(self, expr: FStringExpr, env: TypeEnv) -> Any:
        parts: list[str] = []
        for part in expr.parts:
            if isinstance(part, str):
                parts.append(part)
                continue
            value = self._static_value(part, env)
            if value is _NO_STATIC_VALUE:
                return _NO_STATIC_VALUE
            parts.append(str(value))
        return "".join(parts)

    def _static_BoolLiteral(self, expr: BoolLiteral, env: TypeEnv) -> Any:
        return expr.value

    def _static_NullLiteral(self, expr: NullLiteral, env: TypeEnv) -> Any:
        return None

    def _static_IdentifierExpr(self, expr: IdentifierExpr, env: TypeEnv) -> Any:
        if expr.name == "सत्य":
            return True
        if expr.name == "असत्य":
            return False
        return env.lookup_static(expr.name)

    def _static_ListLiteral(self, expr: ListLiteral, env: TypeEnv) -> Any:
        values = []
        for element in expr.elements:
            value = self._static_value(element, env)
            if value is _NO_STATIC_VALUE:
                return _NO_STATIC_VALUE
            values.append(value)
        return values

    def _static_SetLiteral(self, expr: SetLiteral, env: TypeEnv) -> Any:
        values = []
        for element in expr.elements:
            value = self._static_value(element, env)
            if value is _NO_STATIC_VALUE:
                return _NO_STATIC_VALUE
            values.append(value)
        return set(values)

    def _static_TupleLiteral(self, expr: TupleLiteral, env: TypeEnv) -> Any:
        values = []
        for element in expr.elements:
            value = self._static_value(element, env)
            if value is _NO_STATIC_VALUE:
                return _NO_STATIC_VALUE
            values.append(value)
        return tuple(values)

    def _static_DictLiteral(self, expr: DictLiteral, env: TypeEnv) -> Any:
        values: dict[Any, Any] = {}
        for key_expr, value_expr in expr.pairs:
            key = self._static_value(key_expr, env)
            value = self._static_value(value_expr, env)
            if key is _NO_STATIC_VALUE or value is _NO_STATIC_VALUE:
                return _NO_STATIC_VALUE
            values[key] = value
        return values

    def _static_UnaryExpr(self, expr: UnaryExpr, env: TypeEnv) -> Any:
        operand = self._static_value(expr.operand, env)
        if operand is _NO_STATIC_VALUE:
            return _NO_STATIC_VALUE
        try:
            if expr.op == "+":
                return +operand
            if expr.op == "-":
                return -operand
            if expr.op in ("न", "not"):
                return not operand
            if expr.op == "~":
                return ~operand
        except Exception:
            return _NO_STATIC_VALUE
        return _NO_STATIC_VALUE

    def _static_BinaryExpr(self, expr: BinaryExpr, env: TypeEnv) -> Any:
        left = self._static_value(expr.left, env)
        right = self._static_value(expr.right, env)
        if left is _NO_STATIC_VALUE or right is _NO_STATIC_VALUE:
            return _NO_STATIC_VALUE
        try:
            if expr.op == "+":
                return left + right
            if expr.op == "-":
                return left - right
            if expr.op == "*":
                return left * right
            if expr.op == "/":
                return left / right
            if expr.op == "//":
                return left // right
            if expr.op == "%":
                return left % right
            if expr.op == "**":
                return left ** right
            if expr.op == "==":
                return left == right
            if expr.op == "!=":
                return left != right
            if expr.op == "<":
                return left < right
            if expr.op == "<=":
                return left <= right
            if expr.op == ">":
                return left > right
            if expr.op == ">=":
                return left >= right
            if expr.op == "और":
                return left and right
            if expr.op == "अथवा":
                return left or right
            if expr.op == "|":
                return left | right
            if expr.op == "&":
                return left & right
            if expr.op == "^":
                return left ^ right
            if expr.op == "<<":
                return left << right
            if expr.op == ">>":
                return left >> right
            if expr.op == "in":
                return left in right
            if expr.op == "not in":
                return left not in right
        except Exception:
            return _NO_STATIC_VALUE
        return _NO_STATIC_VALUE

    def _static_ConditionalExpr(self, expr: ConditionalExpr, env: TypeEnv) -> Any:
        condition = self._static_value(expr.condition, env)
        if condition is _NO_STATIC_VALUE:
            return _NO_STATIC_VALUE
        branch = expr.then_expr if condition else expr.else_expr
        return self._static_value(branch, env)

    def _static_IndexExpr(self, expr: IndexExpr, env: TypeEnv) -> Any:
        obj = self._static_value(expr.obj, env)
        index = self._static_value(expr.index, env)
        if obj is _NO_STATIC_VALUE or index is _NO_STATIC_VALUE:
            return _NO_STATIC_VALUE
        try:
            return obj[index]
        except Exception:
            return _NO_STATIC_VALUE

    def _require_bool(self, value_type: VakType, line: int, context: str) -> None:
        if value_type != ANY and not is_assignable(value_type, BOOL):
            raise CompileError(f"{context} के लिए बूल चाहिए, मिला {value_type}", line)

    def _base_type(self, value_type: VakType) -> VakType:
        while isinstance(value_type, RefinementType):
            value_type = value_type.base_type
        return value_type

    def _block_guarantees_exit(self, stmts: list[Any]) -> bool:
        for stmt in stmts:
            if self._stmt_guarantees_exit(stmt):
                return True
        return False

    def _stmt_guarantees_exit(self, stmt: Node) -> bool:
        if isinstance(stmt, (ReturnStmt, ThrowStmt)):
            return True
        if isinstance(stmt, Block):
            return self._block_guarantees_exit(stmt.stmts)
        if isinstance(stmt, IfStmt):
            branches = [stmt.then_body, *(body for _, body in stmt.elif_clauses)]
            return stmt.else_body is not None and all(
                self._block_guarantees_exit(branch.stmts)
                for branch in [*branches, stmt.else_body]
            )
        if isinstance(stmt, MatchStmt):
            return bool(getattr(stmt, "exhaustive", False)) and all(
                self._block_guarantees_exit(case.body.stmts)
                for case in stmt.cases
            )
        if isinstance(stmt, TryStmt):
            if stmt.finally_body is not None and self._block_guarantees_exit(stmt.finally_body.stmts):
                return True
            return bool(stmt.handlers) and self._block_guarantees_exit(stmt.try_body.stmts) and all(
                self._block_guarantees_exit(handler.body.stmts)
                for handler in stmt.handlers
            )
        return False

    def _destructure_types(self, value_type: VakType, count: int) -> list[VakType]:
        if isinstance(value_type, TupleType) and len(value_type.element_types) == count:
            return list(value_type.element_types)
        if isinstance(value_type, ListType):
            return [value_type.element_type] * count
        return [ANY] * count

    def _possible_match_coverage(self, subject_type: VakType) -> set[str] | None:
        if isinstance(subject_type, ResultType):
            return {"सिद्ध", "असिद्ध"}
        if subject_type == BOOL:
            return {"सत्य", "असत्य"}
        if subject_type == NULL:
            return {"शून्य"}
        if isinstance(subject_type, ADTType):
            data_info = self.data_types.get(subject_type.name)
            if data_info is None:
                return None
            return set(data_info.variants.keys())
        if isinstance(subject_type, VariantValueType):
            return {subject_type.variant_name}
        if isinstance(subject_type, UnionType):
            combined: set[str] = set()
            for option in subject_type.options:
                option_coverage = self._possible_match_coverage(option)
                if option_coverage is None:
                    return None
                combined.update(option_coverage)
            return combined
        return None

    def _pattern_coverage(self, pattern: Node, subject_type: VakType) -> str | None:
        if isinstance(pattern, (WildcardPattern, BindingPattern)):
            return "__all__"
        if isinstance(pattern, LiteralPattern):
            if pattern.value is True:
                return "सत्य"
            if pattern.value is False:
                return "असत्य"
            if pattern.value is None:
                return "शून्य"
            return None
        if isinstance(pattern, CallPattern):
            if self._field_types_for_call_pattern(pattern.callee, subject_type) is not None:
                return pattern.callee
        return None

    def _field_types_for_call_pattern(self, callee_name: str, subject_type: VakType) -> tuple[VakType, ...] | None:
        if callee_name == "सिद्ध" and isinstance(subject_type, ResultType):
            return (subject_type.ok_type,)
        if callee_name == "असिद्ध" and isinstance(subject_type, ResultType):
            return (subject_type.err_type,)
        if isinstance(subject_type, VariantValueType):
            if subject_type.variant_name == callee_name:
                return subject_type.field_types
            return None
        if isinstance(subject_type, ADTType):
            data_info = self.data_types.get(subject_type.name)
            if data_info is None or callee_name not in data_info.variants:
                return None
            bindings = {
                param: arg
                for param, arg in zip(data_info.type_params, subject_type.type_args)
            }
            variant = data_info.variants[callee_name]
            return tuple(instantiate_type(field_type, bindings) for field_type in variant.field_types)
        if isinstance(subject_type, UnionType):
            candidates = [
                self._field_types_for_call_pattern(callee_name, option)
                for option in subject_type.options
            ]
            candidates = [candidate for candidate in candidates if candidate is not None]
            if not candidates:
                return None
            if len({len(candidate) for candidate in candidates}) != 1:
                return None
            return tuple(
                combine_types(*(candidate[index] for candidate in candidates))
                for index in range(len(candidates[0]))
            )
        return None

    def _pattern_bindings(self, pattern: Node, subject_type: VakType) -> dict[str, VakType]:
        if isinstance(pattern, WildcardPattern):
            return {}
        if isinstance(pattern, BindingPattern):
            return {pattern.name: subject_type}
        if isinstance(pattern, LiteralPattern):
            return {}
        if isinstance(pattern, SequencePattern):
            bindings: dict[str, VakType] = {}
            element_type = iterable_element_type(subject_type)
            tuple_elements = subject_type.element_types if isinstance(subject_type, TupleType) else ()
            for index, element in enumerate(pattern.elements):
                current_type = tuple_elements[index] if index < len(tuple_elements) else element_type
                bindings.update(self._pattern_bindings(element, current_type))
            if pattern.rest_name and pattern.rest_name != "_":
                if pattern.kind == "tuple":
                    bindings[pattern.rest_name] = TupleType(tuple())
                else:
                    bindings[pattern.rest_name] = ListType(element_type)
            return bindings
        if isinstance(pattern, CallPattern):
            field_types = self._field_types_for_call_pattern(pattern.callee, subject_type)
            bindings: dict[str, VakType] = {}
            for index, arg in enumerate(pattern.args):
                current_type = field_types[index] if field_types is not None and index < len(field_types) else ANY
                bindings.update(self._pattern_bindings(arg, current_type))
            return bindings
        return {}

    def _infer_expr(self, expr: Any, env: TypeEnv) -> VakType:
        if expr is None:
            return NULL
        method = getattr(self, f"_infer_{type(expr).__name__}", None)
        if method is None:
            return ANY
        inferred = method(expr, env)
        setattr(expr, "inferred_type", inferred)
        return inferred

    def _infer_NumberLiteral(self, expr: NumberLiteral, env: TypeEnv) -> VakType:
        return FLOAT if isinstance(expr.value, float) else INT

    def _infer_StringLiteral(self, expr: StringLiteral, env: TypeEnv) -> VakType:
        return STR

    def _infer_FStringExpr(self, expr: FStringExpr, env: TypeEnv) -> VakType:
        for part in expr.parts:
            if not isinstance(part, str):
                self._infer_expr(part, env)
        return STR

    def _infer_BoolLiteral(self, expr: BoolLiteral, env: TypeEnv) -> VakType:
        return BOOL

    def _infer_NullLiteral(self, expr: NullLiteral, env: TypeEnv) -> VakType:
        return NULL

    def _infer_IdentifierExpr(self, expr: IdentifierExpr, env: TypeEnv) -> VakType:
        if expr.name in ("सत्य", "असत्य"):
            return BOOL
        symbol = env.lookup(expr.name)
        return symbol if symbol is not None else ANY

    def _infer_ListLiteral(self, expr: ListLiteral, env: TypeEnv) -> VakType:
        if not expr.elements:
            return ListType(ANY)
        return ListType(combine_types(*(self._infer_expr(item, env) for item in expr.elements)))

    def _infer_SetLiteral(self, expr: SetLiteral, env: TypeEnv) -> VakType:
        if not expr.elements:
            return SetType(ANY)
        return SetType(combine_types(*(self._infer_expr(item, env) for item in expr.elements)))

    def _infer_TupleLiteral(self, expr: TupleLiteral, env: TypeEnv) -> VakType:
        return TupleType(tuple(self._infer_expr(item, env) for item in expr.elements))

    def _infer_DictLiteral(self, expr: DictLiteral, env: TypeEnv) -> VakType:
        if not expr.pairs:
            return DictType(ANY, ANY)
        key_type = combine_types(*(self._infer_expr(key, env) for key, _ in expr.pairs))
        value_type = combine_types(*(self._infer_expr(value, env) for _, value in expr.pairs))
        return DictType(key_type, value_type)

    def _infer_ListComp(self, expr: ListComp, env: TypeEnv) -> VakType:
        loop_env = env.child()
        loop_env.define(expr.var_name, iterable_element_type(self._infer_expr(expr.iterable, env)))
        if expr.filter_expr is not None:
            self._require_bool(
                self._infer_expr(expr.filter_expr, loop_env),
                getattr(expr.filter_expr, "line", expr.line),
                "सूची comprehension filter",
            )
        return ListType(self._infer_expr(expr.expr, loop_env))

    def _infer_DictComp(self, expr: DictComp, env: TypeEnv) -> VakType:
        loop_env = env.child()
        loop_env.define(expr.var_name, iterable_element_type(self._infer_expr(expr.iterable, env)))
        if expr.filter_expr is not None:
            self._require_bool(
                self._infer_expr(expr.filter_expr, loop_env),
                getattr(expr.filter_expr, "line", expr.line),
                "शब्दकोश comprehension filter",
            )
        return DictType(
            self._infer_expr(expr.key_expr, loop_env),
            self._infer_expr(expr.value_expr, loop_env),
        )

    def _infer_IndexExpr(self, expr: IndexExpr, env: TypeEnv) -> VakType:
        obj_type = self._base_type(self._infer_expr(expr.obj, env))
        index_type = self._infer_expr(expr.index, env)
        if isinstance(obj_type, ListType):
            if index_type != ANY and not is_assignable(index_type, INT):
                raise CompileError(f"सूची अनुक्रमण के लिए संख्या चाहिए, मिला {index_type}", expr.line)
            return obj_type.element_type
        if isinstance(obj_type, SetType):
            return obj_type.element_type
        if isinstance(obj_type, TupleType):
            if index_type != ANY and not is_assignable(index_type, INT):
                raise CompileError(f"tuple अनुक्रमण के लिए संख्या चाहिए, मिला {index_type}", expr.line)
            return combine_types(*obj_type.element_types)
        if isinstance(obj_type, DictType):
            if index_type != ANY and not is_assignable(index_type, obj_type.key_type):
                raise CompileError(
                    f"शब्दकोश कुंजी को {obj_type.key_type} चाहिए, मिला {index_type}",
                    expr.line,
                )
            return obj_type.value_type
        if obj_type == STR:
            if index_type != ANY and not is_assignable(index_type, INT):
                raise CompileError(f"तार अनुक्रमण के लिए संख्या चाहिए, मिला {index_type}", expr.line)
            return STR
        return ANY

    def _infer_SliceExpr(self, expr: SliceExpr, env: TypeEnv) -> VakType:
        obj_type = self._base_type(self._infer_expr(expr.obj, env))
        for part in (expr.start, expr.stop, expr.step):
            if part is not None:
                self._infer_expr(part, env)
        if obj_type == STR:
            return STR
        if isinstance(obj_type, ListType | TupleType):
            return obj_type
        return ANY

    def _infer_MemberExpr(self, expr: MemberExpr, env: TypeEnv) -> VakType:
        obj_type = self._base_type(self._infer_expr(expr.obj, env))
        if isinstance(obj_type, ModuleType):
            return ANY
        if isinstance(obj_type, InstanceType):
            field_type = self.class_fields.get(obj_type.name, {}).get(expr.attr)
            if field_type is not None:
                return field_type
            methods = self.class_methods.get(obj_type.name, {})
            method = methods.get(expr.attr)
            if method is not None and method.param_types:
                return FunctionType(
                    method.param_types[1:],
                    method.return_type,
                    method.param_names[1:],
                    max(0, method.defaults_count - 1),
                    method.varargs_name,
                    method.is_async,
                )
        return ANY

    def _infer_UnaryExpr(self, expr: UnaryExpr, env: TypeEnv) -> VakType:
        operand = self._infer_expr(expr.operand, env)
        operand_base = self._base_type(operand)
        if expr.op in ("-", "+"):
            if operand_base != ANY and operand_base not in (INT, FLOAT):
                raise CompileError(f"एकपदीय '{expr.op}' को संख्या चाहिए, मिला {operand}", expr.line)
            return operand_base if operand_base != ANY else ANY
        if expr.op in ("न", "not"):
            return BOOL
        if expr.op == "~":
            if operand_base != ANY and operand_base != INT:
                raise CompileError(f"एकपदीय '~' को पूर्णांक चाहिए, मिला {operand}", expr.line)
            return INT
        return ANY

    def _infer_BinaryExpr(self, expr: BinaryExpr, env: TypeEnv) -> VakType:
        left = self._infer_expr(expr.left, env)
        right = self._infer_expr(expr.right, env)
        left_base = self._base_type(left)
        right_base = self._base_type(right)
        if expr.op in ("==", "!=", "<", "<=", ">", ">=", "in", "not in"):
            return BOOL
        if expr.op in ("और", "अथवा"):
            return BOOL if left_base == BOOL and right_base == BOOL else combine_types(left_base, right_base)
        if expr.op in ("+", "-", "*", "/", "//", "%", "**"):
            if expr.op == "+" and left_base == STR and right_base == STR:
                return STR
            if expr.op == "+" and isinstance(left_base, ListType) and isinstance(right_base, ListType):
                return ListType(combine_types(left_base.element_type, right_base.element_type))
            if left_base != ANY and right_base != ANY and left_base not in (INT, FLOAT) and right_base not in (INT, FLOAT):
                raise CompileError(f"'{expr.op}' संख्याओं पर चाहिए, मिला {left} और {right}", expr.line)
            if expr.op == "/":
                return FLOAT
            if left_base == FLOAT or right_base == FLOAT:
                return FLOAT
            return INT if left_base != ANY and right_base != ANY else ANY
        if expr.op in ("|", "&", "^", "<<", ">>"):
            if left_base != ANY and left_base != INT:
                raise CompileError(f"'{expr.op}' के लिए पूर्णांक चाहिए, मिला {left}", expr.line)
            if right_base != ANY and right_base != INT:
                raise CompileError(f"'{expr.op}' के लिए पूर्णांक चाहिए, मिला {right}", expr.line)
            return INT
        return ANY

    def _infer_ConditionalExpr(self, expr: ConditionalExpr, env: TypeEnv) -> VakType:
        self._require_bool(
            self._infer_expr(expr.condition, env),
            expr.line,
            "शर्तीय अभिव्यक्ति",
        )
        return combine_types(
            self._infer_expr(expr.then_expr, env),
            self._infer_expr(expr.else_expr, env),
        )

    def _infer_AssignExpr(self, expr: AssignExpr, env: TypeEnv) -> VakType:
        value_type = self._infer_expr(expr.value, env)
        static_value = self._static_value(expr.value, env)
        if isinstance(expr.target, IdentifierExpr):
            current = env.lookup(expr.target.name)
            if expr.op == "=" or expr.op == ":=":
                fixed = env.is_fixed(expr.target.name)
                if fixed and current is not None and current != ANY and not is_assignable(value_type, current):
                    raise CompileError(
                        f"'{expr.target.name}' को {current} चाहिए, मिला {value_type}",
                        expr.line,
                    )
                if fixed and current not in (None, ANY):
                    final_type = current
                elif current is None:
                    final_type = value_type
                else:
                    final_type = combine_types(current, value_type)
                self._require_refinement_constraint(
                    expr.value,
                    value_type,
                    final_type,
                    env,
                    expr.line,
                    f"'{expr.target.name}'",
                )
                env.assign(expr.target.name, final_type, static_value=static_value)
                return final_type
            if current not in (ANY, INT, FLOAT, STR, None):
                raise CompileError(
                    f"समिश्र नियोजन '{expr.op}' के लिए '{expr.target.name}' का उपयुक्त प्रकार नहीं है",
                    expr.line,
                )
            return self._infer_BinaryExpr(
                BinaryExpr(op=expr.op[:-1], left=expr.target, right=expr.value, line=expr.line),
                env,
            )
        if isinstance(expr.target, MemberExpr):
            return self._check_member_assignment(expr.target, expr.value, value_type, expr.line, env)
        if isinstance(expr.target, IndexExpr):
            return self._check_index_assignment(expr.target, expr.value, value_type, expr.line, env)
        return ANY

    def _check_member_assignment(
        self,
        target: MemberExpr,
        value_expr: Any,
        value_type: VakType,
        line: int,
        env: TypeEnv,
    ) -> VakType:
        obj_type = self._infer_expr(target.obj, env)
        if not isinstance(obj_type, InstanceType):
            return value_type

        known_fields = self.class_fields.setdefault(obj_type.name, {})
        known_type = known_fields.get(target.attr)
        current_fn = self._function_stack[-1] if self._function_stack else None
        is_self_init_assignment = (
            current_fn is not None
            and current_fn.owner_class == obj_type.name
            and current_fn.name == "__init__"
            and isinstance(target.obj, IdentifierExpr)
            and target.obj.name in ("स्वयं", "self")
        )

        if known_type is None and is_self_init_assignment:
            known_fields[target.attr] = value_type
            return value_type

        if known_type is not None and known_type != ANY and not is_assignable(value_type, known_type):
            raise CompileError(
                    f"सदस्य '{target.attr}' को {known_type} चाहिए, मिला {value_type}",
                    line,
                )

        target_type = known_type if known_type not in (None, ANY) else value_type
        self._require_refinement_constraint(
            value_expr,
            value_type,
            target_type,
            env,
            line,
            f"सदस्य '{target.attr}'",
        )
        return target_type

    def _check_index_assignment(
        self,
        target: IndexExpr,
        value_expr: Any,
        value_type: VakType,
        line: int,
        env: TypeEnv,
    ) -> VakType:
        obj_type = self._base_type(self._infer_expr(target.obj, env))
        index_type = self._infer_expr(target.index, env)

        if isinstance(obj_type, ListType):
            if index_type != ANY and not is_assignable(index_type, INT):
                raise CompileError(f"सूची अनुक्रमण के लिए संख्या चाहिए, मिला {index_type}", line)
            if obj_type.element_type != ANY and not is_assignable(value_type, obj_type.element_type):
                raise CompileError(
                    f"सूची तत्व को {obj_type.element_type} चाहिए, मिला {value_type}",
                    line,
                )
            target_type = obj_type.element_type if obj_type.element_type != ANY else value_type
            self._require_refinement_constraint(
                value_expr,
                value_type,
                target_type,
                env,
                line,
                "सूची तत्व",
            )
            return target_type

        if isinstance(obj_type, DictType):
            if index_type != ANY and not is_assignable(index_type, obj_type.key_type):
                raise CompileError(
                    f"शब्दकोश कुंजी को {obj_type.key_type} चाहिए, मिला {index_type}",
                    line,
                )
            if obj_type.value_type != ANY and not is_assignable(value_type, obj_type.value_type):
                raise CompileError(
                    f"शब्दकोश मान को {obj_type.value_type} चाहिए, मिला {value_type}",
                    line,
                )
            target_type = obj_type.value_type if obj_type.value_type != ANY else value_type
            self._require_refinement_constraint(
                value_expr,
                value_type,
                target_type,
                env,
                line,
                "शब्दकोश मान",
            )
            return target_type

        if isinstance(obj_type, TupleType):
            raise CompileError("tuple अपरिवर्तनीय है; अनुक्रमित नियोजन संभव नहीं", line)

        if obj_type == STR:
            raise CompileError("तार अपरिवर्तनीय है; अनुक्रमित नियोजन संभव नहीं", line)

        return value_type

    def _infer_CallExpr(self, expr: CallExpr, env: TypeEnv) -> VakType:
        callee_type = self._infer_expr(expr.callee, env)
        arg_types = [self._infer_expr(arg, env) for arg in expr.args]
        kwarg_types = {name: self._infer_expr(value, env) for name, value in expr.kwargs.items()}

        if isinstance(expr.callee, IdentifierExpr):
            if expr.callee.name in self.variant_constructors:
                return self._infer_variant_constructor_call(expr.callee.name, arg_types, kwarg_types, expr.line)
            builtin = self._infer_builtin_call(
                expr.callee.name,
                arg_types,
                kwarg_types,
                expr.line,
                arg_exprs=expr.args,
                kwarg_exprs=expr.kwargs,
                env=env,
            )
            if builtin is not None:
                return builtin

        if isinstance(callee_type, ClassType):
            return InstanceType(callee_type.name)

        if isinstance(callee_type, FunctionType):
            self._validate_function_call(
                callee_type,
                arg_types,
                kwarg_types,
                expr.line,
                arg_exprs=expr.args,
                kwarg_exprs=expr.kwargs,
                env=env,
            )
            return callee_type.return_type
        return ANY

    def _infer_variant_constructor_call(
        self,
        variant_name: str,
        arg_types: list[VakType],
        kwarg_types: dict[str, VakType],
        line: int,
    ) -> VakType:
        if kwarg_types:
            names = ", ".join(sorted(kwarg_types.keys()))
            raise CompileError(f"डेटा variant '{variant_name}' नामित तर्क स्वीकार नहीं करता: {names}", line)

        data_info, variant_info = self.variant_constructors[variant_name]
        if len(arg_types) != len(variant_info.field_types):
            raise CompileError(
                f"variant '{variant_name}' को {len(variant_info.field_types)} तर्क चाहिए, मिला {len(arg_types)}",
                line,
            )

        bindings: dict[str, VakType] = {}
        for actual, expected in zip(arg_types, variant_info.field_types):
            if not bind_typevars(expected, actual, bindings):
                raise CompileError(
                    f"variant '{variant_name}' के लिए {expected} अपेक्षित था, मिला {actual}",
                    line,
                )

        instantiated_fields = tuple(instantiate_type(field_type, bindings) for field_type in variant_info.field_types)
        type_args = tuple(bindings.get(param, ANY) for param in data_info.type_params)
        return VariantValueType(
            data_name=data_info.name,
            variant_name=variant_name,
            field_types=instantiated_fields,
            type_args=type_args,
        )

    def _infer_LambdaExpr(self, expr: LambdaExpr, env: TypeEnv) -> VakType:
        lambda_env = env.child()
        param_types: list[VakType] = []
        for param in expr.params:
            lambda_env.define(param, ANY)
            param_types.append(ANY)
        if expr.varargs:
            lambda_env.define(expr.varargs, ListType(ANY))
        return_type = self._infer_expr(expr.body, lambda_env)
        return FunctionType(tuple(param_types), return_type, tuple(expr.params), varargs_name=expr.varargs)

    def _infer_AwaitExpr(self, expr: AwaitExpr, env: TypeEnv) -> VakType:
        return self._infer_expr(expr.operand, env)

    def _infer_builtin_call(
        self,
        name: str,
        arg_types: list[VakType],
        kwarg_types: dict[str, VakType],
        line: int,
        *,
        arg_exprs: list[Any] | None = None,
        kwarg_exprs: dict[str, Any] | None = None,
        env: TypeEnv | None = None,
    ) -> VakType | None:
        if name in ("सिद्ध", "असिद्ध"):
            inner = arg_types[0] if arg_types else ANY
            return ResultType(inner, ANY) if name == "सिद्ध" else ResultType(ANY, inner)
        if name == "फल_खोलो":
            if arg_types and isinstance(arg_types[0], ResultType):
                return arg_types[0].ok_type
            return ANY
        if name == "फल_त्रुटि":
            if arg_types and isinstance(arg_types[0], ResultType):
                return arg_types[0].err_type
            return ANY
        if name in ("फल_सफल_है", "फल_विफल_है", "isinstance", "hasattr", "all", "any", "callable"):
            return BOOL
        if name in ("पाठ_कर", "str", "प्रकार", "type", "chr"):
            return STR
        if name in ("संख्या", "int", "ord", "दीर्घता", "len", "पूर्णांक_कर"):
            return INT
        if name in ("दशमलव", "float", "round", "वर्गमूल", "परम"):
            return FLOAT
        if name in ("परास", "range"):
            return RANGE
        if name in ("list",):
            if arg_types:
                return ListType(iterable_element_type(arg_types[0]))
            return ListType(ANY)
        if name in ("set",):
            if arg_types:
                return SetType(iterable_element_type(arg_types[0]))
            return SetType(ANY)
        if name in ("dict",):
            return DictType(ANY, ANY)
        if name in ("enumerate",):
            inner = iterable_element_type(arg_types[0]) if arg_types else ANY
            return ListType(TupleType((INT, inner)))
        if name in ("zip",):
            zipped = tuple(iterable_element_type(arg) for arg in arg_types) or (ANY,)
            return ListType(TupleType(zipped))
        if name in ("map",):
            if len(arg_types) >= 2:
                func_type = arg_types[0]
                iterable_type = arg_types[1]
                if isinstance(func_type, FunctionType):
                    return ListType(func_type.return_type)
                return ListType(iterable_element_type(iterable_type))
            return ListType(ANY)
        if name in ("filter",):
            if len(arg_types) >= 2:
                return ListType(iterable_element_type(arg_types[1]))
            return ListType(ANY)
        if name in ("sorted", "क्रमबद्ध"):
            if arg_types:
                base = arg_types[0]
                if isinstance(base, ListType):
                    return base
                return ListType(iterable_element_type(base))
            return ListType(ANY)
        if name in ("sum", "योग", "min", "न्यूनतम", "max", "अधिकतम"):
            if arg_types:
                return iterable_element_type(arg_types[0])
            return ANY
        if name in ("मुद्रय", "print"):
            return NULL
        builtin_type = self.globals.lookup(name)
        if isinstance(builtin_type, FunctionType):
            self._validate_function_call(
                builtin_type,
                arg_types,
                kwarg_types,
                line,
                arg_exprs=arg_exprs,
                kwarg_exprs=kwarg_exprs,
                env=env,
            )
            return builtin_type.return_type
        return None

    def _validate_function_call(
        self,
        signature: FunctionType,
        arg_types: list[VakType],
        kwarg_types: dict[str, VakType],
        line: int,
        *,
        arg_exprs: list[Any] | None = None,
        kwarg_exprs: dict[str, Any] | None = None,
        env: TypeEnv | None = None,
    ) -> None:
        arg_exprs = [] if arg_exprs is None else arg_exprs
        kwarg_exprs = {} if kwarg_exprs is None else kwarg_exprs
        max_args = signature.max_args
        if max_args is not None and len(arg_types) > max_args:
            raise CompileError(
                f"अधिक तर्क: अधिकतम {max_args}, मिला {len(arg_types)}",
                line,
            )
        provided_named = set(kwarg_types.keys())
        unknown_kwargs = provided_named - set(signature.param_names)
        if unknown_kwargs:
            names = ", ".join(sorted(unknown_kwargs))
            raise CompileError(f"अज्ञात नामित तर्क: {names}", line)
        positional_names = set(signature.param_names[:min(len(arg_types), len(signature.param_names))])
        duplicate_args = positional_names & provided_named
        if duplicate_args:
            names = ", ".join(sorted(duplicate_args))
            raise CompileError(f"तर्क बार-बार दिया गया: {names}", line)

        required = signature.min_args
        provided_total = len(arg_types) + len(kwarg_types)
        if signature.varargs_name is None and provided_total < required:
            raise CompileError(
                f"अपर्याप्त तर्क: कम से कम {required}, मिला {provided_total}",
                line,
            )

        for index, arg_type in enumerate(arg_types):
            if index >= len(signature.param_types):
                break
            expected = signature.param_types[index]
            param_name = signature.param_names[index] if index < len(signature.param_names) else f"arg{index + 1}"
            if expected != ANY and not is_assignable(arg_type, expected):
                raise CompileError(
                    f"तर्क '{param_name}' को {expected} चाहिए, मिला {arg_type}",
                    line,
                )
            if env is not None and index < len(arg_exprs):
                self._require_refinement_constraint(
                    arg_exprs[index],
                    arg_type,
                    expected,
                    env,
                    getattr(arg_exprs[index], "line", line),
                    f"तर्क '{param_name}'",
                )

        for name, arg_type in kwarg_types.items():
            if name not in signature.param_names:
                continue
            index = signature.param_names.index(name)
            expected = signature.param_types[index]
            if expected != ANY and not is_assignable(arg_type, expected):
                raise CompileError(
                    f"तर्क '{name}' को {expected} चाहिए, मिला {arg_type}",
                    line,
                )
            if env is not None and name in kwarg_exprs:
                kw_expr = kwarg_exprs[name]
                self._require_refinement_constraint(
                    kw_expr,
                    arg_type,
                    expected,
                    env,
                    getattr(kw_expr, "line", line),
                    f"तर्क '{name}'",
                )
