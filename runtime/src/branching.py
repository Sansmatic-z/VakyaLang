from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


class BranchError(Exception):
    """Base exception for Vak branch integration."""


class BranchActivationError(BranchError):
    """Raised when a requested branch cannot be loaded safely."""


@dataclass
class BranchDiagnostic:
    level: str
    message: str
    phase: str


@dataclass
class BranchState:
    metadata: dict[str, Any] = field(default_factory=dict)
    diagnostics: list[BranchDiagnostic] = field(default_factory=list)


@dataclass
class BranchHookContext:
    runtime: "BranchRuntime"
    branch_name: str
    phase: str
    filename: str | None = None
    compiler: Any = None
    interpreter: Any = None
    vm: Any = None

    def set_metadata(self, key: str, value: Any) -> None:
        self.runtime.set_metadata(self.branch_name, key, value)

    def emit(self, message: str, *, level: str = "info") -> None:
        self.runtime.emit_diagnostic(self.branch_name, message, phase=self.phase, level=level)


class VakBranch:
    """
    Safe first-stage branch contract for Vak.

    Branches are additive observers/validators for now. They may inspect parsed
    programs and emitted bytecode, but they should not mutate the trunk's core
    semantics in this stage.
    """

    name = ""
    kind = "validation"
    priority = 100

    def register(self, runtime: "BranchRuntime") -> None:
        """Called once when the branch is activated."""

    def on_program_parsed(self, program: Any, context: BranchHookContext) -> None:
        """Inspect the parsed program before compilation."""

    def before_compile(self, program: Any, context: BranchHookContext) -> None:
        """Inspect the program at compiler entry."""

    def after_typecheck(self, program: Any, context: BranchHookContext) -> None:
        """Inspect the program after the trunk type-checking pass."""

    def after_compile(self, bytecode: Any, context: BranchHookContext) -> None:
        """Inspect the emitted bytecode."""

    def extend_vm_builtins(
        self,
        builtins: dict[str, Any],
        context: BranchHookContext,
    ) -> None:
        """Additive runtime builtin registration hook."""

    def extend_rupantar_rules(
        self,
        rules: dict[str, Any],
        context: BranchHookContext,
    ) -> None:
        """Additive source-repair rule registration hook."""

    def extend_codex_pages(
        self,
        pages: list[Any],
        context: BranchHookContext,
    ) -> None:
        """Additive Codex page registration hook."""


class BranchRuntime:
    """Coordinates active branches across interpreter/compiler phases."""

    def __init__(self, branches: list[VakBranch]):
        self.branches = sorted(
            list(branches),
            key=lambda branch: (getattr(branch, "priority", 100), branch.name),
        )
        self._state: dict[str, BranchState] = {
            branch.name: BranchState() for branch in self.branches
        }
        for branch in self.branches:
            branch.register(self)

    def active_names(self) -> list[str]:
        return [branch.name for branch in self.branches]

    def emit_diagnostic(
        self,
        branch_name: str,
        message: str,
        *,
        phase: str,
        level: str = "info",
    ) -> None:
        self._state[branch_name].diagnostics.append(
            BranchDiagnostic(level=level, message=message, phase=phase)
        )

    def set_metadata(self, branch_name: str, key: str, value: Any) -> None:
        self._state[branch_name].metadata[key] = value

    def report(self) -> dict[str, dict[str, Any]]:
        payload: dict[str, dict[str, Any]] = {}
        for name, state in self._state.items():
            payload[name] = {
                "metadata": dict(state.metadata),
                "diagnostics": [
                    {
                        "level": item.level,
                        "message": item.message,
                        "phase": item.phase,
                    }
                    for item in state.diagnostics
                ],
            }
        return payload

    def _dispatch(
        self,
        phase: str,
        attr_name: str,
        payload: Any,
        *,
        filename: Optional[str] = None,
        compiler: Any = None,
        interpreter: Any = None,
        vm: Any = None,
    ) -> None:
        for branch in self.branches:
            handler = getattr(branch, attr_name, None)
            if handler is None:
                continue
            context = BranchHookContext(
                runtime=self,
                branch_name=branch.name,
                phase=phase,
                filename=filename,
                compiler=compiler,
                interpreter=interpreter,
                vm=vm,
            )
            handler(payload, context)

    def on_program_parsed(
        self,
        program: Any,
        *,
        filename: Optional[str] = None,
        interpreter: Any = None,
    ) -> None:
        self._dispatch(
            "parsed",
            "on_program_parsed",
            program,
            filename=filename,
            interpreter=interpreter,
        )

    def before_compile(
        self,
        program: Any,
        *,
        filename: Optional[str] = None,
        compiler: Any = None,
    ) -> None:
        self._dispatch(
            "before_compile",
            "before_compile",
            program,
            filename=filename,
            compiler=compiler,
        )

    def after_typecheck(
        self,
        program: Any,
        *,
        filename: Optional[str] = None,
        compiler: Any = None,
    ) -> None:
        self._dispatch(
            "after_typecheck",
            "after_typecheck",
            program,
            filename=filename,
            compiler=compiler,
        )

    def after_compile(
        self,
        bytecode: Any,
        *,
        filename: Optional[str] = None,
        compiler: Any = None,
    ) -> None:
        self._dispatch(
            "after_compile",
            "after_compile",
            bytecode,
            filename=filename,
            compiler=compiler,
        )

    def extend_vm_builtins(
        self,
        builtins: dict[str, Any],
        *,
        vm: Any = None,
    ) -> None:
        for branch in self.branches:
            handler = getattr(branch, "extend_vm_builtins", None)
            if handler is None:
                continue

            previous_keys = set(builtins)
            previous_values = {key: builtins[key] for key in previous_keys}
            context = BranchHookContext(
                runtime=self,
                branch_name=branch.name,
                phase="vm_builtins",
                vm=vm,
            )
            handler(builtins, context)

            current_keys = set(builtins)
            removed = sorted(previous_keys - current_keys)
            overridden = sorted(
                key
                for key in (previous_keys & current_keys)
                if builtins[key] is not previous_values[key]
            )

            if removed:
                raise BranchActivationError(
                    f"Branch '{branch.name}' removed protected builtins: {', '.join(removed)}"
                )
            if overridden:
                raise BranchActivationError(
                    f"Branch '{branch.name}' attempted to override protected builtins: {', '.join(overridden)}"
                )

    def extend_rupantar_rules(self, rules: dict[str, Any]) -> None:
        for branch in self.branches:
            handler = getattr(branch, "extend_rupantar_rules", None)
            if handler is None:
                continue
            context = BranchHookContext(
                runtime=self,
                branch_name=branch.name,
                phase="rupantar_rules",
            )
            handler(rules, context)

    def extend_codex_pages(self, pages: list[Any]) -> None:
        for branch in self.branches:
            handler = getattr(branch, "extend_codex_pages", None)
            if handler is None:
                continue
            context = BranchHookContext(
                runtime=self,
                branch_name=branch.name,
                phase="codex_pages",
            )
            handler(pages, context)
