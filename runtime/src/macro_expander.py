# वाक् भाषा - सूत्र विस्तारक (Macro Expander)
# Vak Language - Compile-time Macro Expansion
#
# Implements Pāṇini's Aṣṭādhyāyī-inspired macro system:
# - सूत्र (Sūtra): Macro definition rules
# - अनुवाद (Anuvāda): Translation/expansion template
# - अनुवृत्ति (Anuvṛtti): Context continuation across rules

from typing import Any, Dict, List, Optional
from .ast_nodes import *
from .errors import MacroError
from .rewrite_engine import (
    match_pattern,
    pattern_specificity,
    rewrite_fixed_point,
    substitute_bindings,
)


class MacroExpander:
    """
    Compile-time AST transformer for Pāṇinian macros.
    
    Expands सूत्र (macro) definitions into their अनुवाद (translations).
    Uses pattern matching and context-aware expansion.
    
    Architecture inspired by:
    - Lisp macros (compile-time AST transformation)
    - Pāṇini's Aṣṭādhyāyī (rule-based grammar)
    - Anuvritti (context continuation across rules)
    
    Example usage:
        सूत्र double(x):
            अनुवाद -> x * 2
        
        double(5)  # Expands to: 5 * 2
    """
    
    def __init__(self, sutras: Dict[str, Any] = None):
        """Initialize with optional macro definitions."""
        self.sutras: Dict[str, List[SutraDecl]] = {}
        if sutras:
            for name, value in sutras.items():
                if isinstance(value, list):
                    self.sutras[name] = list(value)
                else:
                    self.sutras[name] = [value]
        self.parinama: Dict[str, ParinamaDecl] = {}
        self.anuvritti = {}  # Context continuation
    
    def expand(self, ast: Program) -> Program:
        """
        Expand all macros in the AST.
        
        Walks the AST and replaces macro calls with their expansions.
        Must be run BEFORE bytecode generation.
        
        Args:
            ast: The parsed AST (Program node)
            
        Returns:
            Transformed AST with all macros expanded
        """
        return self._transform_node(ast)
    
    def _transform_node(self, node: Node) -> Optional[Node]:
        """
        Recursively transform AST nodes.
        
        This is the core transformation engine that:
        1. Registers SutraDecl nodes (macro definitions)
        2. Expands CallExpr nodes that match registered macros
        3. Recursively transforms all other nodes
        """
        if isinstance(node, Program):
            new_body = []
            for stmt in node.body:
                transformed = self._transform_node(stmt)
                if isinstance(transformed, list):
                    new_body.extend(transformed)
                elif transformed is not None:
                    new_body.append(transformed)
            return Program(body=new_body)
        
        elif isinstance(node, SutraDecl):
            self.register_sutra(node)
            return None  # Remove from AST (macro definitions are compile-time only)

        elif isinstance(node, ParinamaDecl):
            self.parinama[node.name] = node
            return node  # Keep for runtime registration while still enabling compile-time rewrites
        
        elif isinstance(node, CallExpr):
            if isinstance(node.callee, IdentifierExpr):
                func_name = node.callee.name
                if func_name in self.parinama:
                    return self._expand_parinama(self.parinama[func_name], node.args, node.kwargs, node.line)
                if func_name in self.sutras:
                    return self._expand_sutra(func_name, node.args, node.kwargs, node.line)
            
            new_callee = self._transform_node(node.callee)
            new_args = [self._transform_node(arg) for arg in node.args]
            new_kwargs = {key: self._transform_node(value) for key, value in node.kwargs.items()}
            return CallExpr(callee=new_callee, args=new_args, kwargs=new_kwargs, line=node.line)
        
        elif isinstance(node, BinaryExpr):
            return BinaryExpr(
                op=node.op,
                left=self._transform_node(node.left),
                right=self._transform_node(node.right),
                line=node.line
            )
        
        elif isinstance(node, UnaryExpr):
            return UnaryExpr(
                op=node.op,
                operand=self._transform_node(node.operand),
                line=node.line
            )
        
        elif isinstance(node, IfStmt):
            return IfStmt(
                condition=self._transform_node(node.condition),
                then_body=self._transform_node(node.then_body),
                elif_clauses=[
                    (self._transform_node(c), self._transform_node(b)) 
                    for c, b in node.elif_clauses
                ],
                else_body=self._transform_node(node.else_body) if node.else_body else None,
                line=node.line
            )
        
        elif isinstance(node, WhileStmt):
            return WhileStmt(
                condition=self._transform_node(node.condition),
                body=self._transform_node(node.body),
                line=node.line
            )
        
        elif isinstance(node, ForStmt):
            return ForStmt(
                var_names=list(node.var_names),
                iterable=self._transform_node(node.iterable),
                body=self._transform_node(node.body),
                line=node.line
            )
        
        elif isinstance(node, FuncDecl):
            return FuncDecl(
                name=node.name,
                params=node.params,
                defaults=node.defaults,
                varargs=node.varargs,
                body=self._transform_node(node.body),
                return_type=node.return_type,
                is_async=node.is_async,
                vibhakti_signature=getattr(node, 'vibhakti_signature', None),
                line=node.line
            )
        
        elif isinstance(node, ClassDecl):
            return ClassDecl(
                name=node.name,
                superclass=self._transform_node(node.superclass) if node.superclass else None,
                body=self._transform_node(node.body),
                line=node.line
            )
        
        elif isinstance(node, VarDecl):
            return VarDecl(
                names=node.names,
                value=self._transform_node(node.value) if node.value else None,
                type_hint=node.type_hint,
                line=node.line
            )
        
        elif isinstance(node, ConstDecl):
            return ConstDecl(
                name=node.name,
                value=self._transform_node(node.value),
                type_hint=node.type_hint,
                line=node.line
            )
        
        elif isinstance(node, ReturnStmt):
            return ReturnStmt(
                value=self._transform_node(node.value) if node.value else None,
                line=node.line
            )
        
        elif isinstance(node, PrintStmt):
            return PrintStmt(
                values=[self._transform_node(v) for v in node.values],
                line=node.line
            )
        
        elif isinstance(node, Block):
            new_stmts = []
            for stmt in node.stmts:
                transformed = self._transform_node(stmt)
                if isinstance(transformed, list):
                    new_stmts.extend(transformed)
                elif transformed is not None:
                    new_stmts.append(transformed)
            return Block(stmts=new_stmts, line=node.line)
        
        elif isinstance(node, ExprStmt):
            return ExprStmt(
                expr=self._transform_node(node.expr),
                line=node.line
            )
        
        elif isinstance(node, AssignExpr):
            return AssignExpr(
                target=self._transform_node(node.target),
                op=node.op,
                value=self._transform_node(node.value),
                line=node.line
            )
        
        elif isinstance(node, MemberExpr):
            return MemberExpr(
                obj=self._transform_node(node.obj),
                attr=node.attr,
                line=node.line
            )
        
        elif isinstance(node, IndexExpr):
            return IndexExpr(
                obj=self._transform_node(node.obj),
                index=self._transform_node(node.index),
                line=node.line
            )
        
        elif isinstance(node, LambdaExpr):
            return LambdaExpr(
                params=node.params,
                varargs=node.varargs,
                body=self._transform_node(node.body),
                line=node.line
            )
        
        elif isinstance(node, ListLiteral):
            return ListLiteral(
                elements=[self._transform_node(e) for e in node.elements],
                line=node.line
            )

        elif isinstance(node, TupleLiteral):
            return TupleLiteral(
                elements=[self._transform_node(e) for e in node.elements],
                line=node.line
            )
        
        elif isinstance(node, ListComp):
            return ListComp(
                expr=self._transform_node(node.expr),
                var_name=node.var_name,
                iterable=self._transform_node(node.iterable),
                filter_expr=self._transform_node(node.filter_expr) if node.filter_expr else None,
                line=node.line
            )

        elif isinstance(node, DictComp):
            return DictComp(
                key_expr=self._transform_node(node.key_expr),
                value_expr=self._transform_node(node.value_expr),
                var_name=node.var_name,
                iterable=self._transform_node(node.iterable),
                filter_expr=self._transform_node(node.filter_expr) if node.filter_expr else None,
                line=node.line
            )
        
        elif isinstance(node, DictLiteral):
            return DictLiteral(
                pairs=[(self._transform_node(k), self._transform_node(v)) for k, v in node.pairs],
                line=node.line
            )
        
        elif isinstance(node, WithStmt):
            return WithStmt(
                expr=self._transform_node(node.expr),
                var_name=node.var_name,
                body=self._transform_node(node.body),
                line=node.line
            )
        
        elif isinstance(node, TryStmt):
            return TryStmt(
                try_body=self._transform_node(node.try_body),
                handlers=[
                    CatchHandler(
                        match_name=handler.match_name,
                        bind_name=handler.bind_name,
                        body=self._transform_node(handler.body),
                        line=handler.line,
                    )
                    for handler in node.handlers
                ],
                finally_body=self._transform_node(node.finally_body) if node.finally_body else None,
                line=node.line
            )
        
        # Leaf nodes - return as-is
        return node
    
    def _expand_sutra(self, name: str, args: List[Any], kwargs: Dict[str, Any], line: int) -> Any:
        """
        Expand a macro call.
        
        Substitutes arguments into the expansion template.
        
        Args:
            name: The macro family name
            args: The arguments passed to the macro call
            
        Returns:
            The expanded AST node
            
        Raises:
            MacroError: If argument count doesn't match
        """
        transformed_args = [self._transform_node(arg) for arg in args]
        scope = self._extract_scope(kwargs)
        extra_kwargs = {key: value for key, value in kwargs.items() if key not in ('अधिकार', 'scope')}
        if extra_kwargs:
            raise MacroError(f"सूत्र '{name}' does not accept keyword arguments", line)

        rules = self.sutras.get(name, [])
        matches = []
        for index, sutra in enumerate(rules):
            if len(transformed_args) != len(sutra.patterns):
                continue
            if not self._scope_matches(sutra.scope, scope):
                continue

            env = {}
            for pattern, arg in zip(sutra.patterns, transformed_args):
                env = match_pattern(pattern, arg, env)
                if env is None:
                    break
            if env is None:
                continue

            matches.append((
                1 if sutra.is_apavada else 0,
                1 if scope is not None and sutra.scope == scope else 0,
                sum(pattern_specificity(pattern) for pattern in sutra.patterns),
                -index,
                sutra,
                env,
            ))

        if not matches:
            raise MacroError(f"सूत्र '{name}' के लिए कोई उपयुक्त नियम नहीं मिला", line)

        apavada_matches = [item for item in matches if item[0] == 1]
        selected_pool = apavada_matches or matches
        selected_pool.sort(reverse=True)
        best = selected_pool[0]
        ambiguous = [item for item in selected_pool if item[:3] == best[:3]]
        if len(ambiguous) > 1:
            raise MacroError(f"सूत्र '{name}' के लिए अस्पष्ट नियम चयन", line)

        _, _, _, _, sutra, env = best
        expanded = substitute_bindings(sutra.expansion, env)
        if sutra.anuvritti_rules:
            expanded = self._apply_anuvritti(expanded, sutra.anuvritti_rules)
        return self._transform_node(expanded)

    def _expand_parinama(self, decl: ParinamaDecl, args: List[Any], kwargs: Dict[str, Any], line: int) -> Any:
        if len(args) != 1:
            raise MacroError(f"पारिणाम '{decl.name}' expects exactly one argument", line)

        scope = self._extract_scope(kwargs)
        extra_kwargs = {key: value for key, value in kwargs.items() if key not in ('अधिकार', 'scope')}
        if extra_kwargs:
            raise MacroError(f"पारिणाम '{decl.name}' does not accept keyword arguments", line)

        if not self._scope_matches(decl.scope, scope):
            raise MacroError(f"पारिणाम '{decl.name}' is not visible in scope '{scope}'", line)

        rewritten = rewrite_fixed_point(self._transform_node(args[0]), decl.rules)
        return self._transform_node(rewritten)

    def _extract_scope(self, kwargs: Dict[str, Any]) -> Optional[str]:
        scope_expr = kwargs.get('अधिकार', kwargs.get('scope'))
        if scope_expr is None:
            return None
        scope_expr = self._transform_node(scope_expr)
        if isinstance(scope_expr, StringLiteral):
            return scope_expr.value
        if isinstance(scope_expr, IdentifierExpr):
            return scope_expr.name
        raise MacroError("अधिकार must be a string or identifier literal", getattr(scope_expr, 'line', 0))

    def _scope_matches(self, declared_scope: Optional[str], requested_scope: Optional[str]) -> bool:
        if declared_scope is None:
            return True
        if requested_scope is None:
            return False
        return declared_scope == requested_scope
    
    def _substitute(self, node: Node, env: Dict[str, Any]) -> Any:
        """
        Substitute variables in expansion template.
        
        Replaces identifier nodes with their bound values.
        
        Args:
            node: The AST node to substitute in
            env: The substitution environment (param -> arg mapping)
            
        Returns:
            The node with substitutions applied
        """
        return substitute_bindings(node, env)
    
    def _apply_anuvritti(self, node: Node, rules: List[Any]) -> Node:
        """
        Apply anuvritti (context continuation) rules.
        
        Anuvritti allows rules to inherit context from previous rules.
        This is a simplified implementation - full implementation would
        carry context across multiple sutras.
        
        Args:
            node: The AST node to apply rules to
            rules: List of anuvritti rules
            
        Returns:
            Transformed node with anuvritti applied
        """
        # For now, just transform normally
        # Full implementation would carry context across multiple sutras
        # and apply transformation rules based on inherited context
        return self._transform_node(node)
    
    def register_sutra(self, sutra: SutraDecl):
        """
        Register a macro definition.
        
        Args:
            sutra: The macro definition to register
        """
        bucket = self.sutras.setdefault(sutra.name, [])
        if sutra not in bucket:
            bucket.append(sutra)
    
    def unregister_sutra(self, name: str):
        """
        Unregister a macro definition.
        
        Args:
            name: The name of the macro to unregister
        """
        self.sutras.pop(name, None)
        self.parinama.pop(name, None)
    
    def is_macro(self, name: str) -> bool:
        """
        Check if a name is a registered macro.
        
        Args:
            name: The name to check
            
        Returns:
            True if the name is a registered macro
        """
        return name in self.sutras or name in self.parinama
    
    def get_sutra(self, name: str) -> Optional[Any]:
        """
        Get a macro definition by name.
        
        Args:
            name: The macro name
            
        Returns:
            The macro definition or None if not found
        """
        if name in self.sutras:
            return self.sutras.get(name)
        return self.parinama.get(name)


