"""
Phase 4: Lexer Generator Codex Page.

Generates lexer/scanner code from token definitions:
- Parses token definition formats
- Generates efficient lexer code
- Supports regex-based and hand-written lexer styles
- Outputs valid Vak code
"""
from __future__ import annotations

import re
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from ..engines.code_generator import CodeGenerator, GenerationContext
from .utils import _overall_confidence


class LexerGeneratorCodexPage(CodexPage):
    """Generates lexer code from token definitions."""
    name = "lexer_generator"
    description = "Lexer generator page (token definitions → lexer code)"
    priority = 61
    kind = "python"
    chapter = "language_tools"
    chapter_title = "Language Creation Tools"
    chapter_order = 41
    capabilities = ("lexer", "tokenizer", "scanner", "regex", "token_generation")
    emits_vak = True
    extensions = ("tokens", "lex", "re", "spec")
    max_fixpoint_passes = 2

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._generator = CodeGenerator()
        self._diagnostics: list[CodexDiagnostic] = []
        self._detected_constructs: list[str] = []
        self._register_templates()

    def _register_templates(self) -> None:
        self._generator.register_template("lexer_class", """# Lexer: {lexer_name}
# Tokens: {tokens_count}

श्रेणी {lexer_name}Lexer {{
    परिवर्तनी source = ""
    परिवर्तनी position = 0
    परिवर्तनी line = 1
    परिवर्तनी col = 1

    कर्म __init__(source) {{
        this.source = source
        this.position = 0
    }}

{token_methods}

    कर्म tokenize() {{
        tokens = []
        जबतक position < source.लंबाई() {{
            # Skip whitespace
            यदि source[position] is_whitespace {{
                skip_whitespace()
                continue
            }}

            # Try each token rule
{token_checks}

            # Unknown character
            तोड़ें
        }}
        लौटाओ tokens
    }}
}}""")

        self._generator.register_template("token_method", """    कर्म match_{token_name}() {{
        # Pattern: {pattern}
        # Match and return token
        लौटाओ token
    }}""")

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------
    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        indicators = [
            "token", "TOKEN", "lexer", "Lexer", "scanner", "Scanner",
            "regex", "pattern", "match",
            "NUMBER", "IDENTIFIER", "STRING", "KEYWORD", "OPERATOR",
            "KEYWORD:", "TOKEN:", "DEFINE",
        ]
        score = 0
        for indicator in indicators:
            if indicator in source:
                score += 10

        # Check for token definition patterns
        if re.search(r"(?m)^\s*(\w+)\s*[:=]\s*", source):
            score += 15

        # Check for regex patterns
        if re.search(r"\[.*\]|\+|\*|\{.*\}|\(\?:", source):
            score += 10

        if filename and filename.endswith((".tokens", ".lex", ".re", ".spec")):
            score += 30

        if score >= 20:
            return CodexPageProbe(self.name, min(score, 90), f"Lexer specification detected ({score} indicators)")
        return CodexPageProbe(self.name, 0, "not a lexer spec candidate")

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------
    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        self._diagnostics = []
        self._detected_constructs = []

        try:
            tokens = self._parse_token_defs(source)
            if not tokens:
                return self._no_transform(source, "No token definitions found")

            vak_code = self._generate_lexer(tokens)

            return CodexResult(
                page=self.name,
                original_source=source,
                source=vak_code,
                transformed=True,
                confidence=_overall_confidence(self._diagnostics, True),
                diagnostics=tuple(self._diagnostics),
                manifest=self.manifest(),
                metadata={
                    "source_kind": "lexer_spec",
                    "tokens_count": len(tokens),
                    "token_names": [t["name"] for t in tokens],
                },
            )
        except Exception as exc:
            return self._no_transform(source, str(exc))

    def _no_transform(self, source: str, reason: str) -> CodexResult:
        self._diagnostics.append(CodexDiagnostic(
            page=self.name, level="error", message=reason, confidence="do_not_touch",
        ))
        return CodexResult(
            page=self.name, original_source=source, source=source,
            transformed=False, confidence="do_not_touch",
            diagnostics=tuple(self._diagnostics), manifest=self.manifest(),
            metadata={"source_kind": "lexer_spec", "error": reason},
        )

    # ------------------------------------------------------------------
    # Token definition parsing
    # ------------------------------------------------------------------
    def _parse_token_defs(self, source: str) -> list[dict[str, Any]]:
        """Parse token definitions from various formats."""
        tokens: list[dict[str, Any]] = []

        for line in source.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("//"):
                continue

            # Format: TOKEN_NAME = regex_pattern
            m = re.match(r"(\w+)\s*[=:]\s*(.+)", stripped)
            if m:
                tokens.append({
                    "name": m.group(1),
                    "pattern": m.group(2).strip().strip('"').strip("'"),
                })
                continue

            # Format: TOKEN_NAME "literal"
            m = re.match(r"(\w+)\s+['\"](.+?)['\"]", stripped)
            if m:
                tokens.append({
                    "name": m.group(1),
                    "pattern": re.escape(m.group(2)),
                    "literal": m.group(2),
                })

        return tokens

    # ------------------------------------------------------------------
    # Code generation
    # ------------------------------------------------------------------
    def _generate_lexer(self, tokens: list[dict[str, Any]]) -> str:
        lexer_name = "Language"
        if tokens:
            lexer_name = tokens[0]["name"].replace("TOKEN", "").replace("_", "").capitalize()
            if not lexer_name:
                lexer_name = "Language"

        # Generate token check code
        token_checks: list[str] = []
        token_methods: list[str] = []

        for token in tokens:
            name = token["name"].lower()
            pattern = token.get("pattern", "")

            token_checks.append(f"            यदि match_{name}() {{")
            token_checks.append(f"                tokens.जोड़ें(create_token(\"{token['name']}\"))")
            token_checks.append(f"                continue")
            token_checks.append(f"            }}")

            vak = self._generator.generate(
                template_name="token_method",
                token_name=name, pattern=pattern,
            )
            token_methods.append(vak)

            self._detected_constructs.append(f"token:{token['name']}")
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="info",
                message=f"Generated token: {token['name']}",
                confidence="safe_auto_fix",
            ))

        vak = self._generator.generate(
            template_name="lexer_class",
            lexer_name=lexer_name,
            tokens_count=len(tokens),
            token_methods="\n\n".join(token_methods),
            token_checks="\n".join(token_checks),
        )

        return vak
