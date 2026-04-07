from __future__ import annotations

from ..models import CodexDiagnostic, CodexPageProbe, CodexResult
from ..page import CodexPage
from ...rupantar import VakyaRupantar


def _has_devanagari(source: str) -> bool:
    return any("\u0900" <= ch <= "\u097f" for ch in source)


def _overall_confidence(diagnostics: list[CodexDiagnostic], transformed: bool) -> str:
    if any(item.confidence == "do_not_touch" for item in diagnostics):
        return "do_not_touch"
    if any(item.confidence == "suggest_only" for item in diagnostics) and not transformed:
        return "suggest_only"
    return "safe_auto_fix"


class VakCodexPage(CodexPage):
    name = "vak"
    description = "Live Vak compatibility and normalization page"
    priority = 10
    kind = "python"
    chapter = "vak_core"
    chapter_title = "Vak Core"
    chapter_order = 10
    capabilities = ("vak", "normalize", "repair")
    emits_vak = True
    extensions = ("vak",)
    max_fixpoint_passes = 2

    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        if filename and filename.endswith(".vak"):
            return CodexPageProbe(self.name, 100, ".vak source path")
        if _has_devanagari(source):
            return CodexPageProbe(self.name, 95, "contains Devanagari Vak markers")
        if any(marker in source for marker in ("कर्म ", "चर ", "स्थिर ", "आयात ", "यदि ")):
            return CodexPageProbe(self.name, 80, "contains likely Vak syntax")
        return CodexPageProbe(self.name, 10, "fallback Vak page")

    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        engine = VakyaRupantar(
            active_branches=list(self.active_branches) if self.active_branches else None,
            branch_registry=self.branch_registry,
        )
        result = engine.transform_source(source, source_path=filename)
        diagnostics: list[CodexDiagnostic] = []

        for edit in result.edits:
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

        for item in result.rejected_fixes:
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

        for item in result.suggestions:
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

        if result.translation_blocked_reason:
            diagnostics.append(
                CodexDiagnostic(
                    page=self.name,
                    level="error",
                    message=result.translation_blocked_reason,
                    confidence="do_not_touch",
                )
            )

        metadata = {
            "source_kind": "vak",
            "detected_constructs": [
                marker.strip()
                for marker in ("कर्म ", "चर ", "स्थिर ", "आयात ", "यदि ", "यावत् ", "जबतक ")
                if marker in source
            ],
            "syntax_valid": result.syntax_valid,
            "compiled": result.compiled,
            "active_branches": list(result.active_branches),
            "translation_used": result.translation_used,
            "validation_events": [
                {
                    "stage": event.stage,
                    "syntax_valid": event.syntax_valid,
                    "compiled": event.compiled,
                    "warnings_count": event.warnings_count,
                    "unresolved_count": event.unresolved_count,
                    "error_kind": event.error_kind,
                    "error_line": event.error_line,
                    "error_message": event.error_message,
                }
                for event in result.validation_events
            ],
        }
        return CodexResult(
            page=self.name,
            original_source=source,
            source=result.source,
            transformed=result.transformed or result.translation_used,
            confidence=_overall_confidence(diagnostics, result.transformed or result.translation_used),
            diagnostics=tuple(diagnostics),
            manifest=self.manifest(),
            metadata=metadata,
        )
