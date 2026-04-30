"""
AST Builder Engine — Language-agnostic Abstract Syntax Tree construction.

Provides:
- ASTNodeType enum for node categories
- ASTNode dataclass for tree nodes
- ASTBuilder for constructing ASTs from token streams or parsed input
"""
from __future__ import annotations

import ast as py_ast
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class ASTNodeType(str, Enum):
    """Categories of AST nodes."""
    PROGRAM = auto()
    MODULE = auto()
    IMPORT = auto()
    FUNCTION_DEF = auto()
    CLASS_DEF = auto()
    VARIABLE_DEF = auto()
    ASSIGNMENT = auto()
    IF_STMT = auto()
    WHILE_STMT = auto()
    FOR_STMT = auto()
    RETURN_STMT = auto()
    CALL_EXPR = auto()
    BINARY_EXPR = auto()
    UNARY_EXPR = auto()
    IDENTIFIER = auto()
    LITERAL = auto()
    BLOCK = auto()
    PARAMETER = auto()
    ARGUMENT = auto()
    LAMBDA = auto()
    TRY_EXCEPT = auto()
    WITH_STMT = auto()
    BREAK_STMT = auto()
    CONTINUE_STMT = auto()
    PASS_STMT = auto()
    COMMENT = auto()
    DECORATOR = auto()
    UNKNOWN = auto()


@dataclass
class ASTNode:
    """
    Generic AST node with type, value, children, and source position.

    Attributes
    ----------
    node_type : ASTNodeType
        The category of this node.
    value : Any
        The node's payload (identifier name, literal value, operator, etc.).
    children : list[ASTNode]
        Child nodes in the tree.
    line : int
        1-based source line.
    col : int
        1-based source column.
    metadata : dict
        Extra attributes (type hints, scope info, etc.).
    """
    node_type: ASTNodeType = ASTNodeType.UNKNOWN
    value: Any = None
    children: list[ASTNode] = field(default_factory=list)
    line: int = 0
    col: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_child(self, child: ASTNode) -> ASTNode:
        self.children.append(child)
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.node_type.value if isinstance(self.node_type, ASTNodeType) else str(self.node_type),
            "value": self.value,
            "children": [c.to_dict() for c in self.children],
            "line": self.line,
            "col": self.col,
            "metadata": dict(self.metadata),
        }

    def to_lisp(self, indent: int = 0) -> str:
        """Render AST as a Lisp-like S-expression for debugging."""
        prefix = "  " * indent
        val = f" {self.value!r}" if self.value is not None else ""
        if not self.children:
            return f"{prefix}({self.node_type.value}{val})"
        child_lines = [c.to_lisp(indent + 1) for c in self.children]
        return f"{prefix}({self.node_type.value}{val}\n" + "\n".join(child_lines) + f"\n{prefix})"


