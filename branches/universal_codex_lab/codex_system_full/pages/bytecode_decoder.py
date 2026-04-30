"""
Pipeline Page: Bytecode Decoder.

Provides bytecode/ABI decoding capabilities as a Codex page:
- Decode .vakc bytecode to readable representation
- Decode JSON ABI to structured metadata
- Decode documentation artifacts

*Visionary RM (Raj Mitra)* ⚡
"""
from __future__ import annotations

import json
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from ..ir import (
    DecodedIR,
    EncodedArtifact,
    SourceLanguage,
    TargetFormat,
    VerificationResult,
    TransformedIR,
    NormalizedIR,
    AnalyzedIR,
)


class BytecodeDecoderCodexPage(CodexPage):
    """Decodes bytecode and ABI artifacts to readable form."""
    name = "bytecode_decoder"
    description = "Bytecode/ABI decoder page"
    priority = 70
    kind = "bytecode_decoder"
    chapter = "decoders"
    chapter_title = "Language Family Decoders"
    chapter_order = 10
    capabilities = ("decode", "bytecode", "abi", "inspect")
    emits_vak = False
    extensions = ("vakc", "json", "abi", "md")
    max_fixpoint_passes = 1

    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        indicators = ["\\x00VAK", "vakc", "bytecode", "abi", "source_hash"]
        score = 0
        for indicator in indicators:
            if indicator in source:
                score += 15

        if filename and filename.endswith((".vakc", ".abi", ".abi.json")):
            score += 30

        if score >= 15:
            return CodexPageProbe(self.name, min(score, 90), "Bytecode/ABI artifact detected")
        return CodexPageProbe(self.name, 0, "not a bytecode artifact")

    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        diagnostics: list[CodexDiagnostic] = []
        metadata: dict[str, Any] = {}

        # Try JSON ABI first
        try:
            data = json.loads(source)
            metadata["format"] = "json_abi"
            metadata["version"] = data.get("version", "unknown")
            metadata["constructs"] = data.get("constructs", [])
            metadata["source_hash"] = data.get("source_hash", "unknown")
            diagnostics.append(CodexDiagnostic(
                page=self.name, level="info",
                message=f"Decoded JSON ABI with {len(metadata['constructs'])} constructs",
                confidence="verified",
            ))
            return CodexResult(
                page=self.name, original_source=source, source=source,
                transformed=True, confidence="verified",
                diagnostics=tuple(diagnostics), metadata=metadata,
            )
        except (json.JSONDecodeError, ValueError):
            pass

        # Try Vak bytecode
        if isinstance(source, str) and "\\x00VAK" in source:
            metadata["format"] = "vak_bytecode"
            metadata["header_valid"] = True
            diagnostics.append(CodexDiagnostic(
                page=self.name, level="info",
                message="Vak bytecode header detected",
                confidence="safe_auto_fix",
            ))
            return CodexResult(
                page=self.name, original_source=source, source=source,
                transformed=True, confidence="safe_auto_fix",
                diagnostics=tuple(diagnostics), metadata=metadata,
            )

        # Fallback
        diagnostics.append(CodexDiagnostic(
            page=self.name, level="info",
            message="No recognized bytecode format detected",
            confidence="suggest_only",
        ))
        return CodexResult(
            page=self.name, original_source=source, source=source,
            transformed=False, confidence="suggest_only",
            diagnostics=tuple(diagnostics), metadata=metadata,
        )
