# वाक् भाषा - परिणाम पुनर्लेखन इंजन
# Vak Language - Fixed-point rewrite engine for परिणाम rules and macro matching

from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, Iterable, Optional, Tuple

from .ast_nodes import (
    AssignExpr,
    BinaryExpr,
    Block,
    BoolLiteral,
    CallExpr,
    ClassDecl,
    ConditionalExpr,
    ConstDecl,
    DictComp,
    DictLiteral,
    ExprStmt,
    FStringExpr,
    ForStmt,
    FuncDecl,
    IdentifierExpr,
    IfStmt,
    ImportStmt,
    IndexExpr,
    LambdaExpr,
    ListComp,
    ListLiteral,
    MemberExpr,
    NullLiteral,
    NumberLiteral,
    Program,
    ReturnStmt,
    RewriteRule,
    SetLiteral,
    SliceExpr,
    StringLiteral,
    TryStmt,
    TupleLiteral,
    UnaryExpr,
    VarDecl,
    WhileStmt,
    WithStmt,
)
from .errors import MacroError


def structural_equal(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False

    if isinstance(left, (NumberLiteral, StringLiteral, BoolLiteral)):
        return left.value == right.value
    if isinstance(left, NullLiteral):
        return True
    if isinstance(left, IdentifierExpr):
        return left.name == right.name
    if isinstance(left, BinaryExpr):
        return (
            left.op == right.op
            and structural_equal(left.left, right.left)
            and structural_equal(left.right, right.right)
        )
    if isinstance(left, UnaryExpr):
        return left.op == right.op and structural_equal(left.operand, right.operand)
    if isinstance(left, CallExpr):
        return (
            structural_equal(left.callee, right.callee)
            and len(left.args) == len(right.args)
            and all(structural_equal(a, b) for a, b in zip(left.args, right.args))
            and left.kwargs.keys() == right.kwargs.keys()
            and all(structural_equal(left.kwargs[key], right.kwargs[key]) for key in left.kwargs)
        )
    if isinstance(left, MemberExpr):
        return left.attr == right.attr and structural_equal(left.obj, right.obj)
    if isinstance(left, IndexExpr):
        return structural_equal(left.obj, right.obj) and structural_equal(left.index, right.index)
    if isinstance(left, SliceExpr):
        return (
            structural_equal(left.obj, right.obj)
            and structural_equal(left.start, right.start)
            and structural_equal(left.stop, right.stop)
            and structural_equal(left.step, right.step)
        )
    if isinstance(left, (ListLiteral, TupleLiteral, SetLiteral)):
        return len(left.elements) == len(right.elements) and all(
            structural_equal(a, b) for a, b in zip(left.elements, right.elements)
        )
    if isinstance(left, DictLiteral):
        return len(left.pairs) == len(right.pairs) and all(
            structural_equal(lk, rk) and structural_equal(lv, rv)
            for (lk, lv), (rk, rv) in zip(left.pairs, right.pairs)
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(structural_equal(a, b) for a, b in zip(left, right))
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(structural_equal(left[k], right[k]) for k in left)
    return left == right


def match_pattern(pattern: Any, value: Any, bindings: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    bindings = dict(bindings or {})

    if isinstance(pattern, IdentifierExpr):
        if pattern.name == "_":
            return bindings
        existing = bindings.get(pattern.name)
        if existing is not None and not structural_equal(existing, value):
            return None
        bindings[pattern.name] = value
        return bindings

    if type(pattern) is not type(value):
        return None

    if isinstance(pattern, NumberLiteral):
        return bindings if pattern.value == value.value else None
    if isinstance(pattern, StringLiteral):
        return bindings if pattern.value == value.value else None
    if isinstance(pattern, BoolLiteral):
        return bindings if pattern.value == value.value else None
    if isinstance(pattern, NullLiteral):
        return bindings
    if isinstance(pattern, BinaryExpr):
        if pattern.op != value.op:
            return None
        bindings = match_pattern(pattern.left, value.left, bindings)
        return None if bindings is None else match_pattern(pattern.right, value.right, bindings)
    if isinstance(pattern, UnaryExpr):
        if pattern.op != value.op:
            return None
        return match_pattern(pattern.operand, value.operand, bindings)
    if isinstance(pattern, CallExpr):
        if len(pattern.args) != len(value.args) or pattern.kwargs.keys() != value.kwargs.keys():
            return None
        bindings = match_pattern(pattern.callee, value.callee, bindings)
        if bindings is None:
            return None
        for left_arg, right_arg in zip(pattern.args, value.args):
            bindings = match_pattern(left_arg, right_arg, bindings)
            if bindings is None:
                return None
        for key in pattern.kwargs:
            bindings = match_pattern(pattern.kwargs[key], value.kwargs[key], bindings)
            if bindings is None:
                return None
        return bindings
    if isinstance(pattern, MemberExpr):
        if pattern.attr != value.attr:
            return None
        return match_pattern(pattern.obj, value.obj, bindings)
    if isinstance(pattern, IndexExpr):
        bindings = match_pattern(pattern.obj, value.obj, bindings)
        return None if bindings is None else match_pattern(pattern.index, value.index, bindings)
    if isinstance(pattern, SliceExpr):
        for left_part, right_part in (
            (pattern.obj, value.obj),
            (pattern.start, value.start),
            (pattern.stop, value.stop),
            (pattern.step, value.step),
        ):
            if left_part is None or right_part is None:
                if left_part is not right_part:
                    return None
            else:
                bindings = match_pattern(left_part, right_part, bindings)
                if bindings is None:
                    return None
        return bindings
    if isinstance(pattern, (ListLiteral, TupleLiteral, SetLiteral)):
        if len(pattern.elements) != len(value.elements):
            return None
        for left_item, right_item in zip(pattern.elements, value.elements):
            bindings = match_pattern(left_item, right_item, bindings)
            if bindings is None:
                return None
        return bindings
    if isinstance(pattern, DictLiteral):
        if len(pattern.pairs) != len(value.pairs):
            return None
        for (left_key, left_value), (right_key, right_value) in zip(pattern.pairs, value.pairs):
            bindings = match_pattern(left_key, right_key, bindings)
            if bindings is None:
                return None
            bindings = match_pattern(left_value, right_value, bindings)
            if bindings is None:
                return None
        return bindings

    return bindings if pattern == value else None


def pattern_specificity(node: Any) -> int:
    if node is None:
        return 0
    if isinstance(node, IdentifierExpr):
        return 0 if node.name != "_" else -1
    if isinstance(node, (NumberLiteral, StringLiteral, BoolLiteral, NullLiteral)):
        return 2
    if isinstance(node, BinaryExpr):
        return 1 + pattern_specificity(node.left) + pattern_specificity(node.right)
    if isinstance(node, UnaryExpr):
        return 1 + pattern_specificity(node.operand)
    if isinstance(node, CallExpr):
        return 2 + pattern_specificity(node.callee) + sum(pattern_specificity(arg) for arg in node.args)
    if isinstance(node, MemberExpr):
        return 1 + pattern_specificity(node.obj)
    if isinstance(node, IndexExpr):
        return 1 + pattern_specificity(node.obj) + pattern_specificity(node.index)
    if isinstance(node, SliceExpr):
        return 1 + sum(pattern_specificity(part) for part in (node.obj, node.start, node.stop, node.step))
    if isinstance(node, (ListLiteral, TupleLiteral, SetLiteral)):
        return 1 + sum(pattern_specificity(item) for item in node.elements)
    if isinstance(node, DictLiteral):
        return 1 + sum(pattern_specificity(key) + pattern_specificity(value) for key, value in node.pairs)
    return 1


def substitute_bindings(node: Any, bindings: Dict[str, Any]) -> Any:
    if node is None:
        return None
    if isinstance(node, IdentifierExpr):
        return bindings.get(node.name, node)
    if isinstance(node, BinaryExpr):
        return replace(
            node,
            left=substitute_bindings(node.left, bindings),
            right=substitute_bindings(node.right, bindings),
        )
    if isinstance(node, UnaryExpr):
        return replace(node, operand=substitute_bindings(node.operand, bindings))
    if isinstance(node, CallExpr):
        return replace(
            node,
            callee=substitute_bindings(node.callee, bindings),
            args=[substitute_bindings(arg, bindings) for arg in node.args],
            kwargs={key: substitute_bindings(value, bindings) for key, value in node.kwargs.items()},
        )
    if isinstance(node, MemberExpr):
        return replace(node, obj=substitute_bindings(node.obj, bindings))
    if isinstance(node, IndexExpr):
        return replace(
            node,
            obj=substitute_bindings(node.obj, bindings),
            index=substitute_bindings(node.index, bindings),
        )
    if isinstance(node, SliceExpr):
        return replace(
            node,
            obj=substitute_bindings(node.obj, bindings),
            start=substitute_bindings(node.start, bindings),
            stop=substitute_bindings(node.stop, bindings),
            step=substitute_bindings(node.step, bindings),
        )
    if isinstance(node, ListLiteral):
        return replace(node, elements=[substitute_bindings(item, bindings) for item in node.elements])
    if isinstance(node, TupleLiteral):
        return replace(node, elements=[substitute_bindings(item, bindings) for item in node.elements])
    if isinstance(node, SetLiteral):
        return replace(node, elements=[substitute_bindings(item, bindings) for item in node.elements])
    if isinstance(node, DictLiteral):
        return replace(
            node,
            pairs=[(substitute_bindings(key, bindings), substitute_bindings(value, bindings)) for key, value in node.pairs],
        )
    if isinstance(node, ListComp):
        return replace(
            node,
            expr=substitute_bindings(node.expr, bindings),
            iterable=substitute_bindings(node.iterable, bindings),
            filter_expr=substitute_bindings(node.filter_expr, bindings),
        )
    if isinstance(node, DictComp):
        return replace(
            node,
            key_expr=substitute_bindings(node.key_expr, bindings),
            value_expr=substitute_bindings(node.value_expr, bindings),
            iterable=substitute_bindings(node.iterable, bindings),
            filter_expr=substitute_bindings(node.filter_expr, bindings),
        )
    if isinstance(node, ConditionalExpr):
        return replace(
            node,
            condition=substitute_bindings(node.condition, bindings),
            then_expr=substitute_bindings(node.then_expr, bindings),
            else_expr=substitute_bindings(node.else_expr, bindings),
        )
    if isinstance(node, FStringExpr):
        return replace(node, parts=[substitute_bindings(part, bindings) for part in node.parts])
    return node


def rewrite_fixed_point(node: Any, rules: Iterable[RewriteRule], max_iterations: int = 128) -> Any:
    current = node
    ordered_rules = list(rules)
    for _ in range(max_iterations):
        current, changed = _rewrite_once(current, ordered_rules)
        if not changed:
            return current
    raise MacroError("पारिणाम पुनर्लेखन स्थिर-बिंदु तक नहीं पहुंचा", getattr(node, "line", 0))


def _rewrite_once(node: Any, rules: list[RewriteRule]) -> Tuple[Any, bool]:
    direct = _apply_direct_rules(node, rules)
    if direct is not None:
        return direct, True

    if isinstance(node, BinaryExpr):
        left, changed = _rewrite_once(node.left, rules)
        if changed:
            return replace(node, left=left), True
        right, changed = _rewrite_once(node.right, rules)
        if changed:
            return replace(node, right=right), True
        return node, False
    if isinstance(node, UnaryExpr):
        operand, changed = _rewrite_once(node.operand, rules)
        return (replace(node, operand=operand), True) if changed else (node, False)
    if isinstance(node, CallExpr):
        callee, changed = _rewrite_once(node.callee, rules)
        if changed:
            return replace(node, callee=callee), True
        for index, arg in enumerate(node.args):
            new_arg, changed = _rewrite_once(arg, rules)
            if changed:
                args = list(node.args)
                args[index] = new_arg
                return replace(node, args=args), True
        for key, value in node.kwargs.items():
            new_value, changed = _rewrite_once(value, rules)
            if changed:
                kwargs = dict(node.kwargs)
                kwargs[key] = new_value
                return replace(node, kwargs=kwargs), True
        return node, False
    if isinstance(node, (ListLiteral, TupleLiteral, SetLiteral)):
        for index, element in enumerate(node.elements):
            new_element, changed = _rewrite_once(element, rules)
            if changed:
                elements = list(node.elements)
                elements[index] = new_element
                return replace(node, elements=elements), True
        return node, False
    if isinstance(node, DictLiteral):
        for index, (key, value) in enumerate(node.pairs):
            new_key, changed = _rewrite_once(key, rules)
            if changed:
                pairs = list(node.pairs)
                pairs[index] = (new_key, value)
                return replace(node, pairs=pairs), True
            new_value, changed = _rewrite_once(value, rules)
            if changed:
                pairs = list(node.pairs)
                pairs[index] = (key, new_value)
                return replace(node, pairs=pairs), True
        return node, False
    return node, False


def _apply_direct_rules(node: Any, rules: list[RewriteRule]) -> Optional[Any]:
    matches = []
    for index, rule in enumerate(rules):
        bindings = match_pattern(rule.pattern, node, {})
        if bindings is not None:
            matches.append((pattern_specificity(rule.pattern), index, rule, bindings))

    if not matches:
        return None

    matches.sort(key=lambda item: (-item[0], item[1]))
    top_specificity = matches[0][0]
    ambiguous = [item for item in matches if item[0] == top_specificity]
    if len(ambiguous) > 1:
        raise MacroError(
            "अस्पष्ट पारिणाम नियम: एक ही स्तर पर अनेक नियम मेल खाते हैं",
            getattr(node, "line", 0),
        )

    _, _, rule, bindings = matches[0]
    return substitute_bindings(rule.replacement, bindings)


def encode_rewrite_node(node: Any) -> Any:
    """Serialize rewrite-capable AST nodes into ABI-safe specs."""
    if node is None:
        return None

    if isinstance(node, NumberLiteral):
        return {'kind': 'number', 'value': node.value, 'line': node.line}
    if isinstance(node, StringLiteral):
        return {'kind': 'string', 'value': node.value, 'line': node.line}
    if isinstance(node, BoolLiteral):
        return {'kind': 'bool', 'value': node.value, 'line': node.line}
    if isinstance(node, NullLiteral):
        return {'kind': 'null', 'line': node.line}
    if isinstance(node, IdentifierExpr):
        return {'kind': 'identifier', 'name': node.name, 'line': node.line}
    if isinstance(node, BinaryExpr):
        return {
            'kind': 'binary',
            'op': node.op,
            'left': encode_rewrite_node(node.left),
            'right': encode_rewrite_node(node.right),
            'line': node.line,
        }
    if isinstance(node, UnaryExpr):
        return {
            'kind': 'unary',
            'op': node.op,
            'operand': encode_rewrite_node(node.operand),
            'line': node.line,
        }
    if isinstance(node, CallExpr):
        return {
            'kind': 'call',
            'callee': encode_rewrite_node(node.callee),
            'args': [encode_rewrite_node(arg) for arg in node.args],
            'kwargs': {key: encode_rewrite_node(value) for key, value in node.kwargs.items()},
            'line': node.line,
        }
    if isinstance(node, MemberExpr):
        return {
            'kind': 'member',
            'obj': encode_rewrite_node(node.obj),
            'attr': node.attr,
            'line': node.line,
        }
    if isinstance(node, IndexExpr):
        return {
            'kind': 'index',
            'obj': encode_rewrite_node(node.obj),
            'index': encode_rewrite_node(node.index),
            'line': node.line,
        }
    if isinstance(node, SliceExpr):
        return {
            'kind': 'slice',
            'obj': encode_rewrite_node(node.obj),
            'start': encode_rewrite_node(node.start),
            'stop': encode_rewrite_node(node.stop),
            'step': encode_rewrite_node(node.step),
            'line': node.line,
        }
    if isinstance(node, ListLiteral):
        return {
            'kind': 'list',
            'elements': [encode_rewrite_node(element) for element in node.elements],
            'line': node.line,
        }
    if isinstance(node, TupleLiteral):
        return {
            'kind': 'tuple',
            'elements': [encode_rewrite_node(element) for element in node.elements],
            'line': node.line,
        }
    if isinstance(node, SetLiteral):
        return {
            'kind': 'set',
            'elements': [encode_rewrite_node(element) for element in node.elements],
            'line': node.line,
        }
    if isinstance(node, DictLiteral):
        return {
            'kind': 'dict',
            'pairs': [
                {'key': encode_rewrite_node(key), 'value': encode_rewrite_node(value)}
                for key, value in node.pairs
            ],
            'line': node.line,
        }
    raise TypeError(f"Unsupported rewrite node: {type(node).__name__}")


def decode_rewrite_node(spec: Any) -> Any:
    """Deserialize rewrite node specs back into AST nodes."""
    if spec is None:
        return None
    if not isinstance(spec, dict):
        raise TypeError(f"Unsupported rewrite spec: {spec!r}")

    kind = spec.get('kind')
    line = spec.get('line', 0)

    if kind == 'number':
        return NumberLiteral(value=spec.get('value'), line=line)
    if kind == 'string':
        return StringLiteral(value=spec.get('value', ''), line=line)
    if kind == 'bool':
        return BoolLiteral(value=bool(spec.get('value')), line=line)
    if kind == 'null':
        return NullLiteral(line=line)
    if kind == 'identifier':
        return IdentifierExpr(name=spec.get('name', ''), line=line)
    if kind == 'binary':
        return BinaryExpr(
            op=spec.get('op', ''),
            left=decode_rewrite_node(spec.get('left')),
            right=decode_rewrite_node(spec.get('right')),
            line=line,
        )
    if kind == 'unary':
        return UnaryExpr(
            op=spec.get('op', ''),
            operand=decode_rewrite_node(spec.get('operand')),
            line=line,
        )
    if kind == 'call':
        return CallExpr(
            callee=decode_rewrite_node(spec.get('callee')),
            args=[decode_rewrite_node(arg) for arg in spec.get('args', [])],
            kwargs={
                key: decode_rewrite_node(value)
                for key, value in spec.get('kwargs', {}).items()
            },
            line=line,
        )
    if kind == 'member':
        return MemberExpr(
            obj=decode_rewrite_node(spec.get('obj')),
            attr=spec.get('attr', ''),
            line=line,
        )
    if kind == 'index':
        return IndexExpr(
            obj=decode_rewrite_node(spec.get('obj')),
            index=decode_rewrite_node(spec.get('index')),
            line=line,
        )
    if kind == 'slice':
        return SliceExpr(
            obj=decode_rewrite_node(spec.get('obj')),
            start=decode_rewrite_node(spec.get('start')),
            stop=decode_rewrite_node(spec.get('stop')),
            step=decode_rewrite_node(spec.get('step')),
            line=line,
        )
    if kind == 'list':
        return ListLiteral(
            elements=[decode_rewrite_node(element) for element in spec.get('elements', [])],
            line=line,
        )
    if kind == 'tuple':
        return TupleLiteral(
            elements=[decode_rewrite_node(element) for element in spec.get('elements', [])],
            line=line,
        )
    if kind == 'set':
        return SetLiteral(
            elements=[decode_rewrite_node(element) for element in spec.get('elements', [])],
            line=line,
        )
    if kind == 'dict':
        return DictLiteral(
            pairs=[
                (decode_rewrite_node(pair.get('key')), decode_rewrite_node(pair.get('value')))
                for pair in spec.get('pairs', [])
            ],
            line=line,
        )
    raise TypeError(f"Unsupported rewrite spec kind: {kind}")
