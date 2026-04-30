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
        from .codex_system_pages import build_integrated_codex_system_pages
        from .translator_pages import (
            JavaScriptToVakExperimentalCodexPage,
            PseudocodeToVakExperimentalCodexPage,
            PythonToVakExperimentalCodexPage,
        )

        active_names = context.runtime.active_names()
        pages.extend(
            [
                CSubsetCodexPage(active_branches=active_names),
                RustSubsetCodexPage(active_branches=active_names),
                NaturalLanguageSuggestCodexPage(active_branches=active_names),
                PythonToVakExperimentalCodexPage(active_branches=active_names),
                JavaScriptToVakExperimentalCodexPage(active_branches=active_names),
                PseudocodeToVakExperimentalCodexPage(active_branches=active_names),
            ]
        )
        integrated_pack = build_integrated_codex_system_pages(
            active_branches=active_names,
            branch_registry=None,
        )
        pages.extend(integrated_pack)
        integrated_names = [page.name for page in integrated_pack]
        context.set_metadata(
            "codex_pages",
            [
                "c_subset",
                "rust_subset",
                "natural_language",
                "python_to_vak_experimental",
                "javascript_to_vak_experimental",
                "pseudocode_to_vak_experimental",
            ]
            + integrated_names,
        )
        context.set_metadata("codex_system_pack_pages", integrated_names)
        context.emit("experimental Codex pages enabled", level="warning")


BRANCH_CLASS = UniversalCodexLabBranch


def create_branch() -> VakBranch:
    return UniversalCodexLabBranch()
