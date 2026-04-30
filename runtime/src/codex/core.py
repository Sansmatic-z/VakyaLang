from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from ..compiler import Compiler
from ..errors import CompileError, LexerError, ParseError
from ..lexer import Lexer
from ..parser import Parser
from .models import (
    CodexChapterManifest,
    CodexDiagnostic,
    CodexPageManifest,
    CodexPageProbe,
    CodexResult,
    CodexRuleEvent,
    CodexValidation,
)
from .promotion import CodexPromotionReport, evaluate_promotion_candidate
from .page import CodexPage
from .pages import (
    EnglishVakCodexPage,
    JavaScriptVakCodexPage,
    MathLogicCodexPage,
    PseudocodeVakCodexPage,
    PythonVakCodexPage,
    SanskritNotationCodexPage,
    VakCodexPage,
    VakLegacyCodexPage,
    VakModuleCodexPage,
)


_CONFIDENCE_RANK = {
    "do_not_touch": 0,
    "suggest_only": 1,
    "safe_auto_fix": 2,
}


def _discover_vak_pages(
    *,
    active_branches: list[str] | None = None,
    branch_registry: Any = None,
    deep_meaning_mode: bool = False,
) -> tuple[CodexPage, ...]:
    pages_root = Path(__file__).resolve().parents[2] / "codex_pages"
    if not pages_root.exists():
        return ()
    discovered: list[CodexPage] = []
    for path in sorted(pages_root.glob("*.vak")):
        discovered.append(
            VakModuleCodexPage(
                path,
                active_branches=active_branches,
                branch_registry=branch_registry,
                deep_meaning_mode=deep_meaning_mode,
            )
        )
    return tuple(discovered)


def _discover_branch_pages(
    *,
    active_branches: list[str] | None = None,
    branch_registry: Any = None,
    deep_meaning_mode: bool = False,
) -> tuple[CodexPage, ...]:
    if not active_branches:
        return ()
    registry = branch_registry
    if registry is None:
        from branches.registry import create_default_registry

        registry = create_default_registry()
    runtime = registry.create_runtime(list(active_branches), include_defaults=True)
    pages: list[CodexPage] = []
    runtime.extend_codex_pages(pages)
    return tuple(pages)


