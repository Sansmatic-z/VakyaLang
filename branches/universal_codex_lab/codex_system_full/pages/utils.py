"""
Shared utilities for Codex page implementations.
"""
from __future__ import annotations

from typing import Any

from ..models import CodexDiagnostic, CodexPageProbe, CodexResult
from ..vak_surface import normalize_vak_surface, validate_vak_surface


def _make_result(
    page: CodexPageProbe | str,
    original_source: str,
    source: str,
    transformed: bool,
    confidence: str,
    diagnostics: tuple[CodexDiagnostic, ...] = (),
    manifest: Any = None,
    metadata: dict[str, Any] | None = None,
) -> CodexResult:
    """Helper to construct a CodexResult."""
    return CodexResult(
        page=page if isinstance(page, str) else page.page,
        original_source=original_source,
        source=source,
        transformed=transformed,
        confidence=confidence,
        diagnostics=diagnostics,
        manifest=manifest,
        metadata=metadata or {},
    )


def _overall_confidence(diagnostics: list[CodexDiagnostic], transformed: bool) -> str:
    """Determine overall confidence from diagnostics."""
    if any(item.confidence == "do_not_touch" for item in diagnostics):
        return "do_not_touch"
    if any(item.confidence == "suggest_only" for item in diagnostics) and not transformed:
        return "suggest_only"
    return "safe_auto_fix" if transformed else "suggest_only"


def _score_for_probe(page: str, score: int, reason: str) -> CodexPageProbe:
    """Create a CodexPageProbe with a non-empty page name."""
    if not page:
        page = "unknown"
    return CodexPageProbe(page=page, score=score, reason=reason)


def _validate_vak_output(
    source: str,
    *,
    page_name: str = "",
) -> tuple[bool, str | None]:
    """
    Attempt to validate that source is valid Vak code.

    Returns (is_valid, error_message).
    Uses the VakyaLang compiler if available, falls back to heuristic.
    """
    normalized = normalize_vak_surface(source)
    is_valid, error = validate_vak_surface(normalized)
    if is_valid:
        return True, None
    return _heuristic_vak_check(normalized) if error is None else (False, error)


def _heuristic_vak_check(source: str) -> tuple[bool, str | None]:
    """Basic heuristic to check if source looks like valid Vak code."""
    vak_keywords = [
        "कर्म", "यदि", "अन्यथा", "यावत्", "प्रत्येक", "अन्तर्गत", "प्रत्यागच्छ",
        "आयात", "से", "वर्ग", "स्थिर", "चर", "नया",
        "संग्रह", "समुच्चय", "मानचित्र", "सत्य", "असत्य", "अपरिभाषित",
    ]
    has_vak = any(kw in source for kw in vak_keywords)
    # If it has no devanagari and no vak keywords, probably not Vak
    has_devanagari = any("\u0900" <= ch <= "\u097f" for ch in source)
    if not has_vak and not has_devanagari:
        return False, "No Vak syntax detected"
    return True, None
