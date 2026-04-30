"""
Codex Bytecode Decompiler.

DECOMPILE stage: bytecode → source (with confidence).

Supports:
- .vakc → .vak decompiler
- JSON ABI → source reconstruction
- Only for supported formats with explicit confidence scores

*Visionary RM (Raj Mitra)* ⚡
"""
from __future__ import annotations

import json
import re
from typing import Any

from .ir import (
    DecompiledResult,
    EncodedArtifact,
    TargetFormat,
)


# ──────────────────────────────────────────────────────────────
# Vak Bytecode Decompiler
# ──────────────────────────────────────────────────────────────

_VAKC_MAGIC = b"\x00VAK"


def decompile_vak_bytecode(artifact: EncodedArtifact) -> DecompiledResult:
    """
    Decompile .vakc bytecode back to .vak source.

    The current format is: magic + version + length + checksum + payload.
    Decompilation extracts the payload directly.
    """
    content = artifact.content
    if not isinstance(content, bytes):
        content = content.encode("utf-8")

    warnings: list[str] = []
    unsupported: list[str] = []

    # Validate magic
    if not content.startswith(_VAKC_MAGIC):
        warnings.append("Missing or invalid VAK bytecode magic header")
        return DecompiledResult(
            artifact=artifact,
            decompiled_source=str(content),
            confidence=0.1,
            decompiler_name="vak_bytecode_decompiler",
            decompiler_version="1.0.0",
            warnings=warnings,
            unsupported_ops=unsupported,
            decompile_metadata={"format": "unknown_bytecode"},
        )

    # Parse header: magic(4) + version(2) + length(4) + checksum(8) = 18 bytes
    HEADER_SIZE = 18
    if len(content) < HEADER_SIZE:
        warnings.append("Bytecode too short for valid header")
        return DecompiledResult(
            artifact=artifact,
            decompiled_source="",
            confidence=0.0,
            decompiler_name="vak_bytecode_decompiler",
            decompiler_version="1.0.0",
            warnings=warnings,
            unsupported_ops=unsupported,
            decompile_metadata={"format": "vak_bytecode"},
        )

    import struct
    payload_length = struct.unpack(">I", content[6:10])[0]
    payload = content[HEADER_SIZE:]

    # Decode payload
    try:
        source = payload.decode("utf-8")
    except UnicodeDecodeError as e:
        warnings.append(f"Payload decode error: {e}")
        source = payload.decode("utf-8", errors="replace")

    confidence = 1.0 if len(payload) == payload_length else 0.8
    if warnings:
        confidence *= 0.5

    return DecompiledResult(
        artifact=artifact,
        decompiled_source=source,
        confidence=confidence,
        decompiler_name="vak_bytecode_decompiler",
        decompiler_version="1.0.0",
        warnings=warnings,
        unsupported_ops=unsupported,
        decompile_metadata={
            "format": "vak_bytecode",
            "payload_length": payload_length,
            "actual_length": len(payload),
        },
    )


# ──────────────────────────────────────────────────────────────
# JSON ABI Decompiler
# ──────────────────────────────────────────────────────────────

def decompile_json_abi(artifact: EncodedArtifact) -> DecompiledResult:
    """
    Reconstruct source from JSON ABI metadata.

    This is a best-effort reconstruction — the ABI contains structural
    information but not the full source. Confidence is inherently lower.
    """
    content = artifact.content
    if isinstance(content, bytes):
        content = content.decode("utf-8")

    warnings: list[str] = []
    unsupported: list[str] = ["full_source_recovery"]

    try:
        abi = json.loads(content)
    except json.JSONDecodeError as e:
        return DecompiledResult(
            artifact=artifact,
            decompiled_source="",
            confidence=0.0,
            decompiler_name="json_abi_decompiler",
            decompiler_version="1.0.0",
            warnings=[f"Invalid JSON ABI: {e}"],
            unsupported_ops=unsupported,
            decompile_metadata={"format": "json_abi"},
        )

    # Reconstruct from ABI constructs
    lines: list[str] = [
        "# Reconstructed from JSON ABI",
        f"# Source hash: {abi.get('source_hash', 'unknown')}",
        "",
    ]

    constructs = abi.get("constructs", [])
    for construct in constructs:
        name = construct.get("name", "unknown")
        ctype = construct.get("type", "function")
        if ctype == "function":
            lines.append(f"कर्म {name}() {{")
            lines.append("    # Reconstructed from ABI — body not preserved")
            lines.append("    लौटाओ अपरिभाषित")
            lines.append("}")
            lines.append("")
        else:
            lines.append(f"श्रेणी {name} {{")
            lines.append("    # Reconstructed from ABI — body not preserved")
            lines.append("}")
            lines.append("")

    if not constructs:
        lines.append("# No constructs found in ABI")
        lines.append("")

    source = "\n".join(lines)
    confidence = 0.4  # Partial reconstruction
    warnings.append("Source reconstructed from ABI — body content not preserved")

    return DecompiledResult(
        artifact=artifact,
        decompiled_source=source,
        confidence=confidence,
        decompiler_name="json_abi_decompiler",
        decompiler_version="1.0.0",
        warnings=warnings,
        unsupported_ops=unsupported,
        decompile_metadata={
            "format": "json_abi",
            "constructs_reconstructed": len(constructs),
        },
    )


