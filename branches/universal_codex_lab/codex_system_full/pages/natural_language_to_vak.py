"""
Phase 1: Natural Language → Vak Translator Codex Page.

Translates natural English descriptions of algorithms/programs into VakyaLang code by:
1. Parsing intent from English descriptions
2. Mapping common programming phrases to code constructs
3. Generating structured Vak code from understood intent
4. Supporting imperative, descriptive, and query-based input
"""
from __future__ import annotations

import re
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from .utils import _overall_confidence
from ..vak_surface import normalize_vak_surface


# ------------------------------------------------------------------
# Natural language patterns → Vak code templates
# ------------------------------------------------------------------
_NL_PATTERNS: list[tuple[re.Pattern, str, str]] = []


def _register_pattern(regex: str, construct: str, template: str) -> None:
    _NL_PATTERNS.append((re.compile(regex, re.IGNORECASE), construct, template))


# Function definition patterns
_register_pattern(
    r"(?:create|make|define|write|build)\s+(?:a\s+)?(?:function|method|procedure|routine)\s+(?:(?:called|named)\s+)?`?(\w+)`?",
    "function",
    "कर्म {name}({params}):\n    # {description}\n    कोई_कार्य_नहीं"
)
_register_pattern(
    r"(?:function|method|procedure)\s+(?:(?:called|named)\s+)?`?(\w+)`?\s+(?:that|which|to)\s+(.+)",
    "function",
    "कर्म {name}({params}):\n    # {description}\n    कोई_कार्य_नहीं"
)

# Variable patterns
_register_pattern(
    r"(?:create|make|define|declare)\s+(?:a\s+)?(?:variable|counter|flag)\s+(?:(?:called|named)\s+)?`?(\w+)`?",
    "variable",
    "चर {name} = शून्य"
)
_register_pattern(
    r"(?:let|set)\s+(\w+)\s+(?:be|to|as)\s+(.+)",
    "variable",
    "चर {name} = {value}"
)

# Loop patterns
_register_pattern(
    r"(?:for|iterate over|go through|loop through)\s+(?:each|every|all\s+)?(\w+)\s+(?:in|from|of)\s+(\w+)",
    "loop",
    "प्रत्येक {var} अन्तर्गत {iterable}:\n    # process {var}\n    कोई_कार्य_नहीं"
)
_register_pattern(
    r"(?:while|as long as|keep)\s+(.+?)\s*(?:,|\.|do|then|$)",
    "loop",
    "यावत् ({condition}):\n    # body\n    कोई_कार्य_नहीं"
)
_register_pattern(
    r"(?:repeat|do)\s+(?:this\s+)?(.+?)\s+(?:until|while not)\s+(.+)",
    "loop",
    "# repeat until\nयावत् (न ({condition})):\n    # {action}\n    कोई_कार्य_नहीं"
)

# Conditional patterns
_register_pattern(
    r"if\s+(.+?)\s+(?:then|,|\.|$)",
    "conditional",
    "यदि ({condition}):\n    # action\n    कोई_कार्य_नहीं"
)
_register_pattern(
    r"(?:when|whenever)\s+(.+?)\s+(?:,|\.|then|$)",
    "conditional",
    "यदि ({condition}):\n    # action\n    कोई_कार्य_नहीं"
)

# Return patterns
_register_pattern(
    r"(?:return|give back|output|produce)\s+(.+)",
    "return",
    "प्रत्यागच्छ {value}"
)

# Import patterns
_register_pattern(
    r"(?:import|use|load|include)\s+(?:the\s+)?(?:module|library|package\s+)?[`\"']?(\w+)",
    "import",
    'आयात "{module}"'
)

# Print patterns
_register_pattern(
    r"(?:print|display|show|output|write)\s+(.+)",
    "output",
    "मुद्रय({value})"
)

# Sort patterns
_register_pattern(
    r"(?:sort|order|arrange)\s+(\w+)\s+(?:in\s+)?(?:ascending|increasing|increasing)?\s*(?:order)?",
    "sort",
    "{array}.क्रमबद्ध()"
)
_register_pattern(
    r"(?:sort|order|arrange)\s+(\w+)\s+in\s+(?:descending|decreasing)\s*order",
    "sort",
    "{array}.क्रमबद्ध().उलटा()"
)

# Check patterns
_register_pattern(
    r"(?:check|verify|test|determine)\s+if\s+(.+)",
    "conditional",
    "यदि ({condition}):\n    # handle true case\n    कोई_कार्य_नहीं\nअन्यथा:\n    # handle false case\n    कोई_कार्य_नहीं"
)

