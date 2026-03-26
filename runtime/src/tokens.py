# वाक् भाषा - शब्द-चिह्न परिभाषाएँ (Token Definitions)
# Vak Language - Token Types

from enum import Enum, auto


class TokenType(Enum):
    # ── Literals ──────────────────────────────────────────────────────────────
    NUMBER      = auto()   # 42, ४२, 3.14, ३.१४
    STRING      = auto()   # "नमस्ते"
    FSTRING     = auto()   # f"नमस्ते {नाम}"
    TRUE        = auto()   # सत्य
    FALSE       = auto()   # असत्य
    NULL        = auto()   # शून्य

    # ── Identifiers & Keywords ────────────────────────────────────────────────
    IDENTIFIER  = auto()

    VAR         = auto()   # चर      (variable)
    CONST       = auto()   # स्थिर   (constant)
    FUNC        = auto()   # कर्म    (function / action)
    CLASS       = auto()   # वर्ग    (class / category)
    DATA        = auto()   # डेटा   (algebraic data / tagged union)
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
    MATCH       = auto()   # प्रत्यभिज्ञा (pattern matching / recognition)
    FROM        = auto()   # से      (from)
    WITH        = auto()   # साथ     (with)
    AS          = auto()   # जैसे    (as)
    NEW         = auto()   # नव      (new)
    SELF        = auto()   # स्वयं   (self / oneself)
    SUPER       = auto()   # अभिभावक (super / parent)
    GLOBAL      = auto()   # वैश्विक (global)
    NONLOCAL    = auto()   # अस्थानिक (nonlocal)
    
    # ── Async/Await Keywords ──────────────────────────────────────────────────
    ASYNC       = auto()   # अतुल्यकालिक (async - asynchronous)
    AWAIT       = auto()   # प्रतीक्षा   (await - wait)

    # ── Arithmetic Operators ──────────────────────────────────────────────────
    PLUS        = auto()   # +
    MINUS       = auto()   # -
    STAR        = auto()   # *
    SLASH       = auto()   # /
    DOUBLESLASH = auto()   # // (integer division)
    PERCENT     = auto()   # %
    POWER       = auto()   # **

    # ── Bitwise Operators ─────────────────────────────────────────────────────
    BAND        = auto()   # &
    BOR         = auto()   # |
    BXOR        = auto()   # ^
    BNOT        = auto()   # ~
    PIPE_OP     = auto()   # |>
    LSHIFT      = auto()   # <<
    RSHIFT      = auto()   # >>

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
    WALRUS      = auto()   # :=

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

    # ── Macro Keywords (Pāṇinian Macro System) ───────────────────────────────
    SUTRA       = auto()   # सूत्र (macro definition)
    APAVADA     = auto()   # अपवाद (exception rule)
    PARINAMA    = auto()   # पारिणाम (rewrite/fixpoint rules)
    ADHIKARA    = auto()   # अधिकार (scope declaration)
    ANUVADA     = auto()   # अनुवाद (macro expansion template)
    LARROW      = auto()   # -> (expansion arrow)

    # ── Vibhakti Semantic Roles (विभक्तियाँ) ─────────────────────────────────
    # The 8 Sanskrit grammatical cases for semantic role-based arguments
    KARTA       = auto()   # कर्ता (Agent/Doer - 1st case)
    KARMA       = auto()   # कर्म (Object/Patient - 2nd case)
    KARANA      = auto()   # करण (Instrument/Means - 3rd case)
    SAMPRADANA  = auto()   # सम्प्रदान (Recipient/Goal - 4th case)
    APADANA     = auto()   # अपादान (Source/Origin - 5th case)
    SAMBANDHA   = auto()   # सम्बन्ध (Possession/Relation - 6th case)
    ADHIKARANA  = auto()   # अधिकरण (Location/Locus - 7th case)
    AMANTRANA   = auto()   # आमन्त्रण (Address/Vocative - 8th case)

    # ── Nyāya Proof System Keywords (न्याय प्रमाण) ───────────────────────────
    SIDDHI      = auto()   # सिद्धि (proof/achievement)
    PRAMANA     = auto()   # प्रमाण (evidence/proof method)
    PRAMANA_PATRA = auto() # प्रमाण_पत्र (proof certificate)


