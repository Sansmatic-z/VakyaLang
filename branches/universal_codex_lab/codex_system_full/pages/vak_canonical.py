"""
Pipeline Page: Vak Canonical.

Vak as the canonical target language for the pipeline:
- Canonical Vak source generation
- Vak syntax validation
- Vak module structure
- Vak standard library references

*Visionary RM (Raj Mitra)* ⚡
"""
from __future__ import annotations

import re
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage


# Vak built-in keywords
_VAK_KEYWORDS = {
    "कर्म",       # function
    "श्रेणी",      # class
    "परिवर्तनी",   # variable
    "लौटाओ",      # return
    "छापो",       # print
    "मानचित्र",    # map/dictionary
    "क्षेत्र",      # field
    "सूची",        # list
    "समूह",        # set
    "पूर्णांक",     # integer
    "दशमलव",      # decimal/float
    "पाठ",         # text/string
    "बूलियन",      # boolean
    "अपरिभाषित",   # undefined
    "सत्य",        # true
    "असत्य",       # false
    "रिक्त",        # void/null
    "अक्षर",        # char
    "गणना",        # enum
    "प्रमेय",       # theorem
    "प्रमाण",       # proof
    "सिद्ध",        # proven
    "यदि",          # if
    "अन्यथा",       # else
    "जबतक",        # while
    "केलिए",       # for
    "प्रत्येक",     # each
    "टूटो",         # break
    "जारी",         # continue
}


class VakCanonicalCodexPage(CodexPage):
    """Vak as the canonical target language."""
    name = "vak_canonical"
    description = "Vak canonical target language page"
    priority = 75
    kind = "vak_canonical"
    chapter = "compatibility"
    chapter_title = "Old-Language Compatibility Layers"
    chapter_order = 75
    capabilities = ("vak", "canonical", "validate", "module", "stdlib")
    emits_vak = True
    extensions = ("vak", "vakc")
    max_fixpoint_passes = 1

    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        """Check if source is Vak or Vak-compatible."""
        score = 0
        keywords_found = 0

        for keyword in _VAK_KEYWORDS:
            if keyword in source:
                score += 10
                keywords_found += 1

        if filename and filename.endswith((".vak", ".vakc")):
            score += 30

        if keywords_found >= 1:
            return CodexPageProbe(
                self.name, min(score, 90),
                f"Vak code detected ({keywords_found} keywords)",
            )
        return CodexPageProbe(self.name, 0, "not Vak code")

    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        diagnostics: list[CodexDiagnostic] = []
        metadata: dict[str, Any] = {}

        # Validate Vak syntax
        syntax_errors = self._validate_syntax(source)
        metadata["syntax_errors"] = syntax_errors
        metadata["keywords_used"] = self._detect_keywords(source)
        metadata["structure"] = self._analyze_structure(source)

        # Build canonical Vak output
        output = self._canonicalize(source)

        if syntax_errors:
            diagnostics.append(CodexDiagnostic(
                page=self.name, level="warning",
                message=f"Syntax issues: {'; '.join(syntax_errors[:3])}",
                confidence="suggest_only",
            ))
        else:
            diagnostics.append(CodexDiagnostic(
                page=self.name, level="info",
                message="Vak syntax valid",
                confidence="verified",
            ))

        return CodexResult(
            page=self.name, original_source=source, source=output,
            transformed=source != output,
            confidence="verified" if not syntax_errors else "suggest_only",
            diagnostics=tuple(diagnostics), metadata=metadata,
        )

    def _validate_syntax(self, source: str) -> list[str]:
        """Validate Vak syntax."""
        errors: list[str] = []
        brace_depth = 0
        paren_depth = 0

        for i, line in enumerate(source.split("\n"), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            for ch in stripped:
                if ch == "{":
                    brace_depth += 1
                elif ch == "}":
                    brace_depth -= 1
                    if brace_depth < 0:
                        errors.append(f"Line {i}: Unmatched '}}'")
                        brace_depth = 0
                elif ch == "(":
                    paren_depth += 1
                elif ch == ")":
                    paren_depth -= 1
                    if paren_depth < 0:
                        errors.append(f"Line {i}: Unmatched ')'")
                        paren_depth = 0

        if brace_depth != 0:
            errors.append(f"Unmatched braces (depth: {brace_depth})")
        if paren_depth != 0:
            errors.append(f"Unmatched parentheses (depth: {paren_depth})")

        return errors

    def _detect_keywords(self, source: str) -> dict[str, int]:
        """Detect which Vak keywords are used."""
        found: dict[str, int] = {}
        for keyword in _VAK_KEYWORDS:
            count = len(re.findall(re.escape(keyword), source))
            if count > 0:
                found[keyword] = count
        return found

    def _analyze_structure(self, source: str) -> dict[str, Any]:
        """Analyze Vak source structure."""
        functions: list[str] = []
        classes: list[str] = []
        variables: list[str] = []

        for line in source.split("\n"):
            stripped = line.strip()
            m = re.match(r"कर्म\s+(\w+)", stripped)
            if m:
                functions.append(m.group(1))
            m = re.match(r"श्रेणी\s+(\w+)", stripped)
            if m:
                classes.append(m.group(1))
            m = re.match(r"परिवर्तनी\s+(\w+)", stripped)
            if m:
                variables.append(m.group(1))

        return {
            "functions": functions,
            "classes": classes,
            "variables": variables,
        }

    def _canonicalize(self, source: str) -> str:
        """Canonicalize Vak source (normalize formatting, remove excess blanks)."""
        lines: list[str] = []
        prev_blank = False

        for line in source.split("\n"):
            stripped = line.rstrip()
            is_blank = not stripped.strip()

            # Skip consecutive blank lines
            if is_blank and prev_blank:
                continue
            prev_blank = is_blank

            lines.append(stripped)

        # Remove trailing blank lines
        while lines and not lines[-1].strip():
            lines.pop()

        # Add header if not present
        if not lines or not lines[0].startswith("#"):
            header = [
                "# Canonical Vak Source",
                "# Generated by Codex Pipeline",
                "",
            ]
            lines = header + lines

        return "\n".join(lines)
