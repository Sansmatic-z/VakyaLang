"""
Codex Multi-Format Decoder.

DECODE stage: source → structured IR.

Supports:
- Language decoders (Python, JS, C, etc.)
- Syntax decoders (EBNF, PEG, etc.)
- Format decoders (JSON, YAML, TOML, etc.)

Each decoder attempts to parse source into a structured AST / token stream,
producing a `DecodedIR` with language identification and parse results.

*Visionary RM (Raj Mitra)* ⚡
"""
from __future__ import annotations

import json
import re
import tokenize
import io
from typing import Any

from .ir import DecodedIR, SourceLanguage


# ──────────────────────────────────────────────────────────────
# Decoder Registry
# ──────────────────────────────────────────────────────────────

class DecoderRegistry:
    """Registry mapping languages to their decoder functions."""

    def __init__(self) -> None:
        self._decoders: dict[SourceLanguage, callable] = {}  # type: ignore[name-defined]

    def register(self, language: SourceLanguage, decoder: callable) -> None:  # type: ignore[name-defined]
        """Register a decoder function for a language."""
        self._decoders[language] = decoder

    def get(self, language: SourceLanguage) -> callable | None:  # type: ignore[name-defined]
        """Get the decoder for a language, or None."""
        return self._decoders.get(language)

    def list_languages(self) -> list[SourceLanguage]:
        """List all registered languages."""
        return list(self._decoders.keys())

    def auto_detect(self, source: str, filename: str | None = None) -> SourceLanguage:
        """Auto-detect the source language from content and filename."""
        # Filename-based detection
        if filename:
            ext_map = {
                ".py": SourceLanguage.PYTHON,
                ".js": SourceLanguage.JAVASCRIPT,
                ".ts": SourceLanguage.TYPESCRIPT,
                ".c": SourceLanguage.C,
                ".cpp": SourceLanguage.CPP,
                ".cc": SourceLanguage.CPP,
                ".h": SourceLanguage.C,
                ".hpp": SourceLanguage.CPP,
                ".java": SourceLanguage.JAVA,
                ".go": SourceLanguage.GO,
                ".rs": SourceLanguage.RUST,
                ".vak": SourceLanguage.VAK,
                ".json": SourceLanguage.JSON,
                ".yaml": SourceLanguage.YAML,
                ".yml": SourceLanguage.YAML,
                ".toml": SourceLanguage.TOML,
                ".xml": SourceLanguage.XML,
                ".ebnf": SourceLanguage.EBNF,
                ".peg": SourceLanguage.PEG,
            }
            for ext, lang in ext_map.items():
                if filename.endswith(ext):
                    return lang

        # Content-based heuristics
        stripped = source.strip()
        if not stripped:
            return SourceLanguage.UNKNOWN

        # JSON detection
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                json.loads(stripped)
                return SourceLanguage.JSON
            except (json.JSONDecodeError, ValueError):
                pass

        # XML detection
        if stripped.startswith("<?xml") or stripped.startswith("<"):
            if re.search(r"<\w+[^>]*>.*</\w+>", stripped, re.DOTALL):
                return SourceLanguage.XML

        # EBNF detection
        if re.search(r"^\w+\s*=\s*.+\s*;", source, re.MULTILINE):
            return SourceLanguage.EBNF

        # PEG detection
        if re.search(r"^\w+\s*<-\s*.+", source, re.MULTILINE):
            return SourceLanguage.PEG

        # YAML detection (before Python tokenization)
        if re.search(r"^\w+:\s+.+", source, re.MULTILINE) and not stripped.startswith("{"):
            # Could be YAML, but avoid false positives
            lines = source.strip().split("\n")
            if all(":" in line or line.strip().startswith("-") or not line.strip() for line in lines[:10]):
                return SourceLanguage.YAML

        # JavaScript detection (BEFORE Python tokenization)
        # JS-specific keywords that aren't Python keywords
        if re.search(r"\bconst\b\s+\w+\s*=", source) or re.search(r"\blet\b\s+\w+\s*=", source):
            return SourceLanguage.JAVASCRIPT
        if re.search(r"\bvar\b\s+\w+\s*=", source):
            return SourceLanguage.JAVASCRIPT
        if re.search(r"function\s+\w+\s*\(", source):
            return SourceLanguage.JAVASCRIPT
        if "=>" in source and re.search(r"\([^)]*\)\s*=>", source):
            return SourceLanguage.JAVASCRIPT

        # Python detection
        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
            if tokens:
                return SourceLanguage.PYTHON
        except tokenize.TokenError:
            pass

        # JavaScript detection
        if re.search(r"(const|let|var)\s+\w+\s*=", source):
            return SourceLanguage.JAVASCRIPT
        if re.search(r"function\s+\w+\s*\(", source):
            return SourceLanguage.JAVASCRIPT
        if "=>" in source and re.search(r"\([^)]*\)\s*=>", source):
            return SourceLanguage.JAVASCRIPT

        # Go detection
        if re.search(r"func\s+\w+\s*\(", source):
            return SourceLanguage.GO

        # Rust detection
        if re.search(r"fn\s+\w+\s*\(", source) and ("let " in source or "mut " in source):
            return SourceLanguage.RUST

        # C/C++ detection
        if re.search(r"#include\s*<", source):
            if "class " in source or "template " in source:
                return SourceLanguage.CPP
            return SourceLanguage.C
        if re.search(r"(public|private|protected)\s*:", source):
            return SourceLanguage.CPP

        # Java detection
        if re.search(r"(public|private|protected)\s+class\s+\w+", source):
            return SourceLanguage.JAVA

        return SourceLanguage.UNKNOWN


