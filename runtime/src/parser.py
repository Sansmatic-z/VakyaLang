# वाक् भाषा - व्याकरण विश्लेषक (Parser)
# Vak Language - Recursive Descent Parser

from .tokens import Token, TokenType, KEYWORDS
from .ast_nodes import *
from .errors import ParseError

NAME_LIKE_TOKEN_TYPES = {TokenType.IDENTIFIER} | set(KEYWORDS.values())


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

    def check_name(self) -> bool:
        return self.current.type in NAME_LIKE_TOKEN_TYPES

    def expect_name(self, msg: str = None) -> Token:
        if self.check_name():
            tok = self.current
            self.pos += 1
            return tok
        raise ParseError(
            msg or f"अपेक्षित IDENTIFIER, मिला {self.current.type.name}",
            self.current.line
        )

    def _looks_like_lambda_expr(self) -> bool:
        if not (
            self.current.type == TokenType.IDENTIFIER
            and self.current.value in ('lambda', 'कार्य')
        ):
            return False

        next_tok = self.peek()
        if next_tok.type == TokenType.LPAREN:
            depth = 0
            i = self.pos + 1
            while i < len(self.tokens):
                tok_type = self.tokens[i].type
                if tok_type == TokenType.LPAREN:
                    depth += 1
                elif tok_type == TokenType.RPAREN:
                    depth -= 1
                    if depth == 0:
                        return self.peek(i - self.pos + 1).type == TokenType.COLON
                i += 1
            return False

        if next_tok.type == TokenType.COLON:
            return True

        i = self.pos + 1
        expect_param = True
        while i < len(self.tokens):
            tok_type = self.tokens[i].type
            if expect_param:
                if tok_type == TokenType.STAR:
                    i += 1
                    if i >= len(self.tokens) or self.tokens[i].type not in NAME_LIKE_TOKEN_TYPES:
                        return False
                    expect_param = False
                elif tok_type in NAME_LIKE_TOKEN_TYPES:
                    expect_param = False
                else:
                    return False
            else:
                if tok_type == TokenType.COMMA:
                    expect_param = True
                elif tok_type == TokenType.COLON:
                    return True
                else:
                    return False
            i += 1

        return False

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

        # Check for proof declaration FIRST (Nyāya सिद्धि)
        if self.check(TokenType.SIDDHI):
            return self._proof_decl()

        # Check for macro definition FIRST (Pāṇinian सूत्र)
        if self.check(TokenType.SUTRA):
            return self._sutra_decl()
        if self.check(TokenType.APAVADA):
            return self._sutra_decl(is_apavada=True)
        if self.check(TokenType.PARINAMA):
            return self._parinama_decl()

        if self.check(TokenType.VAR):
            return self._var_decl()
        if self.check(TokenType.CONST):
            return self._const_decl()
        if self.check(TokenType.FUNC, TokenType.ASYNC):
            return self._func_decl()
        if self.check(TokenType.CLASS):
            return self._class_decl()
        if self.check(TokenType.DATA):
            return self._data_decl()
        if self.check(TokenType.MATCH):
            return self._match_stmt()
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

        # Legacy compatibility: `चर global x, y` was used widely in older test files.
        if self.check(TokenType.GLOBAL):
            self.expect(TokenType.GLOBAL)
            names = [self.expect_name().value]
            while self.match(TokenType.COMMA):
                names.append(self.expect_name().value)
            self._end_stmt()
            return GlobalStmt(names=names, line=ln)

        names = [self.expect_name().value]
        while self.match(TokenType.COMMA):
            names.append(self.expect_name().value)

        type_hint = None
        if self.match(TokenType.COLON):
            type_hint = self._type_hint()

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
        name = self.expect_name().value
        type_hint = None
        if self.match(TokenType.COLON):
            type_hint = self._type_hint()
        self.expect(TokenType.ASSIGN, "स्थिर को मान चाहिए (const requires a value)")
        value = self._expr()
        self._end_stmt()
        return ConstDecl(name=name, value=value, type_hint=type_hint, line=ln)

    def _func_decl(self) -> FuncDecl:
        ln = self.line()
        # Check for async keyword (अतुल्यकालिक)
        is_async = self.match(TokenType.ASYNC)
        
        self.expect(TokenType.FUNC)
        name = self.expect_name().value
        self.expect(TokenType.LPAREN)
        params, defaults, varargs = self._param_list()
        self.expect(TokenType.RPAREN)

        return_type = None
        if self.match(TokenType.LARROW):
            # Format: कर्म नाम(...) → प्रकार:
            return_type = self._type_hint()
            self.expect(TokenType.COLON)
        else:
            self.expect(TokenType.COLON)
            if self.check_name() and self.peek().type == TokenType.COLON:
                return_type = self._type_hint()
                self.expect(TokenType.COLON)

        body = self._block()
        return FuncDecl(name=name, params=params, defaults=defaults,
                        varargs=varargs, body=body, return_type=return_type,
                        is_async=is_async, line=ln)

    def _param_list(self):
        """
        Parse parameter list with optional Vibhakti (semantic role) markers.
        
        Supports:
        - Regular params: name, name: type
        - Vibhakti params: कर्ता name, कर्म name: type
        - Variadic: *name
        - Defaults: name = value
        """
        from .ast_nodes import VibhaktiParam
        from .vibhakti import VIBHAKTI_KEYWORDS
        
        params, defaults = [], []
        varargs = None
        while not self.check(TokenType.RPAREN):
            # Check for variadic argument: *name
            if self.match(TokenType.STAR):
                varargs = self.expect_name().value
                # Variadic must be the last parameter
                if not self.check(TokenType.RPAREN):
                    raise ParseError("अनियत तर्क (*args) अंतिम होना चाहिए", self.line())
                break

            # Check for Vibhakti semantic role marker
            # Note: कर्म (KARMA) is excluded as it's the FUNC keyword
            vibhakti_role = None
            if self.current.type in (TokenType.KARTA,
                                      TokenType.FUNC, # कर्म is mapped to FUNC
                                      TokenType.KARANA,
                                      TokenType.SAMPRADANA,
                                      TokenType.APADANA,
                                      TokenType.SAMBANDHA,
                                      TokenType.ADHIKARANA,
                                      TokenType.AMANTRANA) and self.peek().type in NAME_LIKE_TOKEN_TYPES:
                vibhakti_role = 'कर्म' if self.current.type == TokenType.FUNC else self.current.value
                self.pos += 1
            
            # Allow स्वयं (SELF) and अभिभावक (SUPER) as parameter names
            if self.check(TokenType.SELF, TokenType.SUPER):
                p = self.current.value
                self.pos += 1
            else:
                p = self.expect_name().value

            # Optional type hint for param
            p_type = None
            if self.match(TokenType.COLON):
                p_type = self._type_hint()

            # Create VibhaktiParam if role was specified, otherwise regular param
            if vibhakti_role:
                params.append(VibhaktiParam(name=p, vibhakti=vibhakti_role, 
                                           type_hint=p_type, line=self.line()))
            else:
                params.append((p, p_type))

            if self.match(TokenType.ASSIGN):
                defaults.append(self._expr())
            else:
                defaults.append(None)
            if not self.match(TokenType.COMMA):
                break
        return params, defaults, varargs

    def _type_hint(self) -> str:
        return self._type_hint_union()

    def _type_hint_union(self) -> str:
        parts = [self._type_hint_primary()]
        while self.match(TokenType.BOR):
            parts.append(self._type_hint_primary())
        return " | ".join(parts)

    def _type_hint_primary(self) -> str:
        ln = self.line()

        if self.match(TokenType.LPAREN):
            items = []
            if not self.check(TokenType.RPAREN):
                items.append(self._type_hint_union())
                while self.match(TokenType.COMMA):
                    if self.check(TokenType.RPAREN):
                        break
                    items.append(self._type_hint_union())
            self.expect(TokenType.RPAREN)
            if len(items) == 1:
                return items[0]
            return f"({', '.join(items)})"

        if not self.check_name():
            raise ParseError(f"अपेक्षित type hint, मिला {self.current.type.name}", ln)

        base = self.expect_name().value
        if self.match(TokenType.LBRACKET):
            args = []
            if not self.check(TokenType.RBRACKET):
                args.append(self._type_hint_union())
                while self.match(TokenType.COMMA):
                    if self.check(TokenType.RBRACKET):
                        break
                    args.append(self._type_hint_union())
            self.expect(TokenType.RBRACKET)
            return f"{base}[{', '.join(args)}]"
        return base

    def _class_decl(self) -> ClassDecl:
        ln = self.line()
        self.expect(TokenType.CLASS)
        name = self.expect_name().value
        superclass = None
        if self.match(TokenType.LPAREN):
            superclass = IdentifierExpr(
                name=self.expect_name().value, line=ln)
            self.expect(TokenType.RPAREN)
        self.expect(TokenType.COLON)
        body = self._block()
        return ClassDecl(name=name, superclass=superclass, body=body, line=ln)

    def _data_decl(self) -> DataDecl:
        ln = self.line()
        self.expect(TokenType.DATA)
        name = self.expect_name().value

        type_params = []
        if self.match(TokenType.LBRACKET):
            if not self.check(TokenType.RBRACKET):
                type_params.append(self.expect_name().value)
                while self.match(TokenType.COMMA):
                    if self.check(TokenType.RBRACKET):
                        break
                    type_params.append(self.expect_name().value)
            self.expect(TokenType.RBRACKET)

        self.expect(TokenType.COLON)
        self.skip_newlines()
        self.expect(TokenType.INDENT)
        self.skip_newlines()

        variants = []
        while not self.check(TokenType.DEDENT, TokenType.EOF):
            variant_line = self.line()
            variant_name = self.expect_name().value
            field_types = []
            if self.match(TokenType.LPAREN):
                if not self.check(TokenType.RPAREN):
                    field_types.append(self._type_hint())
                    while self.match(TokenType.COMMA):
                        if self.check(TokenType.RPAREN):
                            break
                        field_types.append(self._type_hint())
                self.expect(TokenType.RPAREN)
            self._end_stmt()
            variants.append(DataVariantDecl(name=variant_name, field_types=field_types, line=variant_line))
            self.skip_newlines()

        self.expect(TokenType.DEDENT)
        return DataDecl(name=name, type_params=type_params, variants=variants, line=ln)

    def _match_stmt(self) -> MatchStmt:
        ln = self.line()
        self.expect(TokenType.MATCH)
        subject = self._expr()
        self.expect(TokenType.COLON)
        self.skip_newlines()
        self.expect(TokenType.INDENT)
        self.skip_newlines()

        cases = []
        while not self.check(TokenType.DEDENT, TokenType.EOF):
            case_line = self.line()
            pattern = self._pattern()
            guard = None
            if self.match(TokenType.IF):
                guard = self._expr()
            self.expect(TokenType.COLON)
            body = self._block()
            cases.append(MatchCase(pattern=pattern, body=body, guard=guard, line=case_line))
            self.skip_newlines()

        self.expect(TokenType.DEDENT)
        return MatchStmt(subject=subject, cases=cases, line=ln)

    def _if_stmt(self) -> IfStmt:
        ln = self.line()
        self.expect(TokenType.IF)
        condition = self._expr()
        self.expect(TokenType.COLON)
        then_body = self._block()
        self.skip_newlines()

        elif_clauses = []
        while self.check(TokenType.ELIF) or (
            self.check(TokenType.ELSE) and self.peek().type == TokenType.IF
        ):
            if self.match(TokenType.ELIF):
                pass
            else:
                self.expect(TokenType.ELSE)
                self.expect(TokenType.IF)
            ec = self._expr()
            self.expect(TokenType.COLON)
            eb = self._block()
            elif_clauses.append((ec, eb))
            self.skip_newlines()

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
        var_names = [self.expect_name().value]
        while self.match(TokenType.COMMA):
            var_names.append(self.expect_name().value)
        self.expect(TokenType.IN)
        iterable = self._expr()
        self.expect(TokenType.COLON)
        body = self._block()
        return ForStmt(var_names=var_names, iterable=iterable, body=body, line=ln)

    def _return_stmt(self) -> ReturnStmt:
        ln = self.line()
        self.expect(TokenType.RETURN)
        value = None
        if not self.check(TokenType.NEWLINE, TokenType.SEMICOLON, TokenType.EOF):
            values = [self._expr()]
            while self.match(TokenType.COMMA):
                values.append(self._expr())
            value = values[0] if len(values) == 1 else TupleLiteral(elements=values, line=ln)
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

        handlers = []
        while self.match(TokenType.CATCH):
            handler_line = self.line()
            match_name, bind_name = None, None
            if self.check_name():
                provisional_name = self.current.value
                self.pos += 1
                if self.match(TokenType.AS):
                    match_name = provisional_name
                    bind_name = self.expect_name().value
                else:
                    match_name = provisional_name
                    bind_name = provisional_name
            self.expect(TokenType.COLON)
            catch_body = self._block()
            handlers.append(
                CatchHandler(
                    match_name=match_name,
                    bind_name=bind_name,
                    body=catch_body,
                    line=handler_line,
                )
            )

        finally_body = None
        if self.match(TokenType.FINALLY):
            self.expect(TokenType.COLON)
            finally_body = self._block()

        return TryStmt(
            try_body=try_body,
            handlers=handlers,
            finally_body=finally_body,
            line=ln,
        )

    def _with_stmt(self) -> WithStmt:
        ln = self.line()
        self.expect(TokenType.WITH)
        expr = self._expr()

        var_name = None
        if self.match(TokenType.AS):
            var_name = self.expect_name().value

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
        first = self.expect_name().value
        names = [first]

        while self.match(TokenType.COMMA):
            names.append(self.expect_name().value)

        # Check for 'से' (FROM) syntax: आयात name से module.submodule
        if self.match(TokenType.FROM):
            module_parts = [self.expect_name().value]
            while self.match(TokenType.DOT):
                module_parts.append(self.expect_name().value)
            module = '.'.join(module_parts)
            self._end_stmt()
            return ImportStmt(module=module, names=names, line=ln)

        if len(names) > 1:
            raise ParseError("अनेक नामों का आयात केवल 'से' रूप में समर्थित है", ln)

        # Check for regular import with potential dots: आयात module.submodule
        module_parts = [first]
        while self.match(TokenType.DOT):
            module_parts.append(self.expect_name().value)
        module = '.'.join(module_parts)
        self._end_stmt()
        return ImportStmt(module=module, names=None, line=ln)

    def _global_stmt(self) -> GlobalStmt:
        ln = self.line()
        self.expect(TokenType.GLOBAL)
        names = [self.expect_name().value]
        while self.match(TokenType.COMMA):
            names.append(self.expect_name().value)
        self._end_stmt()
        return GlobalStmt(names=names, line=ln)

    def _nonlocal_stmt(self) -> NonlocalStmt:
        ln = self.line()
        self.expect(TokenType.NONLOCAL)
        names = [self.expect_name().value]
        while self.match(TokenType.COMMA):
            names.append(self.expect_name().value)
        self._end_stmt()
        return NonlocalStmt(names=names, line=ln)

    def _macro_pattern_list(self) -> List[Node]:
        patterns = []
        if not self.check(TokenType.RPAREN):
            patterns.append(self._expr())
            while self.match(TokenType.COMMA):
                patterns.append(self._expr())
        return patterns

    def _macro_scope_value(self) -> str:
        if self.check(TokenType.STRING):
            return self.expect(TokenType.STRING).value
        return self.expect_name().value

    def _macro_param_names(self, patterns: List[Node]) -> List[str]:
        names = []
        for pattern in patterns:
            if isinstance(pattern, IdentifierExpr) and pattern.name != "_":
                names.append(pattern.name)
        return names

    def _sutra_decl(self, is_apavada: bool = False) -> SutraDecl:
        """
        Parse a macro definition (सूत्र / अपवाद).
        
        Syntax:
            सूत्र name(params):
                अनुवाद -> expansion
        """
        ln = self.line()
        if is_apavada:
            self.expect(TokenType.APAVADA)
        else:
            self.expect(TokenType.SUTRA)
        name = self.expect_name().value
        
        self.expect(TokenType.LPAREN)
        patterns = self._macro_pattern_list()
        self.expect(TokenType.RPAREN)
        
        self.expect(TokenType.COLON)
        block_form = False
        scope = None
        if self.match(TokenType.NEWLINE):
            self.skip_newlines()
            if self.match(TokenType.INDENT):
                block_form = True
                self.skip_newlines()

        if block_form and self.match(TokenType.ADHIKARA):
            scope = self._macro_scope_value()
            self._end_stmt()
            self.skip_newlines()

        if not block_form and self.match(TokenType.ADHIKARA):
            scope = self._macro_scope_value()
            self._end_stmt()

        self.expect(TokenType.ANUVADA)
        self.expect(TokenType.LARROW)  # ->
        expansion = self._expr()
        self._end_stmt()

        if block_form:
            self.skip_newlines()
            self.match(TokenType.DEDENT)
        
        return SutraDecl(
            name=name,
            params=self._macro_param_names(patterns),
            patterns=patterns,
            expansion=expansion,
            scope=scope,
            is_apavada=is_apavada,
            line=ln,
        )

    def _parinama_decl(self) -> ParinamaDecl:
        ln = self.line()
        self.expect(TokenType.PARINAMA)
        name = self.expect_name().value
        self.expect(TokenType.COLON)
        self.expect(TokenType.NEWLINE)
        self.skip_newlines()
        self.expect(TokenType.INDENT)
        self.skip_newlines()

        scope = None
        if self.match(TokenType.ADHIKARA):
            scope = self._macro_scope_value()
            self._end_stmt()
            self.skip_newlines()

        rules = []
        while not self.check(TokenType.DEDENT, TokenType.EOF):
            pattern = self._expr()
            self.expect(TokenType.LARROW)
            replacement = self._expr()
            self._end_stmt()
            rules.append(RewriteRule(pattern=pattern, replacement=replacement, line=ln))
            self.skip_newlines()

        self.expect(TokenType.DEDENT)
        return ParinamaDecl(name=name, rules=rules, scope=scope, line=ln)

    def _proof_decl(self) -> ProofDeclaration:
        """
        Parse a Nyāya proof declaration (सिद्धि).
        
        Syntax:
            सिद्धि: statement
                प्रमाण:
                    evidence_code
                प्रमाण_पत्र: "certificate_string"
        """
        from .ast_nodes import ProofDeclaration
        
        ln = self.line()
        self.expect(TokenType.SIDDHI)
        self.expect(TokenType.COLON)
        
        # Parse the statement to prove (can be a function call or expression)
        statement_expr = self._expr()
        statement = self._expr_to_string(statement_expr)
        
        self.skip_newlines()
        self.expect(TokenType.INDENT)
        self.skip_newlines()
        
        # Parse evidence block (प्रमाण)
        evidence_body = None
        certificate = None
        
        if self.check(TokenType.PRAMANA):
            self.expect(TokenType.PRAMANA)
            self.expect(TokenType.COLON)
            self.skip_newlines()
            evidence_body = self._block()
            self.skip_newlines()
        
        # Parse optional proof certificate (प्रमाण_पत्र)
        if self.check(TokenType.PRAMANA_PATRA):
            self.expect(TokenType.PRAMANA_PATRA)
            self.expect(TokenType.COLON)
            cert_token = self.expect(TokenType.STRING)
            certificate = cert_token.value
            self._end_stmt()
        
        self.match(TokenType.DEDENT)
        
        return ProofDeclaration(
            statement=statement,
            evidence_body=evidence_body,
            statement_expr=statement_expr,
            certificate=certificate,
            line=ln
        )

    def _match_ellipsis(self) -> bool:
        return (
            self.check(TokenType.DOT)
            and self.peek().type == TokenType.DOT
            and self.peek(2).type == TokenType.DOT
        )

    def _consume_ellipsis(self) -> None:
        if not self._match_ellipsis():
            raise ParseError("अपेक्षित '...'", self.line())
        self.pos += 3

    def _pattern(self) -> Node:
        ln = self.line()
        tok = self.current

        if tok.type == TokenType.NUMBER:
            self.pos += 1
            return LiteralPattern(value=tok.value, line=ln)

        if tok.type == TokenType.STRING:
            self.pos += 1
            return LiteralPattern(value=tok.value, line=ln)

        if tok.type == TokenType.TRUE:
            self.pos += 1
            return LiteralPattern(value=True, line=ln)

        if tok.type == TokenType.FALSE:
            self.pos += 1
            return LiteralPattern(value=False, line=ln)

        if tok.type == TokenType.NULL:
            self.pos += 1
            return LiteralPattern(value=None, line=ln)

        if tok.type in NAME_LIKE_TOKEN_TYPES:
            name = self.expect_name().value
            if name == "_":
                return WildcardPattern(line=ln)
            if self.match(TokenType.LPAREN):
                args = []
                if not self.check(TokenType.RPAREN):
                    args.append(self._pattern())
                    while self.match(TokenType.COMMA):
                        if self.check(TokenType.RPAREN):
                            break
                        args.append(self._pattern())
                self.expect(TokenType.RPAREN)
                return CallPattern(callee=name, args=args, line=ln)
            return BindingPattern(name=name, line=ln)

        if self.match(TokenType.LBRACKET):
            elements = []
            rest_name = None
            self.skip_newlines()
            while not self.check(TokenType.RBRACKET):
                if self._match_ellipsis():
                    self._consume_ellipsis()
                    if self.check_name():
                        rest_name = self.expect_name().value
                    else:
                        rest_name = "_"
                    self.skip_newlines()
                    break
                elements.append(self._pattern())
                self.skip_newlines()
                if not self.match(TokenType.COMMA):
                    break
                self.skip_newlines()
            self.expect(TokenType.RBRACKET)
            return SequencePattern(kind='list', elements=elements, rest_name=rest_name, line=ln)

        if self.match(TokenType.LPAREN):
            elements = []
            rest_name = None
            self.skip_newlines()
            while not self.check(TokenType.RPAREN):
                if self._match_ellipsis():
                    self._consume_ellipsis()
                    if self.check_name():
                        rest_name = self.expect_name().value
                    else:
                        rest_name = "_"
                    self.skip_newlines()
                    break
                elements.append(self._pattern())
                self.skip_newlines()
                if not self.match(TokenType.COMMA):
                    break
                self.skip_newlines()
            self.expect(TokenType.RPAREN)
            return SequencePattern(kind='tuple', elements=elements, rest_name=rest_name, line=ln)

        raise ParseError(f"अवैध pattern: {tok.type.name}", ln)
    
    def _expr_to_string(self, expr: Node) -> str:
        """Convert an expression AST to a string representation for proof statements."""
        from .ast_nodes import (
            CallExpr, IdentifierExpr, NumberLiteral, StringLiteral,
            BinaryExpr, UnaryExpr
        )
        
        if isinstance(expr, IdentifierExpr):
            return expr.name
        elif isinstance(expr, NumberLiteral):
            return str(expr.value)
        elif isinstance(expr, StringLiteral):
            return expr.value
        elif isinstance(expr, CallExpr):
            callee = self._expr_to_string(expr.callee)
            args = ', '.join(self._expr_to_string(a) for a in expr.args)
            return f"{callee}({args})"
        elif isinstance(expr, BinaryExpr):
            left = self._expr_to_string(expr.left)
            right = self._expr_to_string(expr.right)
            return f"({left} {expr.op} {right})"
        elif isinstance(expr, UnaryExpr):
            operand = self._expr_to_string(expr.operand)
            return f"({expr.op}{operand})"
        else:
            return str(expr)

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
        left = self._conditional()

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

    def _conditional(self) -> Node:
        ln = self.line()
        then_expr = self._pipeline()

        if self.match(TokenType.IF):
            condition = self._pipeline()
            self.expect(TokenType.ELSE)
            else_expr = self._conditional()
            return ConditionalExpr(
                condition=condition,
                then_expr=then_expr,
                else_expr=else_expr,
                line=ln,
            )

        return then_expr

    def _pipeline(self) -> Node:
        ln = self.line()
        left = self._or_expr()
        while self.match(TokenType.PIPE_OP):
            right = self._call()
            if isinstance(right, CallExpr):
                left = CallExpr(
                    callee=right.callee,
                    args=[left, *right.args],
                    kwargs=right.kwargs,
                    line=ln,
                )
            elif isinstance(right, (IdentifierExpr, MemberExpr)):
                left = CallExpr(callee=right, args=[left], kwargs={}, line=ln)
            else:
                raise ParseError("pipe target must be a callable name or call", self.line())
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
        if self.check(TokenType.NOT):
            next_type = self.peek().type
            if next_type in {
                TokenType.NUMBER,
                TokenType.STRING,
                TokenType.FSTRING,
                TokenType.TRUE,
                TokenType.FALSE,
                TokenType.NULL,
                TokenType.IDENTIFIER,
                TokenType.PRINT,
                TokenType.SELF,
                TokenType.SUPER,
                TokenType.LPAREN,
                TokenType.LBRACKET,
                TokenType.LBRACE,
                TokenType.NEW,
                TokenType.AWAIT,
                TokenType.FUNC,
                TokenType.NOT,
            } or next_type in NAME_LIKE_TOKEN_TYPES:
                self.pos += 1
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

        while self.current.type in cmp_map or (
            self.current.type == TokenType.NOT and self.peek().type == TokenType.IN
        ):
            if self.current.type == TokenType.NOT and self.peek().type == TokenType.IN:
                op = 'not in'
                self.pos += 2
            else:
                op = cmp_map[self.current.type]
                self.pos += 1
            right = self._bitwise_or()
            # If we already have a comparison, we chain it with 'और'
            if isinstance(left, BinaryExpr) and left.op in (*cmp_map.values(), 'not in'):
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
            if (self.check_name() and
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

        # Handle await expression (प्रतीक्षा)
        if self.match(TokenType.AWAIT):
            operand = self._unary()
            return AwaitExpr(operand=operand, line=ln)

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

        if self._looks_like_lambda_expr():
            self.pos += 1
            params = []
            varargs = None

            if self.match(TokenType.LPAREN):
                params, _, varargs = self._param_list()
                self.expect(TokenType.RPAREN)
            elif not self.check(TokenType.COLON):
                while True:
                    if self.match(TokenType.STAR):
                        varargs = self.expect_name().value
                        break
                    params.append((self.expect_name().value, None))
                    if not self.match(TokenType.COMMA):
                        break

            self.expect(TokenType.COLON)
            expr_body = self._expr()
            return_stmt = ReturnStmt(value=expr_body, line=ln)
            block = Block(stmts=[return_stmt], line=ln)
            return LambdaExpr(params=params, varargs=varargs, body=block, line=ln)

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
            if self.check(TokenType.RPAREN):
                self.pos += 1
                return TupleLiteral(elements=[], line=ln)

            expr = self._expr()
            if self.match(TokenType.COMMA):
                elements = [expr]
                self.skip_newlines()
                while not self.check(TokenType.RPAREN):
                    elements.append(self._expr())
                    self.skip_newlines()
                    if not self.match(TokenType.COMMA):
                        break
                    self.skip_newlines()
                self.expect(TokenType.RPAREN)
                return TupleLiteral(elements=elements, line=ln)
            self.expect(TokenType.RPAREN)
            return expr

        if tok.type == TokenType.LBRACKET:
            return self._list_literal()

        if tok.type == TokenType.LBRACE:
            return self._brace_literal()

        if tok.type == TokenType.NEW:
            self.pos += 1
            # Handle dotted names: nav a.b.c
            parts = [self.expect_name().value]
            while self.match(TokenType.DOT):
                parts.append(self.expect_name().value)

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

        if tok.type in NAME_LIKE_TOKEN_TYPES:
            self.pos += 1
            return IdentifierExpr(name=tok.value, line=ln)

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
            var_name = self.expect_name().value
            self.expect(TokenType.IN)
            iterable = self._or_expr()
            filter_expr = None
            if self.match(TokenType.IF):
                filter_expr = self._expr()
            self.skip_newlines()
            self.expect(TokenType.RBRACKET)
            return ListComp(
                expr=first_expr,
                var_name=var_name,
                iterable=iterable,
                filter_expr=filter_expr,
                line=ln,
            )

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
            first_value = self._expr()
            self.skip_newlines()
            if self.match(TokenType.FOR):
                self.match(TokenType.VAR)
                var_name = self.expect_name().value
                self.expect(TokenType.IN)
                iterable = self._or_expr()
                filter_expr = None
                if self.match(TokenType.IF):
                    filter_expr = self._expr()
                self.skip_newlines()
                self.expect(TokenType.RBRACE)
                return DictComp(
                    key_expr=first_expr,
                    value_expr=first_value,
                    var_name=var_name,
                    iterable=iterable,
                    filter_expr=filter_expr,
                    line=ln,
                )

            pairs = [(first_expr, first_value)]
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
