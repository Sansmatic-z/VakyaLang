from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any

from .ast_nodes import Node


@dataclass
class FunctionScopeInfo:
    local_names: set[str] = field(default_factory=set)
    global_names: set[str] = field(default_factory=set)
    nonlocal_names: set[str] = field(default_factory=set)
    used_names: set[str] = field(default_factory=set)
    closure_names: set[str] = field(default_factory=set)


RETURN_TYPE_HINT_KEY = "__return__"


def copy_dynamic_node_attrs(source: Node, target: Node) -> Node:
    """Preserve compiler metadata attached outside dataclass fields."""
    target_fields = set(getattr(target, "__dataclass_fields__", {}).keys())
    for key, value in getattr(source, "__dict__", {}).items():
        if key not in target_fields:
            setattr(target, key, value)
    return target


def iter_child_nodes(value: Any):
    if isinstance(value, Node):
        yield value
        return
    if isinstance(value, list):
        for item in value:
            yield from iter_child_nodes(item)
        return
    if isinstance(value, tuple):
        for item in value:
            yield from iter_child_nodes(item)
        return
    if isinstance(value, dict):
        for item in value.values():
            yield from iter_child_nodes(item)


def function_contains_yield(value: Any) -> bool:
    """Return True if a function body contains yield outside nested declarations."""
    node_type = type(value).__name__
    if node_type in {"YieldStmt", "YieldFromStmt"}:
        return True
    if node_type in {"FuncDecl", "LambdaExpr", "ClassDecl"}:
        return False
    if isinstance(value, Node) and is_dataclass(value):
        for field_info in fields(value):
            if field_info.name == "line":
                continue
            if function_contains_yield(getattr(value, field_info.name)):
                return True
        return False
    if isinstance(value, dict):
        return any(function_contains_yield(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(function_contains_yield(item) for item in value)
    return False
