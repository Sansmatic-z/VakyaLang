# VakyaLang (????) � Copyright (c) 2026 Raj Mitra. All Rights Reserved.
# Original author: Raj Mitra (Visionary RM)
# Licensed under GNU AGPL v3.0 � see LICENSE and NOTICE.
# Any use, modification, or derivative work must preserve this header
# and include the NOTICE file. https://github.com/Sansmatic-z/VakyaLang

# वाक् भाषा - अमूर्त वाक्य-वृक्ष (Abstract Syntax Tree Nodes)
# Vak Language - AST Node Definitions

from dataclasses import dataclass, field
from typing import Any, List, Optional

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
    """चर name = value"""
    name: str
    value: Any
    line: int = 0

@dataclass
class ConstDecl(Node):
    """स्थिर name = value"""
    name: str
    value: Any
    line: int = 0

@dataclass
class FuncDecl(Node):
    """
    कर्म name(params...):
    body
    """
    name: str
    params: List[str]
    defaults: List[Any] # default values (None if no default)
    body: Any # Block
    line: int = 0

@dataclass
class ClassDecl(Node):
    """
    वर्ग Name(Parent):
    body
    """
    name: str
    superclass: Optional[Any]
    body: Any # Block
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
    elif_clauses: List[Any] # list of (condition, body) tuples
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
    var_name: str
    iterable: Any
    body: Any
    line: int = 0

@dataclass
class BreakStmt(Node):
    """विराम"""
    line: int = 0

@dataclass
class ContinueStmt(Node):
    """अग्रे"""
    line: int = 0

@dataclass
class TryStmt(Node):
    """
    प्रयत्न:
    try_body
    दोष var:
    catch_body
    अन्ततः:
    finally_body
    """
    try_body: Any
    catch_var: Optional[str]
    catch_body: Optional[Any]
    finally_body: Optional[Any]
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
    names: Optional[List[str]] # None = import whole module
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
class IdentifierExpr(Node):
    """A bare name."""
    name: str
    line: int = 0

@dataclass
class NumberLiteral(Node):
    value: Any # int or float
    line: int = 0

@dataclass
class StringLiteral(Node):
    value: str
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
class DictLiteral(Node):
    pairs: List[Any] # list of (key_expr, val_expr) tuples
    line: int = 0

@dataclass
class LambdaExpr(Node):
    """Anonymous function expression."""
    params: List[str]
    body: Any
    line: int = 0

