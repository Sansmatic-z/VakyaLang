# वाक् भाषा - शब्द-चिह्न परिभाषाएँ (Token Definitions)
# Vak Language - Token Types

from enum import Enum, auto


class TokenType(Enum):
    # ── Literals ──────────────────────────────────────────────────────────────
    NUMBER      = auto()   # 42, ४२, 3.14, ३.१४
    STRING      = auto()   # "नमस्ते"
    TRUE        = auto()   # सत्य
    FALSE       = auto()   # असत्य
    NULL        = auto()   # शून्य

    # ── Identifiers & Keywords ────────────────────────────────────────────────
    IDENTIFIER  = auto()

    VAR         = auto()   # चर      (variable)
    CONST       = auto()   # स्थिर   (constant)
    FUNC        = auto()   # कर्म    (function / action)
    CLASS       = auto()   # वर्ग    (class / category)
    RETURN      = auto()   # प्रत्यागच्छ (return / come back)
    IF          = auto()   # यदि     (if)
    ELIF        = auto()   # अन्यत्  (else-if / otherwise)
    ELSE        = auto()   # अन्यथा  (else / otherwise)
    WHILE       = auto()   # यावत्   (while / as long as)
    FOR         = auto()   # प्रत्येक (for each)
    IN          = auto()   # अन्तर्गत (in / within)
    BREAK       = auto()   # विराम   (break / stop)
    CONTINUE    = auto()   # अग्रे   (continue / forward)
    PRINT       = auto()   # मुद्रय  (print / imprint)
    AND         = auto()   # और      (and)
    OR          = auto()   # अथवा   (or)
    NOT         = auto()   # न       (not / no)
    TRY         = auto()   # प्रयत्न (try / attempt)
    CATCH       = auto()   # दोष     (catch / fault-handler)
    FINALLY     = auto()   # अन्ततः  (finally / ultimately)
    THROW       = auto()   # उत्क्षिप (throw)
    IMPORT      = auto()   # आयात    (import / bring in)
    FROM        = auto()   # से      (from)
    NEW         = auto()   # नव      (new)
    SELF        = auto()   # स्वयं   (self / oneself)
    SUPER       = auto()   # अभिभावक (super / parent)

    # ── Arithmetic Operators ──────────────────────────────────────────────────
    PLUS        = auto()   # +
    MINUS       = auto()   # -
    STAR        = auto()   # *
    SLASH       = auto()   # /
    DOUBLESLASH = auto()   # // (integer division)
    PERCENT     = auto()   # %
    POWER       = auto()   # **

    # ── Comparison Operators ──────────────────────────────────────────────────
    EQ          = auto()   # ==
    NEQ         = auto()   # !=
    LT          = auto()   # <
    GT          = auto()   # >
    LTE         = auto()   # <=
    GTE         = auto()   # >=

    # ── Assignment Operators ──────────────────────────────────────────────────
    ASSIGN      = auto()   # =
    PLUS_ASSIGN = auto()   # +=
    MINUS_ASSIGN= auto()   # -=
    STAR_ASSIGN = auto()   # *=
    SLASH_ASSIGN= auto()   # /=

    # ── Delimiters ────────────────────────────────────────────────────────────
    LPAREN      = auto()   # (
    RPAREN      = auto()   # )
    LBRACE      = auto()   # {
    RBRACE      = auto()   # }
    LBRACKET    = auto()   # [
    RBRACKET    = auto()   # ]
    COMMA       = auto()   # ,
    DOT         = auto()   # .
    COLON       = auto()   # :
    SEMICOLON   = auto()   # ;

    # ── Structure ─────────────────────────────────────────────────────────────
    NEWLINE     = auto()
    INDENT      = auto()
    DEDENT      = auto()
    EOF         = auto()
    COMMENT     = auto()


# Sanskrit keyword map: Devanagari → TokenType
KEYWORDS = {
    'चर':           TokenType.VAR,
    'स्थिर':        TokenType.CONST,
    'कर्म':         TokenType.FUNC,
    'वर्ग':         TokenType.CLASS,
    'प्रत्यागच्छ':  TokenType.RETURN,
    'यदि':          TokenType.IF,
    'अन्यत्':       TokenType.ELIF,
    'अन्यथा':       TokenType.ELSE,
    'यावत्':        TokenType.WHILE,
    'प्रत्येक':     TokenType.FOR,
    'अन्तर्गत':     TokenType.IN,
    'विराम':        TokenType.BREAK,
    'अग्रे':        TokenType.CONTINUE,
    'मुद्रय':       TokenType.PRINT,
    'और':           TokenType.AND,
    'अथवा':         TokenType.OR,
    'न':            TokenType.NOT,
    'सत्य':         TokenType.TRUE,
    'असत्य':        TokenType.FALSE,
    'शून्य':        TokenType.NULL,
    'प्रयत्न':      TokenType.TRY,
    'दोष':          TokenType.CATCH,
    'अन्ततः':       TokenType.FINALLY,
    'उत्क्षिप':     TokenType.THROW,
    'आयात':         TokenType.IMPORT,
    'से':           TokenType.FROM,
    'नव':           TokenType.NEW,
    'स्वयं':        TokenType.SELF,
    'अभिभावक':      TokenType.SUPER,
}

# Devanagari digit map
DEVA_DIGITS = {
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
    '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
}


class Token:
    """A single lexical token."""
    __slots__ = ('type', 'value', 'line')

    def __init__(self, type_: TokenType, value, line: int):
        self.type  = type_
        self.value = value
        self.line  = line

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line})"