# ──────────────────────────────────────────────────────────────
# Documentation Artifact Decompiler
# ──────────────────────────────────────────────────────────────

def decompile_documentation(artifact: EncodedArtifact) -> DecompiledResult:
    """Extract source code from documentation artifact."""
    content = artifact.content
    if isinstance(content, bytes):
        content_str = content.decode("utf-8")
    else:
        content_str = content

    # Extract code from markdown code blocks
    code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", content_str, re.DOTALL)

    if code_blocks:
        source = "\n\n".join(code_blocks)
        confidence = 0.9
    else:
        source = "# No code blocks found in documentation"
        confidence = 0.1

    return DecompiledResult(
        artifact=artifact,
        decompiled_source=source,
        confidence=confidence,
        decompiler_name="doc_decompiler",
        decompiler_version="1.0.0",
        warnings=[] if code_blocks else ["No code blocks found"],
        unsupported_ops=[],
        decompile_metadata={
            "format": "documentation",
            "code_blocks_found": len(code_blocks),
        },
    )


# ──────────────────────────────────────────────────────────────
# Decompiler Registry
# ──────────────────────────────────────────────────────────────

_DECOMPILER_MAP: dict[TargetFormat, callable] = {  # type: ignore[name-defined]
    TargetFormat.VAK_BYTECODE: decompile_vak_bytecode,
    TargetFormat.JSON_ABI: decompile_json_abi,
    TargetFormat.DOCUMENTATION: decompile_documentation,
}


class CodexDecompiler:
    """
    Bytecode and artifact decompiler.

    Usage:
        decompiler = CodexDecompiler()
        result = decompiler.decompile(artifact)
        print(result.decompiled_source)
        print(result.confidence)
    """

    def __init__(self) -> None:
        self._decompilers: dict[TargetFormat, callable] = dict(_DECOMPILER_MAP)  # type: ignore[name-defined]

    def decompile(self, artifact: EncodedArtifact) -> DecompiledResult:
        """
        Decompile an encoded artifact back to source.

        Args:
            artifact: The encoded artifact to decompile.

        Returns:
            DecompiledResult with decompiled source and confidence.

        Raises:
            ValueError: If no decompiler exists for the artifact format.
        """
        fmt = artifact.format
        decompiler = self._decompilers.get(fmt)

        if decompiler is None:
            return DecompiledResult(
                artifact=artifact,
                decompiled_source="",
                confidence=0.0,
                decompiler_name="unknown",
                decompiler_version="0.0.0",
                warnings=[f"No decompiler for format: {fmt.value}"],
                unsupported_ops=[fmt.value],
                decompile_metadata={"format": fmt.value, "supported": False},
            )

        return decompiler(artifact)

    def register_decompiler(
        self,
        fmt: TargetFormat,
        decompiler: callable,  # type: ignore[name-defined]
    ) -> None:
        """Register a custom decompiler for a format."""
        self._decompilers[fmt] = decompiler

    def supported_formats(self) -> list[TargetFormat]:
        """List all decompilable formats."""
        return list(self._decompilers.keys())

    def is_supported(self, fmt: TargetFormat) -> bool:
        """Check if a format is decompilable."""
        return fmt in self._decompilers
