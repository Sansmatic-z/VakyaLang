# वाक् भाषा - अमूर्त वाक्य-वृक्ष (Abstract Syntax Tree Nodes)
# Vak Language - AST Node Definitions

from dataclasses import dataclass, field
from typing import Any, List, Optional, Dict

# ── Base ──────────────────────────────────────────────────────────────────────

class Node:
    """Base class for all AST nodes."""
    line: int = 0

# ── Statements ────────────────────────────────────────────────────────────────

@dataclass
class Program(Node):
    body: List[Any]

@dataclass
class VarDecl(Node):
    """चर a, b = value"""
    names: List[str]
    value: Any
    type_hint: Optional[str] = None
    line: int = 0

@dataclass
class ConstDecl(Node):
    name: str
    value: Any
    type_hint: Optional[str] = None
    line: int = 0

@dataclass
class FuncDecl(Node):
    """
    कर्म name(params...):
    body
    
    Or async:
    अतुल्यकालिक कर्म name(params...):
    body
    """
    name: str
    params: List[Any]  # List of (name, type_hint) tuples
    defaults: List[Any]  # default values (None if no default)
    varargs: Optional[str]
    body: Any
    return_type: Optional[str] = None
    is_async: bool = False  # True if declared with अतुल्यकालिक (async)
    line: int = 0

@dataclass
class ClassDecl(Node):
    """
    वर्ग Name(Parent):
    body
    """
    name: str
    superclass: Optional[Any]
    body: Any  # Block
    line: int = 0


@dataclass
class DataVariantDecl(Node):
    """Variant declaration inside डेटा."""
    name: str
    field_types: List[str] = field(default_factory=list)
    line: int = 0


@dataclass
class DataDecl(Node):
    """
    डेटा Option[T]:
        कुछ(T)
        रिक्त
    """
    name: str
    type_params: List[str]
    variants: List[DataVariantDecl]
    line: int = 0

# ── Macro System (Pāṇinian सूत्र) ─────────────────────────────────────────────

@dataclass
class SutraDecl(Node):
    """
    सूत्र name(params):
        अनुवाद -> expansion
    
    Macro definition using Pāṇini's sūtra (rule) concept.
    The expansion template (अनुवाद) is substituted at compile-time.
    """
    name: str
    params: List[str]
    expansion: Any  # The AST node to expand to
    patterns: List[Any] = field(default_factory=list)
    line: int = 0
    anuvritti_rules: Optional[List[Any]] = None  # Context continuation rules
    scope: Optional[str] = None
    is_apavada: bool = False

@dataclass
class RewriteRule(Node):
    """pattern -> replacement"""
    pattern: Any
    replacement: Any
    line: int = 0

@dataclass
class ParinamaDecl(Node):
    """
    पारिणाम name:
        pattern -> replacement
    
    A fixed-point rewrite system applied at compile time.
    """
    name: str
    rules: List[RewriteRule]
    line: int = 0
    scope: Optional[str] = None

@dataclass
class MacroPattern(Node):
    """
    Pattern matching for macro expansion.
    
    Allows sophisticated pattern matching in macro templates.
    """
    pattern_type: str  # 'identifier', 'expression', 'statement', 'block'
    name: str
    constraints: Optional[Dict[str, Any]] = None
    line: int = 0

@dataclass
class ReturnStmt(Node):
    """प्रत्यागच्छ expr"""
    value: Any
    line: int = 0

@dataclass
class PrintStmt(Node):
    """मुद्रय expr, expr, ..."""
    values: List[Any]
    line: int = 0

@dataclass
class IfStmt(Node):
    """
    यदि cond:
    then_body
    अन्यत् cond:
    elif_body
    अन्यथा:
    else_body
    """
    condition: Any
    then_body: Any
    elif_clauses: List[Any]  # list of (condition, body) tuples
    else_body: Optional[Any]
    line: int = 0

@dataclass
class WhileStmt(Node):
    """यावत् cond: body"""
    condition: Any
    body: Any
    line: int = 0

@dataclass
class ForStmt(Node):
    """प्रत्येक चर var अन्तर्गत iterable: body"""
    var_names: List[str]
    iterable: Any
    body: Any
    line: int = 0

    @property
    def var_name(self):
        return self.var_names[0] if len(self.var_names) == 1 else tuple(self.var_names)

    @var_name.setter
    def var_name(self, value):
        if isinstance(value, list):
            self.var_names = value
        elif isinstance(value, tuple):
            self.var_names = list(value)
        else:
            self.var_names = [value]

