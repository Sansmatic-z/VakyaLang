"""
Pipeline Page: Decompiler Page.

Provides bytecode decompilation as a Codex page:
- .vakc → .vak decompilation
- JSON ABI → source reconstruction
- Confidence reporting

*Visionary RM (Raj Mitra)* ⚡
"""
from __future__ import annotations

import json
import re
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from ..decompiler import CodexDecompiler
from ..ir import EncodedArtifact, TargetFormat


class DecompilerPageCodexPage(CodexPage):
    """Decompiles bytecode artifacts back to source."""
    name = "decompiler_page"
    description = "Bytecode decompiler page"
    priority = 72
    kind = "decompiler"
    chapter = "decompilers"
    chapter_title = "Supported Artifact Decompilers"
    chapter_order = 50
    capabilities = ("decompile", "reconstruct", "bytecode_to_source")
    emits_vak = True
    extensions = ("vakc", "json", "abi")
    max_fixpoint_passes = 1

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._decompiler = CodexDecompiler()

    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        """Check if source looks like a decompilable artifact."""
        score = 0
        if "\\x00VAK" in source:
            score += 30
        try:
            data = json.loads(source)
            if "constructs" in data or "source_hash" in data:
                score += 25
        except (json.JSONDecodeError, ValueError):
            pass

        if filename and filename.endswith((".vakc", ".abi.json")):
            score += 30

        if score >= 15:
            return CodexPageProbe(self.name, min(score, 90), "Decompilable artifact detected")
        return CodexPageProbe(self.name, 0, "not a decompilable artifact")

    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        diagnostics: list[CodexDiagnostic] = []
        metadata: dict[str, Any] = {}

        # Determine format
        fmt = self._detect_format(source, filename)
        if fmt is None:
            diagnostics.append(CodexDiagnostic(
                page=self.name, level="warning",
                message="Unrecognized artifact format",
                confidence="suggest_only",
            ))
            return CodexResult(
                page=self.name, original_source=source, source=source,
                transformed=False, confidence="suggest_only",
                diagnostics=tuple(diagnostics), metadata=metadata,
            )

        # Create artifact and decompile
        content_bytes = source.encode("utf-8") if isinstance(source, str) else source
        artifact = EncodedArtifact(
            verified=self._dummy_verification(),
            format=fmt,
            content=content_bytes,
            filename=filename or "artifact",
        )

        result = self._decompiler.decompile(artifact)

        metadata["decompiler"] = result.decompiler_name
        metadata["decompiler_version"] = result.decompiler_version
        metadata["confidence"] = result.confidence
        metadata["is_faithful"] = result.is_faithful
        metadata["warnings"] = result.warnings
        metadata["unsupported_ops"] = result.unsupported_ops

        for warning in result.warnings:
            diagnostics.append(CodexDiagnostic(
                page=self.name, level="warning", message=warning,
                confidence="safe_auto_fix",
            ))

        output = result.decompiled_source
        if not result.is_faithful:
            output = f"# Warning: Decompiled source may not be faithful (confidence: {result.confidence:.2f})\n\n" + output

        return CodexResult(
            page=self.name, original_source=source, source=output,
            transformed=True,
            confidence="verified" if result.is_faithful else "suggest_only",
            diagnostics=tuple(diagnostics), metadata=metadata,
        )

    def _detect_format(self, source: str, filename: str | None) -> TargetFormat | None:
        """Detect the artifact format."""
        if filename and filename.endswith(".vakc"):
            return TargetFormat.VAK_BYTECODE
        if filename and filename.endswith((".abi", ".abi.json")):
            return TargetFormat.JSON_ABI

        # Content-based detection
        if "\\x00VAK" in source:
            return TargetFormat.VAK_BYTECODE
        try:
            data = json.loads(source)
            if "constructs" in data:
                return TargetFormat.JSON_ABI
        except (json.JSONDecodeError, ValueError):
            pass

        return None

    def _dummy_verification(self) -> Any:
        """Create a minimal VerificationResult for artifact creation."""
        from ..ir import VerificationResult, TransformedIR
        return VerificationResult(
            transformed=TransformedIR(
                normalized=None, target_source="", target_language=None,  # type: ignore[arg-type]
            ),
            parse_valid=True, compile_valid=True, type_valid=True,
            proof_valid=True, audit_valid=True,
        )
