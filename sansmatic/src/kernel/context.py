from __future__ import annotations

from dataclasses import dataclass

from .errors import KernelScopeError
from .syntax import KernelTerm


@dataclass(frozen=True)
class ContextEntry:
    name: str
    value_type: KernelTerm


@dataclass(frozen=True)
class KernelContext:
    entries: tuple[ContextEntry, ...] = ()

    def extend(self, name: str, value_type: KernelTerm) -> "KernelContext":
        return KernelContext(entries=(*self.entries, ContextEntry(name, value_type)))

    def lookup(self, name: str) -> KernelTerm:
        for entry in reversed(self.entries):
            if entry.name == name:
                return entry.value_type
        raise KernelScopeError(f"Unbound kernel variable: {name}")

    def names(self) -> set[str]:
        return {entry.name for entry in self.entries}