# Calculate patterns
_register_pattern(
    r"(?:calculate|compute|find)\s+(?:the\s+)?(\w+)\s+(?:of|from)\s+(\w+)",
    "function",
    "कर्म calculate_{what}({data}):\n    # compute {what}\n    प्रत्यागच्छ शून्य"
)

# Search patterns
_register_pattern(
    r"(?:search|find|look for)\s+(\w+)\s+(?:in|within|among)\s+(\w+)",
    "search",
    "प्रत्येक item अन्तर्गत {collection}:\n    यदि item == {target}:\n        प्रत्यागच्छ item"
)

# Add/Remove patterns
_register_pattern(
    r"(?:add|insert|append|push)\s+(\w+)\s+(?:to|into)\s+(\w+)",
    "add",
    "{collection}.जोड़ें({item})"
)
_register_pattern(
    r"(?:remove|delete|pop)\s+(\w+)\s+(?:from)\s+(\w+)",
    "remove",
    "{collection}.हटाएं({item})"
)

# Class patterns
_register_pattern(
    r"(?:create|define|make)\s+(?:a\s+)?class\s+(?:(?:called|named)\s+)?`?(\w+)`?",
    "class",
    "वर्ग {name}:\n    # properties and methods\n    कोई_कार्य_नहीं"
)


