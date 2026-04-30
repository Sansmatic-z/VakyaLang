"""
Shared helpers for Codex pages that emit Vak source.

This experiment accumulated a mix of current Vak syntax and older Vak-like
surface forms (brace blocks, legacy keywords, doubled template braces). The
main VakLang repo is the source of truth, so Codex pages should normalize to a
current Vak surface before reporting success.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Final


_IDENT_BOUNDARY = r"(?<![A-Za-z0-9_\u0900-\u097F]){token}(?![A-Za-z0-9_\u0900-\u097F])"
_TOKEN_REPLACEMENTS: Final[tuple[tuple[str, str], ...]] = (
    ("श्रेणी", "वर्ग"),
    ("परिवर्तनी", "चर"),
    ("लौटाओ", "प्रत्यागच्छ"),
    ("छापो", "मुद्रय"),
    ("टूटो", "विराम"),
    ("समूह", "समुच्चय"),
)
_SURFACE_MARKERS: Final[tuple[str, ...]] = (
    "कर्म",
    "वर्ग",
    "श्रेणी",
    "चर",
    "परिवर्तनी",
    "प्रत्यागच्छ",
    "लौटाओ",
    "यदि",
    "अन्यथा",
    "यावत्",
    "प्रत्येक",
    "आयात",
)


def looks_like_vak_surface(source: str) -> bool:
    return any(marker in source for marker in _SURFACE_MARKERS)


def normalize_vak_surface(source: str) -> str:
    """Normalize legacy Vak-like output to current Vak surface syntax."""
    if not source:
        return source

    normalized = source.replace("\r\n", "\n").replace("{{", "{").replace("}}", "}")

    for old, new in _TOKEN_REPLACEMENTS:
        normalized = re.sub(_IDENT_BOUNDARY.format(token=re.escape(old)), new, normalized)

    normalized = _normalize_print_calls(normalized)
    normalized = _normalize_brace_blocks(normalized)
    normalized = _squash_excess_blank_lines(normalized)
    return normalized


def validate_vak_surface(source: str) -> tuple[bool, str | None]:
    """Validate Vak source with the real sibling Vak compiler when available."""
    try:
        from runtime.src.compiler import Compiler
        from runtime.src.lexer import Lexer
        from runtime.src.parser import Parser

        compiler = Compiler()
        program = Parser(Lexer(source).tokenize()).parse()
        compiler.compile(program)
        return True, None
    except Exception as exc:
        return False, str(exc)


def _normalize_print_calls(source: str) -> str:
    lines: list[str] = []
    for line in source.split("\n"):
        stripped = line.strip()
        indent = line[: len(line) - len(line.lstrip())]
        if (
            stripped.startswith("मुद्रय ")
            and not stripped.startswith("मुद्रय(")
            and not stripped.startswith("मुद्रय (")
        ):
            payload = stripped[len("मुद्रय ") :].strip()
            lines.append(f"{indent}मुद्रय({payload})")
            continue
        lines.append(line)
    return "\n".join(lines)


def _normalize_brace_blocks(source: str) -> str:
    lines: list[str] = []
    indent_level = 0

    for raw_line in source.split("\n"):
        stripped = raw_line.strip()
        original_indent = len(raw_line) - len(raw_line.lstrip())
        if not stripped:
            lines.append("")
            continue

        while stripped.startswith("}"):
            indent_level = max(0, indent_level - 1)
            stripped = stripped[1:].lstrip()

        if not stripped:
            continue

        block_open = stripped.endswith("{")
        if block_open:
            stripped = stripped[:-1].rstrip()
            if stripped and not stripped.endswith(":"):
                stripped += ":"

        effective_indent = max(indent_level * 4, original_indent)
        lines.append(f"{' ' * effective_indent}{stripped}")

        if block_open:
            indent_level += 1

    return "\n".join(lines)


def _squash_excess_blank_lines(source: str) -> str:
    result: list[str] = []
    prev_blank = False
    for line in source.split("\n"):
        blank = not line.strip()
        if blank and prev_blank:
            continue
        result.append(line.rstrip())
        prev_blank = blank
    return "\n".join(result).strip()
