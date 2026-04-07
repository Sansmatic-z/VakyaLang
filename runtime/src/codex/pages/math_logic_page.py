from __future__ import annotations

import re

from ..models import CodexDiagnostic, CodexPageProbe, CodexResult
from ..page import CodexPage
from .vak_page import _overall_confidence
from ...rupantar import VakyaRupantar


_MATH_LOGIC_SYMBOLS = ("¬", "∧", "∨", "⇒", "⇔", "∈", "⊤", "⊥")
_SIMPLE_IMPLICATION_RE = re.compile(r"(?P<left>[\w\)\]\"']+)\s*⇒\s*(?P<right>[\w\(\[\"']+)")
_SIMPLE_EQUIV_RE = re.compile(r"(?P<left>[\w\)\]\"']+)\s*⇔\s*(?P<right>[\w\(\[\"']+)")


class MathLogicCodexPage(CodexPage):
    name = "math_logic"
    description = "Math and symbolic logic notation page"
    priority = 15
    kind = "python"
    chapter = "math_logic"
    chapter_title = "Math and Logic"
    chapter_order = 30
    capabilities = ("math_logic", "symbolic_notation", "normalize")
    emits_vak = True
    extensions = ("logic", "math", "bool", "proof")
    max_fixpoint_passes = 2

    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        if filename:
            suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            if suffix in self.extensions:
                return CodexPageProbe(self.name, 105, f".{suffix} symbolic notation path")
        if any(symbol in source for symbol in _MATH_LOGIC_SYMBOLS):
            return CodexPageProbe(self.name, 90, "symbolic logic markers detected")
        return CodexPageProbe(self.name, 0, "not a math/logic candidate")

    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        diagnostics: list[CodexDiagnostic] = []
        rewritten = source

        simple_replacements = (
            ("¬", "न "),
            ("∧", " और "),
            ("∨", " अथवा "),
            ("∈", " अन्तर्गत "),
            ("⊤", "सत्य"),
            ("⊥", "असत्य"),
        )
        for before, after in simple_replacements:
            if before in rewritten:
                rewritten = rewritten.replace(before, after)
                diagnostics.append(
                    CodexDiagnostic(
                        page=self.name,
                        level="info",
                        message=f"normalized symbolic token {before}",
                        confidence="safe_auto_fix",
                        before=before,
                        after=after,
                    )
                )

        rewritten, count = _SIMPLE_IMPLICATION_RE.subn(
            lambda match: f"(न ({match.group('left')}) अथवा ({match.group('right')}))",
            rewritten,
        )
        if count:
            diagnostics.append(
                CodexDiagnostic(
                    page=self.name,
                    level="info",
                    message="rewrote symbolic implication",
                    confidence="safe_auto_fix",
                    before="⇒",
                    after="(न (...) अथवा (...))",
                )
            )

        rewritten, count = _SIMPLE_EQUIV_RE.subn(
            lambda match: f"(({match.group('left')}) == ({match.group('right')}))",
            rewritten,
        )
        if count:
            diagnostics.append(
                CodexDiagnostic(
                    page=self.name,
                    level="info",
                    message="rewrote symbolic equivalence",
                    confidence="safe_auto_fix",
                    before="⇔",
                    after="==",
                )
            )

        if "∀" in rewritten or "∃" in rewritten:
            diagnostics.append(
                CodexDiagnostic(
                    page=self.name,
                    level="warning",
                    message="quantifier notation still requires manual Vak expression shaping",
                    confidence="suggest_only",
                )
            )

        engine = VakyaRupantar(
            active_branches=list(self.active_branches) if self.active_branches else None,
            branch_registry=self.branch_registry,
        )
        normalized = engine.transform_source(rewritten, source_path=filename)
        for edit in normalized.edits:
            diagnostics.append(
                CodexDiagnostic(
                    page=self.name,
                    level="info",
                    message=edit.reason,
                    confidence=edit.confidence,
                    line=edit.line,
                    before=edit.before,
                    after=edit.after,
                )
            )
        for item in normalized.rejected_fixes:
            diagnostics.append(
                CodexDiagnostic(
                    page=self.name,
                    level="warning",
                    message=item.message,
                    confidence=item.confidence,
                    line=item.line,
                    before=item.before,
                    after=item.after,
                )
            )
        return CodexResult(
            page=self.name,
            original_source=source,
            source=normalized.source,
            transformed=rewritten != source or normalized.transformed or normalized.translation_used,
            confidence=_overall_confidence(
                diagnostics,
                rewritten != source or normalized.transformed or normalized.translation_used,
            ),
            diagnostics=tuple(diagnostics),
            manifest=self.manifest(),
            metadata={
                "source_kind": "math_logic",
                "detected_constructs": [symbol for symbol in _MATH_LOGIC_SYMBOLS if symbol in source],
            },
        )
