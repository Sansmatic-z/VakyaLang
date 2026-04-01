from __future__ import annotations

from typing import Any

from runtime.src.branching import BranchHookContext, VakBranch

from .runtime import CHITRAKALA_BUILTIN_NAMES, build_chitrakala_builtins


class ChitrakalaBranch(VakBranch):
    """Runtime branch that contributes Chitrakala builtins to the Vak VM."""

    name = "chitrakala"
    kind = "runtime"
    priority = 40

    def extend_vm_builtins(
        self,
        builtins: dict[str, Any],
        context: BranchHookContext,
    ) -> None:
        support = build_chitrakala_builtins()
        builtins.update(support.builtins)
        context.set_metadata("builtin_count", len(CHITRAKALA_BUILTIN_NAMES))
        context.set_metadata("available", support.available)
        if not support.available:
            context.emit(
                "चित्रकला runtime unavailable; builtins remain registered but fail on use",
                level="warning",
            )


BRANCH_CLASS = ChitrakalaBranch


def create_branch() -> VakBranch:
    return ChitrakalaBranch()
