from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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


@dataclass
class FunctionContext:
    name: str
    declared_return: VakType
    observed_return: VakType = NEVER


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

    def define(self, name: str, value_type: VakType, *, fixed: bool = False) -> None:
        self.values[name] = value_type
        if fixed:
            self.fixed_names.add(name)
        else:
            self.fixed_names.discard(name)

    def lookup(self, name: str) -> VakType | None:
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.lookup(name)
        return None

    def assign(self, name: str, value_type: VakType) -> None:
        if name in self.values:
            self.values[name] = value_type
            return
        if self.parent is not None and self.parent.lookup(name) is not None:
            self.parent.assign(name, value_type)
            return
        self.values[name] = value_type

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
        self.data_types: dict[str, DataInfo] = {}
        self.variant_constructors: dict[str, tuple[DataInfo, DataVariantInfo]] = {}
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
            final_type = declared_type if declared_type != ANY else value_type
            if len(stmt.names) == 1:
                env.define(stmt.names[0], final_type, fixed=declared_type != ANY)
            else:
                element_types = self._destructure_types(final_type, len(stmt.names))
                for name, element_type in zip(stmt.names, element_types):
                    env.define(name, element_type, fixed=declared_type != ANY)
            return

        if isinstance(stmt, ConstDecl):
            value_type = self._infer_expr(stmt.value, env)
            declared_type = parse_type_hint(stmt.type_hint)
            if declared_type != ANY and not is_assignable(value_type, declared_type):
                raise CompileError(
                    f"स्थिर '{stmt.name}' को {declared_type} चाहिए, मिला {value_type}",
                    stmt.line,
                )
            env.define(stmt.name, declared_type if declared_type != ANY else value_type, fixed=True)
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
            fn_ctx.observed_return = combine_types(fn_ctx.observed_return, value_type)
            return

        if isinstance(stmt, IfStmt):
            self._infer_expr(stmt.condition, env)
            self._check_block(stmt.then_body.stmts, env.child(), fn_ctx)
            for cond, body in stmt.elif_clauses:
                self._infer_expr(cond, env)
                self._check_block(body.stmts, env.child(), fn_ctx)
            if stmt.else_body:
                self._check_block(stmt.else_body.stmts, env.child(), fn_ctx)
            return

        if isinstance(stmt, WhileStmt):
            self._infer_expr(stmt.condition, env)
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
                    self._infer_expr(case.guard, case_env)
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
                with_env.define(stmt.var_name, expr_type)
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
        for stmt in node.body.stmts:
            if isinstance(stmt, FuncDecl):
                self._check_function(stmt, class_env, class_name=node.name)

    def _check_function(self, node: FuncDecl, env: TypeEnv, class_name: str | None = None) -> None:
        signature = self._signature_from_func(node, class_name=class_name)
        fn_env = env.child()
        for name, value_type in zip(signature.param_names, signature.param_types):
            fn_env.define(name, value_type, fixed=True)
        if node.varargs:
            fn_env.define(node.varargs, ListType(ANY), fixed=True)
        fn_ctx = FunctionContext(
            name=node.name,
            declared_return=signature.return_type,
        )
        self._check_block(node.body.stmts, fn_env, fn_ctx)
        final_return = signature.return_type if signature.return_type != ANY else (
            fn_ctx.observed_return if fn_ctx.observed_return != NEVER else NULL
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
            self._infer_expr(expr.filter_expr, loop_env)
        return ListType(self._infer_expr(expr.expr, loop_env))

    def _infer_DictComp(self, expr: DictComp, env: TypeEnv) -> VakType:
        loop_env = env.child()
        loop_env.define(expr.var_name, iterable_element_type(self._infer_expr(expr.iterable, env)))
        if expr.filter_expr is not None:
            self._infer_expr(expr.filter_expr, loop_env)
        return DictType(
            self._infer_expr(expr.key_expr, loop_env),
            self._infer_expr(expr.value_expr, loop_env),
        )

    def _infer_IndexExpr(self, expr: IndexExpr, env: TypeEnv) -> VakType:
        obj_type = self._infer_expr(expr.obj, env)
        self._infer_expr(expr.index, env)
        if isinstance(obj_type, ListType):
            return obj_type.element_type
        if isinstance(obj_type, SetType):
            return obj_type.element_type
        if isinstance(obj_type, TupleType):
            return combine_types(*obj_type.element_types)
        if isinstance(obj_type, DictType):
            return obj_type.value_type
        if obj_type == STR:
            return STR
        return ANY

    def _infer_SliceExpr(self, expr: SliceExpr, env: TypeEnv) -> VakType:
        obj_type = self._infer_expr(expr.obj, env)
        for part in (expr.start, expr.stop, expr.step):
            if part is not None:
                self._infer_expr(part, env)
        if obj_type == STR:
            return STR
        if isinstance(obj_type, ListType | TupleType):
            return obj_type
        return ANY

    def _infer_MemberExpr(self, expr: MemberExpr, env: TypeEnv) -> VakType:
        obj_type = self._infer_expr(expr.obj, env)
        if isinstance(obj_type, ModuleType):
            return ANY
        if isinstance(obj_type, InstanceType):
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
        if expr.op in ("-", "+"):
            if operand != ANY and operand not in (INT, FLOAT):
                raise CompileError(f"एकपदीय '{expr.op}' को संख्या चाहिए, मिला {operand}", expr.line)
            return operand if operand != ANY else ANY
        if expr.op in ("न", "not"):
            return BOOL
        if expr.op == "~":
            if operand != ANY and operand != INT:
                raise CompileError(f"एकपदीय '~' को पूर्णांक चाहिए, मिला {operand}", expr.line)
            return INT
        return ANY

    def _infer_BinaryExpr(self, expr: BinaryExpr, env: TypeEnv) -> VakType:
        left = self._infer_expr(expr.left, env)
        right = self._infer_expr(expr.right, env)
        if expr.op in ("==", "!=", "<", "<=", ">", ">=", "in", "not in"):
            return BOOL
        if expr.op in ("और", "अथवा"):
            return BOOL if left == BOOL and right == BOOL else combine_types(left, right)
        if expr.op in ("+", "-", "*", "/", "//", "%", "**"):
            if expr.op == "+" and left == STR and right == STR:
                return STR
            if expr.op == "+" and isinstance(left, ListType) and isinstance(right, ListType):
                return ListType(combine_types(left.element_type, right.element_type))
            if left != ANY and right != ANY and left not in (INT, FLOAT) and right not in (INT, FLOAT):
                raise CompileError(f"'{expr.op}' संख्याओं पर चाहिए, मिला {left} और {right}", expr.line)
            if expr.op == "/":
                return FLOAT
            if left == FLOAT or right == FLOAT:
                return FLOAT
            return INT if left != ANY and right != ANY else ANY
        if expr.op in ("|", "&", "^", "<<", ">>"):
            if left != ANY and left != INT:
                raise CompileError(f"'{expr.op}' के लिए पूर्णांक चाहिए, मिला {left}", expr.line)
            if right != ANY and right != INT:
                raise CompileError(f"'{expr.op}' के लिए पूर्णांक चाहिए, मिला {right}", expr.line)
            return INT
        return ANY

    def _infer_ConditionalExpr(self, expr: ConditionalExpr, env: TypeEnv) -> VakType:
        self._infer_expr(expr.condition, env)
        return combine_types(
            self._infer_expr(expr.then_expr, env),
            self._infer_expr(expr.else_expr, env),
        )

    def _infer_AssignExpr(self, expr: AssignExpr, env: TypeEnv) -> VakType:
        value_type = self._infer_expr(expr.value, env)
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
                env.assign(expr.target.name, final_type)
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
        if isinstance(expr.target, (MemberExpr, IndexExpr)):
            return value_type
        return ANY

    def _infer_CallExpr(self, expr: CallExpr, env: TypeEnv) -> VakType:
        callee_type = self._infer_expr(expr.callee, env)
        arg_types = [self._infer_expr(arg, env) for arg in expr.args]
        kwarg_types = {name: self._infer_expr(value, env) for name, value in expr.kwargs.items()}

        if isinstance(expr.callee, IdentifierExpr):
            if expr.callee.name in self.variant_constructors:
                return self._infer_variant_constructor_call(expr.callee.name, arg_types, kwarg_types, expr.line)
            builtin = self._infer_builtin_call(expr.callee.name, arg_types, kwarg_types, expr.line)
            if builtin is not None:
                return builtin

        if isinstance(callee_type, ClassType):
            return InstanceType(callee_type.name)

        if isinstance(callee_type, FunctionType):
            self._validate_function_call(callee_type, arg_types, kwarg_types, expr.line)
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
            self._validate_function_call(builtin_type, arg_types, kwarg_types, line)
            return builtin_type.return_type
        return None

    def _validate_function_call(
        self,
        signature: FunctionType,
        arg_types: list[VakType],
        kwarg_types: dict[str, VakType],
        line: int,
    ) -> None:
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
            if expected != ANY and not is_assignable(arg_type, expected):
                param_name = signature.param_names[index] if index < len(signature.param_names) else f"arg{index + 1}"
                raise CompileError(
                    f"तर्क '{param_name}' को {expected} चाहिए, मिला {arg_type}",
                    line,
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
