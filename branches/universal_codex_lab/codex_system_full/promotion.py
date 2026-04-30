from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .models import CodexPageManifest

if TYPE_CHECKING:
    from .core import SanskritVakyaUniversalCodex


@dataclass(frozen=True)
class CodexPromotionGate:
    name: str
    passed: bool
    detail: str

    def payload(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class CodexPromotionReport:
    page: str
    manifest: CodexPageManifest
    corpus_root: str
    corpus_files: tuple[str, ...]
    compiled_cases: int
    syntax_valid_cases: int
    total_cases: int
    safe_auto_fix_cases: int
    suggest_only_cases: int
    do_not_touch_cases: int
    gates: tuple[CodexPromotionGate, ...]
    ready_for_main: bool

    def text(self) -> str:
        lines = [
            "कोडेक्स उन्नयन रिपोर्ट",
            f"पृष्ठ: {self.page}",
            f"अध्याय: {self.manifest.chapter}",
            f"प्रयोगात्मक: {'हाँ' if self.manifest.experimental else 'नहीं'}",
            f"कॉर्पस मूल: {self.corpus_root}",
            f"कॉर्पस फ़ाइलें: {self.total_cases}",
            f"संकलन सफल: {self.compiled_cases}/{self.total_cases}",
            f"वाक्यरचना सफल: {self.syntax_valid_cases}/{self.total_cases}",
            (
                "विश्वास-वर्ग: "
                f"safe_auto_fix={self.safe_auto_fix_cases}, "
                f"suggest_only={self.suggest_only_cases}, "
                f"do_not_touch={self.do_not_touch_cases}"
            ),
            f"मुख्य में उन्नयन हेतु तैयार: {'हाँ' if self.ready_for_main else 'नहीं'}",
            "द्वार:",
        ]
        for gate in self.gates:
            lines.append(
                f"  - {gate.name}: {'PASS' if gate.passed else 'FAIL'} ({gate.detail})"
            )
        if self.corpus_files:
            lines.append("कॉर्पस सूची:")
            for item in self.corpus_files:
                lines.append(f"  - {item}")
        return "\n".join(lines)

    def payload(self) -> dict[str, Any]:
        return {
            "page": self.page,
            "manifest": self.manifest.payload(),
            "corpus_root": self.corpus_root,
            "corpus_files": list(self.corpus_files),
            "compiled_cases": self.compiled_cases,
            "syntax_valid_cases": self.syntax_valid_cases,
            "total_cases": self.total_cases,
            "safe_auto_fix_cases": self.safe_auto_fix_cases,
            "suggest_only_cases": self.suggest_only_cases,
            "do_not_touch_cases": self.do_not_touch_cases,
            "gates": [gate.payload() for gate in self.gates],
            "ready_for_main": self.ready_for_main,
        }


def _default_corpus_root() -> Path:
    return Path(__file__).resolve().parents[3] / "stress" / "codex_corpus"


def _matching_corpus_files(
    manifest: CodexPageManifest,
    corpus_root: Path,
) -> list[Path]:
    if not corpus_root.exists():
        return []
    if manifest.extensions:
        matched: list[Path] = []
        for extension in manifest.extensions:
            matched.extend(sorted(corpus_root.glob(f"*.{extension}")))
        if matched:
            return matched
    return sorted(path for path in corpus_root.iterdir() if path.is_file())


def evaluate_promotion_candidate(
    codex: "SanskritVakyaUniversalCodex",
    page_name: str,
    *,
    corpus_root: str | Path | None = None,
) -> CodexPromotionReport:
    manifest = codex.page_manifest(page_name)
    corpus_path = Path(corpus_root) if corpus_root is not None else _default_corpus_root()
    corpus_files = _matching_corpus_files(manifest, corpus_path)

    syntax_valid_cases = 0
    compiled_cases = 0
    safe_auto_fix_cases = 0
    suggest_only_cases = 0
    do_not_touch_cases = 0

    for file_path in corpus_files:
        try:
            source = file_path.read_text(encoding="utf-8")
        except OSError:
            do_not_touch_cases += 1
            continue
        result = codex.transform_source(
            source,
            filename=str(file_path),
            page=page_name,
        )
        if result.validation is not None and result.validation.syntax_valid:
            syntax_valid_cases += 1
        if result.validation is not None and result.validation.compiled:
            compiled_cases += 1
        if result.confidence == "safe_auto_fix":
            safe_auto_fix_cases += 1
        elif result.confidence == "suggest_only":
            suggest_only_cases += 1
        else:
            do_not_touch_cases += 1

    total_cases = len(corpus_files)
    gates = (
        CodexPromotionGate(
            "corpus_coverage",
            total_cases > 0,
            "matching Codex corpus files found" if total_cases > 0 else "no matching corpus files",
        ),
        CodexPromotionGate(
            "compiled_validation",
            total_cases > 0 and compiled_cases == total_cases,
            f"{compiled_cases}/{total_cases} compiled successfully",
        ),
        CodexPromotionGate(
            "confidence_floor",
            total_cases > 0 and do_not_touch_cases == 0,
            f"{do_not_touch_cases} do_not_touch results",
        ),
        CodexPromotionGate(
            "deterministic_support",
            not manifest.experimental,
            "page is already non-experimental" if not manifest.experimental else "page is still marked experimental",
        ),
    )
    ready_for_main = all(gate.passed for gate in gates)

    return CodexPromotionReport(
        page=page_name,
        manifest=manifest,
        corpus_root=str(corpus_path),
        corpus_files=tuple(str(item) for item in corpus_files),
        compiled_cases=compiled_cases,
        syntax_valid_cases=syntax_valid_cases,
        total_cases=total_cases,
        safe_auto_fix_cases=safe_auto_fix_cases,
        suggest_only_cases=suggest_only_cases,
        do_not_touch_cases=do_not_touch_cases,
        gates=gates,
        ready_for_main=ready_for_main,
    )
