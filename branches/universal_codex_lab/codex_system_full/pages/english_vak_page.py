from __future__ import annotations

import re

from ..models import CodexDiagnostic, CodexPageProbe, CodexResult
from ..page import CodexPage
from .vak_page import _overall_confidence

from runtime.src.code_transformer import VakCodeTransformer
from runtime.src.rupantar import VakyaRupantar


_ENGLISH_SHAPE_RE = re.compile(
    r"^\s*(def|class|from|import|if|elif|else|while|for|try|except|finally|with|async)\b",
    re.MULTILINE,
)


class EnglishVakCodexPage(CodexPage):
    name = "english_vak"
    description = "English/Python-style source to Vak page"
    priority = 20
    kind = "python"
    chapter = "bridges"
    chapter_title = "Bridge Pages"
    chapter_order = 20
    capabilities = ("bridge", "translate", "normalize")
    emits_vak = True
    extensions = ("py",)
    max_fixpoint_passes = 2

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._transformer = VakCodeTransformer(deep_meaning_mode=self.deep_meaning_mode)

    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        result = self._transformer.transform(source)
        if filename and filename.endswith(".py"):
            return CodexPageProbe(self.name, 100, ".py source path")
        if result.language == "english":
            return CodexPageProbe(self.name, 95, "recognized English/Python-style source")
        if _ENGLISH_SHAPE_RE.search(source) and not any("\u0900" <= ch <= "\u097f" for ch in source):
            return CodexPageProbe(self.name, 70, "ASCII source with Python-style structure")
        return CodexPageProbe(self.name, 0, "not an English/Vak bridge candidate")

    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        transformed = self._transformer.transform(source)
        diagnostics: list[CodexDiagnostic] = []

        if transformed.blocked_reason:
            diagnostics.append(
                CodexDiagnostic(
                    page=self.name,
                    level="error",
                    message=transformed.blocked_reason,
                    confidence="do_not_touch",
                    line=transformed.blocked_line,
                )
            )
            return CodexResult(
                page=self.name,
                original_source=source,
                source=source,
                transformed=False,
                confidence="do_not_touch",
                diagnostics=tuple(diagnostics),
                manifest=self.manifest(),
                metadata={
                    "source_kind": "english_vak",
                    "detected_constructs": list(transformed.features),
                    "language": transformed.language,
                    "translation_confidence": transformed.confidence,
                    "features": list(transformed.features),
                    "changed_lines": list(transformed.changed_lines),
                },
            )

        if transformed.transformed:
            diagnostics.append(
                CodexDiagnostic(
                    page=self.name,
                    level="info",
                    message="English source translated into Vak surface syntax",
                    confidence="safe_auto_fix",
                )
            )

        engine = VakyaRupantar(
            active_branches=list(self.active_branches) if self.active_branches else None,
            branch_registry=self.branch_registry,
        )
        normalized = engine.transform_source(transformed.source, source_path=filename)

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

        for item in normalized.suggestions:
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

        metadata = {
            "source_kind": "english_vak",
            "detected_constructs": list(transformed.features),
            "language": transformed.language,
            "translation_confidence": transformed.confidence,
            "translation_features": list(transformed.features),
            "translation_changed_lines": list(transformed.changed_lines),
            "syntax_valid": normalized.syntax_valid,
            "compiled": normalized.compiled,
        }
        return CodexResult(
            page=self.name,
            original_source=source,
            source=normalized.source,
            transformed=transformed.transformed or normalized.transformed or normalized.translation_used,
            confidence=_overall_confidence(
                diagnostics,
                transformed.transformed or normalized.transformed or normalized.translation_used,
            ),
            diagnostics=tuple(diagnostics),
            manifest=self.manifest(),
            metadata=metadata,
        )
