from __future__ import annotations

from dataclasses import dataclass
import difflib
from typing import Any


@dataclass(frozen=True)
class RupantarEdit:
    line: int
    layer: str
    before: str
    after: str
    reason: str
    confidence: str = "safe_auto_fix"


@dataclass(frozen=True)
class RupantarSuggestion:
    line: int
    layer: str
    message: str
    confidence: str
    before: str | None = None
    after: str | None = None


@dataclass(frozen=True)
class ValidationEvent:
    stage: str
    syntax_valid: bool
    compiled: bool
    warnings_count: int
    unresolved_count: int
    error_kind: str | None = None
    error_line: int = 0
    error_message: str | None = None


@dataclass(frozen=True)
class _UnresolvedNameIssue:
    name: str
    line: int
    suggestion: str | None
    candidates: tuple[str, ...] = ()


@dataclass(frozen=True)
class _CallSignature:
    name: str
    required_args: int
    max_args: int | None
    keyword_names: tuple[str, ...] = ()
    accepts_varargs: bool = False
    accepts_kwargs: bool = False
    source: str = "builtin"


@dataclass(frozen=True)
class _TypedMemberRepair:
    line: int
    receiver: str
    before_attr: str
    after_attr: str
    receiver_kind: str


@dataclass(frozen=True)
class _ModuleMemberRepair:
    line: int
    module_alias: str
    module_name: str
    before_attr: str
    after_attr: str


def _build_unified_diff(
    original_source: str,
    source: str,
    *,
    fromfile: str = "before.vak",
    tofile: str = "after.vak",
    limit: int = 120,
) -> tuple[str, ...]:
    if original_source == source:
        return ()
    diff = list(
        difflib.unified_diff(
            original_source.splitlines(),
            source.splitlines(),
            fromfile=fromfile,
            tofile=tofile,
            lineterm="",
        )
    )
    return tuple(diff[:limit])


