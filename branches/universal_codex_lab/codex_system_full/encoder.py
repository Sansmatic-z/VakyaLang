"""
Codex Multi-Format Encoder.

ENCODE stage: target IR → output artifacts.

Supports:
- .vak source code
- .vakc bytecode (simulated)
- JSON ABI
- Documentation (Markdown)
- Reports (text/JSON)

*Visionary RM (Raj Mitra)* ⚡
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from .ir import (
    EncodedArtifact,
    TargetFormat,
    TransformedIR,
    VerificationResult,
)


# ──────────────────────────────────────────────────────────────
# Encoder Implementations
# ──────────────────────────────────────────────────────────────

def encode_vak_source(transformed: TransformedIR) -> tuple[str, str]:
    """Encode to .vak source code format."""
    content = transformed.target_source
    return content, "output.vak"


def encode_vak_bytecode(transformed: TransformedIR) -> tuple[bytes, str]:
    """
    Encode to simulated .vakc bytecode format.

    Produces a binary header + UTF-8 encoded source payload.
    In a real implementation this would invoke the Vak compiler.
    """
    source = transformed.target_source
    source_bytes = source.encode("utf-8")
    header = _bytecode_header(source_bytes)
    bytecode = header + source_bytes
    return bytecode, "output.vakc"


def encode_json_abi(transformed: TransformedIR) -> tuple[str, str]:
    """
    Encode to JSON ABI (Application Binary Interface) format.

    Produces a structured JSON describing the exported interface.
    """
    abi: dict[str, Any] = {
        "version": "1.0.0",
        "format": "vak_abi",
        "source_hash": hashlib.sha256(transformed.target_source.encode()).hexdigest(),
        "constructs": [],
        "metadata": transformed.transform_metadata,
    }

    for construct_name in transformed.constructs_mapped:
        abi["constructs"].append({
            "name": construct_name,
            "type": "function",  # Could be refined per construct
        })

    content = json.dumps(abi, indent=2, ensure_ascii=False)
    return content, "output.abi.json"


def encode_documentation(transformed: TransformedIR) -> tuple[str, str]:
    """Encode to Markdown documentation."""
    lines: list[str] = [
        "# Generated Documentation",
        "",
        f"- **Source**: {transformed.transform_metadata.get('source_id', 'unknown')}",
        f"- **Target Language**: {transformed.target_language.value}",
        f"- **Constructs Mapped**: {len(transformed.constructs_mapped)}",
        "",
        "## Constructs",
        "",
    ]

    if transformed.constructs_mapped:
        for name in transformed.constructs_mapped:
            lines.append(f"### `{name}`")
            lines.append("")
    else:
        lines.append("*No constructs detected.*")
        lines.append("")

    lines.append("## Source")
    lines.append("")
    lines.append("```vak")
    lines.append(transformed.target_source)
    lines.append("```")
    lines.append("")

    content = "\n".join(lines)
    return content, "output.md"


def encode_report(transformed: TransformedIR) -> tuple[str, str]:
    """Encode to a structured JSON report."""
    report: dict[str, Any] = {
        "report_type": "codex_transformation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_hash": hashlib.sha256(
            transformed.normalized.normalized_source.encode()
            if transformed.normalized else b""
        ).hexdigest()[:16],
        "target_language": transformed.target_language.value,
        "constructs_mapped": transformed.constructs_mapped,
        "transforms_applied": transformed.transforms_applied,
        "metadata": transformed.transform_metadata,
    }
    content = json.dumps(report, indent=2, ensure_ascii=False)
    return content, "report.json"


# ──────────────────────────────────────────────────────────────
# Bytecode Header Utilities
# ──────────────────────────────────────────────────────────────

_VAKC_MAGIC = b"\x00VAK"
_VAKC_VERSION = b"\x01\x00"


def _bytecode_header(source_bytes: bytes) -> bytes:
    """Generate a simple bytecode header."""
    length = len(source_bytes).to_bytes(4, "big")
    checksum = hashlib.sha256(source_bytes).digest()[:8]
    return _VAKC_MAGIC + _VAKC_VERSION + length + checksum


# ──────────────────────────────────────────────────────────────
# Encoder Registry
# ──────────────────────────────────────────────────────────────

_ENCODER_MAP: dict[TargetFormat, callable] = {  # type: ignore[name-defined]
    TargetFormat.VAK_SOURCE: encode_vak_source,
    TargetFormat.VAK_BYTECODE: encode_vak_bytecode,
    TargetFormat.JSON_ABI: encode_json_abi,
    TargetFormat.DOCUMENTATION: encode_documentation,
    TargetFormat.REPORT: encode_report,
}


class CodexEncoder:
    """
    Multi-format output encoder.

    Usage:
        encoder = CodexEncoder()
        artifact = encoder.encode(transformed, TargetFormat.VAK_SOURCE)
        print(artifact.filename)  # "output.vak"
    """

    def __init__(self) -> None:
        self._encoders: dict[TargetFormat, callable] = dict(_ENCODER_MAP)  # type: ignore[name-defined]

    def encode(
        self,
        verified: VerificationResult,
        fmt: TargetFormat,
    ) -> EncodedArtifact:
        """
        Encode a verified transformation into the target format.

        Args:
            verified: The verified transformation result.
            fmt: The desired output format.

        Returns:
            EncodedArtifact with content, filename, and checksum.

        Raises:
            ValueError: If the format is not supported.
        """
        encoder = self._encoders.get(fmt)
        if encoder is None:
            raise ValueError(f"Unsupported output format: {fmt}")

        content, filename = encoder(verified.transformed)

        # Normalize content to bytes for checksum
        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        else:
            content_bytes = content

        return EncodedArtifact(
            verified=verified,
            format=fmt,
            content=content,
            filename=filename,
            checksum=hashlib.sha256(content_bytes).hexdigest()[:16],
            encoding_metadata={
                "format": fmt.value,
                "filename": filename,
                "content_length": len(content_bytes),
            },
        )

    def register_encoder(
        self,
        fmt: TargetFormat,
        encoder: callable,  # type: ignore[name-defined]
    ) -> None:
        """Register a custom encoder for a format."""
        self._encoders[fmt] = encoder

    def supported_formats(self) -> list[TargetFormat]:
        """List all supported output formats."""
        return list(self._encoders.keys())