@dataclass
class BreakStmt(Node):
    """विराम"""
    line: int = 0

@dataclass
class ContinueStmt(Node):
    """अग्रे"""
    line: int = 0

@dataclass
class GlobalStmt(Node):
    """वैश्विक a, b, c"""
    names: List[str]
    line: int = 0

@dataclass
class NonlocalStmt(Node):
    """अस्थानिक a, b, c"""
    names: List[str]
    line: int = 0

@dataclass
class CatchHandler(Node):
    """Single पकड़ो/दोष handler."""
    match_name: Optional[str]
    bind_name: Optional[str]
    body: Any
    line: int = 0


@dataclass
class TryStmt(Node):
    """
    प्रयत्न:
    try_body
    दोष handler:
    catch_body
    अन्ततः:
    finally_body
    """
    try_body: Any
    handlers: List[CatchHandler] = field(default_factory=list)
    finally_body: Optional[Any] = None
    line: int = 0

    @property
    def catch_var(self) -> Optional[str]:
        if not self.handlers:
            return None
        return self.handlers[0].bind_name

    @catch_var.setter
    def catch_var(self, value: Optional[str]) -> None:
        if not self.handlers:
            if value is not None:
                self.handlers = [CatchHandler(match_name=value, bind_name=value, body=None, line=self.line)]
            return
        self.handlers[0].bind_name = value

    @property
    def catch_body(self) -> Optional[Any]:
        if not self.handlers:
            return None
        return self.handlers[0].body

    @catch_body.setter
    def catch_body(self, value: Optional[Any]) -> None:
        if not self.handlers:
            if value is not None:
                self.handlers = [CatchHandler(match_name=None, bind_name=None, body=value, line=self.line)]
            return
        self.handlers[0].body = value

@dataclass
class WithStmt(Node):
    """साथ expr जैसे var: body"""
    expr: Any
    var_name: Optional[str]
    body: Any
    line: int = 0

@dataclass
class ThrowStmt(Node):
    """उत्क्षिप expr"""
    value: Any
    line: int = 0

@dataclass
class ImportStmt(Node):
    """
    आयात module
    आयात name से module
    """
    module: str
    names: Optional[List[str]]  # None = import whole module
    line: int = 0

@dataclass
class ExprStmt(Node):
    """A bare expression used as a statement."""
    expr: Any
    line: int = 0

@dataclass
class Block(Node):
    """A sequence of statements."""
    stmts: List[Any]
    line: int = 0

@dataclass
class MatchCase(Node):
    """Single pattern-matching arm."""
    pattern: Any
    body: Any
    guard: Optional[Any] = None
    line: int = 0

@dataclass
class MatchStmt(Node):
    """प्रत्यभिज्ञा subject: pattern: body"""
    subject: Any
    cases: List[MatchCase]
    line: int = 0

# ── Expressions ───────────────────────────────────────────────────────────────

@dataclass
class BinaryExpr(Node):
    """left op right"""
    op: str
    left: Any
    right: Any
    line: int = 0

@dataclass
class UnaryExpr(Node):
    """op expr"""
    op: str
    operand: Any
    line: int = 0

@dataclass
class ConditionalExpr(Node):
    """then_expr if condition else else_expr"""
    condition: Any
    then_expr: Any
    else_expr: Any
    line: int = 0

@dataclass
class AssignExpr(Node):
    """target = value (also +=, -=, etc.)"""
    target: Any
    op: str
    value: Any
    line: int = 0

@dataclass
class CallExpr(Node):
    """callee(args, kwargs)"""
    callee: Any
    args: List[Any]
    kwargs: dict
    line: int = 0

@dataclass
class MemberExpr(Node):
    """object.attribute"""
    obj: Any
    attr: str
    line: int = 0

@dataclass
class IndexExpr(Node):
    """object[index]"""
    obj: Any
    index: Any
    line: int = 0

@dataclass
class SliceExpr(Node):
    """object[start:stop:step]"""
    obj: Any
    start: Optional[Any]
    stop: Optional[Any]
    step: Optional[Any]
    line: int = 0

@dataclass
class IdentifierExpr(Node):
    """A bare name."""
    name: str
    line: int = 0

@dataclass
class NumberLiteral(Node):
    value: Any  # int or float
    line: int = 0

@dataclass
class StringLiteral(Node):
    value: str
    line: int = 0

