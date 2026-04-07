from __future__ import annotations

import re

from ..models import CodexDiagnostic, CodexPageProbe, CodexResult
from ..page import CodexPage
from .vak_page import _overall_confidence
from ...rupantar import VakyaRupantar


_TRANSLIT_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("karma", "कर्म"),
    ("chara", "चर"),
    ("sthira", "स्थिर"),
    ("yadi", "यदि"),
    ("anyatha", "अन्यथा"),
    ("pratyagaccha", "प्रत्यागच्छ"),
    ("mudraya", "मुद्रय"),
    ("satya", "सत्य"),
    ("asatya", "असत्य"),
    ("shunya", "शून्य"),
    ("yavat", "यावत्"),
    ("ayat", "आयात"),
    ("viram", "विराम"),
)
_TRANSLIT_RE = re.compile(
    r"\b(" + "|".join(re.escape(item[0]) for item in _TRANSLIT_KEYWORDS) + r")\b",
    re.IGNORECASE,
)


class SanskritNotationCodexPage(CodexPage):
    name = "sanskrit_notation"
    description = "Transliterated Sanskrit programming notation page"
    priority = 17
    kind = "python"
    chapter = "sanskrit_notation"
    chapter_title = "Sanskrit Notation"
    chapter_order = 40
    capabilities = ("sanskrit_notation", "transliteration", "normalize")
    emits_vak = True
    extensions = ("svk", "vakroman")
    max_fixpoint_passes = 2

    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        if filename:
            suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            if suffix in self.extensions:
                return CodexPageProbe(self.name, 100, f".{suffix} transliterated Vak path")
        if _TRANSLIT_RE.search(source):
            return CodexPageProbe(self.name, 78, "transliterated Sanskrit keywords detected")
        return CodexPageProbe(self.name, 0, "not a transliterated Sanskrit notation candidate")

    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        diagnostics: list[CodexDiagnostic] = []

        def replace_keyword(match: re.Match[str]) -> str:
            token = match.group(1)
            for before, after in _TRANSLIT_KEYWORDS:
                if token.lower() == before:
                    diagnostics.append(
                        CodexDiagnostic(
                            page=self.name,
                            level="info",
                            message=f"normalized transliterated keyword {before}",
                            confidence="safe_auto_fix",
                            before=before,
                            after=after,
                        )
                    )
                    return after
            return token

        rewritten = _TRANSLIT_RE.sub(replace_keyword, source)
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
                "source_kind": "sanskrit_notation",
                "detected_constructs": [
                    before
                    for before, _ in _TRANSLIT_KEYWORDS
                    if re.search(rf"\b{re.escape(before)}\b", source, re.IGNORECASE)
                ],
            },
        )
