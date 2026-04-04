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

    def extend_rupantar_rules(
        self,
        rules: dict[str, Any],
        context: BranchHookContext,
    ) -> None:
        branch_aliases = rules.setdefault("branch_member_aliases", {})
        chitra_aliases = branch_aliases.setdefault(self.name, {})
        chitra_aliases.setdefault("चित्रकला", {}).update(
            {
                "कैनवास_निर्माण": "_chitra_canvas",
                "रेखा": "_chitra_line",
                "वृत्त": "_chitra_circle",
                "आयत": "_chitra_rect",
                "बहुभुज": "_chitra_polygon",
                "पाठ": "_chitra_text",
                "मध्य_पाठ": "_chitra_text_centered",
                "सहेजो": "_chitra_save",
                "लोड": "_chitra_load",
                "रंग": "_chitra_color",
                "रंगसूची": "_chitra_colors",
                "मण्डल": "_chitra_mandala",
                "मंडल": "_chitra_mandala",
                "ढाल": "_chitra_gradient",
                "घुमाओ": "_chitra_rotate",
            }
        )
        chitra_aliases.setdefault("chitrakala", {}).update(
            {
                "canvas": "_chitra_canvas",
                "line": "_chitra_line",
                "circle": "_chitra_circle",
                "rect": "_chitra_rect",
                "polygon": "_chitra_polygon",
                "text": "_chitra_text",
                "text_centered": "_chitra_text_centered",
                "save": "_chitra_save",
                "load": "_chitra_load",
                "color": "_chitra_color",
                "colors": "_chitra_colors",
                "mandala": "_chitra_mandala",
                "gradient": "_chitra_gradient",
                "rotate": "_chitra_rotate",
                "kaleidoscope": "_chitra_kaleidoscope",
            }
        )
        context.set_metadata("rupantar_module_aliases", len(chitra_aliases))
        context.emit("registered Chitrakala रुपान्तर aliases")


BRANCH_CLASS = ChitrakalaBranch


def create_branch() -> VakBranch:
    return ChitrakalaBranch()