@dataclass(frozen=True)
class RupantarResult:
    original_source: str
    source: str
    transformed: bool
    edits: tuple[RupantarEdit, ...] = ()
    rejected_fixes: tuple[RupantarSuggestion, ...] = ()
    suggestions: tuple[RupantarSuggestion, ...] = ()
    warnings: tuple[str, ...] = ()
    active_branches: tuple[str, ...] = ()
    translation_used: bool = False
    translation_blocked_reason: str | None = None
    syntax_valid: bool = False
    compiled: bool = False
    validation_events: tuple[ValidationEvent, ...] = ()

    def diff_lines(self, *, limit: int = 120) -> tuple[str, ...]:
        return _build_unified_diff(
            self.original_source,
            self.source,
            fromfile="original.vak",
            tofile="rupantar.vak",
            limit=limit,
        )

    def diff_text(self, *, limit: int = 120) -> str:
        diff_lines = self.diff_lines(limit=limit)
        if not diff_lines:
            return "कोई अंतर नहीं"
        return "\n".join(diff_lines)

    def report_text(self) -> str:
        lines = [
            "वाक्य-रूपान्तर रिपोर्ट",
            f"  परिवर्तन: {'हाँ' if self.transformed else 'नहीं'}",
            f"  अनुवाद चरण: {'हाँ' if self.translation_used else 'नहीं'}",
            f"  सक्रिय शाखाएँ: {', '.join(self.active_branches) if self.active_branches else 'कोई नहीं'}",
            f"  वाक्यरचना मान्य: {'हाँ' if self.syntax_valid else 'नहीं'}",
            f"  संकलन मान्य: {'हाँ' if self.compiled else 'नहीं'}",
            f"  संशोधन संख्या: {len(self.edits)}",
            f"  अस्वीकृत संशोधन: {len(self.rejected_fixes)}",
            f"  सुझाव संख्या: {len(self.suggestions)}",
        ]
        if self.translation_blocked_reason:
            lines.append(f"  अनुवाद चेतावनी: {self.translation_blocked_reason}")
        if self.validation_events:
            lines.append("  सत्यापन चरण:")
            for event in self.validation_events:
                outcome = (
                    f"वाक्यरचना={'हाँ' if event.syntax_valid else 'नहीं'}, "
                    f"संकलन={'हाँ' if event.compiled else 'नहीं'}, "
                    f"चेतावनी={event.warnings_count}, "
                    f"अपरिभाषित={event.unresolved_count}"
                )
                if event.error_message:
                    error_detail = f" [{event.error_kind or 'त्रुटि'}"
                    if event.error_line:
                        error_detail += f" L{event.error_line}"
                    error_detail += f"] {event.error_message}"
                else:
                    error_detail = ""
                lines.append(f"    - {event.stage}: {outcome}{error_detail}")
        if self.edits:
            lines.append("  संशोधन विवरण:")
            for edit in self.edits:
                lines.append(
                    f"    - L{edit.line} [{edit.layer}/{edit.confidence}] {edit.reason}: "
                    f"{edit.before!r} -> {edit.after!r}"
                )
        if self.suggestions:
            lines.append("  सुझाव:")
            for suggestion in self.suggestions:
                detail = ""
                if suggestion.before is not None or suggestion.after is not None:
                    detail = f" ({suggestion.before!r} -> {suggestion.after!r})"
                lines.append(
                    f"    - L{suggestion.line} [{suggestion.layer}/{suggestion.confidence}] "
                    f"{suggestion.message}{detail}"
                )
        if self.rejected_fixes:
            lines.append("  अस्वीकृत संशोधन:")
            for suggestion in self.rejected_fixes:
                detail = ""
                if suggestion.before is not None or suggestion.after is not None:
                    detail = f" ({suggestion.before!r} -> {suggestion.after!r})"
                lines.append(
                    f"    - L{suggestion.line} [{suggestion.layer}/{suggestion.confidence}] "
                    f"{suggestion.message}{detail}"
                )
        if self.warnings:
            lines.append("  चेतावनियाँ:")
            for warning in self.warnings:
                lines.append(f"    - {warning}")
        diff_lines = self.diff_lines(limit=40)
        if diff_lines:
            lines.append("  अंतर:")
            lines.extend(f"    {line}" for line in diff_lines)
        return "\n".join(lines)

    def report_payload(self) -> dict[str, Any]:
        return {
            "transformed": self.transformed,
            "translation_used": self.translation_used,
            "translation_blocked_reason": self.translation_blocked_reason,
            "syntax_valid": self.syntax_valid,
            "compiled": self.compiled,
            "active_branches": list(self.active_branches),
            "original_source": self.original_source,
            "source": self.source,
            "diff": list(self.diff_lines()),
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
                for event in self.validation_events
            ],
            "edits": [
                {
                    "line": edit.line,
                    "layer": edit.layer,
                    "confidence": edit.confidence,
                    "before": edit.before,
                    "after": edit.after,
                    "reason": edit.reason,
                }
                for edit in self.edits
            ],
            "rejected_fixes": [
                {
                    "line": item.line,
                    "layer": item.layer,
                    "message": item.message,
                    "confidence": item.confidence,
                    "before": item.before,
                    "after": item.after,
                }
                for item in self.rejected_fixes
            ],
            "suggestions": [
                {
                    "line": item.line,
                    "layer": item.layer,
                    "message": item.message,
                    "confidence": item.confidence,
                    "before": item.before,
                    "after": item.after,
                }
                for item in self.suggestions
            ],
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class _ValidationReport:
    syntax_valid: bool
    compiled: bool
    warnings: tuple[str, ...]
    unresolved: tuple[_UnresolvedNameIssue, ...]
    suggestions: tuple[RupantarSuggestion, ...]
    program: Any = None
    error: Exception | None = None
    error_kind: str | None = None
    error_line: int = 0
    error_message: str | None = None
    event: ValidationEvent | None = None