class NaturalLanguageToVakCodexPage(CodexPage):
    """Translates natural English descriptions to VakyaLang code."""
    name = "natural_language_to_vak"
    description = "Natural language (English) to Vak translator page"
    priority = 33
    kind = "natural_language"
    chapter = "translators"
    chapter_title = "Language Translators"
    chapter_order = 13
    capabilities = ("translate", "natural_language", "english", "intent", "generate")
    emits_vak = True
    extensions = ("md",)
    max_fixpoint_passes = 3
    max_source_length = 100_000

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._diagnostics: list[CodexDiagnostic] = []
        self._detected_constructs: list[str] = []

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------
    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        if filename and filename.endswith((".md", ".txt", ".nl")):
            return CodexPageProbe(self.name, 70, f"{filename} source path")

        # Check if source looks like natural English describing code
        nl_indicators = [
            r"(?i)\b(create|make|define|write)\b.*\b(function|method|program|algorithm)\b",
            r"(?i)\b(print|display|show|output)\b",
            r"(?i)\b(sort|search|find|check)\b",
            r"(?i)\b(if|when|while|for each)\b.*\b(then|do|process)\b",
            r"(?i)\b(return|give back|output)\b",
            r"(?i)\b(add|remove|insert|delete)\b.*\b(to|from)\b",
            r"(?i)\b(calculate|compute)\b.*\b(of|from)\b",
        ]
        score = 0
        for pattern in nl_indicators:
            if re.search(pattern, source):
                score += 15

        # Must be primarily English (not code)
        english_ratio = self._estimate_english_ratio(source)
        if english_ratio > 0.5 and score >= 15:
            return CodexPageProbe(self.name, min(int(score * english_ratio), 85), "Natural English description detected")
        return CodexPageProbe(self.name, 0, "not a natural language candidate")

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------
    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        self._diagnostics = []
        self._detected_constructs = []

        if len(source) > getattr(self, "max_source_length", 100_000):
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="error",
                message=f"Source too large ({len(source)} bytes, max {getattr(self, 'max_source_length', 100_000)})",
                confidence="do_not_touch",
            ))
            return CodexResult(
                page=self.name, original_source=source, source=source,
                transformed=False, confidence="do_not_touch",
                diagnostics=tuple(self._diagnostics), manifest=self.manifest(),
                metadata={"source_kind": "natural_language", "error": "source_too_large"},
            )

        try:
            vak_code = self._translate_natural_language(source)
            transformed = vak_code != source

            if transformed:
                self._diagnostics.append(CodexDiagnostic(
                    page=self.name, level="info",
                    message="Natural language description translated to Vak",
                    confidence="safe_auto_fix" if len(vak_code) > 10 else "suggest_only",
                ))

            return CodexResult(
                page=self.name,
                original_source=source,
                source=vak_code,
                transformed=transformed,
                confidence=_overall_confidence(self._diagnostics, transformed),
                diagnostics=tuple(self._diagnostics),
                manifest=self.manifest(),
                metadata={
                    "source_kind": "natural_language",
                    "detected_constructs": list(self._detected_constructs),
                    "translation_method": "pattern_matching",
                    "english_ratio": self._estimate_english_ratio(source),
                },
            )
        except Exception as exc:
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="error",
                message=f"Translation error: {exc}",
                confidence="do_not_touch",
            ))
            return CodexResult(
                page=self.name, original_source=source, source=source,
                transformed=False, confidence="do_not_touch",
                diagnostics=tuple(self._diagnostics), manifest=self.manifest(),
                metadata={"source_kind": "natural_language", "error": str(exc)},
            )

    # ------------------------------------------------------------------
    # Translation engine
    # ------------------------------------------------------------------
    def _translate_natural_language(self, source: str) -> str:
        """Translate natural English to Vak code by matching patterns."""
        if not source or not source.strip():
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="warning",
                message="Empty natural language description provided",
                confidence="suggest_only",
            ))
            return ""
        lines = source.strip().split("\n")
        output: list[str] = []
        context: dict[str, str] = {}

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Skip markdown headers that are not code descriptions
            if stripped.startswith("#") and not any(
                re.search(p[0], stripped) for p in _NL_PATTERNS
            ):
                output.append(f"# {stripped.lstrip('#').strip()}")
                continue

            # Skip bullet points that are just descriptions
            if stripped.startswith(("-", "*", "•")):
                text = stripped.lstrip("-*• ").strip()
                output.append(f"# {text}")
                continue

            matched = False
            for pattern, construct, template in _NL_PATTERNS:
                m = pattern.search(stripped)
                if m:
                    self._detected_constructs.append(construct)
                    # Extract named groups or positional groups
                    groups = m.groupdict()
                    # Also capture positional groups
                    for i, g in enumerate(m.groups(), start=1):
                        if g and str(i) not in groups:
                            groups.setdefault(f"group_{i}", g)

                    # Build template substitutions
                    subs: dict[str, str] = {}
                    subs["name"] = groups.get("name", groups.get("group_1", "unknown"))
                    subs["params"] = groups.get("params", "")
                    subs["value"] = groups.get("value", groups.get("group_2", "शून्य"))
                    subs["description"] = groups.get("description", groups.get("group_2", stripped))
                    subs["condition"] = groups.get("condition", groups.get("group_1", "सत्य"))
                    subs["var"] = groups.get("var", groups.get("group_1", "x"))
                    subs["iterable"] = groups.get("iterable", groups.get("group_2", "संग्रह"))
                    subs["module"] = groups.get("module", groups.get("group_1", ""))
                    subs["array"] = groups.get("array", groups.get("group_1", "arr"))
                    subs["collection"] = groups.get("collection", groups.get("group_2", groups.get("group_1", "संग्रह")))
                    subs["item"] = groups.get("item", groups.get("group_1", "item"))
                    subs["target"] = groups.get("target", groups.get("group_1", "target"))
                    subs["action"] = groups.get("action", groups.get("group_1", ""))
                    subs["data"] = groups.get("data", groups.get("group_2", "data"))
                    subs["what"] = groups.get("what", groups.get("group_1", "result"))

                    rendered = template
                    for key, val in subs.items():
                        rendered = rendered.replace(f"{{{key}}}", val)
                    output.append(rendered)
                    context["last_construct"] = construct
                    matched = True
                    break

            if not matched:
                # Treat as a comment or description
                self._diagnostics.append(CodexDiagnostic(
                    page=self.name, level="info",
                    message=f"Unmatched line treated as comment: {stripped[:50]}",
                    confidence="suggest_only",
                ))
                output.append(f"# {stripped}")

        return normalize_vak_surface("\n".join(output))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _estimate_english_ratio(text: str) -> float:
        """Estimate what fraction of text is English vs code-like."""
        if not text:
            return 0.0
        english_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "shall", "can", "need", "dare", "ought",
            "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "as", "into", "through", "during", "before", "after", "above",
            "below", "between", "out", "off", "over", "under", "again",
            "further", "then", "once", "and", "but", "or", "nor", "not",
            "so", "yet", "both", "either", "neither", "each", "every",
            "all", "any", "few", "more", "most", "other", "some", "such",
            "no", "only", "own", "same", "than", "too", "very", "just",
            "because", "if", "when", "where", "while", "how", "what",
            "which", "who", "whom", "this", "that", "these", "those",
            "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
            "you", "your", "yours", "yourself", "he", "him", "his",
            "she", "her", "hers", "it", "its", "they", "them", "their",
            "create", "make", "function", "method", "variable", "return",
            "print", "display", "show", "sort", "search", "find", "check",
            "add", "remove", "insert", "delete", "calculate", "compute",
        }
        words = re.findall(r"\b[a-z]+\b", text.lower())
        if not words:
            return 0.0
        english_count = sum(1 for w in words if w in english_words)
        return english_count / len(words)