class SansmaticMacroEngine:
    """
    Macro engine integrated with Sansmatic reasoning.
    
    Uses Sansmatic to validate macro expansions logically.
    Only expands macros if they pass logical proof.
    
    Example validation:
        "Only expand this loop if x is a Number"
        "Only expand this macro if precondition P holds"
    """
    
    def __init__(self, sansmatic_engine=None):
        """
        Initialize with optional Sansmatic engine.
        
        Args:
            sansmatic_engine: Optional Sansmatic logic engine for validation
        """
        self.sansmatic = sansmatic_engine
        self.expander = MacroExpander()
    
    def expand_with_proof(self, ast: Program, context: Dict = None) -> Program:
        """
        Expand macros with logical validation.
        
        Before expanding a macro, checks if the expansion is logically valid.
        For example: "Only expand this loop if x is a Number"
        
        Args:
            ast: The AST to expand
            context: Optional context for validation (variable types, etc.)
            
        Returns:
            Transformed AST with validated macro expansions
        """
        context = context or {}
        
        # Register all sutras first
        sutras = {}
        for node in ast.body:
            if isinstance(node, SutraDecl):
                sutras[node.name] = node
        
        self.expander = MacroExpander(sutras=sutras)
        
        # Expand with validation
        expanded_ast = self.expander.expand(ast)
        
        # Validate with Sansmatic if available
        if self.sansmatic:
            self._validate_expansion(expanded_ast, context)
        
        return expanded_ast
    
    def _validate_expansion(self, ast: Program, context: Dict):
        """
        Validate macro expansion using Sansmatic logic.

        The validation surface is intentionally small but real:
        - seed declared facts and rules into Sansmatic
        - enforce explicit type constraints
        - reject failed preconditions/postconditions
        """
        facts = context.get('facts', [])
        rules = context.get('rules', [])
        type_constraints = context.get('type_constraints', {})
        preconditions = context.get('preconditions', [])
        postconditions = context.get('postconditions', [])

        for fact in facts:
            if isinstance(fact, tuple) and len(fact) == 3:
                self.sansmatic.add_fact(str(fact[0]), str(fact[1]), str(fact[2]), source='macro')
            else:
                parsed = self.sansmatic.parse_statement(fact)
                if parsed.get('kind') == 'fact':
                    self.sansmatic.add_fact(*parsed['fact'], source='macro')

        for rule in rules:
            if isinstance(rule, tuple) and len(rule) == 2:
                self.sansmatic.rule(rule[0], rule[1])

        for var_name, expected_type in type_constraints.items():
            if not self.validate_type_constraint(var_name, expected_type, context):
                raise ValueError(
                    f"Sansmatic type validation failed for {var_name}: expected {expected_type}"
                )

        for precondition in preconditions:
            if not self.validate_precondition(precondition, context):
                raise ValueError(f"Sansmatic precondition failed: {precondition}")

        for postcondition in postconditions:
            if not self.validate_precondition(postcondition, context):
                raise ValueError(f"Sansmatic postcondition failed: {postcondition}")

        if self.sansmatic.contradictions:
            raise ValueError(
                f"Sansmatic contradiction after macro expansion: {self.sansmatic.contradictions[0]}"
            )
    
    def validate_type_constraint(self, var_name: str, expected_type: str, context: Dict) -> bool:
        """
        Validate a type constraint using Sansmatic logic.
        
        Args:
            var_name: The variable name to check
            expected_type: The expected type
            context: The validation context
            
        Returns:
            True if the constraint is satisfied
        """
        var_type = context.get(var_name, {}).get('type', 'Any')
        if var_type == expected_type or var_type == 'Any':
            if self.sansmatic:
                self.sansmatic.add_fact(var_name, 'IS', var_type, source='macro-type')
            return True

        if self.sansmatic:
            probe = self.sansmatic.clone(verbose=False)
            probe.add_fact(var_name, 'IS', var_type, source='macro-type')
            return probe.verify_statement((var_name, 'IS', expected_type))
        return False
    
    def validate_precondition(self, precondition: str, context: Dict) -> bool:
        """
        Validate a precondition before macro expansion.
        
        Args:
            precondition: The precondition to validate
            context: The validation context
            
        Returns:
            True if the precondition is satisfied
        """
        if not self.sansmatic:
            if precondition in context:
                return bool(context[precondition])
            return False

        probe = self.sansmatic.clone(verbose=False)
        facts = context.get('facts', [])
        for fact in facts:
            if isinstance(fact, tuple) and len(fact) == 3:
                probe.add_fact(str(fact[0]), str(fact[1]), str(fact[2]), source='macro')
        return probe.verify_statement(precondition)


# ── Convenience Functions ─────────────────────────────────────────────────────

def expand_macros(ast: Program, sutras: Dict[str, SutraDecl] = None) -> Program:
    """
    Convenience function to expand macros in an AST.
    
    Args:
        ast: The AST to expand
        sutras: Optional pre-defined macro definitions
        
    Returns:
        Transformed AST with all macros expanded
    """
    expander = MacroExpander(sutras=sutras)
    return expander.expand(ast)


def expand_with_validation(ast: Program, sansmatic_engine=None, context: Dict = None) -> Program:
    """
    Convenience function to expand macros with Sansmatic validation.
    
    Args:
        ast: The AST to expand
        sansmatic_engine: Optional Sansmatic engine for validation
        context: Optional validation context
        
    Returns:
        Transformed AST with validated macro expansions
    """
    engine = SansmaticMacroEngine(sansmatic_engine)
    return engine.expand_with_proof(ast, context)
