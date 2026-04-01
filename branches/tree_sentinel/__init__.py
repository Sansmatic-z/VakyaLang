from __future__ import annotations

from collections import Counter
from typing import Any

from runtime.src.ast_nodes import Node, Program
from runtime.src.branching import BranchHookContext, VakBranch


class TreeSentinelBranch(VakBranch):
    """
    Harmless validation branch used to prove the branch system is safe.

    It only observes the tree and records metadata. It does not mutate AST,
    bytecode, or runtime behavior.
    """

    name = "tree_sentinel"
    kind = "validation"
    priority = 10

    def on_program_parsed(self, program: Any, context: BranchHookContext) -> None:
        if not isinstance(program, Program):
            context.emit("expected Program root", level="warning")
            return

        counts = Counter()
        self._count_nodes(program, counts)
        context.set_metadata("root_type", type(program).__name__)
        context.set_metadata("top_level_statements", len(program.body))
        context.set_metadata("node_counts", dict(counts))
        context.emit("tree inspected successfully")

    def after_compile(self, bytecode: Any, context: BranchHookContext) -> None:
        code = getattr(bytecode, "code", [])
        constants = getattr(bytecode, "constants", [])
        context.set_metadata("bytecode_size", len(code))
        context.set_metadata("constant_count", len(constants))

    def _count_nodes(self, value: Any, counts: Counter[str]) -> None:
        if isinstance(value, Node):
            counts[type(value).__name__] += 1
            for item in getattr(value, "__dict__", {}).values():
                self._count_nodes(item, counts)
            return
        if isinstance(value, list):
            for item in value:
                self._count_nodes(item, counts)
            return
        if isinstance(value, tuple):
            for item in value:
                self._count_nodes(item, counts)
            return
        if isinstance(value, dict):
            for item in value.values():
                self._count_nodes(item, counts)


BRANCH_CLASS = TreeSentinelBranch


def create_branch() -> VakBranch:
    return TreeSentinelBranch()
