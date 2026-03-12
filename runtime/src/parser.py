# VakyaLang (वाक्) — Copyright (c) 2026 Raj Mitra. All Rights Reserved.
# Original author: Raj Mitra (Visionary RM)
# Licensed under GNU AGPL v3.0 — see LICENSE and NOTICE.
# Any use, modification, or derivative work must preserve this header
# and include the NOTICE file. https://github.com/Sansmatic-z/VakyaLang
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
        if self.check(TokenType.TRY):
            return self._try_stmt()
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
        name = self.expect(TokenType.IDENTIFIER).value
        value = None
        if self.match(TokenType.ASSIGN):
            value = self._expr()
        self._end_stmt()
        return VarDecl(name=name, value=value, line=ln)

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
        params, defaults = self._param_list()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.COLON)
        body = self._block()
        return FuncDecl(name=name, params=params, defaults=defaults,
                        body=body, line=ln)

    def _param_list(self):
        params, defaults = [], []
        while not self.check(TokenType.RPAREN):
            # Allow स्वयं (SELF) and अभिभावक (SUPER) as parameter names
            if self.check(TokenType.SELF, TokenType.SUPER):
                p = self.current.value
                self.pos += 1
            else:
                p = self.expect(TokenType.IDENTIFIER).value
            params.append(p)
            if self.match(TokenType.ASSIGN):
                defaults.append(self._expr())
            else:
                defaults.append(None)
            if not self.match(TokenType.COMMA):
                break
        return params, defaults

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
        left = self._additive()
        cmp_map = {
            TokenType.EQ: '==', TokenType.NEQ: '!=',
            TokenType.LT: '<',  TokenType.GT:  '>',
            TokenType.LTE: '<=', TokenType.GTE: '>=',
            TokenType.IN: 'अन्तर्गत',
        }
        while self.current.type in cmp_map:
            op = cmp_map[self.current.type]
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
                index = self._expr()
                self.expect(TokenType.RBRACKET)
                expr = IndexExpr(obj=expr, index=index, line=ln)
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
            return self._dict_literal()

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

        raise ParseError(
            f"अनपेक्षित शब्द-चिह्न: '{tok.value}' ({tok.type.name})",
            ln
        )

    def _list_literal(self) -> ListLiteral:
        ln = self.line()
        self.expect(TokenType.LBRACKET)
        elements = []
        self.skip_newlines()
        while not self.check(TokenType.RBRACKET):
            elements.append(self._expr())
            self.skip_newlines()
            if not self.match(TokenType.COMMA):
                break
            self.skip_newlines()
        self.expect(TokenType.RBRACKET)
        return ListLiteral(elements=elements, line=ln)

    def _dict_literal(self) -> DictLiteral:
        ln = self.line()
        self.expect(TokenType.LBRACE)
        pairs = []
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

