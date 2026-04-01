from __future__ import annotations

from typing import Any

from runtime.src.branching import BranchHookContext, VakBranch


class RuntimeProbeBranch(VakBranch):
    """Harmless runtime validation branch for additive builtin registration."""

    name = "runtime_probe"
    kind = "validation"
    priority = 20

    def extend_vm_builtins(
        self,
        builtins: dict[str, Any],
        context: BranchHookContext,
    ) -> None:
        builtins["_branch_probe"] = lambda: "runtime-probe"
        context.set_metadata("builtin_name", "_branch_probe")
        context.emit("registered additive runtime probe builtin")


BRANCH_CLASS = RuntimeProbeBranch


def create_branch() -> VakBranch:
    return RuntimeProbeBranch()