@dataclass
class FStringExpr(Node):
    parts: List[Any]  # Mix of strings and expressions
    line: int = 0

@dataclass
class BoolLiteral(Node):
    value: bool
    line: int = 0

@dataclass
class NullLiteral(Node):
    line: int = 0

@dataclass
class ListLiteral(Node):
    elements: List[Any]
    line: int = 0

@dataclass
class ListComp(Node):
    """[expr प्रत्येक चर var_name अन्तर्गत iterable]"""
    expr: Any
    var_name: str
    iterable: Any
    filter_expr: Optional[Any] = None
    line: int = 0

@dataclass
class DictLiteral(Node):
    pairs: List[Any]  # list of (key_expr, val_expr) tuples
    line: int = 0

@dataclass
class DictComp(Node):
    """{key: value प्रत्येक चर var_name अन्तर्गत iterable}"""
    key_expr: Any
    value_expr: Any
    var_name: str
    iterable: Any
    filter_expr: Optional[Any] = None
    line: int = 0

@dataclass
class SetLiteral(Node):
    elements: List[Any]
    line: int = 0

@dataclass
class TupleLiteral(Node):
    elements: List[Any]
    line: int = 0

@dataclass
class LambdaExpr(Node):
    """Anonymous function expression."""
    params: List[str]
    varargs: Optional[str]
    body: Any
    line: int = 0

@dataclass
class AwaitExpr(Node):
    """
    प्रतीक्षा expr - await expression

    Waits for a coroutine to complete and returns its result.
    Can only be used inside an async function (अतुल्यकालिक कर्म).
    """
    operand: Any
    line: int = 0


# ── Pattern Matching (प्रत्यभिज्ञा) ──────────────────────────────────────────

@dataclass
class WildcardPattern(Node):
    """_"""
    line: int = 0

@dataclass
class BindingPattern(Node):
    """name"""
    name: str
    line: int = 0

@dataclass
class LiteralPattern(Node):
    """Literal value match."""
    value: Any
    line: int = 0

@dataclass
class SequencePattern(Node):
    """[a, b, ...] or (a, b)"""
    kind: str
    elements: List[Any]
    rest_name: Optional[str] = None
    line: int = 0

@dataclass
class CallPattern(Node):
    """सिद्ध(x), असिद्ध(err), ClassPattern(...)"""
    callee: str
    args: List[Any]
    line: int = 0


# ── Vibhakti Semantic Role System (विभक्ति प्रणाली) ──────────────────────────

@dataclass
class VibhaktiParam(Node):
    """
    Parameter decorated with a Vibhakti (semantic role).
    
    Example:
        कर्म योग(कर्ता: संख्या, कर्म: संख्या) → संख्या:
            प्रत्यागच्छ कर्ता + कर्म
    
    Here कर्ता and कर्म are Vibhakti markers.
    """
    name: str                    # Parameter name
    vibhakti: str                # Vibhakti role (कर्ता, कर्म, करण, etc.)
    type_hint: Optional[str] = None  # Optional type annotation
    default: Any = None          # Optional default value
    line: int = 0


@dataclass
class FuncDecl(Node):
    """
    कर्म name(params...):
    body

    Or async:
    अतुल्यकालिक कर्म name(params...):
    body
    
    Supports Vibhakti-decorated parameters.
    """
    name: str
    params: List[Any]  # List of (name, type_hint) tuples OR VibhaktiParam objects
    defaults: List[Any]  # default values (None if no default)
    varargs: Optional[str]
    body: Any
    return_type: Optional[str] = None
    is_async: bool = False  # True if declared with अतुल्यकालिक (async)
    vibhakti_signature: Any = None  # Optional VibhaktiSignature object
    line: int = 0


# ── Nyāya Proof System (न्याय प्रमाण प्रणाली) ─────────────────────────────────

@dataclass
class ProofDeclaration(Node):
    """
    सिद्धि: statement
        प्रमाण:
            evidence_code
        प्रमाण_पत्र: "certificate_string"
    
    A compile-time proof declaration verified by SansmaticEngine.
    """
    statement: str               # The statement to prove (e.g., "अभाज्य_है(१७)")
    evidence_body: Any           # AST block containing proof evidence
    statement_expr: Any = None   # Original AST expression for stronger proof checking
    certificate: Optional[str] = None  # Proof certificate string
    line: int = 0
    verified: bool = False       # True if proof was verified at compile-time
