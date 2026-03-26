# वाक् भाषा - शब्द-विच्छेदक (Lexer)
# Vak Language - Lexer / Tokenizer
# Handles Devanagari script, Sanskrit keywords, and Devanagari numerals.

import unicodedata
from .tokens import Token, TokenType, KEYWORDS, DEVA_DIGITS
from .errors import LexerError


def is_devanagari(ch: str) -> bool:
    """True if character is in the Devanagari Unicode block (U+0900–U+097F)."""
    if not ch:
        return False
    cp = ord(ch)
    return 0x0900 <= cp <= 0x097F


def is_deva_digit(ch: str) -> bool:
    return ch in DEVA_DIGITS


def is_identifier_start(ch: str) -> bool:
    """Devanagari or ASCII letter / underscore."""
    return is_devanagari(ch) or ch.isalpha() or ch == '_'


def is_identifier_part(ch: str) -> bool:
    """Devanagari, ASCII alnum, or underscore."""
    return is_devanagari(ch) or ch.isalnum() or ch == '_'


def is_digit(ch: str) -> bool:
    return ch.isdigit() or is_deva_digit(ch)


def normalize_digits(s: str) -> str:
    """Convert Devanagari digits to ASCII digits for numeric parsing."""
    return ''.join(DEVA_DIGITS.get(c, c) for c in s)


IDENTIFIER_CONTEXT_TOKENS = {
    TokenType.DOT,
    TokenType.FUNC,
    TokenType.CLASS,
    TokenType.VAR,
    TokenType.CONST,
    TokenType.IMPORT,
    TokenType.FROM,
    TokenType.GLOBAL,
    TokenType.NONLOCAL,
    TokenType.AS,
}

CALLABLE_KEYWORD_TOKENS = {
    TokenType.CLASS,
    TokenType.VAR,
}


