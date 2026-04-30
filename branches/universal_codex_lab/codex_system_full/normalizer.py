"""
Codex Code Normalizer.

NORMALIZE stage: IR → canonical form.

Performs:
- Syntax normalization (consistent formatting)
- Semantic normalization (equivalent constructs)
- Style normalization (consistent naming/spacing)
- Code repair (fix common issues)

*Visionary RM (Raj Mitra)* ⚡
"""
from __future__ import annotations

import ast
import re
import textwrap
from typing import Any

from .ir import (
    AnalyzedIR,
    NormalizedIR,
    RiskLevel,
    SourceLanguage,
)


# ──────────────────────────────────────────────────────────────
# Python Normalizer
# ──────────────────────────────────────────────────────────────

def normalize_python(analyzed: AnalyzedIR) -> NormalizedIR:
    """Normalize Python source to canonical form."""
    source = analyzed.decoded.source
    repairs: list[str] = []
    errors: list[str] = []

    # 1. Syntax repair: try to parse and re-format via AST
    try:
        tree = ast.parse(source)
        # AST round-trip gives us syntax validation
        repairs.append("Syntax validated via AST")
    except SyntaxError as e:
        errors.append(f"Syntax error at line {e.lineno}: {e.msg}")

    # 2. Style normalization
    normalized = _normalize_python_style(source, repairs)

    # 3. Semantic normalization
    normalized = _normalize_python_semantics(normalized, repairs)

    return NormalizedIR(
        analyzed=analyzed,
        normalized_source=normalized,
        repairs_applied=repairs,
        style="canonical",
        is_valid=len(errors) == 0,
        validation_errors=errors,
        normalization_metadata={
            "language": analyzed.decoded.language.value,
            "repairs_count": len(repairs),
        },
    )


def _normalize_python_style(source: str, repairs: list[str]) -> str:
    """Apply PEP-8-inspired style normalization."""
    lines = source.split("\n")
    result: list[str] = []

    for line in lines:
        # Remove trailing whitespace
        stripped = line.rstrip()
        if stripped != line:
            if "trailing_whitespace_removed" not in repairs:
                repairs.append("trailing_whitespace_removed")
            line = stripped

        # Normalize blank lines (no more than 2 consecutive)
        if line.strip() == "":
            result.append("")
        else:
            result.append(line)

    # Collapse excessive blank lines
    text = "\n".join(result)
    text = re.sub(r"\n{4,}", "\n\n\n", text)

    return text


def _normalize_python_semantics(source: str, repairs: list[str]) -> str:
    """Apply semantic normalization (equivalent constructs)."""
    # Normalize common patterns to canonical forms

    # `not x == y` → `x != y`
    new_source = re.sub(r"not\s+(\w+)\s*==\s*(\w+)", r"\1 != \2", source)
    if new_source != source:
        repairs.append("normalized_negated_equality")
        source = new_source

    # `not x != y` → `x == y`
    new_source = re.sub(r"not\s+(\w+)\s*!=\s*(\w+)", r"\1 == \2", source)
    if new_source != source:
        repairs.append("normalized_negated_inequality")
        source = new_source

    # `len(x) == 0` → `not x`
    new_source = re.sub(r"len\((\w+)\)\s*==\s*0", r"not \1", source)
    if new_source != source:
        repairs.append("normalized_empty_check")
        source = new_source

    # `x is True` → `x`
    new_source = re.sub(r"(\w+)\s+is\s+True", r"\1", source)
    if new_source != source:
        repairs.append("normalized_is_true")
        source = new_source

    # `x is False` → `not x`
    new_source = re.sub(r"(\w+)\s+is\s+False", r"not \1", source)
    if new_source != source:
        repairs.append("normalized_is_false")
        source = new_source

    return source


# ──────────────────────────────────────────────────────────────
# Generic Normalizer
# ──────────────────────────────────────────────────────────────

def normalize_generic(analyzed: AnalyzedIR) -> NormalizedIR:
    """Normalize any source to canonical form using heuristics."""
    source = analyzed.decoded.source
    repairs: list[str] = []
    errors: list[str] = []

    # Remove trailing whitespace
    lines = [line.rstrip() for line in source.split("\n")]
    if lines != source.split("\n"):
        repairs.append("trailing_whitespace_removed")

    # Remove leading/trailing blank lines
    while lines and not lines[0].strip():
        lines.pop(0)
        repairs.append("leading_blank_lines_removed")
    while lines and not lines[-1].strip():
        lines.pop()
        repairs.append("trailing_blank_lines_removed")

    # Dedent if uniformly indented
    text = "\n".join(lines)
    try:
        dedented = textwrap.dedent(text)
        if dedented != text:
            repairs.append("dedent_applied")
            text = dedented
    except Exception:
        pass

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    return NormalizedIR(
        analyzed=analyzed,
        normalized_source=text,
        repairs_applied=repairs,
        style="canonical",
        is_valid=len(errors) == 0,
        validation_errors=errors,
        normalization_metadata={
            "language": analyzed.decoded.language.value,
            "repairs_count": len(repairs),
        },
    )


# ──────────────────────────────────────────────────────────────
# JSON/YAML Normalizer
# ──────────────────────────────────────────────────────────────

def normalize_json(analyzed: AnalyzedIR) -> NormalizedIR:
    """Normalize JSON to canonical (sorted keys, 2-space indent) form."""
    import json

    source = analyzed.decoded.source
    repairs: list[str] = []
    errors: list[str] = []

    try:
        data = json.loads(source)
        normalized = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)
        if normalized != source.strip():
            repairs.append("json_canonicalized")
        return NormalizedIR(
            analyzed=analyzed,
            normalized_source=normalized,
            repairs_applied=repairs,
            style="canonical",
            is_valid=True,
            validation_errors=errors,
            normalization_metadata={
                "language": "json",
                "repairs_count": len(repairs),
            },
        )
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {e}")
        return NormalizedIR(
            analyzed=analyzed,
            normalized_source=source,
            repairs_applied=repairs,
            style="canonical",
            is_valid=False,
            validation_errors=errors,
            normalization_metadata={
                "language": "json",
                "repairs_count": len(repairs),
            },
        )


# ──────────────────────────────────────────────────────────────
# Main Normalizer Facade
# ──────────────────────────────────────────────────────────────

class CodexNormalizer:
    """
    Code normalization engine.

    Usage:
        normalizer = CodexNormalizer()
        normalized = normalizer.normalize(analyzed)
        print(normalized.normalized_source)
        print(normalized.repairs_applied)
    """

    def normalize(self, analyzed: AnalyzedIR) -> NormalizedIR:
        """
        Normalize analyzed source to canonical form.

        Args:
            analyzed: The analyzed IR from the analysis stage.

        Returns:
            NormalizedIR with repaired and canonical source.
        """
        language = analyzed.decoded.language

        if language == SourceLanguage.PYTHON:
            return normalize_python(analyzed)
        elif language == SourceLanguage.JSON:
            return normalize_json(analyzed)
        else:
            return normalize_generic(analyzed)

    def register_normalizer(
        self,
        language: SourceLanguage,
        normalizer: callable,  # type: ignore[name-defined]
    ) -> None:
        """Register a custom normalizer for a language."""
        # This would extend a registry in a production system
        pass
