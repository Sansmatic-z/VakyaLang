from __future__ import annotations

from pathlib import Path
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from ..vak_runtime import VakCodexModuleRuntime
from .vak_page import _overall_confidence


def _coerce_string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value if item is not None)
    return (str(value),)


def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class VakModuleCodexPage(CodexPage):
    """Wrapper for a real .vak Codex page module."""
    kind = "vak_module"

    def __init__(
        self,
        module_path: str | Path,
        *,
        module_name: str | None = None,
        active_branches: list[str] | None = None,
        branch_registry: Any = None,
        deep_meaning_mode: bool = False,
    ):
        super().__init__(
            active_branches=active_branches,
            branch_registry=branch_registry,
            deep_meaning_mode=deep_meaning_mode,
        )
        path = Path(module_path).resolve()
        qualified_name = module_name or f"codex_pages.{path.stem}"
        self.module_path = path
        self.module_name = qualified_name
        self._runtime = VakCodexModuleRuntime(
            path,
            module_name=qualified_name,
            active_branches=list(self.active_branches),
            branch_registry=self.branch_registry,
        )
        attrs = self._runtime.attrs()
        self.name = str(attrs.get("CODEX_PAGE_NAME") or path.stem)
        self.description = str(
            attrs.get("CODEX_PAGE_DESCRIPTION")
            or f"Vak Codex page from {path.name}"
        )
        self.priority = _coerce_int(attrs.get("CODEX_PAGE_PRIORITY"), 60)
        self.kind = str(attrs.get("CODEX_PAGE_KIND") or "vak_module")
        self.chapter = str(attrs.get("CODEX_PAGE_CHAPTER") or "vak_native")
        self.chapter_title = str(attrs.get("CODEX_PAGE_CHAPTER_TITLE") or "Vak Native Pages")
        self.chapter_order = _coerce_int(attrs.get("CODEX_PAGE_CHAPTER_ORDER"), 50)
        self.capabilities = _coerce_string_tuple(attrs.get("CODEX_PAGE_CAPABILITIES"))
        self.emits_vak = bool(attrs.get("CODEX_PAGE_EMITS_VAK", True))
        self._extensions = tuple(
            item.lstrip(".").lower() for item in _coerce_string_tuple(attrs.get("CODEX_PAGE_EXTENSIONS"))
        )
        self.extensions = self._extensions
        self._hints = _coerce_string_tuple(attrs.get("CODEX_PAGE_HINTS"))
        self.experimental = bool(attrs.get("CODEX_PAGE_EXPERIMENTAL", False))
        self.max_fixpoint_passes = max(1, _coerce_int(attrs.get("CODEX_PAGE_MAX_FIXPOINT_PASSES"), 1))
        self._has_probe = attrs.get("codex_probe") is not None

    def manifest(self) -> CodexPageManifest:
        manifest = super().manifest()
        return CodexPageManifest(
            name=manifest.name,
            description=manifest.description,
            priority=manifest.priority,
            kind=manifest.kind,
            chapter=manifest.chapter,
            chapter_title=manifest.chapter_title,
            chapter_order=manifest.chapter_order,
            capabilities=manifest.capabilities,
            emits_vak=manifest.emits_vak,
            extensions=manifest.extensions,
            experimental=manifest.experimental,
            module_path=str(self.module_path),
            max_fixpoint_passes=int(self.max_fixpoint_passes),
        )

    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        score = 0
        reasons: list[str] = []
        if filename and self._extensions:
            suffix = Path(filename).suffix.lstrip(".").lower()
            if suffix in self._extensions:
                score = max(score, 70)
                reasons.append(f".{suffix} extension matches Vak page metadata")
        if self._hints and any(hint in source for hint in self._hints):
            score = max(score, 65)
            reasons.append("source matches Vak page hints")

        if self._has_probe:
            probe_value = self._runtime.invoke("codex_probe", source, filename)
            if isinstance(probe_value, dict):
                score = max(score, _coerce_int(probe_value.get("score"), 0))
                reason = str(probe_value.get("reason") or "").strip()
                if reason:
                    reasons.append(reason)
            else:
                score = max(score, _coerce_int(probe_value, 0))
                if probe_value is not None:
                    reasons.append("Vak page codex_probe")

        if not reasons:
            reasons.append(f"Vak module page {self.module_path.name}")
        return CodexPageProbe(self.name, score, "; ".join(reasons))

    def _diagnostics_from_rupantar_payload(self, payload: dict[str, Any]) -> list[CodexDiagnostic]:
        diagnostics: list[CodexDiagnostic] = []
        for edit in payload.get("edits", ()):
            diagnostics.append(
                CodexDiagnostic(
                    page=self.name,
                    level="info",
                    message=str(edit.get("reason", "")),
                    confidence=str(edit.get("confidence", "safe_auto_fix")),
                    line=_coerce_int(edit.get("line"), 0),
                    before=edit.get("before"),
                    after=edit.get("after"),
                )
            )
        for item in payload.get("rejected_fixes", ()):
            diagnostics.append(
                CodexDiagnostic(
                    page=self.name,
                    level="warning",
                    message=str(item.get("message", "")),
                    confidence=str(item.get("confidence", "suggest_only")),
                    line=_coerce_int(item.get("line"), 0),
                    before=item.get("before"),
                    after=item.get("after"),
                )
            )
        for item in payload.get("suggestions", ()):
            diagnostics.append(
                CodexDiagnostic(
                    page=self.name,
                    level="warning",
                    message=str(item.get("message", "")),
                    confidence=str(item.get("confidence", "suggest_only")),
                    line=_coerce_int(item.get("line"), 0),
                    before=item.get("before"),
                    after=item.get("after"),
                )
            )
        for warning in payload.get("warnings", ()):
            diagnostics.append(
                CodexDiagnostic(
                    page=self.name,
                    level="warning",
                    message=str(warning),
                    confidence="suggest_only",
                )
            )
        blocked = payload.get("translation_blocked_reason")
        if blocked:
            diagnostics.append(
                CodexDiagnostic(
                    page=self.name,
                    level="error",
                    message=str(blocked),
                    confidence="do_not_touch",
                )
            )
        return diagnostics

    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        raw = self._runtime.invoke("codex_transform", source, filename)

        if isinstance(raw, str):
            transformed = raw != source
            return CodexResult(
                page=self.name,
                original_source=source,
                source=raw,
                transformed=transformed,
                confidence="safe_auto_fix" if transformed else "suggest_only",
                manifest=self.manifest(),
                metadata={
                    "selected_page": self.name,
                    "page_kind": "vak_module",
                    "vak_page_path": str(self.module_path),
                },
            )

        if not isinstance(raw, dict):
            raise TypeError(
                f"Vak Codex page '{self.name}' returned unsupported result: {type(raw).__name__}"
            )

        result_source = str(raw.get("source", source))
        transformed = bool(raw.get("transformed")) or result_source != source or bool(raw.get("translation_used"))
        diagnostics = self._diagnostics_from_rupantar_payload(raw)
        metadata = dict(raw)
        metadata.setdefault("selected_page", self.name)
        metadata.setdefault("page_kind", "vak_module")
        metadata.setdefault("vak_page_path", str(self.module_path))
        return CodexResult(
            page=self.name,
            original_source=source,
            source=result_source,
            transformed=transformed,
            confidence=str(raw.get("confidence") or _overall_confidence(diagnostics, transformed)),
            diagnostics=tuple(diagnostics),
            manifest=self.manifest(),
            metadata=metadata,
        )
