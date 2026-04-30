from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

from runtime.src.codex.models import (
    CodexDiagnostic,
    CodexPageManifest,
    CodexPageProbe,
    CodexResult,
    CodexRuleEvent,
    CodexValidation,
)
from runtime.src.codex.page import CodexPage

from .codex_system_full import pages as vendor_pages


_PREFIX = "codex_system_"
_VAK_PAGES_ROOT = Path(__file__).resolve().parent / "codex_system_vak_pages"


def _prefixed(name: str) -> str:
    return name if name.startswith(_PREFIX) else f"{_PREFIX}{name}"


def _prefixed_chapter(name: str) -> str:
    return f"{_PREFIX}{name}"


def _convert_diagnostic(
    item: Any,
    *,
    page_name: str,
) -> CodexDiagnostic:
    return CodexDiagnostic(
        page=page_name,
        level=str(getattr(item, "level", "warning")),
        message=str(getattr(item, "message", "")),
        confidence=str(getattr(item, "confidence", "suggest_only")),
        line=int(getattr(item, "line", 0) or 0),
        before=getattr(item, "before", None),
        after=getattr(item, "after", None),
    )


def _convert_rule_event(item: Any) -> CodexRuleEvent:
    return CodexRuleEvent(
        rule=str(getattr(item, "rule", "")),
        status=str(getattr(item, "status", "suggested")),
        confidence=str(getattr(item, "confidence", "suggest_only")),
        message=str(getattr(item, "message", "")),
        line=int(getattr(item, "line", 0) or 0),
        before=getattr(item, "before", None),
        after=getattr(item, "after", None),
    )


def _convert_validation(item: Any) -> CodexValidation | None:
    if item is None:
        return None
    return CodexValidation(
        syntax_valid=bool(getattr(item, "syntax_valid", False)),
        compiled=bool(getattr(item, "compiled", False)),
        stage=str(getattr(item, "stage", "final")),
        pass_index=int(getattr(item, "pass_index", 1) or 1),
        error_kind=getattr(item, "error_kind", None),
        error_line=int(getattr(item, "error_line", 0) or 0),
        error_message=getattr(item, "error_message", None),
    )


