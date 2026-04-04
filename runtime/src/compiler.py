# वाक् भाषा - संकलक (Compiler)
# Vak Language - AST to Bytecode Compiler

from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any, Optional
from .bytecode import Bytecode, NO_DEFAULT
from .opcodes import OpCode
from .runtime_catalog import compiled_builtin_index
from .ast_nodes import *
from .errors import CompileError


@dataclass
class FunctionScopeInfo:
    local_names: set[str] = field(default_factory=set)
    global_names: set[str] = field(default_factory=set)
    nonlocal_names: set[str] = field(default_factory=set)
    used_names: set[str] = field(default_factory=set)
    closure_names: set[str] = field(default_factory=set)


RETURN_TYPE_HINT_KEY = "__return__"


class Compiler:
    """
    Compiles VakyaLang AST into bytecode.

    Single-pass compiler with jump patching.
    Maintains variable scope and constant pool.

    Compilation phases:
    1. Macro Expansion (सूत्र विस्तार) - Expand compile-time macros
    2. Constant Folding (स्थिर गुड़न) - Optimize constant expressions
    3. Dead Code Elimination (मृत कोड उन्मूलन) - Prune unreachable AST paths
    4. Bytecode Generation - Convert optimized AST to bytecode
    """

    def __init__(
        self,
        optimize: bool = True,
        enclosing_function_scopes: Optional[list[set[str]]] = None,
        known_parinama_names: Optional[set[str]] = None,
        branch_runtime: Optional[Any] = None,
        source_path: str | None = None,
    ):
        self.bytecode = Bytecode()
        self.loop_stack = []  # For break/continue
        self.optimize = optimize  # Enable/disable optimizations
        self.enclosing_function_scopes = [
            set(scope) for scope in (enclosing_function_scopes or [])
        ]
        self.known_parinama_names = set(known_parinama_names or set())
        self.scope_info: Optional[FunctionScopeInfo] = None
        self.branch_runtime = branch_runtime
        self.source_path = source_path

    def compile(self, node: Node) -> Bytecode:
        """
        Compile AST node to bytecode.

        Phases:
        1. MACRO EXPANSION: Expand all सूत्र (macros) before bytecode generation
        2. CONSTANT FOLDING: Optimize constant expressions at compile-time
        3. DEAD CODE ELIMINATION: Remove unreachable AST statements safely
        4. BYTECODE GENERATION: Convert optimized AST to bytecode
        """
        import math

        if isinstance(node, Program) and self.branch_runtime is not None:
            self.branch_runtime.before_compile(
                node,
                filename=self.source_path,
                compiler=self,
            )

        # ─────────────────────────────────────────────────────────────────────
        # PHASE 1: MACRO EXPANSION (सूत्र विस्तार)
        # ─────────────────────────────────────────────────────────────────────
        # Expand all macros BEFORE bytecode generation
        # This is compile-time transformation - no runtime overhead
        if isinstance(node, Program):
            from .macro_expander import MacroExpander
            expander = MacroExpander()
            node = expander.expand(node)

        # Freeze lexical scope information before any optimization rewrites.
        # Assignment-based scope rules must reflect the original source, not an
        # optimized AST with dead branches removed.
        self._prepare_scope_metadata(node)

        # ─────────────────────────────────────────────────────────────────────
        # PHASE 2: CONSTANT FOLDING (स्थिर गुड़न) - Optional optimization
        # ─────────────────────────────────────────────────────────────────────
        if self.optimize:
            node = self._constant_fold(node)

        # ─────────────────────────────────────────────────────────────────────
        # PHASE 2.75: DEAD CODE ELIMINATION (मृत कोड उन्मूलन)
        # ─────────────────────────────────────────────────────────────────────
        if self.optimize:
            node = self._eliminate_dead_code(node)

        # ─────────────────────────────────────────────────────────────────────
        # PHASE 2.5: TYPE CHECKING (प्रकार परीक्षण)
        # ─────────────────────────────────────────────────────────────────────
        if isinstance(node, Program):
            from .type_checker import TypeChecker
            TypeChecker().check(node)
            if self.branch_runtime is not None:
                self.branch_runtime.after_typecheck(
                    node,
                    filename=self.source_path,
                    compiler=self,
                )

        # ─────────────────────────────────────────────────────────────────────
        # PHASE 3: BYTECODE GENERATION
        # ─────────────────────────────────────────────────────────────────────

        # Inject PI constant
        pi_idx = self.bytecode.add_constant(math.pi)
        self.bytecode.emit_16bit(OpCode.LOAD_CONST, pi_idx)
        pi_slot = self.bytecode.get_var_slot('पाई')
        self.bytecode.emit(OpCode.STORE_VAR, pi_slot)

        self._compile_node(node)
        self.bytecode.emit(OpCode.HALT)

        if self.branch_runtime is not None:
            self.branch_runtime.after_compile(
                self.bytecode,
                filename=self.source_path,
                compiler=self,
            )

        return self.bytecode

    def _compile_node(self, node: Node):
        """Dispatch to appropriate compile method."""
        method_name = f'_compile_{type(node).__name__}'
        method = getattr(self, method_name, self._compile_generic)
        method(node)

    def _compile_generic(self, node: Node):
        """Fallback for unhandled nodes."""
        raise CompileError(f"Cannot compile {type(node).__name__}", node.line)

    def _direct_parinama_names(self, stmts: list[Any]) -> set[str]:
        return {
            stmt.name
            for stmt in stmts
            if isinstance(stmt, ParinamaDecl)
        }

    def _compile_stmt_sequence(self, stmts: list[Any]) -> None:
        previous_names = set(self.known_parinama_names)
        self.known_parinama_names = previous_names | self._direct_parinama_names(stmts)
        try:
            for stmt in stmts:
                self._compile_node(stmt)
        finally:
            self.known_parinama_names = previous_names

    def _encode_runtime_term_spec(self, node: Node) -> dict[str, Any]:
        from .rewrite_engine import encode_rewrite_node

        try:
            return encode_rewrite_node(node)
        except TypeError as exc:
            raise CompileError(
                f"पारिणाम runtime term does not support {type(node).__name__}: {exc}",
                getattr(node, "line", 0),
            ) from exc

    def _emit_term_builder(self, node: Node) -> None:
        spec_idx = self.bytecode.add_constant(self._encode_runtime_term_spec(node))
        builder_slot = self.bytecode.get_var_slot("__build_term__")
        self.bytecode.emit(OpCode.LOAD_VAR, builder_slot)
        self.bytecode.emit_16bit(OpCode.LOAD_CONST, spec_idx)
        self.bytecode.emit(OpCode.CALL, 1)

    def _copy_dynamic_node_attrs(self, source: Node, target: Node) -> Node:
        """Preserve compiler metadata attached outside dataclass fields."""
        target_fields = set(getattr(target, "__dataclass_fields__", {}).keys())
        for key, value in getattr(source, "__dict__", {}).items():
            if key not in target_fields:
                setattr(target, key, value)
        return target

    def _iter_child_nodes(self, value: Any):
        if isinstance(value, Node):
            yield value
            return
        if isinstance(value, list):
            for item in value:
                yield from self._iter_child_nodes(item)
            return
        if isinstance(value, tuple):
            for item in value:
                yield from self._iter_child_nodes(item)
            return
        if isinstance(value, dict):
            for item in value.values():
                yield from self._iter_child_nodes(item)

    def _prepare_scope_metadata(
        self,
        node: Node | None,
        enclosing_scopes: Optional[list[set[str]]] = None,
    ) -> None:
        if node is None:
            return

        scope_chain = [
            set(scope)
            for scope in (
                self.enclosing_function_scopes
                if enclosing_scopes is None
                else enclosing_scopes
            )
        ]

        if isinstance(node, FuncDecl):
            scope_info = self._analyze_function_scope(
                node.body,
                node.params,
                node.varargs,
                node.line,
                enclosing_scopes=scope_chain,
            )
            setattr(node, "_scope_info", scope_info)

            for default in node.defaults:
                self._prepare_scope_metadata(default, scope_chain)

            for param in node.params:
                if isinstance(param, VibhaktiParam):
                    self._prepare_scope_metadata(param.default, scope_chain)

            self._prepare_scope_metadata(
                node.body,
                scope_chain + [set(scope_info.local_names)],
            )
            return

        if isinstance(node, LambdaExpr):
            scope_info = self._analyze_function_scope(
                node.body,
                node.params,
                node.varargs,
                node.line,
                enclosing_scopes=scope_chain,
            )
            setattr(node, "_scope_info", scope_info)
            self._prepare_scope_metadata(
                node.body,
                scope_chain + [set(scope_info.local_names)],
            )
            return

        if not is_dataclass(node):
            return

        for field_info in fields(node):
            for child in self._iter_child_nodes(getattr(node, field_info.name)):
                self._prepare_scope_metadata(child, scope_chain)

    def _record_local_binding(
        self,
        name: str,
        node: Node,
        bindings: set[str],
        global_names: set[str],
        nonlocal_names: set[str],
        *,
        declaration: bool,
    ) -> None:
        if name in global_names:
            if declaration:
                raise CompileError(
                    f"नाम '{name}' वैश्विक घोषित है; इसे स्थानीय रूप से बाधित नहीं किया जा सकता",
                    node.line,
                )
            return
        if name in nonlocal_names:
            if declaration:
                raise CompileError(
                    f"नाम '{name}' अस्थानिक घोषित है; इसे स्थानीय रूप से बाधित नहीं किया जा सकता",
                    node.line,
                )
            return
        bindings.add(name)

    def _collect_scope_directives(
        self,
        node: Node | None,
        global_names: set[str],
        nonlocal_names: set[str],
    ) -> None:
        if node is None:
            return

        if isinstance(node, GlobalStmt):
            global_names.update(node.names)
            return

        if isinstance(node, NonlocalStmt):
            nonlocal_names.update(node.names)
            return

        if isinstance(node, (FuncDecl, LambdaExpr, ClassDecl, DataDecl, SutraDecl, ParinamaDecl)):
            return

        if isinstance(node, Program):
            for stmt in node.body:
                self._collect_scope_directives(stmt, global_names, nonlocal_names)
            return

        if isinstance(node, Block):
            for stmt in node.stmts:
                self._collect_scope_directives(stmt, global_names, nonlocal_names)
            return

        if isinstance(node, IfStmt):
            self._collect_scope_directives(node.then_body, global_names, nonlocal_names)
            for _, body in node.elif_clauses:
                self._collect_scope_directives(body, global_names, nonlocal_names)
            self._collect_scope_directives(node.else_body, global_names, nonlocal_names)
            return

        if isinstance(node, (WhileStmt, ForStmt, WithStmt)):
            self._collect_scope_directives(node.body, global_names, nonlocal_names)
            return

        if isinstance(node, TryStmt):
            self._collect_scope_directives(node.try_body, global_names, nonlocal_names)
            for handler in node.handlers:
                self._collect_scope_directives(handler.body, global_names, nonlocal_names)
            self._collect_scope_directives(node.finally_body, global_names, nonlocal_names)
            return

        if isinstance(node, MatchStmt):
            for case in node.cases:
                self._collect_scope_directives(case.body, global_names, nonlocal_names)
            return

    def _collect_bound_names(
        self,
        node: Node | None,
        bindings: set[str],
        global_names: set[str],
        nonlocal_names: set[str],
    ) -> None:
        if node is None:
            return

        if isinstance(node, Program):
            for stmt in node.body:
                self._collect_bound_names(stmt, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, Block):
            for stmt in node.stmts:
                self._collect_bound_names(stmt, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, VarDecl):
            for name in node.names:
                self._record_local_binding(
                    name,
                    node,
                    bindings,
                    global_names,
                    nonlocal_names,
                    declaration=True,
                )
            self._collect_bound_names(node.value, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, ConstDecl):
            self._record_local_binding(
                node.name,
                node,
                bindings,
                global_names,
                nonlocal_names,
                declaration=True,
            )
            self._collect_bound_names(node.value, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, FuncDecl):
            self._record_local_binding(
                node.name,
                node,
                bindings,
                global_names,
                nonlocal_names,
                declaration=True,
            )
            for default in node.defaults:
                self._collect_bound_names(default, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, ClassDecl):
            self._record_local_binding(
                node.name,
                node,
                bindings,
                global_names,
                nonlocal_names,
                declaration=True,
            )
            self._collect_bound_names(node.superclass, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, DataDecl):
            self._record_local_binding(
                node.name,
                node,
                bindings,
                global_names,
                nonlocal_names,
                declaration=True,
            )
            for variant in node.variants:
                self._record_local_binding(
                    variant.name,
                    variant,
                    bindings,
                    global_names,
                    nonlocal_names,
                    declaration=True,
                )
            return

        if isinstance(node, ParinamaDecl):
            self._record_local_binding(
                node.name,
                node,
                bindings,
                global_names,
                nonlocal_names,
                declaration=True,
            )
            return

        if isinstance(node, ImportStmt):
            if node.names:
                for name in node.names:
                    self._record_local_binding(
                        name,
                        node,
                        bindings,
                        global_names,
                        nonlocal_names,
                        declaration=True,
                    )
            else:
                self._record_local_binding(
                    node.module.split('.')[-1],
                    node,
                    bindings,
                    global_names,
                    nonlocal_names,
                    declaration=True,
                )
            return

        if isinstance(node, ForStmt):
            for var_name in node.var_names:
                self._record_local_binding(
                    var_name,
                    node,
                    bindings,
                    global_names,
                    nonlocal_names,
                    declaration=True,
                )
            self._collect_bound_names(node.iterable, bindings, global_names, nonlocal_names)
            self._collect_bound_names(node.body, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, WithStmt):
            if node.var_name:
                self._record_local_binding(
                    node.var_name,
                    node,
                    bindings,
                    global_names,
                    nonlocal_names,
                    declaration=True,
                )
            self._collect_bound_names(node.expr, bindings, global_names, nonlocal_names)
            self._collect_bound_names(node.body, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, TryStmt):
            self._collect_bound_names(node.try_body, bindings, global_names, nonlocal_names)
            for handler in node.handlers:
                if handler.bind_name:
                    self._record_local_binding(
                        handler.bind_name,
                        handler,
                        bindings,
                        global_names,
                        nonlocal_names,
                        declaration=True,
                    )
                self._collect_bound_names(handler.body, bindings, global_names, nonlocal_names)
            self._collect_bound_names(node.finally_body, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, MatchStmt):
            self._collect_bound_names(node.subject, bindings, global_names, nonlocal_names)
            for case in node.cases:
                for name in self._pattern_binding_names(case.pattern):
                    self._record_local_binding(
                        name,
                        case,
                        bindings,
                        global_names,
                        nonlocal_names,
                        declaration=True,
                    )
                self._collect_bound_names(case.guard, bindings, global_names, nonlocal_names)
                self._collect_bound_names(case.body, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, ExprStmt):
            self._collect_bound_names(node.expr, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, AssignExpr):
            if isinstance(node.target, IdentifierExpr):
                self._record_local_binding(
                    node.target.name,
                    node,
                    bindings,
                    global_names,
                    nonlocal_names,
                    declaration=False,
                )
            self._collect_bound_names(node.value, bindings, global_names, nonlocal_names)
            if isinstance(node.target, (IndexExpr, MemberExpr)):
                self._collect_bound_names(node.target, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, IfStmt):
            self._collect_bound_names(node.condition, bindings, global_names, nonlocal_names)
            self._collect_bound_names(node.then_body, bindings, global_names, nonlocal_names)
            for cond, body in node.elif_clauses:
                self._collect_bound_names(cond, bindings, global_names, nonlocal_names)
                self._collect_bound_names(body, bindings, global_names, nonlocal_names)
            self._collect_bound_names(node.else_body, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, WhileStmt):
            self._collect_bound_names(node.condition, bindings, global_names, nonlocal_names)
            self._collect_bound_names(node.body, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, PrintStmt):
            for value in node.values:
                self._collect_bound_names(value, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, ReturnStmt):
            self._collect_bound_names(node.value, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, ThrowStmt):
            self._collect_bound_names(node.value, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, CallExpr):
            self._collect_bound_names(node.callee, bindings, global_names, nonlocal_names)
            for arg in node.args:
                self._collect_bound_names(arg, bindings, global_names, nonlocal_names)
            for value in node.kwargs.values():
                self._collect_bound_names(value, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, (BinaryExpr, ConditionalExpr)):
            self._collect_bound_names(node.left if isinstance(node, BinaryExpr) else node.condition, bindings, global_names, nonlocal_names)
            self._collect_bound_names(node.right if isinstance(node, BinaryExpr) else node.then_expr, bindings, global_names, nonlocal_names)
            if isinstance(node, ConditionalExpr):
                self._collect_bound_names(node.else_expr, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, UnaryExpr):
            self._collect_bound_names(node.operand, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, MemberExpr):
            self._collect_bound_names(node.obj, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, IndexExpr):
            self._collect_bound_names(node.obj, bindings, global_names, nonlocal_names)
            self._collect_bound_names(node.index, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, SliceExpr):
            self._collect_bound_names(node.obj, bindings, global_names, nonlocal_names)
            self._collect_bound_names(node.start, bindings, global_names, nonlocal_names)
            self._collect_bound_names(node.stop, bindings, global_names, nonlocal_names)
            self._collect_bound_names(node.step, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, ListLiteral):
            for element in node.elements:
                self._collect_bound_names(element, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, TupleLiteral):
            for element in node.elements:
                self._collect_bound_names(element, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, SetLiteral):
            for element in node.elements:
                self._collect_bound_names(element, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, DictLiteral):
            for key, value in node.pairs:
                self._collect_bound_names(key, bindings, global_names, nonlocal_names)
                self._collect_bound_names(value, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, ListComp):
            self._record_local_binding(
                node.var_name,
                node,
                bindings,
                global_names,
                nonlocal_names,
                declaration=True,
            )
            self._collect_bound_names(node.iterable, bindings, global_names, nonlocal_names)
            self._collect_bound_names(node.filter_expr, bindings, global_names, nonlocal_names)
            self._collect_bound_names(node.expr, bindings, global_names, nonlocal_names)
            return

        if isinstance(node, DictComp):
            self._record_local_binding(
                node.var_name,
                node,
                bindings,
                global_names,
                nonlocal_names,
                declaration=True,
            )
            self._collect_bound_names(node.iterable, bindings, global_names, nonlocal_names)
            self._collect_bound_names(node.filter_expr, bindings, global_names, nonlocal_names)
            self._collect_bound_names(node.key_expr, bindings, global_names, nonlocal_names)
            self._collect_bound_names(node.value_expr, bindings, global_names, nonlocal_names)
            return

    def _collect_used_names(self, node: Node | None, used_names: set[str]) -> None:
        if node is None:
            return

        if isinstance(node, IdentifierExpr):
            used_names.add(node.name)
            return

        if isinstance(node, Program):
            for stmt in node.body:
                self._collect_used_names(stmt, used_names)
            return

        if isinstance(node, Block):
            for stmt in node.stmts:
                self._collect_used_names(stmt, used_names)
            return

        if isinstance(node, (VarDecl, ConstDecl)):
            self._collect_used_names(node.value, used_names)
            return

        if isinstance(node, FuncDecl):
            for default in node.defaults:
                self._collect_used_names(default, used_names)
            return

        if isinstance(node, ClassDecl):
            self._collect_used_names(node.superclass, used_names)
            return

        if isinstance(node, IfStmt):
            self._collect_used_names(node.condition, used_names)
            self._collect_used_names(node.then_body, used_names)
            for cond, body in node.elif_clauses:
                self._collect_used_names(cond, used_names)
                self._collect_used_names(body, used_names)
            self._collect_used_names(node.else_body, used_names)
            return

        if isinstance(node, WhileStmt):
            self._collect_used_names(node.condition, used_names)
            self._collect_used_names(node.body, used_names)
            return

        if isinstance(node, ForStmt):
            self._collect_used_names(node.iterable, used_names)
            self._collect_used_names(node.body, used_names)
            return

        if isinstance(node, WithStmt):
            self._collect_used_names(node.expr, used_names)
            self._collect_used_names(node.body, used_names)
            return

        if isinstance(node, TryStmt):
            self._collect_used_names(node.try_body, used_names)
            for handler in node.handlers:
                self._collect_used_names(handler.body, used_names)
            self._collect_used_names(node.finally_body, used_names)
            return

        if isinstance(node, MatchStmt):
            self._collect_used_names(node.subject, used_names)
            for case in node.cases:
                self._collect_used_names(case.guard, used_names)
                self._collect_used_names(case.body, used_names)
            return

        if isinstance(node, PrintStmt):
            for value in node.values:
                self._collect_used_names(value, used_names)
            return

        if isinstance(node, (ReturnStmt, ThrowStmt, ExprStmt)):
            self._collect_used_names(node.value if not isinstance(node, ExprStmt) else node.expr, used_names)
            return

        if isinstance(node, AssignExpr):
            if node.op != '=' and isinstance(node.target, IdentifierExpr):
                used_names.add(node.target.name)
            elif isinstance(node.target, IndexExpr):
                self._collect_used_names(node.target.obj, used_names)
                self._collect_used_names(node.target.index, used_names)
            elif isinstance(node.target, MemberExpr):
                self._collect_used_names(node.target.obj, used_names)
            self._collect_used_names(node.value, used_names)
            return

        if isinstance(node, CallExpr):
            self._collect_used_names(node.callee, used_names)
            for arg in node.args:
                self._collect_used_names(arg, used_names)
            for value in node.kwargs.values():
                self._collect_used_names(value, used_names)
            return

        if isinstance(node, BinaryExpr):
            self._collect_used_names(node.left, used_names)
            self._collect_used_names(node.right, used_names)
            return

        if isinstance(node, ConditionalExpr):
            self._collect_used_names(node.condition, used_names)
            self._collect_used_names(node.then_expr, used_names)
            self._collect_used_names(node.else_expr, used_names)
            return

        if isinstance(node, UnaryExpr):
            self._collect_used_names(node.operand, used_names)
            return

        if isinstance(node, MemberExpr):
            self._collect_used_names(node.obj, used_names)
            return

        if isinstance(node, IndexExpr):
            self._collect_used_names(node.obj, used_names)
            self._collect_used_names(node.index, used_names)
            return

        if isinstance(node, SliceExpr):
            self._collect_used_names(node.obj, used_names)
            self._collect_used_names(node.start, used_names)
            self._collect_used_names(node.stop, used_names)
            self._collect_used_names(node.step, used_names)
            return

        if isinstance(node, (ListLiteral, TupleLiteral, SetLiteral)):
            for element in node.elements:
                self._collect_used_names(element, used_names)
            return

        if isinstance(node, DictLiteral):
            for key, value in node.pairs:
                self._collect_used_names(key, used_names)
                self._collect_used_names(value, used_names)
            return

        if isinstance(node, ListComp):
            self._collect_used_names(node.iterable, used_names)
            self._collect_used_names(node.filter_expr, used_names)
            self._collect_used_names(node.expr, used_names)
            return

        if isinstance(node, DictComp):
            self._collect_used_names(node.iterable, used_names)
            self._collect_used_names(node.filter_expr, used_names)
            self._collect_used_names(node.key_expr, used_names)
            self._collect_used_names(node.value_expr, used_names)
            return

        if isinstance(node, AwaitExpr):
            self._collect_used_names(node.operand, used_names)

    def _analyze_function_scope(
        self,
        body: Node,
        params: list[Any],
        varargs: Optional[str],
        line: int,
        enclosing_scopes: Optional[list[set[str]]] = None,
    ) -> FunctionScopeInfo:
        scope_chain = (
            self.enclosing_function_scopes
            if enclosing_scopes is None
            else enclosing_scopes
        )
        param_names = {
            param.name if isinstance(param, VibhaktiParam) else (param[0] if isinstance(param, tuple) else param)
            for param in params
        }

        global_names: set[str] = set()
        nonlocal_names: set[str] = set()
        self._collect_scope_directives(body, global_names, nonlocal_names)

        if global_names & nonlocal_names:
            name = sorted(global_names & nonlocal_names)[0]
            raise CompileError(
                f"नाम '{name}' को एक साथ वैश्विक और अस्थानिक घोषित नहीं किया जा सकता",
                line,
            )

        local_names = set(param_names)
        if varargs:
            if varargs in global_names or varargs in nonlocal_names:
                raise CompileError(
                    f"परिवर्ती तर्क '{varargs}' को वैश्विक/अस्थानिक घोषित नहीं किया जा सकता",
                    line,
                )
            local_names.add(varargs)

        self._collect_bound_names(body, local_names, global_names, nonlocal_names)

        for name in sorted(nonlocal_names):
            if name in param_names:
                raise CompileError(
                    f"नाम '{name}' परिमित तर्क है; इसे अस्थानिक घोषित नहीं किया जा सकता",
                    line,
                )
            if not any(name in scope for scope in reversed(scope_chain)):
                raise CompileError(
                    f"अस्थानिक नाम '{name}' के लिए कोई बाहरी बंधन नहीं मिला",
                    line,
                )

        used_names: set[str] = set()
        self._collect_used_names(body, used_names)

        closure_names = {
            name
            for name in used_names
            if name not in local_names
            and name not in global_names
            and any(name in scope for scope in reversed(scope_chain))
        }
        closure_names.update(nonlocal_names)

        return FunctionScopeInfo(
            local_names=local_names,
            global_names=global_names,
            nonlocal_names=nonlocal_names,
            used_names=used_names,
            closure_names=closure_names,
        )

    def _compile_Program(self, node: Program):
        self._compile_stmt_sequence(node.body)

    def _compile_VarDecl(self, node: VarDecl):
        if node.value:
            self._compile_node(node.value)
        else:
            self.bytecode.emit_16bit(OpCode.LOAD_CONST, self.bytecode.add_constant(None))

        if len(node.names) == 1:
            slot = self.bytecode.get_var_slot(node.names[0])
            self.bytecode.emit(OpCode.STORE_VAR, slot)
        else:
            self.bytecode.emit(OpCode.UNPACK_SEQUENCE, len(node.names))
            for name in node.names:
                slot = self.bytecode.get_var_slot(name)
                self.bytecode.emit(OpCode.STORE_VAR, slot)

    def _compile_ConstDecl(self, node: ConstDecl):
        self._compile_node(node.value)
        slot = self.bytecode.get_var_slot(node.name)
        self.bytecode.emit(OpCode.STORE_VAR, slot)

    def _compile_GlobalStmt(self, node: GlobalStmt):
        for name in node.names:
            self.bytecode.global_names.add(name)
            # Ensure it has a slot so STORE_VAR/LOAD_VAR work
            self.bytecode.get_var_slot(name)

    def _compile_NonlocalStmt(self, node: NonlocalStmt):
        # Scope directives are handled by the function-level symbol analysis pass.
        return

    def _compile_FuncDecl(self, node: FuncDecl):
        """
        Compile function declaration with Vibhakti semantic role support.

        If function has Vibhakti-decorated parameters:
        1. Build VibhaktiSignature object
        2. Register with VibhaktiRegistry
        3. Emit CHECK_VIBHAKTI opcode at function entry
        """
        from .ast_nodes import VibhaktiParam
        from .vibhakti import VibhaktiSignature, VibhaktiCase, VIBHAKTI_KEYWORDS, VibhaktiRegistry

        scope_info = getattr(node, "_scope_info", None)
        if scope_info is None:
            scope_info = self._analyze_function_scope(node.body, node.params, node.varargs, node.line)

        # Create separate bytecode for function
        func_compiler = Compiler(
            optimize=self.optimize,
            enclosing_function_scopes=self.enclosing_function_scopes + [set(scope_info.local_names)],
            known_parinama_names=self.known_parinama_names,
        )
        func_compiler.scope_info = scope_info
        func_compiler.bytecode.name = node.name
        func_compiler.bytecode.is_async = node.is_async  # Mark as async coroutine
        func_compiler.bytecode.global_names = set(scope_info.global_names)
        func_compiler.bytecode.nonlocal_names = set(scope_info.nonlocal_names)
        func_compiler.bytecode.local_names = set(scope_info.local_names)
        func_compiler.bytecode.closure_names = set(scope_info.closure_names)

        # Build Vibhakti signature if parameters have Vibhakti roles
        vibhakti_sig = None
        has_vibhakti = any(isinstance(p, VibhaktiParam) for p in node.params)

        if has_vibhakti:
            vibhakti_sig = VibhaktiSignature()

            # Process parameters - convert VibhaktiParam to VibhaktiSignature
            for param in node.params:
                if isinstance(param, VibhaktiParam):
                    from .vibhakti import create_vibhakti_param
                    v_param = create_vibhakti_param(
                        name=param.name,
                        vibhakti_name=param.vibhakti,
                        type_hint=param.type_hint,
                        default=param.default,
                        line=param.line
                    )
                    vibhakti_sig.add_param(v_param)
                    func_compiler.bytecode.get_var_slot(param.name)
                    func_compiler.bytecode.param_names.append(param.name)
                    if param.type_hint:
                        func_compiler.bytecode.type_hints[param.name] = param.type_hint
                else:
                    # Regular parameter tuple
                    p_name = param[0] if isinstance(param, tuple) else param
                    p_type = param[1] if isinstance(param, tuple) else None
                    func_compiler.bytecode.get_var_slot(p_name)
                    func_compiler.bytecode.param_names.append(p_name)
                    if p_type:
                        func_compiler.bytecode.type_hints[p_name] = p_type

            # Register signature
            registry = VibhaktiRegistry()
            registry.register(node.name, vibhakti_sig)
            self._validate_vibhakti_body(node.body, vibhakti_sig, node.line)

        # Handle parameters (non-Vibhakti)
        if not has_vibhakti:
            for param_pair in node.params:
                p_name = param_pair[0] if isinstance(param_pair, tuple) else param_pair
                p_type = param_pair[1] if isinstance(param_pair, tuple) else None
                func_compiler.bytecode.get_var_slot(p_name)
                func_compiler.bytecode.param_names.append(p_name)
                if p_type:
                    func_compiler.bytecode.type_hints[p_name] = p_type

        func_compiler.bytecode.num_params = len(node.params)
        func_compiler.bytecode.vibhakti_signature = vibhakti_sig
        if node.return_type:
            func_compiler.bytecode.type_hints[RETURN_TYPE_HINT_KEY] = node.return_type

        # Handle variadic argument
        if node.varargs:
            func_compiler.bytecode.varargs_name = node.varargs
            func_compiler.bytecode.get_var_slot(node.varargs)

        # Handle default values
        for default_node in node.defaults:
            if default_node is None:
                func_compiler.bytecode.defaults.append(NO_DEFAULT)
            elif isinstance(default_node, NullLiteral):
                func_compiler.bytecode.defaults.append(None)
            elif isinstance(default_node, (NumberLiteral, StringLiteral, BoolLiteral)):
                func_compiler.bytecode.defaults.append(default_node.value)
            else:
                func_compiler.bytecode.defaults.append(NO_DEFAULT)

        # Compile function body
        func_compiler._compile_node(node.body)

        # Ensure function returns
        if not func_compiler.bytecode.code or func_compiler.bytecode.code[-1] != OpCode.RETURN.value:
            func_compiler.bytecode.emit_16bit(OpCode.LOAD_CONST, func_compiler.bytecode.add_constant(None))
            func_compiler.bytecode.emit(OpCode.RETURN)

        # Store function bytecode and flatten inner functions
        self.bytecode.functions[node.name] = func_compiler.bytecode
        self.bytecode.functions.update(func_compiler.bytecode.functions)

        # Load function reference with environment capture
        env = {name: None for name in scope_info.closure_names}

        # Mark function as coroutine if async
        if node.is_async:
            idx = self.bytecode.add_constant(('coroutine', node.name, env))
        else:
            idx = self.bytecode.add_constant(('function', node.name, env))

        self.bytecode.emit_16bit(OpCode.LOAD_CONST, idx)
        slot = self.bytecode.get_var_slot(node.name)
        self.bytecode.emit(OpCode.STORE_VAR, slot)

    def _compile_DataDecl(self, node: DataDecl):
        metadata = DictLiteral(
            pairs=[
                (StringLiteral("__data__", line=node.line), StringLiteral(node.name, line=node.line)),
                (
                    StringLiteral("variants", line=node.line),
                    ListLiteral(
                        elements=[StringLiteral(variant.name, line=variant.line) for variant in node.variants],
                        line=node.line,
                    ),
                ),
                (
                    StringLiteral("type_params", line=node.line),
                    ListLiteral(
                        elements=[StringLiteral(param, line=node.line) for param in node.type_params],
                        line=node.line,
                    ),
                ),
            ],
            line=node.line,
        )
        self._compile_ConstDecl(ConstDecl(name=node.name, value=metadata, line=node.line))

        for variant in node.variants:
            param_names = [f"__field_{index}" for index in range(len(variant.field_types))]
            params = list(zip(param_names, variant.field_types))
            tuple_elements = [StringLiteral(variant.name, line=variant.line)] + [
                IdentifierExpr(name=param_name, line=variant.line)
                for param_name in param_names
            ]
            body = Block(
                stmts=[
                    ReturnStmt(
                        value=TupleLiteral(elements=tuple_elements, line=variant.line),
                        line=variant.line,
                    )
                ],
                line=variant.line,
            )
            synthetic = FuncDecl(
                name=variant.name,
                params=params,
                defaults=[None] * len(params),
                varargs=None,
                body=body,
                line=variant.line,
            )
            self._compile_FuncDecl(synthetic)

    def _compile_LambdaExpr(self, node: LambdaExpr):
        # Generate a unique name for the lambda
        lambda_name = f"<lambda_{id(node)}>"

        scope_info = getattr(node, "_scope_info", None)
        if scope_info is None:
            scope_info = self._analyze_function_scope(node.body, node.params, node.varargs, node.line)

        func_compiler = Compiler(
            optimize=self.optimize,
            enclosing_function_scopes=self.enclosing_function_scopes + [set(scope_info.local_names)],
        )
        func_compiler.scope_info = scope_info
        func_compiler.bytecode.name = lambda_name
        func_compiler.bytecode.local_names = set(scope_info.local_names)
        func_compiler.bytecode.global_names = set(scope_info.global_names)
        func_compiler.bytecode.nonlocal_names = set(scope_info.nonlocal_names)
        func_compiler.bytecode.closure_names = set(scope_info.closure_names)

        # Add parameters
        for param_pair in node.params:
            p_name = param_pair[0] if isinstance(param_pair, tuple) else param_pair
            p_type = param_pair[1] if isinstance(param_pair, tuple) else None
            func_compiler.bytecode.get_var_slot(p_name)
            if p_type:
                func_compiler.bytecode.type_hints[p_name] = p_type
        func_compiler.bytecode.num_params = len(node.params)

        # Handle variadic argument
        if node.varargs:
            func_compiler.bytecode.varargs_name = node.varargs
            func_compiler.bytecode.get_var_slot(node.varargs)

        # Compile body (which is a Block containing a ReturnStmt)
        func_compiler._compile_node(node.body)

        # Ensure return
        if not func_compiler.bytecode.code or func_compiler.bytecode.code[-1] != OpCode.RETURN.value:
            func_compiler.bytecode.emit_16bit(OpCode.LOAD_CONST, func_compiler.bytecode.add_constant(None))
            func_compiler.bytecode.emit(OpCode.RETURN)

        # Store in parent
        self.bytecode.functions[lambda_name] = func_compiler.bytecode
        self.bytecode.functions.update(func_compiler.bytecode.functions)

        # Push function tuple to stack with environment capture
        env = {name: None for name in scope_info.closure_names}
        idx = self.bytecode.add_constant(('function', lambda_name, env))
        self.bytecode.emit_16bit(OpCode.LOAD_CONST, idx)

    def _compile_ReturnStmt(self, node: ReturnStmt):
        if node.value:
            self._compile_node(node.value)
            self.bytecode.emit(OpCode.RETURN)
        else:
            self.bytecode.emit(OpCode.RETURN_VOID)

    def _compile_PrintStmt(self, node: PrintStmt):
        for i, val in enumerate(node.values):
            if i > 0:
                # Load space separator
                idx = self.bytecode.add_constant(' ')
                self.bytecode.emit_16bit(OpCode.LOAD_CONST, idx)
                self.bytecode.emit(OpCode.PRINT)
            self._compile_node(val)
            self.bytecode.emit(OpCode.PRINT)
        # Print newline
        idx = self.bytecode.add_constant('\n')
        self.bytecode.emit_16bit(OpCode.LOAD_CONST, idx)
        self.bytecode.emit(OpCode.PRINT)

    def _pattern_to_spec(self, pattern: Node):
        if isinstance(pattern, WildcardPattern):
            return ('wildcard',)
        if isinstance(pattern, BindingPattern):
            return ('bind', pattern.name)
        if isinstance(pattern, LiteralPattern):
            return ('literal', pattern.value)
        if isinstance(pattern, SequencePattern):
            return (
                'sequence',
                pattern.kind,
                [self._pattern_to_spec(item) for item in pattern.elements],
                pattern.rest_name,
            )
        if isinstance(pattern, CallPattern):
            return (
                'call',
                pattern.callee,
                [self._pattern_to_spec(item) for item in pattern.args],
            )
        raise CompileError(f"Unsupported pattern: {type(pattern).__name__}", pattern.line)

    def _pattern_binding_names(self, pattern: Node) -> list[str]:
        if isinstance(pattern, BindingPattern):
            return [] if pattern.name == "_" else [pattern.name]
        if isinstance(pattern, SequencePattern):
            names = []
            for element in pattern.elements:
                names.extend(self._pattern_binding_names(element))
            if pattern.rest_name and pattern.rest_name != "_":
                names.append(pattern.rest_name)
            return names
        if isinstance(pattern, CallPattern):
            names = []
            for arg in pattern.args:
                names.extend(self._pattern_binding_names(arg))
            return names
        return []

    def _is_catchall_pattern(self, pattern: Node) -> bool:
        return isinstance(pattern, (WildcardPattern, BindingPattern))

    def _node_mutates_symbol(self, node: Node, symbol: str) -> bool:
        if node is None:
            return False

        if isinstance(node, AssignExpr):
            target = node.target
            if isinstance(target, IdentifierExpr):
                return target.name == symbol
            if isinstance(target, MemberExpr) and isinstance(target.obj, IdentifierExpr):
                return target.obj.name == symbol
            if isinstance(target, IndexExpr) and isinstance(target.obj, IdentifierExpr):
                return target.obj.name == symbol
            return False

        if isinstance(node, VarDecl):
            return symbol in node.names

        if isinstance(node, ExprStmt):
            return self._node_mutates_symbol(node.expr, symbol)

        if isinstance(node, ForStmt):
            return symbol in node.var_names or self._node_mutates_symbol(node.body, symbol)

        if isinstance(node, Block):
            return any(self._node_mutates_symbol(stmt, symbol) for stmt in node.stmts)

        if isinstance(node, IfStmt):
            if self._node_mutates_symbol(node.then_body, symbol):
                return True
            if node.else_body and self._node_mutates_symbol(node.else_body, symbol):
                return True
            return any(self._node_mutates_symbol(body, symbol) for _, body in node.elif_clauses)

        if isinstance(node, WhileStmt):
            return self._node_mutates_symbol(node.body, symbol)

        if isinstance(node, TryStmt):
            return any(
                self._node_mutates_symbol(part, symbol)
                for part in (
                    [node.try_body]
                    + [handler.body for handler in node.handlers]
                    + [node.finally_body]
                )
                if part is not None
            )

        if isinstance(node, WithStmt):
            return self._node_mutates_symbol(node.body, symbol)

        if isinstance(node, MatchStmt):
            return any(self._node_mutates_symbol(case.body, symbol) for case in node.cases)

        return False

    def _validate_vibhakti_body(self, body: Node, signature: Any, line: int) -> None:
        from .vibhakti import VibhaktiCase, VIBHAKTI_NAMES

        for param in signature.params:
            if param.vibhakti == VibhaktiCase.KARANA and self._node_mutates_symbol(body, param.name):
                role_name = VIBHAKTI_NAMES[param.vibhakti][0]
                raise CompileError(
                    f"{role_name} '{param.name}' को परिवर्तित नहीं किया जा सकता",
                    line,
                )

    def _compile_MatchStmt(self, node: MatchStmt):
        if not any(self._is_catchall_pattern(case.pattern) for case in node.cases) and not getattr(node, "exhaustive", False):
            raise CompileError("अपूर्ण प्रत्यभिज्ञा: अंतिम '_' या binding case आवश्यक है", node.line)

        subject_name = f"__match_subject_{id(node)}"
        result_name = f"__match_result_{id(node)}"
        subject_slot = self.bytecode.get_var_slot(subject_name)
        result_slot = self.bytecode.get_var_slot(result_name)
        self.bytecode.local_names.update({subject_name, result_name})
        matcher_slot = self.bytecode.get_var_slot("__match_pattern__")
        end_jumps = []

        self._compile_node(node.subject)
        self.bytecode.emit(OpCode.STORE_VAR, subject_slot)

        for case in node.cases:
            self.bytecode.emit(OpCode.LOAD_VAR, matcher_slot)
            self.bytecode.emit(OpCode.LOAD_VAR, subject_slot)
            spec_idx = self.bytecode.add_constant(self._pattern_to_spec(case.pattern))
            self.bytecode.emit_16bit(OpCode.LOAD_CONST, spec_idx)
            self.bytecode.emit(OpCode.CALL, 2)
            self.bytecode.emit(OpCode.STORE_VAR, result_slot)

            self.bytecode.emit(OpCode.LOAD_VAR, result_slot)
            none_idx = self.bytecode.add_constant(None)
            self.bytecode.emit_16bit(OpCode.LOAD_CONST, none_idx)
            self.bytecode.emit(OpCode.NEQ)
            failure_jumps = [self.bytecode.get_current_offset()]
            self.bytecode.emit_16bit(OpCode.JUMP_IF_FALSE, 0)

            for binding_name in self._pattern_binding_names(case.pattern):
                self.bytecode.emit(OpCode.LOAD_VAR, result_slot)
                key_idx = self.bytecode.add_constant(binding_name)
                self.bytecode.emit_16bit(OpCode.LOAD_CONST, key_idx)
                self.bytecode.emit(OpCode.INDEX_GET)
                bind_slot = self.bytecode.get_var_slot(binding_name)
                self.bytecode.emit(OpCode.STORE_VAR, bind_slot)

            if case.guard is not None:
                self._compile_node(case.guard)
                failure_jumps.append(self.bytecode.get_current_offset())
                self.bytecode.emit_16bit(OpCode.JUMP_IF_FALSE, 0)

            self._compile_node(case.body)
            end_jumps.append(self.bytecode.get_current_offset())
            self.bytecode.emit_16bit(OpCode.JUMP, 0)

            next_case_offset = self.bytecode.get_current_offset()
            for jump_pos in failure_jumps:
                self.bytecode.patch_jump(jump_pos, next_case_offset)

        message_idx = self.bytecode.add_constant("कोई प्रत्यभिज्ञा pattern मेल नहीं खाया")
        self.bytecode.emit_16bit(OpCode.LOAD_CONST, message_idx)
        self.bytecode.emit(OpCode.THROW)

        end_offset = self.bytecode.get_current_offset()
        for jump_pos in end_jumps:
            self.bytecode.patch_jump(jump_pos, end_offset)

    def _compile_IfStmt(self, node: IfStmt):
        end_jumps = []

        self._compile_node(node.condition)
        jump_next = self.bytecode.get_current_offset()
        self.bytecode.emit_16bit(OpCode.JUMP_IF_FALSE, 0)
        self._compile_node(node.then_body)
        end_jumps.append(self.bytecode.get_current_offset())
        self.bytecode.emit_16bit(OpCode.JUMP, 0)
        self.bytecode.patch_jump(jump_next, self.bytecode.get_current_offset())

        for elif_cond, elif_body in node.elif_clauses:
            self._compile_node(elif_cond)
            jump_next = self.bytecode.get_current_offset()
            self.bytecode.emit_16bit(OpCode.JUMP_IF_FALSE, 0)
            self._compile_node(elif_body)
            end_jumps.append(self.bytecode.get_current_offset())
            self.bytecode.emit_16bit(OpCode.JUMP, 0)
            self.bytecode.patch_jump(jump_next, self.bytecode.get_current_offset())

        if node.else_body:
            self._compile_node(node.else_body)

        end_offset = self.bytecode.get_current_offset()
        for jump_end in end_jumps:
            self.bytecode.patch_jump(jump_end, end_offset)

    def _compile_WhileStmt(self, node: WhileStmt):
        loop_start = self.bytecode.get_current_offset()

        # Compile condition
        self._compile_node(node.condition)

        # Jump to end if false
        jump_end = self.bytecode.get_current_offset()
        self.bytecode.emit_16bit(OpCode.JUMP_IF_FALSE, 0)

        # Track loop for break/continue
        loop_ctx = {
            "continue_target": loop_start,
            "break_patches": [],
            "break_cleanup_ops": 0,
        }
        self.loop_stack.append(loop_ctx)

        # Compile body
        self._compile_node(node.body)

        loop_ctx = self.loop_stack.pop()

        # Jump back to start
        current_pos = self.bytecode.get_current_offset()
        self.bytecode.emit_16bit(OpCode.JUMP, loop_start - (current_pos + 3))

        # Patch end jump
        end_offset = self.bytecode.get_current_offset()
        self.bytecode.patch_jump(jump_end, end_offset)
        for break_jump in loop_ctx["break_patches"]:
            self.bytecode.patch_jump(break_jump, end_offset)

    def _compile_ForStmt(self, node: ForStmt):
        # 1. Compile iterable and get iterator
        self._compile_node(node.iterable)
        self.bytecode.emit(OpCode.GET_ITER)

        loop_start = self.bytecode.get_current_offset()

        # 2. Iteration step
        jump_end = self.bytecode.get_current_offset()
        self.bytecode.emit_16bit(OpCode.FOR_ITER, 0)  # Patched to loop exit below

        # 3. Store current item in the loop variable(s)
        if len(node.var_names) == 1:
            var_slot = self.bytecode.get_var_slot(node.var_names[0])
            self.bytecode.emit(OpCode.STORE_VAR, var_slot)
        else:
            self.bytecode.emit(OpCode.UNPACK_SEQUENCE, len(node.var_names))
            for var_name in node.var_names:
                var_slot = self.bytecode.get_var_slot(var_name)
                self.bytecode.emit(OpCode.STORE_VAR, var_slot)

        # 4. Compile body
        loop_ctx = {
            "continue_target": loop_start,
            "break_patches": [],
            "break_cleanup_ops": 1,
        }
        self.loop_stack.append(loop_ctx)
        self._compile_node(node.body)
        loop_ctx = self.loop_stack.pop()

        # 5. Loop back
        # The jump back is from the current position to the start of FOR_ITER
        # vm.py: pc += 3 + offset
        current_pos = self.bytecode.get_current_offset()
        back_jump_dist = loop_start - (current_pos + 3)
        self.bytecode.emit_16bit(OpCode.JUMP, back_jump_dist)

        # 6. Patch the FOR_ITER exit jump
        # This will jump past the back-jump instruction
        loop_end = self.bytecode.get_current_offset()
        self.bytecode.patch_jump(jump_end, loop_end)
        for break_jump in loop_ctx["break_patches"]:
            self.bytecode.patch_jump(break_jump, loop_end)

    def _compile_BreakStmt(self, node: BreakStmt):
        if not self.loop_stack:
            raise CompileError("विराम (break) outside loop", node.line)
        for _ in range(self.loop_stack[-1]["break_cleanup_ops"]):
            self.bytecode.emit(OpCode.POP)
        jump_pos = self.bytecode.get_current_offset()
        self.bytecode.emit_16bit(OpCode.JUMP, 0)  # Patched at loop exit
        self.loop_stack[-1]["break_patches"].append(jump_pos)

    def _compile_ContinueStmt(self, node: ContinueStmt):
        if not self.loop_stack:
            raise CompileError("अग्रे (continue) outside loop", node.line)
        loop_start = self.loop_stack[-1]["continue_target"]
        self.bytecode.emit_16bit(OpCode.JUMP, loop_start - (self.bytecode.get_current_offset() + 3))

    def _compile_ClassDecl(self, node: ClassDecl):
        # We need to compile the class body into a dictionary of methods/attributes
        class_compiler = Compiler(
            optimize=self.optimize,
            enclosing_function_scopes=self.enclosing_function_scopes,
            known_parinama_names=self.known_parinama_names,
        )
        class_compiler.bytecode.name = f"<class {node.name}>"

        # Compile methods inside the class body
        if hasattr(node.body, 'stmts'):
            class_compiler._compile_stmt_sequence(node.body.stmts)

        # Ensure it returns
        class_compiler.bytecode.emit(OpCode.RETURN_VOID)

        # Store class initialization bytecode
        self.bytecode.functions[node.name] = class_compiler.bytecode

        # Push parent class if any, else None
        if hasattr(node, 'superclass') and node.superclass:
            if isinstance(node.superclass, IdentifierExpr):
                slot = self.bytecode.get_var_slot(node.superclass.name)
                self.bytecode.emit(OpCode.LOAD_VAR, slot)
            else:
                self._compile_node(node.superclass)
        else:
            idx = self.bytecode.add_constant(None)
            self.bytecode.emit_16bit(OpCode.LOAD_CONST, idx)

        # Push class name
        idx = self.bytecode.add_constant(node.name)
        self.bytecode.emit_16bit(OpCode.LOAD_CONST, idx)

        # Emit BUILD_CLASS
        self.bytecode.emit(OpCode.BUILD_CLASS)

        slot = self.bytecode.get_var_slot(node.name)
        self.bytecode.emit(OpCode.STORE_VAR, slot)

    def _compile_ParinamaDecl(self, node: ParinamaDecl):
        rules_spec = [
            {
                'pattern': self._encode_runtime_term_spec(rule.pattern),
                'replacement': self._encode_runtime_term_spec(rule.replacement),
                'line': rule.line,
            }
            for rule in node.rules
        ]

        make_slot = self.bytecode.get_var_slot("__make_parinama__")
        self.bytecode.emit(OpCode.LOAD_VAR, make_slot)
        self.bytecode.emit_16bit(OpCode.LOAD_CONST, self.bytecode.add_constant(node.name))
        self.bytecode.emit_16bit(OpCode.LOAD_CONST, self.bytecode.add_constant(rules_spec))
        self.bytecode.emit_16bit(OpCode.LOAD_CONST, self.bytecode.add_constant(node.scope))
        self.bytecode.emit(OpCode.CALL, 3)

        slot = self.bytecode.get_var_slot(node.name)
        self.bytecode.emit(OpCode.STORE_VAR, slot)

    def _compile_TryStmt(self, node: TryStmt):
        # Setup exception handler jump
        jump_catch = self.bytecode.get_current_offset()
        self.bytecode.emit_16bit(OpCode.SETUP_EXCEPT, 0)  # Patched to catch entry below

        # Compile try block
        self._compile_node(node.try_body)

        # Pop exception handler if try succeeded
        self.bytecode.emit(OpCode.POP_EXCEPT)
        if node.finally_body:
            self._compile_node(node.finally_body)
        success_jump = self.bytecode.get_current_offset()
        self.bytecode.emit_16bit(OpCode.JUMP, 0)

        # Patch exception jump to here (Start of catch block)
        catch_offset = self.bytecode.get_current_offset()
        self.bytecode.patch_jump(jump_catch, catch_offset)

        end_jumps: list[int] = []
        hidden_exc_name = f"<caught_exception_{id(node)}>"
        hidden_exc_slot = self.bytecode.get_var_slot(hidden_exc_name)
        self.bytecode.emit(OpCode.STORE_VAR, hidden_exc_slot)

        for handler in node.handlers:
            skip_handler_jump = None
            if handler.match_name:
                match_slot = self.bytecode.get_var_slot("__match_exception__")
                self.bytecode.emit(OpCode.LOAD_VAR, match_slot)
                self.bytecode.emit(OpCode.LOAD_VAR, hidden_exc_slot)
                self.bytecode.emit_16bit(
                    OpCode.LOAD_CONST,
                    self.bytecode.add_constant(handler.match_name),
                )
                self.bytecode.emit(OpCode.CALL, 2)
                skip_handler_jump = self.bytecode.get_current_offset()
                self.bytecode.emit_16bit(OpCode.JUMP_IF_FALSE, 0)

            if handler.bind_name:
                slot = self.bytecode.get_var_slot(handler.bind_name)
                self.bytecode.emit(OpCode.LOAD_VAR, hidden_exc_slot)
                self.bytecode.emit(OpCode.STORE_VAR, slot)

            self._compile_node(handler.body)
            if node.finally_body:
                self._compile_node(node.finally_body)
            jump_end = self.bytecode.get_current_offset()
            self.bytecode.emit_16bit(OpCode.JUMP, 0)
            end_jumps.append(jump_end)

            if skip_handler_jump is not None:
                self.bytecode.patch_jump(skip_handler_jump, self.bytecode.get_current_offset())

        if node.finally_body:
            self._compile_node(node.finally_body)
        self.bytecode.emit(OpCode.LOAD_VAR, hidden_exc_slot)
        self.bytecode.emit(OpCode.THROW)

        end_offset = self.bytecode.get_current_offset()
        self.bytecode.patch_jump(success_jump, end_offset)
        for jump_pos in end_jumps:
            self.bytecode.patch_jump(jump_pos, end_offset)

    def _compile_WithStmt(self, node: WithStmt):
        # Evaluate context manager
        self._compile_node(node.expr)

        # Store in hidden local for cleanup
        hidden_name = f"<ctx_{id(node)}>"
        slot = self.bytecode.get_var_slot(hidden_name)
        self.bytecode.emit(OpCode.DUP)
        self.bytecode.emit(OpCode.STORE_VAR, slot)

        # The bound name inside the block should receive __enter__().
        enter_idx = self.bytecode.add_constant('__enter__')
        self.bytecode.emit_16bit(OpCode.LOAD_CONST, enter_idx)
        self.bytecode.emit(OpCode.CALL_METHOD, 0)

        # Store in user variable if provided
        if node.var_name:
            user_slot = self.bytecode.get_var_slot(node.var_name)
            self.bytecode.emit(OpCode.STORE_VAR, user_slot)
        else:
            self.bytecode.emit(OpCode.POP)

        # Execute body
        self._compile_node(node.body)

        # Load for cleanup
        self.bytecode.emit(OpCode.LOAD_VAR, slot)
        self.bytecode.emit(OpCode.WITH_CLEANUP)

    def _compile_ThrowStmt(self, node: ThrowStmt):
        self._compile_node(node.value)
        self.bytecode.emit(OpCode.THROW)

    def _compile_ImportStmt(self, node: ImportStmt):
        idx = self.bytecode.add_constant(node.module)
        self.bytecode.emit_16bit(OpCode.IMPORT_NAME, idx)

        if node.names:
            temp_name = f"__imported_module_{node.line}"
            temp_slot = self.bytecode.get_var_slot(temp_name)
            self.bytecode.local_names.add(temp_name)
            self.bytecode.emit(OpCode.STORE_VAR, temp_slot)

            for name in node.names:
                self.bytecode.emit(OpCode.LOAD_VAR, temp_slot)
                attr_idx = self.bytecode.add_constant(name)
                self.bytecode.emit_16bit(OpCode.ATTR_GET, attr_idx)
                slot = self.bytecode.get_var_slot(name)
                self.bytecode.emit(OpCode.STORE_VAR, slot)
        else:
            # Store module object in local variable
            slot = self.bytecode.get_var_slot(node.module)
            self.bytecode.emit(OpCode.STORE_VAR, slot)
            
    def _compile_Block(self, node: Block):
        self._compile_stmt_sequence(node.stmts)

    def _compile_ExprStmt(self, node: ExprStmt):
        self._compile_node(node.expr)
        self.bytecode.emit(OpCode.POP)  # Discard result

    def _compile_BinaryExpr(self, node: BinaryExpr):
        self._compile_node(node.left)
        self._compile_node(node.right)

        op_map = {
            '+': OpCode.ADD,
            '-': OpCode.SUB,
            '*': OpCode.MUL,
            '/': OpCode.DIV,
            '//': OpCode.IDIV,  # Integer division
            '%': OpCode.MOD,
            '**': OpCode.POW,
            '&': OpCode.BAND,
            '|': OpCode.BOR,
            '^': OpCode.BXOR,
            '<<': OpCode.LSHIFT,
            '>>': OpCode.RSHIFT,
            '==': OpCode.EQ,
            '!=': OpCode.NEQ,
            '<': OpCode.LT,
            '>': OpCode.GT,
            '<=': OpCode.LTE,
            '>=': OpCode.GTE,
            'और': OpCode.AND,
            'अथवा': OpCode.OR,
            'अन्तर्गत': OpCode.CONTAINS,  # Membership test
        }

        if node.op == 'not in':
            self.bytecode.emit(OpCode.CONTAINS)
            self.bytecode.emit(OpCode.NOT)
        elif node.op in op_map:
            self.bytecode.emit(op_map[node.op])
        else:
            raise CompileError(f"Unknown operator: {node.op}", node.line)

    def _compile_UnaryExpr(self, node: UnaryExpr):
        self._compile_node(node.operand)

        if node.op == '-':
            self.bytecode.emit(OpCode.NEG)
        elif node.op == 'न':
            self.bytecode.emit(OpCode.NOT)
        elif node.op == '~':
            self.bytecode.emit(OpCode.BNOT)
        else:
            raise CompileError(f"Unknown unary operator: {node.op}", node.line)

    def _compile_ConditionalExpr(self, node: ConditionalExpr):
        self._compile_node(node.condition)

        jump_else = self.bytecode.get_current_offset()
        self.bytecode.emit_16bit(OpCode.JUMP_IF_FALSE, 0)

        self._compile_node(node.then_expr)

        jump_end = self.bytecode.get_current_offset()
        self.bytecode.emit_16bit(OpCode.JUMP, 0)

        else_offset = self.bytecode.get_current_offset()
        self.bytecode.patch_jump(jump_else, else_offset)

        self._compile_node(node.else_expr)

        end_offset = self.bytecode.get_current_offset()
        self.bytecode.patch_jump(jump_end, end_offset)
            
    def _compile_AssignExpr(self, node: AssignExpr):
        # Determine value to store
        if node.op == '=':
            self._compile_node(node.value)
        else:
            # Compound assignment (+=, -=, etc.)
            # First load the current value
            if isinstance(node.target, IdentifierExpr):
                slot = self.bytecode.get_var_slot(node.target.name)
                self.bytecode.emit(OpCode.LOAD_VAR, slot)
            elif isinstance(node.target, IndexExpr):
                self._compile_node(node.target.obj)
                self._compile_node(node.target.index)
                self.bytecode.emit(OpCode.INDEX_GET)
            elif isinstance(node.target, MemberExpr):
                self._compile_node(node.target.obj)
                idx = self.bytecode.add_constant(node.target.attr)
                self.bytecode.emit_16bit(OpCode.ATTR_GET, idx)

            # Compile right side value
            self._compile_node(node.value)

            # Apply operator
            op_map = {'+=': OpCode.ADD, '-=': OpCode.SUB, '*=': OpCode.MUL, '/=': OpCode.DIV, '%=': OpCode.MOD, ':=': None}
            if node.op in op_map:
                if op_map[node.op]:
                    self.bytecode.emit(op_map[node.op])
            else:
                raise CompileError(f"Unknown assignment operator: {node.op}", node.line)

        # Store the computed value
        if isinstance(node.target, IdentifierExpr):
            slot = self.bytecode.get_var_slot(node.target.name)
            self.bytecode.emit(OpCode.STORE_VAR, slot)
            self.bytecode.emit(OpCode.LOAD_VAR, slot)  # Assignment returns value
        elif isinstance(node.target, IndexExpr):
            # Target stack needs to be: obj, index, value
            # But value is currently on top.
            # We need to temporarily pop value, push obj, push index, push value

            # Since our ISA doesn't have deep stack manipulation, we can use a temp variable
            temp_val_slot = self.bytecode.get_var_slot("__temp_assign_val")
            self.bytecode.local_names.add("__temp_assign_val")
            self.bytecode.emit(OpCode.STORE_VAR, temp_val_slot)

            self._compile_node(node.target.obj)
            self._compile_node(node.target.index)
            self.bytecode.emit(OpCode.LOAD_VAR, temp_val_slot)

            self.bytecode.emit(OpCode.INDEX_SET)
            self.bytecode.emit(OpCode.LOAD_VAR, temp_val_slot) # Return value
        elif isinstance(node.target, MemberExpr):
            temp_val_slot = self.bytecode.get_var_slot("__temp_assign_val")
            self.bytecode.local_names.add("__temp_assign_val")
            self.bytecode.emit(OpCode.STORE_VAR, temp_val_slot)

            self._compile_node(node.target.obj)
            self.bytecode.emit(OpCode.LOAD_VAR, temp_val_slot)

            idx = self.bytecode.add_constant(node.target.attr)
            self.bytecode.emit_16bit(OpCode.ATTR_SET, idx)

            self.bytecode.emit(OpCode.LOAD_VAR, temp_val_slot) # Return value
        else:
            raise CompileError("Invalid assignment target", node.line)

    def _compile_CallExpr(self, node: CallExpr):
        if isinstance(node.callee, IdentifierExpr) and node.callee.name in ('पद', 'term'):
            if len(node.args) != 1 or node.kwargs:
                raise CompileError("पद expects exactly one positional argument", node.line)
            self._emit_term_builder(node.args[0])
            return

        is_method_call = isinstance(node.callee, MemberExpr)
        direct_parinama_call = (
            isinstance(node.callee, IdentifierExpr)
            and node.callee.name in self.known_parinama_names
        )

        if direct_parinama_call:
            if len(node.args) != 1:
                raise CompileError(
                    f"पारिणाम '{node.callee.name}' expects exactly one positional argument",
                    node.line,
                )
            extra_kwargs = [key for key in node.kwargs if key not in ('अधिकार', 'scope')]
            if extra_kwargs:
                raise CompileError(
                    f"पारिणाम '{node.callee.name}' only accepts अधिकार/scope keyword arguments",
                    node.line,
                )

        # Compile callee FIRST
        if isinstance(node.callee, IdentifierExpr):
            slot = self.bytecode.get_var_slot(node.callee.name)
            self.bytecode.emit(OpCode.LOAD_VAR, slot)
        elif is_method_call:
            # MemberExpr: push obj, then push attr string
            self._compile_node(node.callee.obj)
            idx = self.bytecode.add_constant(node.callee.attr)
            self.bytecode.emit_16bit(OpCode.LOAD_CONST, idx)
        else:
            self._compile_node(node.callee)

        # Compile arguments left-to-right
        for index, arg in enumerate(node.args):
            if direct_parinama_call and index == 0:
                self._emit_term_builder(arg)
            else:
                self._compile_node(arg)

        if node.kwargs:
            for key, value in node.kwargs.items():
                self._compile_node(value)
                idx = self.bytecode.add_constant(key)
                self.bytecode.emit_16bit(OpCode.LOAD_CONST, idx)
            self.bytecode.emit(OpCode.BUILD_DICT, len(node.kwargs))

        if is_method_call:
            self.bytecode.emit(OpCode.CALL_METHOD_KW if node.kwargs else OpCode.CALL_METHOD, len(node.args))
        else:
            self.bytecode.emit(OpCode.CALL_KW if node.kwargs else OpCode.CALL, len(node.args))

    def _compile_MemberExpr(self, node: MemberExpr):
        self._compile_node(node.obj)
        idx = self.bytecode.add_constant(node.attr)
        self.bytecode.emit_16bit(OpCode.ATTR_GET, idx)

    def _compile_IndexExpr(self, node: IndexExpr):
        self._compile_node(node.obj)
        self._compile_node(node.index)
        self.bytecode.emit(OpCode.INDEX_GET)

    def _compile_SliceExpr(self, node: SliceExpr):
        self._compile_node(node.obj)

        if node.start:
            self._compile_node(node.start)
        else:
            self.bytecode.emit_16bit(OpCode.LOAD_CONST, self.bytecode.add_constant(None))

        if node.stop:
            self._compile_node(node.stop)
        else:
            self.bytecode.emit_16bit(OpCode.LOAD_CONST, self.bytecode.add_constant(None))

        if node.step:
            self._compile_node(node.step)
        else:
            self.bytecode.emit_16bit(OpCode.LOAD_CONST, self.bytecode.add_constant(None))

        self.bytecode.emit(OpCode.MAKE_SLICE)
        self.bytecode.emit(OpCode.INDEX_GET)

    def _compile_IdentifierExpr(self, node: IdentifierExpr):
        slot = self.bytecode.get_var_slot(node.name)
        self.bytecode.emit(OpCode.LOAD_VAR, slot)

    def _compile_NumberLiteral(self, node: NumberLiteral):
        idx = self.bytecode.add_constant(node.value)
        self.bytecode.emit_16bit(OpCode.LOAD_CONST, idx)

    def _compile_StringLiteral(self, node: StringLiteral):
        idx = self.bytecode.add_constant(node.value)
        self.bytecode.emit_16bit(OpCode.LOAD_CONST, idx)

    def _compile_FStringExpr(self, node: FStringExpr):
        for part in node.parts:
            self._compile_node(part)
        self.bytecode.emit(OpCode.BUILD_STRING, len(node.parts))

    def _compile_BoolLiteral(self, node: BoolLiteral):
        idx = self.bytecode.add_constant(node.value)
        self.bytecode.emit_16bit(OpCode.LOAD_CONST, idx)

    def _compile_NullLiteral(self, node: NullLiteral):
        idx = self.bytecode.add_constant(None)
        self.bytecode.emit_16bit(OpCode.LOAD_CONST, idx)

    def _compile_ListLiteral(self, node: ListLiteral):
        for el in node.elements:
            self._compile_node(el)
        self.bytecode.emit(OpCode.BUILD_LIST, len(node.elements))

    def _compile_TupleLiteral(self, node: TupleLiteral):
        for el in node.elements:
            self._compile_node(el)
        self.bytecode.emit(OpCode.BUILD_TUPLE, len(node.elements))

    def _compile_ListComp(self, node: ListComp):
        # Create an empty list
        self.bytecode.emit(OpCode.BUILD_LIST, 0)

        # Evaluate iterable and get iterator
        self._compile_node(node.iterable)
        self.bytecode.emit(OpCode.GET_ITER)

        # Loop start
        loop_start = self.bytecode.get_current_offset()
        jump_exit = self.bytecode.get_current_offset()
        self.bytecode.emit_16bit(OpCode.FOR_ITER, 0)

        # Store loop variable
        slot = self.bytecode.get_var_slot(node.var_name)
        self.bytecode.emit(OpCode.STORE_VAR, slot)

        filter_jump = None
        if node.filter_expr is not None:
            self._compile_node(node.filter_expr)
            filter_jump = self.bytecode.get_current_offset()
            self.bytecode.emit_16bit(OpCode.JUMP_IF_FALSE, 0)

        # Evaluate expression
        self._compile_node(node.expr)

        # Append to list (stack: [... list, iter, val])
        # We need to rearrange stack or use a specific LIST_APPEND that expects this
        # Actually, LIST_APPEND pops val, and assumes list is at stack[-2].
        # But wait, stack is: list, iter, val.
        # So LIST_APPEND needs to operate on stack[-3]. Let's just emit SWAP, then rot? No.
        # Let's fix LIST_APPEND in VM to append stack[-1] to stack[-3].
        self.bytecode.emit(OpCode.LIST_APPEND)

        if filter_jump is not None:
            self.bytecode.patch_jump(filter_jump, self.bytecode.get_current_offset())

        # Jump to loop start
        jump_dist = loop_start - (self.bytecode.get_current_offset() + 3)
        if jump_dist < 0:
            jump_dist += 65536
        self.bytecode.emit_16bit(OpCode.JUMP, jump_dist)

        # Patch exit
        exit_offset = self.bytecode.get_current_offset()
        self.bytecode.patch_jump(jump_exit, exit_offset)

    def _compile_DictComp(self, node: DictComp):
        dict_name = f"__dict_comp_{id(node)}"
        dict_slot = self.bytecode.get_var_slot(dict_name)
        self.bytecode.local_names.add(dict_name)
        self.bytecode.emit(OpCode.BUILD_DICT, 0)
        self.bytecode.emit(OpCode.STORE_VAR, dict_slot)

        self._compile_node(node.iterable)
        self.bytecode.emit(OpCode.GET_ITER)

        loop_start = self.bytecode.get_current_offset()
        jump_exit = self.bytecode.get_current_offset()
        self.bytecode.emit_16bit(OpCode.FOR_ITER, 0)

        slot = self.bytecode.get_var_slot(node.var_name)
        self.bytecode.emit(OpCode.STORE_VAR, slot)

        filter_jump = None
        if node.filter_expr is not None:
            self._compile_node(node.filter_expr)
            filter_jump = self.bytecode.get_current_offset()
            self.bytecode.emit_16bit(OpCode.JUMP_IF_FALSE, 0)

        self.bytecode.emit(OpCode.LOAD_VAR, dict_slot)
        self._compile_node(node.key_expr)
        self._compile_node(node.value_expr)
        self.bytecode.emit(OpCode.INDEX_SET)

        if filter_jump is not None:
            self.bytecode.patch_jump(filter_jump, self.bytecode.get_current_offset())

        jump_dist = loop_start - (self.bytecode.get_current_offset() + 3)
        if jump_dist < 0:
            jump_dist += 65536
        self.bytecode.emit_16bit(OpCode.JUMP, jump_dist)

        exit_offset = self.bytecode.get_current_offset()
        self.bytecode.patch_jump(jump_exit, exit_offset)
        self.bytecode.emit(OpCode.LOAD_VAR, dict_slot)

    def _compile_DictLiteral(self, node: DictLiteral):
        for key, val in node.pairs:
            self._compile_node(val)
            self._compile_node(key)
        self.bytecode.emit(OpCode.BUILD_DICT, len(node.pairs))

    def _compile_SetLiteral(self, node: SetLiteral):
        for el in node.elements:
            self._compile_node(el)
        self.bytecode.emit(OpCode.BUILD_SET, len(node.elements))

    def _compile_AwaitExpr(self, node: AwaitExpr):
        """
        Compile await expression (प्रतीक्षा).

        The await keyword suspends the coroutine until the awaited
        coroutine completes, then pushes the result onto the stack.
        """
        # Compile the operand (should be a coroutine)
        self._compile_node(node.operand)
        # Emit AWAIT opcode to suspend and wait for result
        self.bytecode.emit(OpCode.AWAIT)

    def _compile_ProofDeclaration(self, node: ProofDeclaration):
        """
        Compile Nyāya proof declaration (सिद्धि).

        At compile-time:
        1. Verify the proof with NyayaProofVerifier + Sansmatic
        2. Embed a verifiable certificate payload in bytecode
        3. Emit VERIFY_PROOF so runtime can reject tampered certificates
        """
        from .nyaya_verifier import NyayaProofVerifier

        verifier = NyayaProofVerifier()
        certificate = verifier.verify_proof(
            node.statement,
            node.evidence_body,
            statement_expr=getattr(node, 'statement_expr', None),
            certificate_hint=node.certificate,
        )

        if not certificate.verified:
            reason = certificate.reason or "unproven statement"
            raise CompileError(
                f"सिद्धि असफल: {node.statement} ({reason})",
                node.line,
            )

        cert_idx = self.bytecode.add_constant(certificate.payload)
        self.bytecode.emit_16bit(OpCode.VERIFY_PROOF, cert_idx)
        self.bytecode.emit(OpCode.POP)

    def _get_builtin_index(self, name: str) -> int:
        """Get index of builtin function."""
        return compiled_builtin_index(name)

    # ─────────────────────────────────────────────────────────────────────────
    # OPTIMIZATION PHASES
    # ─────────────────────────────────────────────────────────────────────────

    def _constant_fold(self, node: Node) -> Node:
        """
        Constant folding optimization (स्थिर गुड़न).

        Evaluates constant expressions at compile-time instead of runtime.
        
        Examples:
        - 2 + 3 → 5
        - 10 * 5 → 50
        - "hello" + " " + "world" → "hello world"
        
        Args:
            node: AST node to optimize
            
        Returns:
            Optimized AST node
        """
        if node is None:
            return None

        if isinstance(node, BinaryExpr):
            # Recursively fold left and right operands
            left = self._constant_fold(node.left)
            right = self._constant_fold(node.right)
            
            # Check if both operands are constants
            if isinstance(left, NumberLiteral) and isinstance(right, NumberLiteral):
                # Fold arithmetic operations
                try:
                    if node.op == '+':
                        return NumberLiteral(left.value + right.value, line=node.line)
                    elif node.op == '-':
                        return NumberLiteral(left.value - right.value, line=node.line)
                    elif node.op == '*':
                        return NumberLiteral(left.value * right.value, line=node.line)
                    elif node.op == '/':
                        if right.value != 0:
                            return NumberLiteral(left.value / right.value, line=node.line)
                    elif node.op == '//':
                        if right.value != 0:
                            return NumberLiteral(left.value // right.value, line=node.line)
                    elif node.op == '%':
                        if right.value != 0:
                            return NumberLiteral(left.value % right.value, line=node.line)
                    elif node.op == '**':
                        return NumberLiteral(left.value ** right.value, line=node.line)
                    elif node.op == '==':
                        return BoolLiteral(left.value == right.value, line=node.line)
                    elif node.op == '!=':
                        return BoolLiteral(left.value != right.value, line=node.line)
                    elif node.op == '<':
                        return BoolLiteral(left.value < right.value, line=node.line)
                    elif node.op == '>':
                        return BoolLiteral(left.value > right.value, line=node.line)
                    elif node.op == '<=':
                        return BoolLiteral(left.value <= right.value, line=node.line)
                    elif node.op == '>=':
                        return BoolLiteral(left.value >= right.value, line=node.line)
                except:
                    pass  # Keep original if folding fails
            
            # String concatenation
            if isinstance(left, StringLiteral) and isinstance(right, StringLiteral):
                if node.op == '+':
                    return StringLiteral(left.value + right.value, line=node.line)
            
            # Boolean operations
            if isinstance(left, BoolLiteral) and isinstance(right, BoolLiteral):
                if node.op == 'और':
                    return BoolLiteral(left.value and right.value, line=node.line)
                elif node.op == 'अथवा':
                    return BoolLiteral(left.value or right.value, line=node.line)
            
            # Return partially folded expression
            return BinaryExpr(op=node.op, left=left, right=right, line=node.line)
        
        elif isinstance(node, UnaryExpr):
            operand = self._constant_fold(node.operand)
            
            if isinstance(operand, NumberLiteral):
                try:
                    if node.op == '-':
                        return NumberLiteral(-operand.value, line=node.line)
                    elif node.op == 'न':
                        return BoolLiteral(not operand.value, line=node.line)
                except:
                    pass
            
            if isinstance(operand, BoolLiteral):
                if node.op == 'न':
                    return BoolLiteral(not operand.value, line=node.line)
            
            return UnaryExpr(op=node.op, operand=operand, line=node.line)

        elif isinstance(node, ConditionalExpr):
            condition = self._constant_fold(node.condition)
            then_expr = self._constant_fold(node.then_expr)
            else_expr = self._constant_fold(node.else_expr)

            if isinstance(condition, BoolLiteral):
                return then_expr if condition.value else else_expr

            return ConditionalExpr(
                condition=condition,
                then_expr=then_expr,
                else_expr=else_expr,
                line=node.line,
            )
        
        elif isinstance(node, IfStmt):
            # Constant condition optimization
            condition = self._constant_fold(node.condition)
            
            if isinstance(condition, BoolLiteral):
                if condition.value:
                    return self._constant_fold(node.then_body)

                for elif_cond, elif_body in node.elif_clauses:
                    folded_elif_cond = self._constant_fold(elif_cond)
                    if isinstance(folded_elif_cond, BoolLiteral):
                        if folded_elif_cond.value:
                            return self._constant_fold(elif_body)
                        continue

                    remaining_elifs = [
                        (self._constant_fold(c), self._constant_fold(b))
                        for c, b in node.elif_clauses[node.elif_clauses.index((elif_cond, elif_body)) + 1:]
                    ]
                    return IfStmt(
                        condition=folded_elif_cond,
                        then_body=self._constant_fold(elif_body),
                        elif_clauses=remaining_elifs,
                        else_body=self._constant_fold(node.else_body) if node.else_body else None,
                        line=node.line,
                    )

                if node.else_body:
                    return self._constant_fold(node.else_body)

                return Block(stmts=[], line=node.line)
            
            # Recursively fold body
            return IfStmt(
                condition=condition,
                then_body=self._constant_fold(node.then_body),
                elif_clauses=[(self._constant_fold(c), self._constant_fold(b)) 
                             for c, b in node.elif_clauses],
                else_body=self._constant_fold(node.else_body) if node.else_body else None,
                line=node.line
            )
        
        elif isinstance(node, WhileStmt):
            # Constant condition - infinite loop or dead loop
            condition = self._constant_fold(node.condition)
            
            if isinstance(condition, BoolLiteral):
                if not condition.value:
                    # Loop never executes - replace with empty block
                    return Block(stmts=[], line=node.line)
                # else: infinite loop, keep as-is
            
            return WhileStmt(
                condition=condition,
                body=self._constant_fold(node.body),
                line=node.line
            )
        
        elif isinstance(node, Block):
            return Block(
                stmts=[self._constant_fold(stmt) for stmt in node.stmts],
                line=node.line
            )
        
        elif isinstance(node, Program):
            return Program(body=[self._constant_fold(stmt) for stmt in node.body])
        
        elif isinstance(node, FuncDecl):
            return self._copy_dynamic_node_attrs(
                node,
                FuncDecl(
                    name=node.name,
                    params=list(node.params),
                    defaults=[
                        self._constant_fold(default) if isinstance(default, Node) else default
                        for default in node.defaults
                    ],
                    varargs=node.varargs,
                    body=self._constant_fold(node.body),
                    return_type=node.return_type,
                    is_async=node.is_async,
                    vibhakti_signature=getattr(node, "vibhakti_signature", None),
                    line=node.line,
                ),
            )
        
        # For other nodes, return as-is
        return node

    def _stmt_completion_kinds(self, node: Node | None) -> set[str]:
        """Return the possible control-flow exits for a statement node."""
        if node is None:
            return {"fallthrough"}

        if isinstance(node, (VarDecl, ConstDecl, PrintStmt, ImportStmt, ExprStmt, GlobalStmt, NonlocalStmt, FuncDecl, ClassDecl, DataDecl, ProofDeclaration, SutraDecl, ParinamaDecl)):
            return {"fallthrough"}

        if isinstance(node, ReturnStmt):
            return {"return"}

        if isinstance(node, ThrowStmt):
            return {"throw"}

        if isinstance(node, BreakStmt):
            return {"break"}

        if isinstance(node, ContinueStmt):
            return {"continue"}

        if isinstance(node, Program):
            return self._block_completion_kinds(node.body)

        if isinstance(node, Block):
            return self._block_completion_kinds(node.stmts)

        if isinstance(node, IfStmt):
            outcomes: set[str] = set()
            outcomes.update(self._stmt_completion_kinds(node.then_body))
            for _, body in node.elif_clauses:
                outcomes.update(self._stmt_completion_kinds(body))
            if node.else_body is not None:
                outcomes.update(self._stmt_completion_kinds(node.else_body))
            else:
                outcomes.add("fallthrough")
            return outcomes

        if isinstance(node, MatchStmt):
            outcomes: set[str] = set()
            for case in node.cases:
                outcomes.update(self._stmt_completion_kinds(case.body))
            if not getattr(node, "exhaustive", False) and not any(
                self._is_catchall_pattern(case.pattern) for case in node.cases
            ):
                outcomes.add("fallthrough")
            return outcomes

        if isinstance(node, TryStmt):
            finally_kinds = (
                self._stmt_completion_kinds(node.finally_body)
                if node.finally_body is not None
                else {"fallthrough"}
            )
            if "fallthrough" not in finally_kinds:
                return finally_kinds

            outcomes = {kind for kind in finally_kinds if kind != "fallthrough"}
            outcomes.update(self._stmt_completion_kinds(node.try_body))
            for handler in node.handlers:
                outcomes.update(self._stmt_completion_kinds(handler.body))
            return outcomes

        if isinstance(node, WithStmt):
            return self._stmt_completion_kinds(node.body)

        if isinstance(node, WhileStmt):
            body_kinds = self._stmt_completion_kinds(node.body)
            escaping = {
                kind for kind in body_kinds
                if kind not in {"fallthrough", "break", "continue"}
            }
            if isinstance(node.condition, BoolLiteral):
                if not node.condition.value:
                    return {"fallthrough"}
                outcomes = set(escaping)
                if "break" in body_kinds:
                    outcomes.add("fallthrough")
                return outcomes
            return {"fallthrough"} | escaping

        if isinstance(node, ForStmt):
            body_kinds = self._stmt_completion_kinds(node.body)
            escaping = {
                kind for kind in body_kinds
                if kind not in {"fallthrough", "break", "continue"}
            }
            return {"fallthrough"} | escaping

        return {"fallthrough"}

    def _block_completion_kinds(self, statements: list[Node]) -> set[str]:
        outcomes: set[str] = set()
        fallthrough_active = True

        for stmt in statements:
            if not fallthrough_active:
                break

            stmt_kinds = self._stmt_completion_kinds(stmt)
            if "fallthrough" in stmt_kinds:
                outcomes.update(kind for kind in stmt_kinds if kind != "fallthrough")
            else:
                outcomes.update(stmt_kinds)
                fallthrough_active = False

        if fallthrough_active:
            outcomes.add("fallthrough")

        return outcomes

    def _eliminate_dead_stmt_list(self, statements: list[Node]) -> list[Node]:
        optimized: list[Node] = []
        for stmt in statements:
            new_stmt = self._eliminate_dead_code(stmt)
            if new_stmt is None:
                continue
            optimized.append(new_stmt)
            if "fallthrough" not in self._stmt_completion_kinds(new_stmt):
                break
        return optimized

    def _eliminate_dead_code(self, node: Node | None) -> Node | None:
        """
        Perform safe AST-level dead-code elimination.

        This pass removes statements that are unreachable after explicit
        control-flow terminators without inspecting raw bytecode bytes.
        """
        if node is None:
            return None

        if isinstance(node, Program):
            node.body = self._eliminate_dead_stmt_list(node.body)
            return node

        if isinstance(node, Block):
            node.stmts = self._eliminate_dead_stmt_list(node.stmts)
            return node

        if isinstance(node, FuncDecl):
            node.defaults = [
                self._eliminate_dead_code(default) if isinstance(default, Node) else default
                for default in node.defaults
            ]
            node.body = self._eliminate_dead_code(node.body)
            return node

        if isinstance(node, LambdaExpr):
            node.body = self._eliminate_dead_code(node.body)
            return node

        if isinstance(node, ClassDecl):
            node.superclass = self._eliminate_dead_code(node.superclass)
            node.body = self._eliminate_dead_code(node.body)
            return node

        if isinstance(node, IfStmt):
            node.condition = self._eliminate_dead_code(node.condition)
            node.then_body = self._eliminate_dead_code(node.then_body)
            node.elif_clauses = [
                (self._eliminate_dead_code(cond), self._eliminate_dead_code(body))
                for cond, body in node.elif_clauses
            ]
            node.else_body = self._eliminate_dead_code(node.else_body)
            return node

        if isinstance(node, WhileStmt):
            node.condition = self._eliminate_dead_code(node.condition)
            node.body = self._eliminate_dead_code(node.body)
            return node

        if isinstance(node, ForStmt):
            node.iterable = self._eliminate_dead_code(node.iterable)
            node.body = self._eliminate_dead_code(node.body)
            return node

        if isinstance(node, WithStmt):
            node.expr = self._eliminate_dead_code(node.expr)
            node.body = self._eliminate_dead_code(node.body)
            return node

        if isinstance(node, TryStmt):
            node.try_body = self._eliminate_dead_code(node.try_body)
            node.handlers = [
                CatchHandler(
                    match_name=handler.match_name,
                    bind_name=handler.bind_name,
                    body=self._eliminate_dead_code(handler.body),
                    line=handler.line,
                )
                for handler in node.handlers
            ]
            node.finally_body = self._eliminate_dead_code(node.finally_body)
            return node

        if isinstance(node, MatchStmt):
            node.subject = self._eliminate_dead_code(node.subject)
            node.cases = [
                self._copy_dynamic_node_attrs(
                    case,
                    MatchCase(
                        pattern=case.pattern,
                        body=self._eliminate_dead_code(case.body),
                        guard=self._eliminate_dead_code(case.guard),
                        line=case.line,
                    ),
                )
                for case in node.cases
            ]
            return node

        if isinstance(node, VarDecl):
            node.value = self._eliminate_dead_code(node.value)
            return node

        if isinstance(node, ConstDecl):
            node.value = self._eliminate_dead_code(node.value)
            return node

        if isinstance(node, PrintStmt):
            node.values = [self._eliminate_dead_code(value) for value in node.values]
            return node

        if isinstance(node, ReturnStmt):
            node.value = self._eliminate_dead_code(node.value)
            return node

        if isinstance(node, ThrowStmt):
            node.value = self._eliminate_dead_code(node.value)
            return node

        if isinstance(node, ExprStmt):
            node.expr = self._eliminate_dead_code(node.expr)
            return node

        if isinstance(node, ProofDeclaration):
            node.evidence_body = self._eliminate_dead_code(node.evidence_body)
            if isinstance(node.statement_expr, Node):
                node.statement_expr = self._eliminate_dead_code(node.statement_expr)
            return node

        if isinstance(node, CallExpr):
            node.callee = self._eliminate_dead_code(node.callee)
            node.args = [self._eliminate_dead_code(arg) for arg in node.args]
            node.kwargs = {
                key: self._eliminate_dead_code(value)
                for key, value in node.kwargs.items()
            }
            return node

        if isinstance(node, AssignExpr):
            node.target = self._eliminate_dead_code(node.target)
            node.value = self._eliminate_dead_code(node.value)
            return node

        if isinstance(node, BinaryExpr):
            node.left = self._eliminate_dead_code(node.left)
            node.right = self._eliminate_dead_code(node.right)
            return node

        if isinstance(node, UnaryExpr):
            node.operand = self._eliminate_dead_code(node.operand)
            return node

        if isinstance(node, ConditionalExpr):
            node.condition = self._eliminate_dead_code(node.condition)
            node.then_expr = self._eliminate_dead_code(node.then_expr)
            node.else_expr = self._eliminate_dead_code(node.else_expr)
            return node

        if isinstance(node, MemberExpr):
            node.obj = self._eliminate_dead_code(node.obj)
            return node

        if isinstance(node, IndexExpr):
            node.obj = self._eliminate_dead_code(node.obj)
            node.index = self._eliminate_dead_code(node.index)
            return node

        if isinstance(node, SliceExpr):
            node.obj = self._eliminate_dead_code(node.obj)
            node.start = self._eliminate_dead_code(node.start)
            node.stop = self._eliminate_dead_code(node.stop)
            node.step = self._eliminate_dead_code(node.step)
            return node

        if isinstance(node, (ListLiteral, TupleLiteral, SetLiteral)):
            node.elements = [self._eliminate_dead_code(element) for element in node.elements]
            return node

        if isinstance(node, DictLiteral):
            node.pairs = [
                (self._eliminate_dead_code(key), self._eliminate_dead_code(value))
                for key, value in node.pairs
            ]
            return node

        if isinstance(node, ListComp):
            node.expr = self._eliminate_dead_code(node.expr)
            node.iterable = self._eliminate_dead_code(node.iterable)
            node.filter_expr = self._eliminate_dead_code(node.filter_expr)
            return node

        if isinstance(node, DictComp):
            node.key_expr = self._eliminate_dead_code(node.key_expr)
            node.value_expr = self._eliminate_dead_code(node.value_expr)
            node.iterable = self._eliminate_dead_code(node.iterable)
            node.filter_expr = self._eliminate_dead_code(node.filter_expr)
            return node

        if isinstance(node, FStringExpr):
            node.parts = [
                self._eliminate_dead_code(part) if isinstance(part, Node) else part
                for part in node.parts
            ]
            return node

        if isinstance(node, AwaitExpr):
            node.operand = self._eliminate_dead_code(node.operand)
            return node

        if isinstance(node, RewriteRule):
            node.pattern = self._eliminate_dead_code(node.pattern)
            node.replacement = self._eliminate_dead_code(node.replacement)
            return node

        if isinstance(node, ParinamaDecl):
            node.rules = [self._eliminate_dead_code(rule) for rule in node.rules]
            return node

        if isinstance(node, SutraDecl):
            node.expansion = self._eliminate_dead_code(node.expansion)
            node.patterns = [
                self._eliminate_dead_code(pattern) if isinstance(pattern, Node) else pattern
                for pattern in node.patterns
            ]
            return node

        return node
