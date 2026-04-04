from __future__ import annotations

from typing import Any

from runtime.src.branching import BranchHookContext, VakBranch


class AdaptiveRupantarBranch(VakBranch):
    """Experimental branch that enables compile-validated adaptive रुपान्तर repairs."""

    name = "adaptive_rupantar"
    kind = "experimental"
    priority = 70

    def extend_rupantar_rules(
        self,
        rules: dict[str, Any],
        context: BranchHookContext,
    ) -> None:
        rules["auto_fix_unresolved_names"] = True
        rules["fuzzy_builtin_cutoff"] = 0.83
        rules["fuzzy_member_cutoff"] = 0.82
        rules["module_match_cutoff"] = 0.66
        rules["candidate_search_width"] = max(int(rules.get("candidate_search_width", 1)), 3)
        rules["unresolved_suggestion_limit"] = max(int(rules.get("unresolved_suggestion_limit", 3)), 4)
        rules["max_fixpoint_passes"] = max(int(rules.get("max_fixpoint_passes", 3)), 5)
        rules["promote_null_guard_defaults"] = True
        rules["infer_missing_optional_params"] = True

        builtin_aliases = rules.setdefault("builtin_aliases", {})
        builtin_aliases.update(
            {
                "isinstance": "उदाहरण_है",
                "hasattr": "गुण_है",
                "getattr": "गुण_प्राप्त",
                "setattr": "गुण_नियत",
                "enumerate": "गणना_सह",
                "zip": "युग्मीकरण",
            }
        )

        member_aliases = rules.setdefault("member_aliases", {})
        member_aliases.update(
            {
                "appendd": "जोड़ो",
                "apend": "जोड़ो",
                "spllit": "विभाजन",
                "strp": "छाँटो",
            }
        )

        context.set_metadata("adaptive_mode", "enabled")
        context.set_metadata("max_fixpoint_passes", rules["max_fixpoint_passes"])
        context.emit("adaptive रुपान्तर heuristics enabled", level="warning")


BRANCH_CLASS = AdaptiveRupantarBranch


def create_branch() -> VakBranch:
    return AdaptiveRupantarBranch()