# ──────────────────────────────────────────────────────────────
# Language-Specific Decoders
# ──────────────────────────────────────────────────────────────

def decode_python(source: str, filename: str | None = None) -> dict[str, Any]:
    """Decode Python source into tokens and (if available) AST."""
    result: dict[str, Any] = {"tokens": [], "ast": None}
    errors: list[str] = []

    # Tokenize
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
        result["tokens"] = [
            {
                "type": tokenize.tok_name.get(t.type, str(t.type)),
                "string": t.string,
                "start": t.start,
                "end": t.end,
                "line": t.start[0],
            }
            for t in tokens
        ]
    except tokenize.TokenError as e:
        errors.append(f"Tokenization error: {e}")

    # AST (optional, may fail on partial code)
    try:
        import ast
        tree = ast.parse(source, filename=filename or "<string>")
        result["ast"] = _ast_summary(tree)
    except SyntaxError:
        pass  # Not a full module, that's ok
    except ImportError:
        pass

    return {"result": result, "errors": errors, "warnings": []}


def decode_json(source: str, filename: str | None = None) -> dict[str, Any]:
    """Decode JSON source into parsed data."""
    result: dict[str, Any] = {"tokens": [], "ast": None}
    errors: list[str] = []

    try:
        data = json.loads(source)
        result["ast"] = data
        result["tokens"] = [{"type": "json_value", "string": json.dumps(data)[:100]}]
    except json.JSONDecodeError as e:
        errors.append(f"JSON decode error: {e}")

    return {"result": result, "errors": errors, "warnings": []}


def decode_ebnf(source: str, filename: str | None = None) -> dict[str, Any]:
    """Decode EBNF grammar into rules."""
    result: dict[str, Any] = {"tokens": [], "ast": None}
    errors: list[str] = []

    rules: list[dict[str, Any]] = []
    for line in source.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("//"):
            continue
        m = re.match(r"(\w+)\s*=\s*(.+?)\s*;", stripped)
        if m:
            name, body = m.group(1), m.group(2).strip()
            is_terminal = bool(re.match(r"^\[", body)) or body.isupper()
            rules.append({
                "name": name, "body": body,
                "is_terminal": is_terminal, "line": line,
            })
        else:
            errors.append(f"Unrecognized EBNF line: {stripped}")

    result["ast"] = {"rules": rules}
    result["tokens"] = [{"type": "rule", "string": r["name"]} for r in rules]
    return {"result": result, "errors": errors, "warnings": []}


def decode_peg(source: str, filename: str | None = None) -> dict[str, Any]:
    """Decode PEG grammar into rules."""
    result: dict[str, Any] = {"tokens": [], "ast": None}
    errors: list[str] = []

    rules: list[dict[str, Any]] = []
    for line in source.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("//"):
            continue
        m = re.match(r"(\w+)\s*<-\s*(.+)", stripped)
        if m:
            name, body = m.group(1), m.group(2).strip()
            is_terminal = body.isupper()
            rules.append({
                "name": name, "body": body,
                "is_terminal": is_terminal, "line": line,
            })
        else:
            errors.append(f"Unrecognized PEG line: {stripped}")

    result["ast"] = {"rules": rules}
    result["tokens"] = [{"type": "rule", "string": r["name"]} for r in rules]
    return {"result": result, "errors": errors, "warnings": []}