# Sanskrit keyword map: Devanagari → TokenType
KEYWORDS = {
    'चर':           TokenType.VAR,
    'मान':          TokenType.VAR,
    'स्थिर':        TokenType.CONST,
    'कर्म':         TokenType.FUNC,
    'वर्ग':         TokenType.CLASS,
    'डेटा':        TokenType.DATA,
    'प्रत्यागच्छ':  TokenType.RETURN,
    'वापस':         TokenType.RETURN,
    'यदि':          TokenType.IF,
    'अन्यत्':       TokenType.ELIF,
    'अन्यथा':       TokenType.ELSE,
    'यावत्':        TokenType.WHILE,
    'प्रत्येक':     TokenType.FOR,
    'प्रति':        TokenType.FOR,
    'अन्तर्गत':     TokenType.IN,
    'में':          TokenType.IN,
    'in':           TokenType.IN,
    'विराम':        TokenType.BREAK,
    'तोड़ो':        TokenType.BREAK,
    'break':        TokenType.BREAK,
    'अग्रे':        TokenType.CONTINUE,
    'जारी':         TokenType.CONTINUE,
    'continue':     TokenType.CONTINUE,
    'वैश्विक':      TokenType.GLOBAL,
    'global':       TokenType.GLOBAL,
    'अस्थानिक':     TokenType.NONLOCAL,
    'मुद्रय':       TokenType.PRINT,
    'बोलो':         TokenType.PRINT,
    'और':           TokenType.AND,
    'अथवा':         TokenType.OR,
    'न':            TokenType.NOT,
    'नो':           TokenType.NOT,
    'not':          TokenType.NOT,
    'सत्य':         TokenType.TRUE,
    'असत्य':        TokenType.FALSE,
    'शून्य':        TokenType.NULL,
    'प्रयत्न':      TokenType.TRY,
    'प्रयास':       TokenType.TRY,
    'दोष':          TokenType.CATCH,
    'पकड़ो':        TokenType.CATCH,
    'अन्ततः':       TokenType.FINALLY,
    'उत्क्षिप':     TokenType.THROW,
    'आयात':         TokenType.IMPORT,
    'प्रत्यभिज्ञा':  TokenType.MATCH,
    'से':           TokenType.FROM,
    'साथ':          TokenType.WITH,
    'जैसे':         TokenType.AS,
    'नव':           TokenType.NEW,
    'स्वयं':        TokenType.SELF,
    'अभिभावक':      TokenType.SUPER,
    # Async/Await keywords
    'अतुल्यकालिक':  TokenType.ASYNC,
    'असंकालिक':     TokenType.ASYNC,
    'प्रतीक्षा':    TokenType.AWAIT,
    # Pāṇinian Macro System keywords
    'सूत्र':        TokenType.SUTRA,
    'उत्सर्ग':      TokenType.SUTRA,
    'अपवाद':       TokenType.APAVADA,
    'पारिणाम':     TokenType.PARINAMA,
    'अधिकार':      TokenType.ADHIKARA,
    'अनुवाद':       TokenType.ANUVADA,
    # Vibhakti Semantic Roles (विभक्तियाँ)
    # Note: कर्म is NOT included here - it remains FUNC (function keyword)
    # Users must use alternative Vibhakti markers or regular parameter names
    'कर्ता':        TokenType.KARTA,
    # 'कर्म' intentionally excluded - stays as FUNC for function declarations
    'करण':         TokenType.KARANA,
    'सम्प्रदान':    TokenType.SAMPRADANA,
    'अपादान':       TokenType.APADANA,
    'सम्बन्ध':      TokenType.SAMBANDHA,
    'अधिकरण':      TokenType.ADHIKARANA,
    'आमन्त्रण':     TokenType.AMANTRANA,
    # Nyāya Proof System keywords
    'सिद्धि':       TokenType.SIDDHI,
    'प्रमाण':       TokenType.PRAMANA,
    'प्रमाण_पत्र':  TokenType.PRAMANA_PATRA,
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


# ─────────────────────────────────────────────────────────────────────────────
# NOTE: Constructor Naming Convention
# ─────────────────────────────────────────────────────────────────────────────
# Class constructors should prefer: प्रारम्भ (praarambha - "beginning/init")
# Compatibility alias: __init__ is also accepted by the VM.
# Example:
#   वर्ग गणक:
#       कर्म प्रारम्भ(स्वयं, मान):
#           स्वयं.मान = मान
#
# This ensures consistent object initialization across all VakyaLang classes.
# ─────────────────────────────────────────────────────────────────────────────
