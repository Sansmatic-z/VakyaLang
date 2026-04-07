from __future__ import annotations

from typing import Any

from runtime.src.branching import BranchHookContext, VakBranch


class UniversalCodexLabBranch(VakBranch):
    """Experimental Codex page pack for non-Vak source families."""

    name = "universal_codex_lab"
    kind = "experimental"
    priority = 80

    def extend_codex_pages(
        self,
        pages: list[Any],
        context: BranchHookContext,
    ) -> None:
        from .pages import CSubsetCodexPage, NaturalLanguageSuggestCodexPage, RustSubsetCodexPage

        active_names = context.runtime.active_names()
        pages.extend(
            [
                CSubsetCodexPage(active_branches=active_names),
                RustSubsetCodexPage(active_branches=active_names),
                NaturalLanguageSuggestCodexPage(active_branches=active_names),
            ]
        )
        context.set_metadata("codex_pages", ["c_subset", "rust_subset", "natural_language"])
        context.emit("experimental Codex pages enabled", level="warning")


BRANCH_CLASS = UniversalCodexLabBranch


def create_branch() -> VakBranch:
    return UniversalCodexLabBranch()
