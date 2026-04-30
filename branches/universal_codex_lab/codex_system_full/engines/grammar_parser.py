"""
Grammar Parser Engine — EBNF/PEG grammar parsing and validation.

Provides:
- GrammarRule dataclass for individual production rules
- GrammarParser for parsing EBNF/PEG grammar strings
- Validation and normalization of grammar definitions
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GrammarRule:
    """Represents a single grammar production rule."""
    name: str
    alternatives: tuple[str, ...]
    is_terminal: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def payload(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "alternatives": list(self.alternatives),
            "is_terminal": self.is_terminal,
            "metadata": dict(self.metadata),
        }


class ParseError(Exception):
    """Raised when grammar parsing fails."""
    def __init__(self, message: str, line: int = 0, column: int = 0):
        super().__init__(message)
        self.line = line
        self.column = column


class GrammarParser:
    """
    Parses EBNF and PEG grammar definitions into structured rule sets.

    EBNF syntax supported:
        expr  = term (('+' | '-') term)* ;
        term  = factor (('*' | '/') factor)* ;
        factor = INT | '(' expr ')' ;
        INT   = [0-9]+ ;

    PEG syntax supported:
        expr  <- term (('+ ' / '- ') term)*
        term  <- factor (('* ' / '/ ') factor)*
        factor<- INT / '(' expr ')'
        INT   <- [0-9]+
    """

    _EBNF_RULE_RE = re.compile(
        r'^\s*(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?P<body>.+?)\s*;\s*$'
    )
    _PEG_RULE_RE = re.compile(
        r'^\s*(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\s*<-\s*(?P<body>.+?)\s*$'
    )
    _TERMINAL_RE = re.compile(r'^[A-Z_]+$')

    def __init__(self) -> None:
        self._rules: list[GrammarRule] = []
        self._errors: list[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def parse(self, grammar_text: str, *, dialect: str = "ebnf") -> tuple[GrammarRule, ...]:
        """
        Parse a grammar definition string into a tuple of GrammarRule objects.

        Parameters
        ----------
        grammar_text : str
            The raw grammar text in EBNF or PEG format.
        dialect : str
            Either "ebnf" (default) or "peg".

        Returns
        -------
        tuple[GrammarRule, ...]
            Parsed grammar rules.

        Raises
        ------
        ParseError
            If the grammar text cannot be parsed.
        """
        self._rules = []
        self._errors = []

        pattern = self._PEG_RULE_RE if dialect == "peg" else self._EBNF_RULE_RE

        for line_num, line in enumerate(grammar_text.strip().splitlines(), start=1):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("//"):
                continue  # skip blanks and comments

            m = pattern.match(line)
            if not m:
                self._errors.append(f"Line {line_num}: cannot parse rule: {line!r}")
                continue

            name = m.group("name")
            body = m.group("body")
            alternatives = self._split_alternatives(body)
            is_terminal = bool(self._TERMINAL_RE.match(name))

            self._rules.append(GrammarRule(
                name=name,
                alternatives=alternatives,
                is_terminal=is_terminal,
                metadata={"line": line_num, "dialect": dialect},
            ))

        if self._errors:
            raise ParseError(
                f"Grammar parse failed with {len(self._errors)} error(s):\n"
                + "\n".join(f"  • {e}" for e in self._errors),
                line=1,
            )

        return tuple(self._rules)

    def parse_file(self, path: str, *, dialect: str = "ebnf") -> tuple[GrammarRule, ...]:
        """Parse a grammar file."""
        from pathlib import Path
        text = Path(path).read_text(encoding="utf-8")
        return self.parse(text, dialect=dialect)

    def to_ebnf(self, rules: tuple[GrammarRule, ...]) -> str:
        """Serialize rules back to EBNF text."""
        lines: list[str] = []
        for rule in rules:
            body = " | ".join(rule.alternatives)
            lines.append(f"{rule.name} = {body} ;")
        return "\n".join(lines)

    def to_peg(self, rules: tuple[GrammarRule, ...]) -> str:
        """Serialize rules back to PEG text."""
        lines: list[str] = []
        for rule in rules:
            body = " / ".join(rule.alternatives)
            lines.append(f"{rule.name} <- {body}")
        return "\n".join(lines)

    @property
    def errors(self) -> list[str]:
        return list(self._errors)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _split_alternatives(body: str) -> tuple[str, ...]:
        """Split a rule body by | or / (EBNF/PEG alternative separators)."""
        # Respect parentheses and brackets grouping
        alternatives: list[str] = []
        current: list[str] = []
        depth = 0
        for ch in body:
            if ch in "([":
                depth += 1
                current.append(ch)
            elif ch in ")]":
                depth -= 1
                current.append(ch)
            elif ch in "|/" and depth == 0:
                alt = "".join(current).strip()
                if alt:
                    alternatives.append(alt)
                current = []
            else:
                current.append(ch)
        tail = "".join(current).strip()
        if tail:
            alternatives.append(tail)
        return tuple(alternatives) if alternatives else (body.strip(),)
