from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CodexChapterManifest:
    name: str
    title: str
    order: int = 100
    description: str = ""
    experimental: bool = False
    pages: tuple[str, ...] = ()

    def payload(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "title": self.title,
            "order": self.order,
            "description": self.description,
            "experimental": self.experimental,
            "pages": list(self.pages),
        }


@dataclass(frozen=True)
class CodexPageManifest:
    name: str
    description: str
    priority: int = 100
    kind: str = "python"
    chapter: str = "misc"
    chapter_title: str = "Miscellaneous"
    chapter_order: int = 100
    capabilities: tuple[str, ...] = ()
    emits_vak: bool = True
    extensions: tuple[str, ...] = ()
    experimental: bool = False
    module_path: str | None = None
    max_fixpoint_passes: int = 1

    def payload(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "kind": self.kind,
            "chapter": self.chapter,
            "chapter_title": self.chapter_title,
            "chapter_order": self.chapter_order,
            "capabilities": list(self.capabilities),
            "emits_vak": self.emits_vak,
            "extensions": list(self.extensions),
            "experimental": self.experimental,
            "module_path": self.module_path,
            "max_fixpoint_passes": self.max_fixpoint_passes,
        }


@dataclass(frozen=True)
class CodexPageProbe:
    page: str
    score: int
    reason: str


@dataclass(frozen=True)
class CodexDiagnostic:
    page: str
    level: str
    message: str
    confidence: str = "suggest_only"
    line: int = 0
    before: str | None = None
    after: str | None = None


@dataclass(frozen=True)
class CodexRuleEvent:
    rule: str
    status: str
    confidence: str
    message: str
    line: int = 0
    before: str | None = None
    after: str | None = None

    def payload(self) -> dict[str, Any]:
        return {
            "rule": self.rule,
            "status": self.status,
            "confidence": self.confidence,
            "message": self.message,
            "line": self.line,
            "before": self.before,
            "after": self.after,
        }


@dataclass(frozen=True)
class CodexValidation:
    syntax_valid: bool
    compiled: bool
    stage: str = "final"
    pass_index: int = 1
    error_kind: str | None = None
    error_line: int = 0
    error_message: str | None = None

    def payload(self) -> dict[str, Any]:
        return {
            "syntax_valid": self.syntax_valid,
            "compiled": self.compiled,
            "stage": self.stage,
            "pass_index": self.pass_index,
            "error_kind": self.error_kind,
            "error_line": self.error_line,
            "error_message": self.error_message,
        }


@dataclass
class CodexResult:
    page: str
    original_source: str
    source: str
    transformed: bool
    confidence: str
    probes: tuple[CodexPageProbe, ...] = ()
    diagnostics: tuple[CodexDiagnostic, ...] = ()
    manifest: CodexPageManifest | None = None
    validation: CodexValidation | None = None
    source_kind: str = "unknown"
    detected_constructs: tuple[str, ...] = ()
    applied_rules: tuple[CodexRuleEvent, ...] = ()
    rejected_rules: tuple[CodexRuleEvent, ...] = ()
    validation_history: tuple[CodexValidation, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def report_text(self) -> str:
        lines = [
            "संस्कृत-वाक्य यूनिवर्सल कोडेक्स रिपोर्ट",
            f"पृष्ठ: {self.page}",
            f"रूपान्तरित: {'हाँ' if self.transformed else 'नहीं'}",
            f"विश्वास: {self.confidence}",
        ]
        if self.manifest is not None:
            lines.append(
                "पृष्ठ-विवरण: "
                f"kind={self.manifest.kind}, "
                f"priority={self.manifest.priority}, "
                f"emits_vak={'हाँ' if self.manifest.emits_vak else 'नहीं'}, "
                f"passes={self.manifest.max_fixpoint_passes}"
            )
            if self.manifest.capabilities:
                lines.append(f"क्षमताएँ: {', '.join(self.manifest.capabilities)}")
            if self.manifest.extensions:
                lines.append(f"विस्तार: {', '.join('.' + ext for ext in self.manifest.extensions)}")
            if self.manifest.module_path:
                lines.append(f"पृष्ठ-पथ: {self.manifest.module_path}")
        if self.validation is not None:
            validation_line = (
                "सत्यापन: "
                f"वाक्यरचना={'हाँ' if self.validation.syntax_valid else 'नहीं'}, "
                f"संकलन={'हाँ' if self.validation.compiled else 'नहीं'}"
            )
            if self.validation.error_message:
                validation_line += (
                    f" [{self.validation.error_kind or 'त्रुटि'}"
                    + (f" L{self.validation.error_line}" if self.validation.error_line else "")
                    + f"] {self.validation.error_message}"
                )
            lines.append(validation_line)
        lines.append(f"स्रोत-प्रकार: {self.source_kind}")
        if self.detected_constructs:
            lines.append(f"चिह्नित संरचनाएँ: {', '.join(self.detected_constructs)}")
        if self.validation_history:
            lines.append("पारण-इतिहास:")
            for item in self.validation_history:
                details = (
                    f"  - pass {item.pass_index}/{item.stage}: "
                    f"syntax={'हाँ' if item.syntax_valid else 'नहीं'}, "
                    f"compile={'हाँ' if item.compiled else 'नहीं'}"
                )
                if item.error_message:
                    details += (
                        f" [{item.error_kind or 'त्रुटि'}"
                        + (f" L{item.error_line}" if item.error_line else "")
                        + f"] {item.error_message}"
                    )
                lines.append(details)
        if self.probes:
            lines.append("चयन:")
            for probe in self.probes:
                lines.append(f"  - {probe.page}: {probe.score} ({probe.reason})")
        if self.applied_rules:
            lines.append("लागू नियम:")
            for item in self.applied_rules:
                prefix = f"  - [{item.status}/{item.confidence}]"
                if item.line:
                    prefix += f" line {item.line}"
                lines.append(f"{prefix} {item.rule}: {item.message}")
        if self.rejected_rules:
            lines.append("अस्वीकृत नियम:")
            for item in self.rejected_rules:
                prefix = f"  - [{item.status}/{item.confidence}]"
                if item.line:
                    prefix += f" line {item.line}"
                lines.append(f"{prefix} {item.rule}: {item.message}")
        if self.diagnostics:
            lines.append("निदान:")
            for item in self.diagnostics:
                prefix = f"  - [{item.level}/{item.confidence}]"
                if item.line:
                    prefix += f" line {item.line}"
                lines.append(f"{prefix} {item.message}")
        return "\n".join(lines)

    def report_payload(self) -> dict[str, Any]:
        return {
            "page": self.page,
            "original_source": self.original_source,
            "source": self.source,
            "transformed": self.transformed,
            "confidence": self.confidence,
            "manifest": self.manifest.payload() if self.manifest is not None else None,
            "validation": self.validation.payload() if self.validation is not None else None,
            "source_kind": self.source_kind,
            "detected_constructs": list(self.detected_constructs),
            "applied_rules": [item.payload() for item in self.applied_rules],
            "rejected_rules": [item.payload() for item in self.rejected_rules],
            "validation_history": [item.payload() for item in self.validation_history],
            "probes": [
                {
                    "page": probe.page,
                    "score": probe.score,
                    "reason": probe.reason,
                }
                for probe in self.probes
            ],
            "diagnostics": [
                {
                    "page": item.page,
                    "level": item.level,
                    "message": item.message,
                    "confidence": item.confidence,
                    "line": item.line,
                    "before": item.before,
                    "after": item.after,
                }
                for item in self.diagnostics
            ],
            "metadata": dict(self.metadata),
        }