class SanskritVakyaUniversalCodex:
    """Book-style modular translation spine for Vak."""

    def __init__(
        self,
        pages: Iterable[CodexPage] | None = None,
        *,
        active_branches: list[str] | None = None,
        branch_registry: Any = None,
        deep_meaning_mode: bool = False,
    ):
        self.active_branches = tuple(active_branches or ())
        self.branch_registry = branch_registry
        self.deep_meaning_mode = deep_meaning_mode
        self._pages: dict[str, CodexPage] = {}
        self._validation_branch_runtime: Any = None

        if pages is None:
            pages = (
                VakLegacyCodexPage(
                    active_branches=list(self.active_branches),
                    branch_registry=self.branch_registry,
                    deep_meaning_mode=self.deep_meaning_mode,
                ),
                VakCodexPage(
                    active_branches=list(self.active_branches),
                    branch_registry=self.branch_registry,
                    deep_meaning_mode=self.deep_meaning_mode,
                ),
                MathLogicCodexPage(
                    active_branches=list(self.active_branches),
                    branch_registry=self.branch_registry,
                    deep_meaning_mode=self.deep_meaning_mode,
                ),
                SanskritNotationCodexPage(
                    active_branches=list(self.active_branches),
                    branch_registry=self.branch_registry,
                    deep_meaning_mode=self.deep_meaning_mode,
                ),
                EnglishVakCodexPage(
                    active_branches=list(self.active_branches),
                    branch_registry=self.branch_registry,
                    deep_meaning_mode=self.deep_meaning_mode,
                ),
                PythonVakCodexPage(
                    active_branches=list(self.active_branches),
                    branch_registry=self.branch_registry,
                    deep_meaning_mode=self.deep_meaning_mode,
                ),
                JavaScriptVakCodexPage(
                    active_branches=list(self.active_branches),
                    branch_registry=self.branch_registry,
                    deep_meaning_mode=self.deep_meaning_mode,
                ),
                PseudocodeVakCodexPage(
                    active_branches=list(self.active_branches),
                    branch_registry=self.branch_registry,
                    deep_meaning_mode=self.deep_meaning_mode,
                ),
            ) + _discover_vak_pages(
                active_branches=list(self.active_branches),
                branch_registry=self.branch_registry,
                deep_meaning_mode=self.deep_meaning_mode,
            ) + _discover_branch_pages(
                active_branches=list(self.active_branches),
                branch_registry=self.branch_registry,
                deep_meaning_mode=self.deep_meaning_mode,
            )

        for page in pages:
            self.register_page(page)

    def register_page(self, page: CodexPage) -> None:
        existing = self._pages.get(page.name)
        if existing is not None and existing is not page:
            if existing.manifest().payload() != page.manifest().payload():
                raise ValueError(f"Duplicate Codex page name: {page.name}")
            return
        self._pages[page.name] = page

    def list_pages(self) -> list[dict[str, Any]]:
        pages = sorted(
            self._pages.values(),
            key=lambda item: (getattr(item, "priority", 100), item.name),
        )
        return [page.manifest().payload() for page in pages]

    def list_chapters(self) -> list[dict[str, Any]]:
        chapters: dict[str, CodexChapterManifest] = {}
        grouped_pages: dict[str, list[str]] = {}
        for page in self._sorted_pages():
            manifest = page.manifest()
            grouped_pages.setdefault(manifest.chapter, []).append(manifest.name)
            existing = chapters.get(manifest.chapter)
            if existing is None:
                chapters[manifest.chapter] = CodexChapterManifest(
                    name=manifest.chapter,
                    title=manifest.chapter_title,
                    order=manifest.chapter_order,
                    description=f"{manifest.chapter_title} chapter",
                    experimental=manifest.experimental,
                    pages=(manifest.name,),
                )
                continue
            chapters[manifest.chapter] = CodexChapterManifest(
                name=existing.name,
                title=existing.title,
                order=min(existing.order, manifest.chapter_order),
                description=existing.description,
                experimental=existing.experimental and manifest.experimental,
                pages=tuple(grouped_pages[manifest.chapter]),
            )
        ordered = sorted(chapters.values(), key=lambda item: (item.order, item.name))
        payloads: list[dict[str, Any]] = []
        for item in ordered:
            payload = item.payload()
            payload["pages"] = grouped_pages.get(item.name, list(item.pages))
            payloads.append(payload)
        return payloads

    def _sorted_pages(self) -> list[CodexPage]:
        return sorted(
            self._pages.values(),
            key=lambda item: (getattr(item, "priority", 100), item.name),
        )

    def page_manifest(self, name: str) -> CodexPageManifest:
        if name not in self._pages:
            raise KeyError(f"Unknown codex page: {name}")
        return self._pages[name].manifest()

    def promotion_report(
        self,
        name: str,
        *,
        corpus_root: str | Path | None = None,
    ) -> CodexPromotionReport:
        return evaluate_promotion_candidate(
            self,
            name,
            corpus_root=corpus_root,
        )

    def _resolve_validation_branch_runtime(self) -> Any:
        if self._validation_branch_runtime is not None:
            return self._validation_branch_runtime
        if not self.active_branches:
            return None
        registry = self.branch_registry
        if registry is None:
            from branches.registry import create_default_registry

            registry = create_default_registry()
        self._validation_branch_runtime = registry.create_runtime(
            list(self.active_branches),
            include_defaults=True,
        )
        return self._validation_branch_runtime

    def _validate_vak_output(
        self,
        source: str,
        *,
        filename: str | None = None,
        stage: str = "final",
        pass_index: int = 1,
    ) -> CodexValidation:
        try:
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            program = parser.parse()
            compiler = Compiler(
                branch_runtime=self._resolve_validation_branch_runtime(),
                source_path=filename,
            )
            compiler.compile(program)
            return CodexValidation(
                syntax_valid=True,
                compiled=True,
                stage=stage,
                pass_index=pass_index,
            )
        except LexerError as exc:
            return CodexValidation(
                syntax_valid=False,
                compiled=False,
                stage=stage,
                pass_index=pass_index,
                error_kind="lexer",
                error_line=getattr(exc, "line", 0),
                error_message=str(exc),
            )
        except ParseError as exc:
            return CodexValidation(
                syntax_valid=False,
                compiled=False,
                stage=stage,
                pass_index=pass_index,
                error_kind="parse",
                error_line=getattr(exc, "line", 0),
                error_message=str(exc),
            )
        except CompileError as exc:
            return CodexValidation(
                syntax_valid=True,
                compiled=False,
                stage=stage,
                pass_index=pass_index,
                error_kind="compile",
                error_line=getattr(exc, "line", 0),
                error_message=str(exc),
            )
        except Exception as exc:
            return CodexValidation(
                syntax_valid=False,
                compiled=False,
                stage=stage,
                pass_index=pass_index,
                error_kind="internal",
                error_line=getattr(exc, "line", 0),
                error_message=str(exc),
            )

    def _validation_rank(self, validation: CodexValidation | None) -> int:
        if validation is None:
            return 1
        if validation.syntax_valid and validation.compiled:
            return 4
        if validation.syntax_valid:
            return 3
        if validation.error_kind == "lexer":
            return 1
        return 2

    def _result_rank(self, result: CodexResult) -> tuple[int, int, int]:
        return (
            self._validation_rank(result.validation),
            _CONFIDENCE_RANK.get(result.confidence, 0),
            1 if result.transformed else 0,
        )

    def _diagnostic_rule_events(
        self,
        diagnostics: tuple[CodexDiagnostic, ...],
    ) -> tuple[tuple[CodexRuleEvent, ...], tuple[CodexRuleEvent, ...]]:
        applied: list[CodexRuleEvent] = []
        rejected: list[CodexRuleEvent] = []
        for index, item in enumerate(diagnostics, start=1):
            if item.level == "info":
                applied.append(
                    CodexRuleEvent(
                        rule=f"{item.page}:{index}",
                        status="applied",
                        confidence=item.confidence,
                        message=item.message,
                        line=item.line,
                        before=item.before,
                        after=item.after,
                    )
                )
                continue
            status = "blocked" if item.level == "error" else "suggested"
            rejected.append(
                CodexRuleEvent(
                    rule=f"{item.page}:{index}",
                    status=status,
                    confidence=item.confidence,
                    message=item.message,
                    line=item.line,
                    before=item.before,
                    after=item.after,
                )
            )
        return tuple(applied), tuple(rejected)

    def _normalize_result_model(self, result: CodexResult) -> None:
        source_kind = result.source_kind
        if source_kind == "unknown":
            source_kind = str(result.metadata.get("source_kind") or result.page)
        result.source_kind = source_kind
        if not result.detected_constructs:
            result.detected_constructs = tuple(
                str(item) for item in result.metadata.get("detected_constructs", ())
            )
        if not result.applied_rules and not result.rejected_rules:
            applied, rejected = self._diagnostic_rule_events(result.diagnostics)
            result.applied_rules = applied
            result.rejected_rules = rejected

    def _fixed_point_rejection(
        self,
        candidate: CodexResult,
        *,
        pass_index: int,
    ) -> CodexRuleEvent:
        return CodexRuleEvent(
            rule="codex_fixpoint",
            status="rejected",
            confidence="suggest_only",
            message=f"Rejected pass {pass_index} because validation/confidence regressed",
            line=candidate.validation.error_line if candidate.validation is not None else 0,
            before=candidate.original_source if candidate.transformed else None,
            after=candidate.source if candidate.transformed else None,
        )

    def _finalize_result(
        self,
        result: CodexResult,
        *,
        selected: CodexPage,
        probes: tuple[CodexPageProbe, ...],
        filename: str | None = None,
        pass_index: int = 1,
        validation_history: tuple[CodexValidation, ...] = (),
    ) -> CodexResult:
        result.probes = probes
        result.manifest = selected.manifest()
        result.metadata.setdefault("selected_page", selected.name)
        result.metadata.setdefault("active_branches", list(self.active_branches))
        result.metadata.setdefault("page_manifest", result.manifest.payload())
        result.metadata.setdefault("pass_limit", getattr(selected, "max_fixpoint_passes", 1))
        if result.manifest.emits_vak:
            validation = self._validate_vak_output(
                result.source,
                filename=filename,
                stage="codex_pass",
                pass_index=pass_index,
            )
            result.validation = validation
            result.metadata.setdefault("codex_validation", validation.payload())
            if not (validation.syntax_valid and validation.compiled):
                diagnostics = list(result.diagnostics)
                diagnostics.append(
                    CodexDiagnostic(
                        page=selected.name,
                        level="error",
                        message="Codex output failed Vak validation",
                        confidence="do_not_touch",
                        line=validation.error_line,
                        after=validation.error_message,
                    )
                )
                result.diagnostics = tuple(diagnostics)
                result.confidence = "do_not_touch"
        self._normalize_result_model(result)
        result.validation_history = validation_history
        return result

    def select_page(
        self,
        source: str,
        *,
        filename: str | None = None,
        page: str = "auto",
    ) -> tuple[CodexPage, tuple[CodexPageProbe, ...]]:
        if page != "auto":
            if page not in self._pages:
                raise KeyError(f"Unknown codex page: {page}")
            selected = self._pages[page]
            probe = selected.probe(source, filename=filename)
            return selected, (probe,)

        probes = tuple(
            page_impl.probe(source, filename=filename)
            for page_impl in self._sorted_pages()
        )
        selected_probe = max(
            probes,
            key=lambda item: (item.score, -self._pages[item.page].priority, item.page),
        )
        return self._pages[selected_probe.page], probes

    def transform_source(
        self,
        source: str,
        *,
        filename: str | None = None,
        page: str = "auto",
    ) -> CodexResult:
        selected, probes = self.select_page(source, filename=filename, page=page)
        pass_limit = max(1, int(getattr(selected, "max_fixpoint_passes", 1)))
        current_source = source
        best_result: CodexResult | None = None
        validation_history: list[CodexValidation] = []

        for pass_index in range(1, pass_limit + 1):
            candidate = selected.transform(current_source, filename=filename)
            candidate = self._finalize_result(
                candidate,
                selected=selected,
                probes=probes,
                filename=filename,
                pass_index=pass_index,
                validation_history=(),
            )
            if candidate.validation is not None:
                validation_history.append(candidate.validation)
            candidate.validation_history = tuple(validation_history)
            candidate.metadata["fixpoint_passes"] = len(validation_history)

            if best_result is None or self._result_rank(candidate) >= self._result_rank(best_result):
                best_result = candidate
            else:
                rejected = list(best_result.rejected_rules)
                rejected.append(self._fixed_point_rejection(candidate, pass_index=pass_index))
                best_result.rejected_rules = tuple(rejected)
                best_result.validation_history = tuple(validation_history)
                best_result.metadata["fixpoint_passes"] = len(validation_history)
                break

            if candidate.source == current_source:
                break
            if pass_index >= pass_limit:
                break
            current_source = candidate.source

        assert best_result is not None
        best_result.validation_history = tuple(validation_history)
        best_result.metadata["fixpoint_passes"] = len(validation_history)
        return best_result

    def transform_file(
        self,
        input_path: str | Path,
        output_path: str | Path,
        *,
        page: str = "auto",
    ) -> CodexResult:
        input_path = Path(input_path).resolve()
        output_path = Path(output_path).resolve()
        source = input_path.read_text(encoding="utf-8")
        result = self.transform_source(source, filename=str(input_path), page=page)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result.source, encoding="utf-8")
        return result


def build_default_codex(
    *,
    active_branches: list[str] | None = None,
    branch_registry: Any = None,
    deep_meaning_mode: bool = False,
) -> SanskritVakyaUniversalCodex:
    return SanskritVakyaUniversalCodex(
        active_branches=active_branches,
        branch_registry=branch_registry,
        deep_meaning_mode=deep_meaning_mode,
    )
