"""
Pattern Matcher Engine — Pattern matching and registry for code patterns.

Provides:
- PatternMatch dataclass for match results
- PatternMatcher for matching code against pattern templates
- PatternRegistry for centralized pattern storage and lookup
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class PatternMatch:
    """Result of a pattern match."""
    pattern_name: str
    score: float  # 0.0 - 1.0 confidence
    captures: dict[str, str]  # Named capture groups
    line: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def payload(self) -> dict[str, Any]:
        return {
            "pattern_name": self.pattern_name,
            "score": self.score,
            "captures": dict(self.captures),
            "line": self.line,
            "metadata": dict(self.metadata),
        }


@dataclass
class PatternEntry:
    """A registered pattern in the registry."""
    name: str
    description: str
    category: str  # "design", "algorithm", "architecture", "domain"
    regex: str | None = None
    template: str | None = None
    transform: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    _compiled_regex: re.Pattern | None = field(default=None, repr=False)

    def compile_regex(self) -> re.Pattern | None:
        if self.regex is None:
            return None
        if self._compiled_regex is None:
            object.__setattr__(self, "_compiled_regex", re.compile(self.regex, re.MULTILINE | re.DOTALL))
        return self._compiled_regex


class PatternMatcher:
    """
    Matches code against registered patterns.

    Usage:
        registry = PatternRegistry()
        registry.register(...)
        matcher = PatternMatcher(registry)
        matches = matcher.match(code)
    """

    def __init__(self, registry: PatternRegistry | None = None):
        self._registry = registry or PatternRegistry()
        self._custom_matchers: list[tuple[str, Callable[[str], list[PatternMatch]]]] = []

    def match(self, source: str, *, category: str | None = None) -> list[PatternMatch]:
        """
        Match source code against all registered patterns.

        Parameters
        ----------
        source : str
            The source code to match.
        category : str | None
            If provided, only match patterns in this category.

        Returns
        -------
        list[PatternMatch]
            All matches sorted by score descending.
        """
        results: list[PatternMatch] = []

        for entry in self._registry.list_patterns(category=category):
            compiled = entry.compile_regex()
            if compiled is not None:
                for m in compiled.finditer(source):
                    line = source[:m.start()].count("\n") + 1
                    results.append(PatternMatch(
                        pattern_name=entry.name,
                        score=self._score_match(m, source),
                        captures=m.groupdict(),
                        line=line,
                        metadata={"category": entry.category, "description": entry.description},
                    ))

        # Also run custom matchers
        if category is None:
            for name, func in self._custom_matchers:
                results.extend(func(source))

        results.sort(key=lambda m: (-m.score, m.line))
        return results

    def match_one(self, source: str, pattern_name: str) -> PatternMatch | None:
        """Match against a single named pattern."""
        entry = self._registry.get(pattern_name)
        if entry is None:
            return None
        compiled = entry.compile_regex()
        if compiled is None:
            return None
        m = compiled.search(source)
        if not m:
            return None
        return PatternMatch(
            pattern_name=pattern_name,
            score=self._score_match(m, source),
            captures=m.groupdict(),
            line=source[:m.start()].count("\n") + 1,
            metadata={"category": entry.category, "description": entry.description},
        )

    def register_custom_matcher(self, name: str, func: Callable[[str], list[PatternMatch]]) -> None:
        """Register a custom matching function."""
        self._custom_matchers.append((name, func))

    def load_from_json(self, path: str | Path) -> None:
        """Load patterns from a JSON file into the registry."""
        self._registry.load_from_json(path)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    @staticmethod
    def _score_match(m: re.Match, source: str) -> float:
        """Heuristic score based on match coverage and specificity."""
        total_lines = source.count("\n") + 1
        match_lines = source[m.start():m.end()].count("\n") + 1
        coverage = match_lines / max(total_lines, 1)
        specificity = len(m.groups()) * 0.1 if m.groups() else 0.0
        return min(1.0, 0.5 + coverage * 0.3 + specificity)


class PatternRegistry:
    """
    Centralized registry for code patterns.

    Supports:
    - Programmatic registration
    - JSON loading/saving
    - Category-based listing
    """

    def __init__(self):
        self._patterns: dict[str, PatternEntry] = {}

    def register(
        self,
        name: str,
        *,
        description: str = "",
        category: str = "general",
        regex: str | None = None,
        template: str | None = None,
        transform: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register a new pattern."""
        if name in self._patterns:
            raise ValueError(f"Pattern already registered: {name}")
        self._patterns[name] = PatternEntry(
            name=name,
            description=description,
            category=category,
            regex=regex,
            template=template,
            transform=transform,
            metadata=metadata or {},
        )

    def get(self, name: str) -> PatternEntry | None:
        return self._patterns.get(name)

    def remove(self, name: str) -> None:
        self._patterns.pop(name, None)

    def list_patterns(self, *, category: str | None = None) -> list[PatternEntry]:
        if category is None:
            return list(self._patterns.values())
        return [p for p in self._patterns.values() if p.category == category]

    def list_categories(self) -> list[str]:
        return sorted({p.category for p in self._patterns.values()})

    def load_from_json(self, path: str | Path) -> None:
        """
        Load patterns from a JSON file.

        Expected JSON format:
        {
            "patterns": [
                {
                    "name": "...",
                    "description": "...",
                    "category": "...",
                    "regex": "...",
                    "template": "...",
                    "transform": "...",
                    "metadata": {}
                }
            ]
        }
        """
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        for p in data.get("patterns", []):
            self.register(
                name=p["name"],
                description=p.get("description", ""),
                category=p.get("category", "general"),
                regex=p.get("regex"),
                template=p.get("template"),
                transform=p.get("transform"),
                metadata=p.get("metadata"),
            )

    def save_to_json(self, path: str | Path) -> None:
        """Save all patterns to a JSON file."""
        data = {
            "patterns": [
                {
                    "name": e.name,
                    "description": e.description,
                    "category": e.category,
                    "regex": e.regex,
                    "template": e.template,
                    "transform": e.transform,
                    "metadata": e.metadata,
                }
                for e in self._patterns.values()
            ]
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def __len__(self) -> int:
        return len(self._patterns)

    def __contains__(self, name: str) -> bool:
        return name in self._patterns