class ASTBuilder:
    """
    Builds ASTNode trees from various inputs.

    Supports:
    - Python source → AST via ast module
    - Token stream → AST via manual construction
    - Dict representation → ASTNode
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def from_python(self, source: str) -> ASTNode:
        """
        Parse Python source code into an ASTNode tree.

        Uses Python's built-in ast module and converts to our ASTNode format.
        """
        py_tree = py_ast.parse(source)
        return self._convert_py_node(py_tree)

    def from_tokens(self, tokens: list[dict[str, Any]]) -> ASTNode:
        """
        Build an AST from a list of token dicts.

        Each token should have at minimum: type, value, line, col.
        Uses a simple expression-statement parser.
        """
        root = ASTNode(node_type=ASTNodeType.PROGRAM)
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            stmt = self._token_to_stmt(tokens, i)
            if stmt is not None:
                root.add_child(stmt)
                i += stmt.metadata.get("token_span", 1)
            else:
                i += 1
        return root

    def from_dict(self, data: dict[str, Any]) -> ASTNode:
        """Reconstruct an ASTNode from a dict (inverse of to_dict)."""
        return self._dict_to_node(data)

    def from_json_file(self, path: str) -> ASTNode:
        import json
        from pathlib import Path
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return self.from_dict(data)

    # ------------------------------------------------------------------
    # Python AST conversion
    # ------------------------------------------------------------------
    _PY_NODE_TYPE_MAP: dict[str, ASTNodeType] = {
        "Module": ASTNodeType.MODULE,
        "FunctionDef": ASTNodeType.FUNCTION_DEF,
        "AsyncFunctionDef": ASTNodeType.FUNCTION_DEF,
        "ClassDef": ASTNodeType.CLASS_DEF,
        "Assign": ASTNodeType.ASSIGNMENT,
        "AugAssign": ASTNodeType.ASSIGNMENT,
        "AnnAssign": ASTNodeType.ASSIGNMENT,
        "If": ASTNodeType.IF_STMT,
        "While": ASTNodeType.WHILE_STMT,
        "For": ASTNodeType.FOR_STMT,
        "AsyncFor": ASTNodeType.FOR_STMT,
        "Return": ASTNodeType.RETURN_STMT,
        "Call": ASTNodeType.CALL_EXPR,
        "BinOp": ASTNodeType.BINARY_EXPR,
        "UnaryOp": ASTNodeType.UNARY_EXPR,
        "Compare": ASTNodeType.BINARY_EXPR,
        "BoolOp": ASTNodeType.BINARY_EXPR,
        "Name": ASTNodeType.IDENTIFIER,
        "Constant": ASTNodeType.LITERAL,
        "Num": ASTNodeType.LITERAL,
        "Str": ASTNodeType.LITERAL,
        "Expr": ASTNodeType.CALL_EXPR,
        "Block": ASTNodeType.BLOCK,
        "arg": ASTNodeType.PARAMETER,
        "Lambda": ASTNodeType.LAMBDA,
        "Try": ASTNodeType.TRY_EXCEPT,
        "With": ASTNodeType.WITH_STMT,
        "AsyncWith": ASTNodeType.WITH_STMT,
        "Break": ASTNodeType.BREAK_STMT,
        "Continue": ASTNodeType.CONTINUE_STMT,
        "Pass": ASTNodeType.PASS_STMT,
        "Import": ASTNodeType.IMPORT,
        "ImportFrom": ASTNodeType.IMPORT,
        "Comment": ASTNodeType.COMMENT,
        "Decorator": ASTNodeType.DECORATOR,
    }

    def _convert_py_node(self, node: py_ast.AST) -> ASTNode:
        """Recursively convert a Python ast node to our ASTNode."""
        class_name = node.__class__.__name__
        ntype = self._PY_NODE_TYPE_MAP.get(class_name, ASTNodeType.UNKNOWN)

        ast_node = ASTNode(
            node_type=ntype,
            line=getattr(node, "lineno", 0),
            col=getattr(node, "col_offset", 0),
            metadata={"py_class": class_name},
        )

        # Handle specific node types
        if isinstance(node, py_ast.Module):
            ast_node.node_type = ASTNodeType.PROGRAM
            for child in node.body:
                ast_node.add_child(self._convert_py_node(child))

        elif isinstance(node, py_ast.FunctionDef):
            ast_node.value = node.name
            for dec in node.decorator_list:
                ast_node.add_child(ASTNode(
                    node_type=ASTNodeType.DECORATOR,
                    children=[self._convert_py_node(dec)],
                ))
            for arg in node.args.args:
                ast_node.add_child(self._convert_py_node(arg))
            for child in node.body:
                ast_node.add_child(self._convert_py_node(child))

        elif isinstance(node, py_ast.ClassDef):
            ast_node.value = node.name
            for child in node.body:
                ast_node.add_child(self._convert_py_node(child))

        elif isinstance(node, py_ast.Assign):
            for target in node.targets:
                ast_node.add_child(self._convert_py_node(target))
            ast_node.add_child(self._convert_py_node(node.value))

        elif isinstance(node, py_ast.If):
            ast_node.add_child(self._convert_py_node(node.test))
            for child in node.body:
                ast_node.add_child(self._convert_py_node(child))
            for child in node.orelse:
                ast_node.add_child(self._convert_py_node(child))

        elif isinstance(node, py_ast.For):
            ast_node.add_child(self._convert_py_node(node.target))
            ast_node.add_child(self._convert_py_node(node.iter))
            for child in node.body:
                ast_node.add_child(self._convert_py_node(child))
            for child in node.orelse:
                ast_node.add_child(self._convert_py_node(child))

        elif isinstance(node, py_ast.While):
            ast_node.add_child(self._convert_py_node(node.test))
            for child in node.body:
                ast_node.add_child(self._convert_py_node(child))
            for child in node.orelse:
                ast_node.add_child(self._convert_py_node(child))

        elif isinstance(node, py_ast.Return):
            if node.value:
                ast_node.add_child(self._convert_py_node(node.value))

        elif isinstance(node, py_ast.Call):
            ast_node.add_child(self._convert_py_node(node.func))
            for arg in node.args:
                child = ASTNode(node_type=ASTNodeType.ARGUMENT)
                child.add_child(self._convert_py_node(arg))
                ast_node.add_child(child)
            for kw in node.keywords:
                if kw.arg:
                    child = ASTNode(node_type=ASTNodeType.ARGUMENT, metadata={"keyword": kw.arg})
                    child.add_child(self._convert_py_node(kw.value))
                    ast_node.add_child(child)

        elif isinstance(node, py_ast.BinOp):
            ast_node.add_child(self._convert_py_node(node.left))
            ast_node.value = node.op.__class__.__name__
            ast_node.add_child(self._convert_py_node(node.right))

        elif isinstance(node, py_ast.UnaryOp):
            ast_node.value = node.op.__class__.__name__
            ast_node.add_child(self._convert_py_node(node.operand))

        elif isinstance(node, py_ast.Compare):
            ast_node.add_child(self._convert_py_node(node.left))
            ast_node.value = node.ops[0].__class__.__name__
            ast_node.add_child(self._convert_py_node(node.comparators[0]))

        elif isinstance(node, py_ast.Name):
            ast_node.value = node.id

        elif isinstance(node, py_ast.Constant):
            ast_node.value = node.value
            ast_node.metadata["literal_type"] = type(node.value).__name__

        elif isinstance(node, py_ast.Num):
            ast_node.value = node.n

        elif isinstance(node, py_ast.Str):
            ast_node.value = node.s

        elif isinstance(node, py_ast.arg):
            ast_node.node_type = ASTNodeType.PARAMETER
            ast_node.value = node.arg

        elif isinstance(node, py_ast.Lambda):
            for arg in node.args.args:
                ast_node.add_child(self._convert_py_node(arg))
            ast_node.add_child(self._convert_py_node(node.body))

        elif isinstance(node, py_ast.Import):
            for alias in node.names:
                child = ASTNode(node_type=ASTNodeType.IMPORT, value=alias.name)
                if alias.asname:
                    child.metadata["alias"] = alias.asname
                ast_node.add_child(child)

        elif isinstance(node, py_ast.ImportFrom):
            for alias in node.names:
                child = ASTNode(
                    node_type=ASTNodeType.IMPORT,
                    value=f"{node.module}.{alias.name}" if node.module else alias.name,
                )
                if alias.asname:
                    child.metadata["alias"] = alias.asname
                ast_node.add_child(child)

        elif isinstance(node, py_ast.Try):
            for child in node.body:
                ast_node.add_child(self._convert_py_node(child))
            for handler in node.handlers:
                exc_node = ASTNode(node_type=ASTNodeType.UNKNOWN, value="except")
                if handler.type:
                    exc_node.add_child(self._convert_py_node(handler.type))
                for child in handler.body:
                    exc_node.add_child(self._convert_py_node(child))
                ast_node.add_child(exc_node)
            for child in node.orelse:
                ast_node.add_child(self._convert_py_node(child))
            for child in node.finalbody:
                final_node = ASTNode(node_type=ASTNodeType.UNKNOWN, value="finally")
                final_node.add_child(self._convert_py_node(child))
                ast_node.add_child(final_node)

        elif isinstance(node, (py_ast.Break, py_ast.Continue, py_ast.Pass)):
            pass  # already set via type map

        elif isinstance(node, py_ast.Expr):
            if node.value:
                child = self._convert_py_node(node.value)
                ast_node.node_type = child.node_type
                ast_node.value = child.value
                ast_node.children = child.children
                ast_node.metadata.update(child.metadata)

        else:
            # Fallback: try to handle as a generic container
            for child_name in py_ast.iter_child_nodes(node):
                ast_node.add_child(self._convert_py_node(child_name))

        return ast_node

    # ------------------------------------------------------------------
    # Dict conversion
    # ------------------------------------------------------------------
    def _dict_to_node(self, data: dict[str, Any]) -> ASTNode:
        raw_type = data["type"]
        # Handle both enum values and string names
        if isinstance(raw_type, ASTNodeType):
            node_type = raw_type
        elif isinstance(raw_type, str):
            try:
                node_type = ASTNodeType(raw_type)
            except ValueError:
                # Try matching by name (e.g., "MODULE" → ASTNodeType.MODULE)
                try:
                    node_type = ASTNodeType[raw_type.upper()]
                except KeyError:
                    node_type = ASTNodeType.UNKNOWN
        else:
            node_type = ASTNodeType.UNKNOWN

        node = ASTNode(
            node_type=node_type,
            value=data.get("value"),
            line=data.get("line", 0),
            col=data.get("col", 0),
            metadata=data.get("metadata", {}),
        )
        for child_data in data.get("children", []):
            node.add_child(self._dict_to_node(child_data))
        return node

    # ------------------------------------------------------------------
    # Token helpers
    # ------------------------------------------------------------------
    def _token_to_stmt(self, tokens: list[dict], idx: int) -> ASTNode | None:
        """Convert a token stream starting at idx into a statement node."""
        if idx >= len(tokens):
            return None
        tok = tokens[idx]
        ttype = tok.get("type", "").upper()
        tval = tok.get("value", "")

        if ttype in ("DEF", "KEYWORD") and tval == "def":
            return self._parse_func_def(tokens, idx)
        elif ttype in ("CLASS", "KEYWORD") and tval == "class":
            return self._parse_class_def(tokens, idx)
        elif ttype in ("IF", "KEYWORD") and tval == "if":
            return self._parse_if_stmt(tokens, idx)
        elif ttype in ("IDENTIFIER", "NAME"):
            return self._parse_assignment_or_expr(tokens, idx)
        elif ttype in ("NUMBER", "STRING", "LITERAL"):
            return ASTNode(
                node_type=ASTNodeType.LITERAL,
                value=tval,
                line=tok.get("line", 0),
                col=tok.get("col", 0),
                metadata={"token_span": 1},
            )
        return None

    def _parse_func_def(self, tokens: list[dict], idx: int) -> ASTNode:
        # Simplified: def NAME ( ... ) :
        node = ASTNode(node_type=ASTNodeType.FUNCTION_DEF, line=tokens[idx].get("line", 0))
        # Next token should be name
        if idx + 1 < len(tokens):
            node.value = tokens[idx + 1].get("value", "anonymous")
        return node

    def _parse_class_def(self, tokens: list[dict], idx: int) -> ASTNode:
        node = ASTNode(node_type=ASTNodeType.CLASS_DEF, line=tokens[idx].get("line", 0))
        if idx + 1 < len(tokens):
            node.value = tokens[idx + 1].get("value", "Anonymous")
        return node

    def _parse_if_stmt(self, tokens: list[dict], idx: int) -> ASTNode:
        return ASTNode(
            node_type=ASTNodeType.IF_STMT,
            line=tokens[idx].get("line", 0),
            value="if",
        )

    def _parse_assignment_or_expr(self, tokens: list[dict], idx: int) -> ASTNode:
        tok = tokens[idx]
        # Look ahead for = or ==
        if idx + 1 < len(tokens) and tokens[idx + 1].get("value") == "=":
            return ASTNode(
                node_type=ASTNodeType.ASSIGNMENT,
                value=tok.get("value"),
                line=tok.get("line", 0),
                metadata={"token_span": 1},
            )
        return ASTNode(
            node_type=ASTNodeType.CALL_EXPR,
            value=tok.get("value"),
            line=tok.get("line", 0),
            metadata={"token_span": 1},
        )
