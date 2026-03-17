# वाक् भाषा - व्याकरण विश्लेषक (Parser)
# Vak Language - Recursive Descent Parser

from .tokens import Token, TokenType
from .ast_nodes import *
from .errors import ParseError


class Parser:
    """
    Converts a flat token list into a typed AST.

    Grammar summary (simplified BNF):

    program     → stmt* EOF
    stmt        → var_decl | const_decl | func_decl | class_decl
                | if_stmt | while_stmt | for_stmt
                | return_stmt | print_stmt | break_stmt | continue_stmt
                | try_stmt | throw_stmt | import_stmt
                | expr_stmt
    block       → NEWLINE INDENT stmt+ DEDENT
    """

    def __init__(self, tokens: list):
        self.tokens  = [t for t in tokens
                        if t.type != TokenType.COMMENT]
        self.pos     = 0

    # ── Token helpers ─────────────────────────────────────────────────────────

    @property
    def current(self) -> Token:
        return self.tokens[self.pos]

    def peek(self, offset=1) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]  # EOF

    def check(self, *types) -> bool:
        return self.current.type in types

    def match(self, *types) -> bool:
        if self.current.type in types:
            self.pos += 1
            return True
        return False

    def expect(self, type_: TokenType, msg: str = None) -> Token:
        if self.current.type == type_:
            tok = self.current
            self.pos += 1
            return tok
        raise ParseError(
            msg or f"अपेक्षित {type_.name}, मिला {self.current.type.name}",
            self.current.line
        )

    def skip_newlines(self):
        while self.check(TokenType.NEWLINE):
            self.pos += 1

    def line(self) -> int:
        return self.current.line

    # ── Entry ─────────────────────────────────────────────────────────────────

    def parse(self) -> Program:
        stmts = []
        self.skip_newlines()
        while not self.check(TokenType.EOF):
            stmts.append(self._stmt())
            self.skip_newlines()
        return Program(body=stmts)

    # ── Statements ────────────────────────────────────────────────────────────

    def _stmt(self) -> Node:
        ln = self.line()

        if self.check(TokenType.VAR):
            return self._var_decl()
        if self.check(TokenType.CONST):
            return self._const_decl()
        if self.check(TokenType.FUNC):
            return self._func_decl()
        if self.check(TokenType.CLASS):
            return self._class_decl()
        if self.check(TokenType.IF):
            return self._if_stmt()
        if self.check(TokenType.WHILE):
            return self._while_stmt()
        if self.check(TokenType.FOR):
            return self._for_stmt()
        if self.check(TokenType.RETURN):
            return self._return_stmt()
        if self.check(TokenType.PRINT):
            return self._print_stmt()
        if self.check(TokenType.BREAK):
            self.pos += 1
            self._end_stmt()
            return BreakStmt(line=ln)
        if self.check(TokenType.CONTINUE):
            self.pos += 1
            self._end_stmt()
            return ContinueStmt(line=ln)
        if self.check(TokenType.GLOBAL):
            return self._global_stmt()
        if self.check(TokenType.NONLOCAL):
            return self._nonlocal_stmt()
        if self.check(TokenType.TRY):
            return self._try_stmt()
        if self.check(TokenType.WITH):
            return self._with_stmt()
        if self.check(TokenType.THROW):
            return self._throw_stmt()
        if self.check(TokenType.IMPORT):
            return self._import_stmt()

        return self._expr_stmt()

    def _end_stmt(self):
        """Consume optional semicolon or newline."""
        if self.check(TokenType.SEMICOLON):
            self.pos += 1
        if self.check(TokenType.NEWLINE):
            self.pos += 1

    def _var_decl(self) -> VarDecl:
        ln = self.line()
        self.expect(TokenType.VAR)
        names = [self.expect(TokenType.IDENTIFIER).value]
        while self.match(TokenType.COMMA):
            names.append(self.expect(TokenType.IDENTIFIER).value)
        
        type_hint = None
        if self.match(TokenType.COLON):
            type_hint = self.expect(TokenType.IDENTIFIER).value
            
        value = None
        if self.match(TokenType.ASSIGN):
            # Parse one or more expressions
            exprs = [self._expr()]
            while self.match(TokenType.COMMA):
                exprs.append(self._expr())
            
            if len(exprs) > 1:
                value = ListLiteral(elements=exprs, line=ln)
            else:
                value = exprs[0]
                
        self._end_stmt()
        return VarDecl(names=names, value=value, type_hint=type_hint, line=ln)

    def _const_decl(self) -> ConstDecl:
        ln = self.line()
        self.expect(TokenType.CONST)
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.ASSIGN, "स्थिर को मान चाहिए (const requires a value)")
        value = self._expr()
        self._end_stmt()
        return ConstDecl(name=name, value=value, line=ln)

    def _func_decl(self) -> FuncDecl:
        ln = self.line()
        self.expect(TokenType.FUNC)
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.LPAREN)
        params, defaults, varargs = self._param_list()
        self.expect(TokenType.RPAREN)
        
        return_type = None
        if self.match(TokenType.COLON):
            # Check if it's followed by an identifier (type hint) or an INDENT (block)
            if self.check(TokenType.IDENTIFIER):
                return_type = self.expect(TokenType.IDENTIFIER).value
                self.expect(TokenType.COLON)
            else:
                # It's the start of the block, back up or just proceed
                # Actually, our block expects a colon. We just consumed it.
                # So if no identifier, it's just the block colon.
                pass
        else:
            self.expect(TokenType.COLON)
            
        body = self._block()
        return FuncDecl(name=name, params=params, defaults=defaults,
                        varargs=varargs, body=body, return_type=return_type, line=ln)

    def _param_list(self):
        params, defaults = [], []
        varargs = None
        while not self.check(TokenType.RPAREN):
            # Check for variadic argument: *name
            if self.match(TokenType.STAR):
                varargs = self.expect(TokenType.IDENTIFIER).value
                # Variadic must be the last parameter
                if not self.check(TokenType.RPAREN):
                    raise ParseError("अनियत तर्क (*args) अंतिम होना चाहिए", self.line())
                break
                
            # Allow स्वयं (SELF) and अभिभावक (SUPER) as parameter names
            if self.check(TokenType.SELF, TokenType.SUPER):
                p = self.current.value
                self.pos += 1
            else:
                p = self.expect(TokenType.IDENTIFIER).value
            
            # Optional type hint for param
            p_type = None
            if self.match(TokenType.COLON):
                p_type = self.expect(TokenType.IDENTIFIER).value
                
            params.append((p, p_type))
            
            if self.match(TokenType.ASSIGN):
                defaults.append(self._expr())
            else:
                defaults.append(None)
            if not self.match(TokenType.COMMA):
                break
        return params, defaults, varargs

    def _class_decl(self) -> ClassDecl:
        ln = self.line()
        self.expect(TokenType.CLASS)
        name = self.expect(TokenType.IDENTIFIER).value
        superclass = None
        if self.match(TokenType.LPAREN):
            superclass = IdentifierExpr(
                name=self.expect(TokenType.IDENTIFIER).value, line=ln)
            self.expect(TokenType.RPAREN)
        self.expect(TokenType.COLON)
        body = self._block()
        return ClassDecl(name=name, superclass=superclass, body=body, line=ln)

    def _if_stmt(self) -> IfStmt:
        ln = self.line()
        self.expect(TokenType.IF)
        condition = self._expr()
        self.expect(TokenType.COLON)
        then_body = self._block()

        elif_clauses = []
        while self.check(TokenType.ELIF):
            self.pos += 1
            ec = self._expr()
            self.expect(TokenType.COLON)
            eb = self._block()
            elif_clauses.append((ec, eb))

        else_body = None
        if self.match(TokenType.ELSE):
            self.expect(TokenType.COLON)
            else_body = self._block()

        return IfStmt(condition=condition, then_body=then_body,
                      elif_clauses=elif_clauses, else_body=else_body, line=ln)

    def _while_stmt(self) -> WhileStmt:
        ln = self.line()
        self.expect(TokenType.WHILE)
        condition = self._expr()
        self.expect(TokenType.COLON)
        body = self._block()
        return WhileStmt(condition=condition, body=body, line=ln)

    def _for_stmt(self) -> ForStmt:
        ln = self.line()
        self.expect(TokenType.FOR)
        # Optional 'चर' before loop variable
        self.match(TokenType.VAR)
        var_name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.IN)
        iterable = self._expr()
        self.expect(TokenType.COLON)
        body = self._block()
        return ForStmt(var_name=var_name, iterable=iterable, body=body, line=ln)

    def _return_stmt(self) -> ReturnStmt:
        ln = self.line()
        self.expect(TokenType.RETURN)
        value = None
        if not self.check(TokenType.NEWLINE, TokenType.SEMICOLON, TokenType.EOF):
            value = self._expr()
        self._end_stmt()
        return ReturnStmt(value=value, line=ln)

    def _print_stmt(self) -> PrintStmt:
        ln = self.line()
        self.expect(TokenType.PRINT)
        values = [self._expr()]
        while self.match(TokenType.COMMA):
            values.append(self._expr())
        self._end_stmt()
        return PrintStmt(values=values, line=ln)

    def _try_stmt(self) -> TryStmt:
        ln = self.line()
        self.expect(TokenType.TRY)
        self.expect(TokenType.COLON)
        try_body = self._block()

        catch_var, catch_body = None, None
        if self.match(TokenType.CATCH):
            if self.check(TokenType.IDENTIFIER):
                catch_var = self.current.value
                self.pos += 1
            self.expect(TokenType.COLON)
            catch_body = self._block()

        finally_body = None
        if self.match(TokenType.FINALLY):
            self.expect(TokenType.COLON)
            finally_body = self._block()

        return TryStmt(try_body=try_body, catch_var=catch_var,
                       catch_body=catch_body, finally_body=finally_body, line=ln)

    def _with_stmt(self) -> WithStmt:
        ln = self.line()
        self.expect(TokenType.WITH)
        expr = self._expr()
        
        var_name = None
        if self.match(TokenType.AS):
            var_name = self.expect(TokenType.IDENTIFIER).value
            
        self.expect(TokenType.COLON)
        body = self._block()
        
        return WithStmt(expr=expr, var_name=var_name, body=body, line=ln)

    def _throw_stmt(self) -> ThrowStmt:
        ln = self.line()
        self.expect(TokenType.THROW)
        value = self._expr()
        self._end_stmt()
        return ThrowStmt(value=value, line=ln)

    def _import_stmt(self) -> ImportStmt:
        ln = self.line()
        self.expect(TokenType.IMPORT)
        
        # Read the first identifier
        first = self.expect(TokenType.IDENTIFIER).value
        
        # Check for 'से' (FROM) syntax: आयात name से module.submodule
        if self.match(TokenType.FROM):
            names = [first]
            module_parts = [self.expect(TokenType.IDENTIFIER).value]
            while self.match(TokenType.DOT):
                module_parts.append(self.expect(TokenType.IDENTIFIER).value)
            module = '.'.join(module_parts)
            self._end_stmt()
            return ImportStmt(module=module, names=names, line=ln)
        
        # Check for regular import with potential dots: आयात module.submodule
        module_parts = [first]
        while self.match(TokenType.DOT):
            module_parts.append(self.expect(TokenType.IDENTIFIER).value)
        module = '.'.join(module_parts)
        self._end_stmt()
        return ImportStmt(module=module, names=None, line=ln)

    def _global_stmt(self) -> GlobalStmt:
        ln = self.line()
        self.expect(TokenType.GLOBAL)
        names = [self.expect(TokenType.IDENTIFIER).value]
        while self.match(TokenType.COMMA):
            names.append(self.expect(TokenType.IDENTIFIER).value)
        self._end_stmt()
        return GlobalStmt(names=names, line=ln)

    def _nonlocal_stmt(self) -> NonlocalStmt:
        ln = self.line()
        self.expect(TokenType.NONLOCAL)
        names = [self.expect(TokenType.IDENTIFIER).value]
        while self.match(TokenType.COMMA):
            names.append(self.expect(TokenType.IDENTIFIER).value)
        self._end_stmt()
        return NonlocalStmt(names=names, line=ln)

    def _expr_stmt(self) -> ExprStmt:
        ln = self.line()
        expr = self._expr()
        self._end_stmt()
        return ExprStmt(expr=expr, line=ln)

    def _block(self) -> Block:
        ln = self.line()
        stmts = []
        self.skip_newlines()

        # Inline single statement (no indent)
        if not self.check(TokenType.INDENT):
            stmts.append(self._stmt())
            return Block(stmts=stmts, line=ln)

        self.expect(TokenType.INDENT)
        self.skip_newlines()
        while not self.check(TokenType.DEDENT, TokenType.EOF):
            stmts.append(self._stmt())
            self.skip_newlines()
        self.match(TokenType.DEDENT)
        return Block(stmts=stmts, line=ln)

    # ── Expressions (Pratt-style precedence climbing) ─────────────────────────

    def _expr(self) -> Node:
        return self._assignment()

    def _assignment(self) -> Node:
        ln = self.line()
        left = self._or_expr()

        assign_ops = {
            TokenType.ASSIGN:       '=',
            TokenType.PLUS_ASSIGN:  '+=',
            TokenType.MINUS_ASSIGN: '-=',
            TokenType.STAR_ASSIGN:  '*=',
            TokenType.SLASH_ASSIGN: '/=',
            TokenType.WALRUS:       ':=',
        }
        if self.current.type in assign_ops:
            op = assign_ops[self.current.type]
            self.pos += 1
            value = self._assignment()
            return AssignExpr(target=left, op=op, value=value, line=ln)

        return left

    def _or_expr(self) -> Node:
        ln = self.line()
        left = self._and_expr()
        while self.match(TokenType.OR):
            right = self._and_expr()
            left = BinaryExpr(op='अथवा', left=left, right=right, line=ln)
        return left

    def _and_expr(self) -> Node:
        ln = self.line()
        left = self._not_expr()
        while self.match(TokenType.AND):
            right = self._not_expr()
            left = BinaryExpr(op='और', left=left, right=right, line=ln)
        return left

    def _not_expr(self) -> Node:
        ln = self.line()
        if self.match(TokenType.NOT):
            return UnaryExpr(op='न', operand=self._not_expr(), line=ln)
        return self._compare()

    def _compare(self) -> Node:
        ln = self.line()
        left = self._bitwise_or()
        cmp_map = {
            TokenType.EQ: '==', TokenType.NEQ: '!=',
            TokenType.LT: '<',  TokenType.GT:  '>',
            TokenType.LTE: '<=', TokenType.GTE: '>=',
            TokenType.IN: 'अन्तर्गत',
        }
        
        while self.current.type in cmp_map:
            op = cmp_map[self.current.type]
            self.pos += 1
            right = self._bitwise_or()
            # If we already have a comparison, we chain it with 'और'
            if isinstance(left, BinaryExpr) and left.op in cmp_map.values():
                # Note: This simple desugaring evaluates the middle expression twice.
                # A professional implementation would use a temporary variable.
                left = BinaryExpr(op='और', 
                                  left=left, 
                                  right=BinaryExpr(op=op, left=left.right, right=right, line=ln), 
                                  line=ln)
            else:
                left = BinaryExpr(op=op, left=left, right=right, line=ln)
        return left

    def _bitwise_or(self) -> Node:
        ln = self.line()
        left = self._bitwise_xor()
        while self.match(TokenType.BOR):
            right = self._bitwise_xor()
            left = BinaryExpr(op='|', left=left, right=right, line=ln)
        return left

    def _bitwise_xor(self) -> Node:
        ln = self.line()
        left = self._bitwise_and()
        while self.match(TokenType.BXOR):
            right = self._bitwise_and()
            left = BinaryExpr(op='^', left=left, right=right, line=ln)
        return left

    def _bitwise_and(self) -> Node:
        ln = self.line()
        left = self._shift()
        while self.match(TokenType.BAND):
            right = self._shift()
            left = BinaryExpr(op='&', left=left, right=right, line=ln)
        return left

    def _shift(self) -> Node:
        ln = self.line()
        left = self._additive()
        while self.check(TokenType.LSHIFT, TokenType.RSHIFT):
            op = self.current.value
            self.pos += 1
            right = self._additive()
            left = BinaryExpr(op=op, left=left, right=right, line=ln)
        return left

    def _additive(self) -> Node:
        ln = self.line()
        left = self._multiplicative()
        while self.check(TokenType.PLUS, TokenType.MINUS):
            op = self.current.value
            self.pos += 1
            right = self._multiplicative()
            left = BinaryExpr(op=op, left=left, right=right, line=ln)
        return left

    def _multiplicative(self) -> Node:
        ln = self.line()
        left = self._power()
        while self.check(TokenType.STAR, TokenType.SLASH,
                          TokenType.DOUBLESLASH, TokenType.PERCENT):
            op = self.current.value
            self.pos += 1
            right = self._power()
            left = BinaryExpr(op=op, left=left, right=right, line=ln)
        return left

    def _power(self) -> Node:
        ln = self.line()
        base = self._unary()
        if self.match(TokenType.POWER):
            exp = self._power()  # right-associative
            return BinaryExpr(op='**', left=base, right=exp, line=ln)
        return base

    def _unary(self) -> Node:
        ln = self.line()
        if self.match(TokenType.MINUS):
            return UnaryExpr(op='-', operand=self._unary(), line=ln)
        if self.match(TokenType.PLUS):
            return self._unary()
        if self.match(TokenType.BNOT):
            return UnaryExpr(op='~', operand=self._unary(), line=ln)
        return self._call()

    def _call(self) -> Node:
        ln = self.line()
        expr = self._primary()

        while True:
            if self.match(TokenType.LPAREN):
                args, kwargs = self._arg_list()
                self.expect(TokenType.RPAREN)
                expr = CallExpr(callee=expr, args=args, kwargs=kwargs, line=ln)
            elif self.match(TokenType.DOT):
                attr = self.expect(TokenType.IDENTIFIER).value
                expr = MemberExpr(obj=expr, attr=attr, line=ln)
            elif self.match(TokenType.LBRACKET):
                if self.check(TokenType.COLON):
                    start = None
                else:
                    start = self._expr()

                if self.match(TokenType.COLON):
                    if self.check(TokenType.RBRACKET, TokenType.COLON):
                        stop = None
                    else:
                        stop = self._expr()

                    if self.match(TokenType.COLON):
                        if self.check(TokenType.RBRACKET):
                            step = None
                        else:
                            step = self._expr()
                    else:
                        step = None

                    self.expect(TokenType.RBRACKET)
                    expr = SliceExpr(obj=expr, start=start, stop=stop, step=step, line=ln)
                else:
                    self.expect(TokenType.RBRACKET)
                    # Check if this was an AtmaLipi [avastha] after an expression
                    # But wait, [ ] is also indexing! We only want AtmaLipi if it's NOT followed by an operator?
                    # Actually, [avastha] typically contains an identifier (the avastha name), not an expression.
                    # Let's check if the index is a bare IdentifierExpr and matches AtmaLipi rules.
                    # Wait, indexing usually uses expressions. If it's `expr[1]`, it's an index.
                    expr = IndexExpr(obj=expr, index=start, line=ln)
            elif self.match(TokenType.LBRACE):
                # AtmaLipi {bhav} syntax
                bhav = self.expect(TokenType.IDENTIFIER).value
                self.expect(TokenType.RBRACE)

                avastha = None
                if self.match(TokenType.LBRACKET):
                    avastha = self.expect(TokenType.IDENTIFIER).value
                    self.expect(TokenType.RBRACKET)

                note = None
                if self.check(TokenType.STRING):
                    note = self.expect(TokenType.STRING).value

                # Desugar to `आत्म_मूल्य(expr, bhav, avastha, note)`
                args = [expr, StringLiteral(value=bhav, line=ln)]
                if avastha:
                    args.append(StringLiteral(value=avastha, line=ln))
                elif note:
                    args.append(NullLiteral(line=ln)) # Pad avastha if only note is present

                if note:
                    args.append(StringLiteral(value=note, line=ln))

                callee = IdentifierExpr(name='आत्म_मूल्य', line=ln)
                expr = CallExpr(callee=callee, args=args, kwargs={}, line=ln)
            else:
                break

        return expr
    def _arg_list(self):
        args, kwargs = [], {}
        while not self.check(TokenType.RPAREN):
            # Check for keyword argument: name=value
            if (self.check(TokenType.IDENTIFIER) and
                    self.peek().type == TokenType.ASSIGN):
                kw = self.current.value
                self.pos += 2
                kwargs[kw] = self._expr()
            else:
                args.append(self._expr())
            if not self.match(TokenType.COMMA):
                break
        return args, kwargs

    def _primary(self) -> Node:
        ln = self.line()
        tok = self.current

        if tok.type == TokenType.NUMBER:
            self.pos += 1
            return NumberLiteral(value=tok.value, line=ln)

        if tok.type == TokenType.STRING:
            self.pos += 1
            return StringLiteral(value=tok.value, line=ln)

        if tok.type == TokenType.FSTRING:
            self.pos += 1
            return self._parse_fstring(tok.value, ln)

        if tok.type == TokenType.TRUE:
            self.pos += 1
            return BoolLiteral(value=True, line=ln)

        if tok.type == TokenType.FALSE:
            self.pos += 1
            return BoolLiteral(value=False, line=ln)

        if tok.type == TokenType.NULL:
            self.pos += 1
            return NullLiteral(line=ln)

        if tok.type == TokenType.IDENTIFIER:
            self.pos += 1
            return IdentifierExpr(name=tok.value, line=ln)

        if tok.type == TokenType.PRINT:
            self.pos += 1
            return IdentifierExpr(name='मुद्रय', line=ln)

        if tok.type == TokenType.SELF:
            self.pos += 1
            return IdentifierExpr(name='स्वयं', line=ln)

        if tok.type == TokenType.SUPER:
            self.pos += 1
            return IdentifierExpr(name='अभिभावक', line=ln)

        if tok.type == TokenType.LPAREN:
            self.pos += 1
            expr = self._expr()
            self.expect(TokenType.RPAREN)
            return expr

        if tok.type == TokenType.LBRACKET:
            return self._list_literal()

        if tok.type == TokenType.LBRACE:
            return self._brace_literal()

        if tok.type == TokenType.NEW:
            self.pos += 1
            # Handle dotted names: nav a.b.c
            parts = [self.expect(TokenType.IDENTIFIER).value]
            while self.match(TokenType.DOT):
                parts.append(self.expect(TokenType.IDENTIFIER).value)
            
            self.expect(TokenType.LPAREN)
            args, kwargs = self._arg_list()
            self.expect(TokenType.RPAREN)
            
            # Construct nested MemberExpr/IdentifierExpr for callee
            callee = IdentifierExpr(name=parts[0], line=ln)
            for i in range(1, len(parts)):
                callee = MemberExpr(obj=callee, attr=parts[i], line=ln)
            
            return CallExpr(callee=callee, args=args, kwargs=kwargs, line=ln)

        if tok.type == TokenType.FUNC:
            # Lambda expression: कर्म(x): x*2
            if self.peek().type == TokenType.LPAREN:
                self.pos += 1 # skip FUNC
                self.expect(TokenType.LPAREN)
                params, _, varargs = self._param_list() # Discard defaults for lambda
                self.expect(TokenType.RPAREN)
                self.expect(TokenType.COLON)
                
                # A lambda body is a single expression, but it acts like a return
                expr_body = self._expr()
                
                # Wrap expression in ReturnStmt inside a Block to match standard func structure
                return_stmt = ReturnStmt(value=expr_body, line=ln)
                block = Block(stmts=[return_stmt], line=ln)
                
                return LambdaExpr(params=params, varargs=varargs, body=block, line=ln)

        raise ParseError(
            f"अनपेक्षित शब्द-चिह्न: '{tok.value}' ({tok.type.name})",
            ln
        )

    def _list_literal(self) -> Node:
        ln = self.line()
        self.expect(TokenType.LBRACKET)
        self.skip_newlines()
        
        if self.check(TokenType.RBRACKET):
            self.pos += 1
            return ListLiteral(elements=[], line=ln)
            
        first_expr = self._expr()
        self.skip_newlines()
        
        if self.match(TokenType.FOR):
            self.match(TokenType.VAR)
            var_name = self.expect(TokenType.IDENTIFIER).value
            self.expect(TokenType.IN)
            iterable = self._expr()
            self.skip_newlines()
            self.expect(TokenType.RBRACKET)
            return ListComp(expr=first_expr, var_name=var_name, iterable=iterable, line=ln)
            
        elements = [first_expr]
        if self.match(TokenType.COMMA):
            self.skip_newlines()
            while not self.check(TokenType.RBRACKET):
                elements.append(self._expr())
                self.skip_newlines()
                if not self.match(TokenType.COMMA):
                    break
                self.skip_newlines()
                
        self.expect(TokenType.RBRACKET)
        return ListLiteral(elements=elements, line=ln)

    def _brace_literal(self) -> Node:
        ln = self.line()
        self.expect(TokenType.LBRACE)
        self.skip_newlines()
        
        if self.check(TokenType.RBRACE):
            self.pos += 1
            return DictLiteral(pairs=[], line=ln) # Empty {} is a dict
            
        first_expr = self._expr()
        self.skip_newlines()
        
        # If there's a colon, it's a dict. Otherwise, it's a set.
        if self.match(TokenType.COLON):
            # It's a dictionary
            pairs = [(first_expr, self._expr())]
            self.skip_newlines()
            if self.match(TokenType.COMMA):
                self.skip_newlines()
                while not self.check(TokenType.RBRACE):
                    k = self._expr()
                    self.expect(TokenType.COLON)
                    v = self._expr()
                    pairs.append((k, v))
                    self.skip_newlines()
                    if not self.match(TokenType.COMMA):
                        break
                    self.skip_newlines()
            self.expect(TokenType.RBRACE)
            return DictLiteral(pairs=pairs, line=ln)
        else:
            # It's a set
            elements = [first_expr]
            if self.match(TokenType.COMMA):
                self.skip_newlines()
                while not self.check(TokenType.RBRACE):
                    elements.append(self._expr())
                    self.skip_newlines()
                    if not self.match(TokenType.COMMA):
                        break
                    self.skip_newlines()
            self.expect(TokenType.RBRACE)
            return SetLiteral(elements=elements, line=ln)

    def _parse_fstring(self, text: str, line: int) -> FStringExpr:
        parts = []
        pos = 0
        while pos < len(text):
            start = text.find('{', pos)
            if start == -1:
                if text[pos:]:
                    parts.append(StringLiteral(value=text[pos:], line=line))
                break
            
            # Handle double {{ as literal {
            if start + 1 < len(text) and text[start+1] == '{':
                parts.append(StringLiteral(value=text[pos:start+1], line=line))
                pos = start + 2
                continue
                
            if start > pos:
                parts.append(StringLiteral(value=text[pos:start], line=line))
            
            end = text.find('}', start)
            if end == -1:
                raise ParseError("अपूर्ण f-string (missing '}')", line)
                
            expr_str = text[start+1:end].strip()
            if expr_str:
                from .lexer import Lexer
                inner_lexer = Lexer(expr_str)
                inner_tokens = inner_lexer.tokenize()
                if inner_tokens and inner_tokens[-1].type == TokenType.EOF:
                    inner_tokens.pop()
                if inner_tokens:
                    inner_parser = Parser(inner_tokens)
                    try:
                        expr = inner_parser._expr()
                        parts.append(expr)
                    except Exception as e:
                        raise ParseError(f"f-string में त्रुटि: {e}", line)
            
            pos = end + 1
            
        return FStringExpr(parts=parts, line=line)