class Lexer:
    """
    Converts a Vak source string into a flat list of Tokens.

    Indentation model: Python-style — significant whitespace with an
    indent-stack.  INDENT and DEDENT tokens are emitted when the
    indentation level changes.
    """

    def __init__(self, source: str):
        self.source   = source
        self.pos      = 0
        self.line     = 1
        self.tokens   = []
        self._indent_stack = [0]   # stack of indent levels
        self._pending_dedents = 0
        self._bracket_depth = 0    # ( [ { nesting depth
        self._in_multiline = False
        self._multiline_quote = ""
        self._multiline_buf = []
        self._multiline_start_line = 0

    # ── Public entry point ────────────────────────────────────────────────────

    def tokenize(self) -> list:
        lines = self.source.split('\n')
        for line_no, line in enumerate(lines, start=1):
            self.line = line_no
            self._process_line(line)

        if self._in_multiline:
            raise LexerError("अपूर्ण बहु-पंक्ति तार (unterminated multiline string)", self._multiline_start_line)

        # Emit remaining DEDENTs at end-of-file
        while len(self._indent_stack) > 1:
            self._indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, None, self.line))

        self.tokens.append(Token(TokenType.EOF, None, self.line))
        return self.tokens

    # ── Line-level processing ─────────────────────────────────────────────────

    def _process_line(self, line: str):
        if self._in_multiline:
            pos = line.find(self._multiline_quote)
            if pos != -1:
                # Found the closing quote
                self._multiline_buf.append(line[:pos])
                raw_str = '\n'.join(self._multiline_buf)
                self.tokens.append(Token(TokenType.STRING, raw_str, self._multiline_start_line))
                self._in_multiline = False
                self._multiline_buf = []
                self._tokenize_segment(line[pos+3:], self.line)
                if self._bracket_depth == 0 and not self._in_multiline:
                    self.tokens.append(Token(TokenType.NEWLINE, '\n', self.line))
            else:
                self._multiline_buf.append(line)
            return

        # Strip trailing whitespace / carriage return
        stripped = line.rstrip()

        # Blank line or comment-only line — emit NEWLINE but no indent change
        content = stripped.lstrip()
        if not content or content.startswith('#') or content.startswith('टीका'):
            if self.tokens and self.tokens[-1].type not in (
                    TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT,
                    TokenType.EOF):
                # Only emit newline if not inside brackets
                if self._bracket_depth == 0:
                    self.tokens.append(Token(TokenType.NEWLINE, '\n', self.line))
            return

        continuation_line = content.startswith('|>')
        if continuation_line and self.tokens and self.tokens[-1].type == TokenType.NEWLINE:
            self.tokens.pop()

        # Compute indent level (spaces / 4 per tab)
        indent = 0
        for ch in line:
            if ch == ' ':
                indent += 1
            elif ch == '\t':
                indent += 4
            else:
                break

        # Only emit INDENT/DEDENT when not inside brackets
        if self._bracket_depth == 0 and not continuation_line:
            current_indent = self._indent_stack[-1]

            if indent > current_indent:
                self._indent_stack.append(indent)
                self.tokens.append(Token(TokenType.INDENT, indent, self.line))
            elif indent < current_indent:
                while self._indent_stack[-1] > indent:
                    self._indent_stack.pop()
                    self.tokens.append(Token(TokenType.DEDENT, None, self.line))
                if self._indent_stack[-1] != indent:
                    raise LexerError("असंगत इंडेंटेशन (inconsistent indentation)",
                                      self.line)

        # Tokenise the content portion of the line
        self._tokenize_segment(stripped.lstrip(), self.line)

        # Emit NEWLINE at end of logical line (only outside brackets)
        if self._bracket_depth == 0 and not self._in_multiline:
            self.tokens.append(Token(TokenType.NEWLINE, '\n', self.line))

    # ── Segment tokeniser ─────────────────────────────────────────────────────

    def _tokenize_segment(self, seg: str, line: int):
        pos = 0
        length = len(seg)

        while pos < length:
            ch = seg[pos]

            # Skip spaces within a line
            if ch in (' ', '\t'):
                pos += 1
                continue

            # Comment: # or टीका
            if ch == '#':
                break  # rest of line is comment
            if seg[pos:pos+4] == 'टीका':
                break

            # String literals
            if ch in ('"', "'"):
                # Check for triple quotes
                if pos + 2 < length and seg[pos] == seg[pos+1] == seg[pos+2]:
                    quote = seg[pos:pos+3]
                    pos += 3
                    end_pos = seg.find(quote, pos)
                    if end_pos != -1:
                        # Found on the same line
                        val = seg[pos:end_pos]
                        self.tokens.append(Token(TokenType.STRING, val, line))
                        pos = end_pos + 3
                        continue
                    else:
                        # Multiline started
                        self._in_multiline = True
                        self._multiline_quote = quote
                        self._multiline_start_line = line
                        self._multiline_buf = [seg[pos:]]
                        return  # Stop processing this line
                else:
                    tok, pos = self._read_string(seg, pos, line)
                    self.tokens.append(tok)
                    continue

            # Numbers (Devanagari or ASCII)
            if is_digit(ch):
                tok, pos = self._read_number(seg, pos, line)
                self.tokens.append(tok)
                continue

            # Identifiers / keywords
            if is_identifier_start(ch):
                if ch == 'f' and pos + 1 < length and seg[pos+1] in ('"', "'"):
                    pos += 1  # Skip the 'f'
                    tok, pos = self._read_string(seg, pos, line)
                    # Convert TokenType.STRING to TokenType.FSTRING
                    tok.type = TokenType.FSTRING
                    self.tokens.append(tok)
                    continue
                tok, pos = self._read_identifier(seg, pos, line)
                self.tokens.append(tok)
                continue

            # Multi-char operators
            two = seg[pos:pos+2]
            if two == '**':
                self.tokens.append(Token(TokenType.POWER, '**', line))
                pos += 2; continue
            if two == '//':
                self.tokens.append(Token(TokenType.DOUBLESLASH, '//', line))
                pos += 2; continue
            if two == '<<':
                self.tokens.append(Token(TokenType.LSHIFT, '<<', line))
                pos += 2; continue
            if two == '>>':
                self.tokens.append(Token(TokenType.RSHIFT, '>>', line))
                pos += 2; continue
            if two == '|>':
                self.tokens.append(Token(TokenType.PIPE_OP, '|>', line))
                pos += 2; continue
            if two == '==':
                self.tokens.append(Token(TokenType.EQ, '==', line))
                pos += 2; continue
            if two == '!=':
                self.tokens.append(Token(TokenType.NEQ, '!=', line))
                pos += 2; continue
            if two == '<=':
                self.tokens.append(Token(TokenType.LTE, '<=', line))
                pos += 2; continue
            if two == '>=':
                self.tokens.append(Token(TokenType.GTE, '>=', line))
                pos += 2; continue
            if two == '+=':
                self.tokens.append(Token(TokenType.PLUS_ASSIGN, '+=', line))
                pos += 2; continue
            if two == '-=':
                self.tokens.append(Token(TokenType.MINUS_ASSIGN, '-=', line))
                pos += 2; continue
            if two == '*=':
                self.tokens.append(Token(TokenType.STAR_ASSIGN, '*=', line))
                pos += 2; continue
            if two == '/=':
                self.tokens.append(Token(TokenType.SLASH_ASSIGN, '/=', line))
                pos += 2; continue
            if two == ':=':
                self.tokens.append(Token(TokenType.WALRUS, ':=', line))
                pos += 2; continue
            
            # Arrow operator for macro expansion (-> or →)
            if two == '->':
                self.tokens.append(Token(TokenType.LARROW, '->', line))
                pos += 2; continue
            if ch == '→':
                self.tokens.append(Token(TokenType.LARROW, '→', line))
                pos += 1; continue

            # Single-char operators and delimiters
            single_map = {
                '+': TokenType.PLUS,
                '-': TokenType.MINUS,
                '*': TokenType.STAR,
                '/': TokenType.SLASH,
                '%': TokenType.PERCENT,
                '&': TokenType.BAND,
                '|': TokenType.BOR,
                '^': TokenType.BXOR,
                '~': TokenType.BNOT,
                '<': TokenType.LT,
                '>': TokenType.GT,
                '=': TokenType.ASSIGN,
                '(': TokenType.LPAREN,
                ')': TokenType.RPAREN,
                '{': TokenType.LBRACE,
                '}': TokenType.RBRACE,
                '[': TokenType.LBRACKET,
                ']': TokenType.RBRACKET,
                ',': TokenType.COMMA,
                '.': TokenType.DOT,
                ':': TokenType.COLON,
                ';': TokenType.SEMICOLON,
            }
            if ch in single_map:
                tt = single_map[ch]
                self.tokens.append(Token(tt, ch, line))
                # Track bracket depth
                if ch in ('(', '[', '{'):
                    self._bracket_depth += 1
                elif ch in (')', ']', '}'):
                    self._bracket_depth = max(0, self._bracket_depth - 1)
                pos += 1
                continue

            raise LexerError(f"अज्ञात चिह्न: '{ch}' (unknown character)", line)

    # ── Readers ───────────────────────────────────────────────────────────────

    def _read_string(self, seg, pos, line):
        quote = seg[pos]
        pos += 1
        buf = []
        while pos < len(seg):
            ch = seg[pos]
            if ch == '\\':
                pos += 1
                escape_map = {
                    'n': '\n', 't': '\t', '\\': '\\',
                    '"': '"', "'": "'", 'r': '\r'
                }
                esc = seg[pos] if pos < len(seg) else ''
                if esc in escape_map:
                    buf.append(escape_map[esc])
                else:
                    buf.append('\\' + esc)
                pos += 1
            elif ch == quote:
                pos += 1
                break
            else:
                buf.append(ch)
                pos += 1
        else:
            raise LexerError("अपूर्ण तार (unterminated string)", line)
        return Token(TokenType.STRING, ''.join(buf), line), pos

    def _read_number(self, seg, pos, line):
        buf = []
        while pos < len(seg) and is_digit(seg[pos]):
            buf.append(seg[pos])
            pos += 1
        # Decimal point
        if pos < len(seg) and seg[pos] == '.':
            buf.append('.')
            pos += 1
            while pos < len(seg) and is_digit(seg[pos]):
                buf.append(seg[pos])
                pos += 1
        if pos < len(seg) and seg[pos] in ('e', 'E'):
            exp_pos = pos
            exp_buf = [seg[pos]]
            pos += 1
            if pos < len(seg) and seg[pos] in ('+', '-'):
                exp_buf.append(seg[pos])
                pos += 1

            exp_digits_start = pos
            while pos < len(seg) and is_digit(seg[pos]):
                exp_buf.append(seg[pos])
                pos += 1

            if pos > exp_digits_start:
                buf.extend(exp_buf)
            else:
                pos = exp_pos
        raw = ''.join(buf)
        normalized = normalize_digits(raw)
        value = float(normalized) if '.' in normalized or 'e' in normalized.lower() else int(normalized)
        return Token(TokenType.NUMBER, value, line), pos

    def _read_identifier(self, seg, pos, line):
        buf = []
        while pos < len(seg) and is_identifier_part(seg[pos]):
            buf.append(seg[pos])
            pos += 1
        name = ''.join(buf)
        tok_type = KEYWORDS.get(name, TokenType.IDENTIFIER)

        # In declaration/attribute contexts, keyword-shaped names are ordinary identifiers.
        if self.tokens:
            last_type = self.tokens[-1].type
            if last_type in IDENTIFIER_CONTEXT_TOKENS:
                legacy_scope_decl = (
                    last_type == TokenType.VAR and tok_type in (TokenType.GLOBAL, TokenType.NONLOCAL)
                )
                if not legacy_scope_decl:
                    tok_type = TokenType.IDENTIFIER

        # Some Sanskrit words are both reserved syntax and callable names.
        # If they are immediately called, keep them as identifiers.
        next_nonspace = self._peek_next_nonspace(seg, pos)
        if tok_type in CALLABLE_KEYWORD_TOKENS and next_nonspace == '(':
            tok_type = TokenType.IDENTIFIER

        return Token(tok_type, name, line), pos

    def _peek_next_nonspace(self, seg: str, pos: int) -> str:
        while pos < len(seg) and seg[pos] in (' ', '\t'):
            pos += 1
        return seg[pos] if pos < len(seg) else ''