class IntegratedCodexSystemPage(CodexPage):
    """Adapter that exposes the full codex-system pack through VakLang Codex."""

    def __init__(self, vendor_page: Any, **kwargs: Any):
        super().__init__(**kwargs)
        self._vendor_page = vendor_page
        self._vendor_manifest = vendor_page.manifest()
        self._vendor_name = str(self._vendor_manifest.name)
        self.name = _prefixed(self._vendor_name)
        self.description = f"Integrated Codex-System page: {self._vendor_manifest.description}"
        self.priority = int(self._vendor_manifest.priority) + 200
        self.kind = f"codex_system_{self._vendor_manifest.kind}"
        self.chapter = _prefixed_chapter(str(self._vendor_manifest.chapter))
        self.chapter_title = f"Codex-System {self._vendor_manifest.chapter_title}"
        self.chapter_order = int(self._vendor_manifest.chapter_order) + 200
        capabilities = list(self._vendor_manifest.capabilities)
        if "codex_system" not in capabilities:
            capabilities.append("codex_system")
        self.capabilities = tuple(capabilities)
        self.emits_vak = bool(self._vendor_manifest.emits_vak)
        self.extensions = tuple(self._vendor_manifest.extensions)
        self.experimental = True
        self.max_fixpoint_passes = max(1, int(self._vendor_manifest.max_fixpoint_passes))
        self._module_path = self._vendor_manifest.module_path

    def manifest(self) -> CodexPageManifest:
        return CodexPageManifest(
            name=self.name,
            description=self.description,
            priority=self.priority,
            kind=self.kind,
            chapter=self.chapter,
            chapter_title=self.chapter_title,
            chapter_order=self.chapter_order,
            capabilities=tuple(self.capabilities),
            emits_vak=bool(self.emits_vak),
            extensions=tuple(self.extensions),
            experimental=bool(self.experimental),
            module_path=self._module_path,
            max_fixpoint_passes=int(self.max_fixpoint_passes),
        )

    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        probe = self._vendor_page.probe(source, filename=filename)
        return CodexPageProbe(
            self.name,
            int(getattr(probe, "score", 0) or 0),
            f"{getattr(probe, 'reason', 'vendor probe')} [vendor={self._vendor_name}]",
        )

    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        raw = self._vendor_page.transform(source, filename=filename)
        diagnostics = tuple(
            _convert_diagnostic(item, page_name=self.name)
            for item in getattr(raw, "diagnostics", ())
        )
        applied_rules = tuple(
            _convert_rule_event(item)
            for item in getattr(raw, "applied_rules", ())
        )
        rejected_rules = tuple(
            _convert_rule_event(item)
            for item in getattr(raw, "rejected_rules", ())
        )
        validation_history = tuple(
            item
            for item in (
                _convert_validation(entry)
                for entry in getattr(raw, "validation_history", ())
            )
            if item is not None
        )
        metadata = dict(getattr(raw, "metadata", {}) or {})
        metadata.setdefault("source_kind", getattr(raw, "source_kind", "unknown"))
        metadata["vendor_page"] = self._vendor_name
        metadata["vendor_manifest"] = self._vendor_manifest.payload()
        metadata["integration_pack"] = "codex_system_full"

        return CodexResult(
            page=self.name,
            original_source=str(getattr(raw, "original_source", source)),
            source=str(getattr(raw, "source", source)),
            transformed=bool(getattr(raw, "transformed", False)),
            confidence=str(getattr(raw, "confidence", "suggest_only")),
            diagnostics=diagnostics,
            manifest=self.manifest(),
            validation=_convert_validation(getattr(raw, "validation", None)),
            source_kind=str(getattr(raw, "source_kind", metadata.get("source_kind", "unknown"))),
            detected_constructs=tuple(
                str(item) for item in getattr(raw, "detected_constructs", ())
            ),
            applied_rules=applied_rules,
            rejected_rules=rejected_rules,
            validation_history=validation_history,
            metadata=metadata,
        )


def _instantiate_vendor_page_classes(
    *,
    active_branches: list[str] | None = None,
    branch_registry: Any = None,
    deep_meaning_mode: bool = False,
) -> list[Any]:
    vendor_instances: list[Any] = []
    page_module_class = getattr(vendor_pages, "VakModuleCodexPage", None)

    for class_name in getattr(vendor_pages, "__all__", ()):
        page_cls = getattr(vendor_pages, class_name, None)
        if not inspect.isclass(page_cls):
            continue
        if page_cls is page_module_class:
            if not _VAK_PAGES_ROOT.exists():
                continue
            for path in sorted(_VAK_PAGES_ROOT.glob("*.vak")):
                vendor_instances.append(
                    page_cls(
                        path,
                        module_name=f"branches.universal_codex_lab.codex_system_vak_pages.{path.stem}",
                        active_branches=active_branches,
                        branch_registry=branch_registry,
                        deep_meaning_mode=deep_meaning_mode,
                    )
                )
            continue
        try:
            vendor_instances.append(
                page_cls(
                    active_branches=active_branches,
                    branch_registry=branch_registry,
                    deep_meaning_mode=deep_meaning_mode,
                )
            )
        except TypeError:
            vendor_instances.append(page_cls())
    return vendor_instances


def build_integrated_codex_system_pages(
    *,
    active_branches: list[str] | None = None,
    branch_registry: Any = None,
    deep_meaning_mode: bool = False,
) -> list[CodexPage]:
    pages: list[CodexPage] = []
    for vendor_page in _instantiate_vendor_page_classes(
        active_branches=active_branches,
        branch_registry=branch_registry,
        deep_meaning_mode=deep_meaning_mode,
    ):
        pages.append(
            IntegratedCodexSystemPage(
                vendor_page,
                active_branches=active_branches,
                branch_registry=branch_registry,
                deep_meaning_mode=deep_meaning_mode,
            )
        )
    return pages