def decode_generic(source: str, filename: str | None = None) -> dict[str, Any]:
    """Generic decoder for languages without a specific decoder."""
    lines = source.split("\n")
    tokens = [{"type": "line", "string": line[:80], "line": i + 1} for i, line in enumerate(lines)]
    return {
        "result": {"tokens": tokens, "ast": None},
        "errors": [],
        "warnings": ["No specific decoder for this language"],
    }


# ──────────────────────────────────────────────────────────────
# AST Helpers
# ──────────────────────────────────────────────────────────────

def _ast_summary(tree: Any) -> dict[str, Any]:
    """Produce a lightweight summary of a Python AST."""
    import ast
    summary: dict[str, Any] = {"type": "Module", "children": []}

    for node in ast.iter_child_nodes(tree):
        child: dict[str, Any] = {"type": type(node).__name__}
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            child["name"] = node.name
            child["args"] = [a.arg for a in node.args.args]
            child["lineno"] = node.lineno
        elif isinstance(node, ast.ClassDef):
            child["name"] = node.name
            child["bases"] = [_name_of(b) for b in node.bases]
            child["lineno"] = node.lineno
        elif isinstance(node, ast.Assign):
            targets = [_name_of(t) for t in node.targets]
            child["targets"] = targets
            child["lineno"] = node.lineno
        elif isinstance(node, ast.Import):
            child["names"] = [n.name for n in node.names]
        elif isinstance(node, ast.ImportFrom):
            child["module"] = node.module
            child["names"] = [n.name for n in node.names]
        summary["children"].append(child)

    return summary


def _name_of(node: Any) -> str:
    """Extract a name string from an AST node."""
    import ast
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_name_of(node.value)}.{node.attr}"
    return str(node)


# ──────────────────────────────────────────────────────────────
# Main Decoder Facade
# ──────────────────────────────────────────────────────────────

class CodexDecoder:
    """
    Multi-format source decoder.

    Usage:
        decoder = CodexDecoder()
        decoded = decoder.decode("def hello(): pass", filename="hello.py")
        print(decoded.language)  # SourceLanguage.PYTHON
    """

    def __init__(self) -> None:
        self.registry = DecoderRegistry()
        self._register_builtin_decoders()

    def _register_builtin_decoders(self) -> None:
        """Register all built-in decoders."""
        self.registry.register(SourceLanguage.PYTHON, decode_python)
        self.registry.register(SourceLanguage.JSON, decode_json)
        self.registry.register(SourceLanguage.EBNF, decode_ebnf)
        self.registry.register(SourceLanguage.PEG, decode_peg)

    def decode(
        self,
        source: str,
        *,
        language: SourceLanguage | None = None,
        filename: str | None = None,
        encoding: str = "utf-8",
    ) -> DecodedIR:
        """
        Decode source code into structured IR.

        Args:
            source: Raw source code text.
            language: Override auto-detection with a specific language.
            filename: Optional filename for extension-based detection.
            encoding: Source encoding (default UTF-8).

        Returns:
            DecodedIR with parsed tokens, AST (if available), and diagnostics.
        """
        if language is None:
            language = self.registry.auto_detect(source, filename)

        decoder = self.registry.get(language)
        if decoder is None:
            decoder = decode_generic

        decode_result = decoder(source, filename)
        parsed = decode_result["result"]

        return DecodedIR(
            language=language,
            source=source,
            filename=filename,
            encoding=encoding,
            syntax_tree=parsed.get("ast"),
            tokens=parsed.get("tokens", []),
            decode_errors=decode_result.get("errors", []),
            decode_warnings=decode_result.get("warnings", []),
        )

    def supported_languages(self) -> list[SourceLanguage]:
        """List all supported source languages."""
        return self.registry.list_languages()

    def register_decoder(self, language: SourceLanguage, decoder: callable) -> None:  # type: ignore[name-defined]
        """Register a custom decoder for a language."""
        self.registry.register(language, decoder)
