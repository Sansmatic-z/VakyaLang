from __future__ import annotations

from typing import Any

from .models import CodexPageManifest, CodexPageProbe, CodexResult


class CodexPage:
    name = ""
    description = ""
    priority = 100
    kind = "python"
    chapter = "misc"
    chapter_title = "Miscellaneous"
    chapter_order = 100
    capabilities: tuple[str, ...] = ()
    emits_vak = True
    extensions: tuple[str, ...] = ()
    experimental = False
    max_fixpoint_passes = 1

    def __init__(
        self,
        *,
        active_branches: list[str] | None = None,
        branch_registry: Any = None,
        deep_meaning_mode: bool = False,
    ):
        self.active_branches = tuple(active_branches or ())
        self.branch_registry = branch_registry
        self.deep_meaning_mode = deep_meaning_mode

    def manifest(self) -> CodexPageManifest:
        return CodexPageManifest(
            name=self.name,
            description=self.description,
            priority=self.priority,
            kind=self.kind,
            chapter=str(self.chapter),
            chapter_title=str(self.chapter_title),
            chapter_order=int(self.chapter_order),
            capabilities=tuple(self.capabilities),
            emits_vak=bool(self.emits_vak),
            extensions=tuple(self.extensions),
            experimental=bool(self.experimental),
            max_fixpoint_passes=int(self.max_fixpoint_passes),
        )

    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        return CodexPageProbe(self.name, 0, "unsupported")

    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        raise NotImplementedError
