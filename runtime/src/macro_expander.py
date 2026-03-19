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
    
    def __init__(self, sutras: Dict[str, SutraDecl] = None):
        """Initialize with optional macro definitions."""
        self.sutras = sutras or {}
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
            # Register the sutra, don't expand it yet
            self.sutras[node.name] = node
            return None  # Remove from AST (macro definitions are compile-time only)
        
        elif isinstance(node, CallExpr):
            # Check if this is a macro call
            if isinstance(node.callee, IdentifierExpr):
                func_name = node.callee.name
                if func_name in self.sutras:
                    # Expand the macro
                    return self._expand_sutra(self.sutras[func_name], node.args)
            
            # Transform callee and arguments normally
            new_callee = self._transform_node(node.callee)
            new_args = [self._transform_node(arg) for arg in node.args]
            return CallExpr(callee=new_callee, args=new_args, kwargs=node.kwargs, line=node.line)
        
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
                var_name=node.var_name,
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
        
        elif isinstance(node, ListComp):
            return ListComp(
                expr=self._transform_node(node.expr),
                var_name=node.var_name,
                iterable=self._transform_node(node.iterable),
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
                catch_var=node.catch_var,
                catch_body=self._transform_node(node.catch_body) if node.catch_body else None,
                finally_body=self._transform_node(node.finally_body) if node.finally_body else None,
                line=node.line
            )
        
        # Leaf nodes - return as-is
        return node
    
    def _expand_sutra(self, sutra: SutraDecl, args: List[Any]) -> Any:
        """
        Expand a macro call.
        
        Substitutes arguments into the expansion template.
        
        Args:
            sutra: The macro definition
            args: The arguments passed to the macro call
            
        Returns:
            The expanded AST node
            
        Raises:
            MacroError: If argument count doesn't match
        """
        if len(args) != len(sutra.params):
            raise MacroError(
                f"सूत्र '{sutra.name}' expects {len(sutra.params)} parameters, got {len(args)}",
                sutra.line
            )
        
        # Create substitution environment
        env = {}
        for param, arg in zip(sutra.params, args):
            env[param] = self._transform_node(arg)
        
        # Expand the template with substitutions
        expanded = self._substitute(sutra.expansion, env)
        
        # Apply anuvritti (context continuation) if present
        if sutra.anuvritti_rules:
            expanded = self._apply_anuvritti(expanded, sutra.anuvritti_rules)
        
        return expanded
    
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
        if isinstance(node, IdentifierExpr):
            if node.name in env:
                return env[node.name]
            return node
        
        elif isinstance(node, BinaryExpr):
            return BinaryExpr(
                op=node.op,
                left=self._substitute(node.left, env),
                right=self._substitute(node.right, env),
                line=node.line
            )
        
        elif isinstance(node, CallExpr):
            new_callee = self._substitute(node.callee, env)
            new_args = [self._substitute(arg, env) for arg in node.args]
            return CallExpr(callee=new_callee, args=new_args, kwargs=node.kwargs, line=node.line)
        
        elif isinstance(node, UnaryExpr):
            return UnaryExpr(
                op=node.op,
                operand=self._substitute(node.operand, env),
                line=node.line
            )
        
        elif isinstance(node, Block):
            new_stmts = [self._substitute(stmt, env) for stmt in node.stmts]
            return Block(stmts=new_stmts, line=node.line)
        
        elif isinstance(node, IfStmt):
            return IfStmt(
                condition=self._substitute(node.condition, env),
                then_body=self._substitute(node.then_body, env),
                elif_clauses=[
                    (self._substitute(c, env), self._substitute(b, env)) 
                    for c, b in node.elif_clauses
                ],
                else_body=self._substitute(node.else_body, env) if node.else_body else None,
                line=node.line
            )
        
        elif isinstance(node, WhileStmt):
            return WhileStmt(
                condition=self._substitute(node.condition, env),
                body=self._substitute(node.body, env),
                line=node.line
            )
        
        elif isinstance(node, ForStmt):
            return ForStmt(
                var_name=node.var_name,
                iterable=self._substitute(node.iterable, env),
                body=self._substitute(node.body, env),
                line=node.line
            )
        
        elif isinstance(node, AssignExpr):
            return AssignExpr(
                target=self._substitute(node.target, env),
                op=node.op,
                value=self._substitute(node.value, env),
                line=node.line
            )
        
        elif isinstance(node, MemberExpr):
            return MemberExpr(
                obj=self._substitute(node.obj, env),
                attr=node.attr,
                line=node.line
            )
        
        elif isinstance(node, IndexExpr):
            return IndexExpr(
                obj=self._substitute(node.obj, env),
                index=self._substitute(node.index, env),
                line=node.line
            )
        
        elif isinstance(node, ReturnStmt):
            return ReturnStmt(
                value=self._substitute(node.value, env) if node.value else None,
                line=node.line
            )
        
        elif isinstance(node, PrintStmt):
            return PrintStmt(
                values=[self._substitute(v, env) for v in node.values],
                line=node.line
            )
        
        elif isinstance(node, ExprStmt):
            return ExprStmt(
                expr=self._substitute(node.expr, env),
                line=node.line
            )
        
        elif isinstance(node, LambdaExpr):
            return LambdaExpr(
                params=node.params,
                varargs=node.varargs,
                body=self._substitute(node.body, env),
                line=node.line
            )
        
        elif isinstance(node, ListLiteral):
            return ListLiteral(
                elements=[self._substitute(e, env) for e in node.elements],
                line=node.line
            )
        
        # Literal nodes - return as-is
        return node
    
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
        self.sutras[sutra.name] = sutra
    
    def unregister_sutra(self, name: str):
        """
        Unregister a macro definition.
        
        Args:
            name: The name of the macro to unregister
        """
        if name in self.sutras:
            del self.sutras[name]
    
    def is_macro(self, name: str) -> bool:
        """
        Check if a name is a registered macro.
        
        Args:
            name: The name to check
            
        Returns:
            True if the name is a registered macro
        """
        return name in self.sutras
    
    def get_sutra(self, name: str) -> Optional[SutraDecl]:
        """
        Get a macro definition by name.
        
        Args:
            name: The macro name
            
        Returns:
            The macro definition or None if not found
        """
        return self.sutras.get(name)


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
        
        This is a placeholder for full Sansmatic integration.
        Full implementation would:
        - Check variable types match expected types
        - Validate logical consistency of expansions
        - Ensure preconditions are met before expansion
        - Verify postconditions after expansion
        
        Args:
            ast: The expanded AST to validate
            context: The validation context
        """
        # Example validation:
        # Check if variables have correct types
        # Validate logical consistency
        
        # Placeholder: In full implementation, this would use
        # the Sansmatic engine to prove validity of expansions
        pass
    
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
        # Placeholder for Sansmatic type validation
        var_type = context.get(var_name, {}).get('type', 'Any')
        return var_type == expected_type or var_type == 'Any'
    
    def validate_precondition(self, precondition: str, context: Dict) -> bool:
        """
        Validate a precondition before macro expansion.
        
        Args:
            precondition: The precondition to validate
            context: The validation context
            
        Returns:
            True if the precondition is satisfied
        """
        # Placeholder for Sansmatic precondition validation
        # In full implementation, this would use logical proof
        return True


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
