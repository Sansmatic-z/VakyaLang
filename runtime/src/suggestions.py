from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from .tokens import KEYWORDS


@dataclass(frozen=True)
class Suggestion:
    """A single user-facing repair suggestion."""

    kind: str
    message_hi: str
    message_en: str
    fix: Optional[str]
    confidence: float


def _levenshtein(s1: str, s2: str) -> int:
    """Wagner-Fischer edit distance using O(m) extra space."""
    if len(s1) < len(s2):
        return _levenshtein(s2, s1)
    if not s2:
        return len(s1)
    previous = list(range(len(s2) + 1))
    for i, left_char in enumerate(s1):
        current = [i + 1]
        for j, right_char in enumerate(s2):
            cost = 0 if left_char == right_char else 1
            current.append(
                min(
                    current[j] + 1,
                    previous[j + 1] + 1,
                    previous[j] + cost,
                )
            )
        previous = current
    return previous[-1]


# Single-codepoint Devanagari confusables only. Multi-codepoint conjuncts
# need grapheme-aware handling and are intentionally excluded here.
DEVANAGARI_CONFUSABLES: Dict[str, tuple[str, ...]] = {
    "ण": ("न",),
    "न": ("ण",),
    "ष": ("श",),
    "श": ("ष",),
    "ठ": ("ट",),
    "ट": ("ठ",),
    "ढ": ("ड",),
    "ड": ("ढ",),
    "थ": ("त",),
    "त": ("थ",),
    "ध": ("द",),
    "द": ("ध",),
    "छ": ("च",),
    "च": ("छ",),
    "झ": ("ज",),
    "ज": ("झ",),
    "फ": ("प",),
    "प": ("फ",),
    "भ": ("ब",),
    "ब": ("भ",),
    "घ": ("ग",),
    "ग": ("घ",),
    "ड़": ("ड",),
    "ढ़": ("ढ",),
    "ृ": ("ु",),
    "ु": ("ृ",),
    "ं": ("ँ",),
    "ँ": ("ं",),
}

_NAME_ERROR_RE = re.compile(r"Name not found: (.+)")
_FUNCTION_ERROR_RE = re.compile(r"Function not found(?::| in module:)\s*(.+)")
_METHOD_ERROR_RE = re.compile(r"Method '(.+?)' not found")
_TOO_MANY_ARGS_RE = re.compile(
    r"Too many positional arguments: expected at most (\d+), got (\d+)"
)
_MISSING_ARG_RE = re.compile(r"Missing required argument: (.+)")
_UNEXPECTED_KWARG_RE = re.compile(r"Unexpected keyword argument: (.+)")
_TYPE_ERROR_RE = re.compile(
    r"प्रकार त्रुटि: (.+?) के लिए '(.+?)' अपेक्षित था, लेकिन '(.+?)' मिला"
)
_VIBHAKTI_TYPE_ERROR_RE = re.compile(
    r"विभक्ति प्रकार त्रुटि(?: \(Vibhakti Type Error\))?: (.+?) के लिए '(.+?)' अपेक्षित था, लेकिन '(.+?)' मिला"
)
_CONTRADICTION_RE = re.compile(
    r"Contradiction detected: (.+?) conflicts with (.+?)(?:\)|$)"
)
_MUTATION_VIOLATION_RE = re.compile(r"विभक्ति त्रुटि: (.+?) को परिवर्तित नहीं")

_TYPE_ALIASES: Dict[str, str] = {
    "संख्या": "int",
    "int": "int",
    "दशमलव": "float",
    "float": "float",
    "str": "str",
    "शब्द": "str",
    "पाठ": "str",
    "bool": "bool",
    "बूलियन": "bool",
    "सूची": "list",
    "list": "list",
    "शब्दकोश": "dict",
    "dict": "dict",
    "समुच्चय": "set",
    "set": "set",
    "tuple": "tuple",
    "टपल": "tuple",
    "none": "none",
    "शून्य": "none",
    "NoneType": "none",
}

TYPE_CONVERSION_HINTS: Dict[tuple[str, str], tuple[str, str, str]] = {
    ("int", "str"): ("संख्या(मान)", "तार से संख्या", "string to integer"),
    ("int", "float"): ("संख्या(मान)", "दशमलव से पूर्ण संख्या", "float to integer"),
    ("int", "bool"): ("संख्या(मान)", "सत्य/असत्य से संख्या", "boolean to integer"),
    ("float", "int"): ("दशमलव(मान)", "पूर्ण संख्या से दशमलव", "integer to float"),
    ("float", "str"): ("दशमलव(मान)", "संख्यात्मक तार से दशमलव", "numeric string to float"),
    ("str", "int"): ("पाठ_कर(मान)", "संख्या से पाठ", "integer to string"),
    ("str", "float"): ("पाठ_कर(मान)", "दशमलव से पाठ", "float to string"),
    ("str", "bool"): ("पाठ_कर(मान)", "सत्य/असत्य से पाठ", "boolean to string"),
    ("str", "list"): ("संयोग(मान)", "सूची तत्वों को जोड़कर पाठ", "join list elements into string"),
    ("list", "str"): ("विभाजन(मान)", "पाठ को सूची में विभाजित करें", "split string into list"),
    ("list", "tuple"): ("list(मान)", "टपल को सूची में बदलें", "tuple to list"),
    ("list", "set"): ("list(मान)", "समुच्चय को सूची में बदलें", "set to list"),
    ("tuple", "list"): ("tuple(मान)", "सूची को टपल में बदलें", "list to tuple"),
    ("bool", "str"): ("मान != शून्य", "रिक्त पाठ की जाँच करें", "check for non-empty string"),
    ("bool", "int"): ("मान != ०", "शून्य-तुलना करें", "compare against zero"),
    ("bool", "list"): ("दीर्घता(मान) > ०", "रिक्त सूची की जाँच करें", "check for non-empty list"),
}

SYNTAX_FIX_PATTERNS: tuple[tuple[str, str, str, float], ...] = (
    (
        r"अपेक्षित COLON",
        "ब्लॉक शीर्षक के बाद कोलन (:) जोड़ें",
        "Add a colon (:) after the block header",
        0.8,
    ),
    (
        r"सिद्धि के लिए प्रमाण: ब्लॉक आवश्यक है",
        "सिद्धि: के नीचे इंडेंटेड प्रमाण: ब्लॉक जोड़ें",
        "Add an indented प्रमाण: block under सिद्धि:",
        0.95,
    ),
    (
        r"सिद्धि के भीतर प्रमाण: अपेक्षित है",
        "सिद्धि ब्लॉक में प्रमाण: खंड जोड़ें",
        "Add a प्रमाण: section inside the सिद्धि block",
        0.95,
    ),
    (
        r"असंगत इंडेंटेशन",
        "इंडेंटेशन को समान रखें; एक ही ब्लॉक में अलग-अलग स्तर न मिलाएँ",
        "Keep indentation consistent within the same block",
        0.85,
    ),
    (
        r"RPAREN",
        'कर्म/यदि/यावत् जैसे ब्लॉक शीर्षकों में कोष्ठक के बजाय ":" उपयोग करें',
        'Use ":" rather than parentheses for कर्म/यदि/यावत् block headers',
        0.6,
    ),
)

FALLBACK_BUILTIN_NAMES: Set[str] = {
    "मुद्रय",
    "print",
    "पाठ_कर",
    "str",
    "दीर्घता",
    "len",
    "संख्या",
    "int",
    "दशमलव",
    "float",
    "bool",
    "प्रकार",
    "type",
    "परास",
    "range",
    "list",
    "dict",
    "set",
    "tuple",
    "संयोग",
    "विभाजन",
    "वर्गमूल",
    "परिभाषय",
    "दावा",
    "नियम",
    "मूल्यांकन",
    "सिद्ध_है",
    "धर्म_निर्माण",
    "धर्म_जाँच",
    "कारक_हस्ताक्षर",
    "कारक_जाँच",
    "न्याय_सिद्धि_रिपोर्ट",
    "पदार्थ_वर्गीकरण",
}


def _extract_name_from_error(message: str) -> Optional[str]:
    for pattern in (
        _NAME_ERROR_RE,
        _FUNCTION_ERROR_RE,
        _METHOD_ERROR_RE,
        _MISSING_ARG_RE,
        _UNEXPECTED_KWARG_RE,
    ):
        match = pattern.search(message)
        if match:
            return match.group(1).strip()
    return None


def _extract_type_info_from_error(message: str) -> Optional[tuple[str, str, str]]:
    for pattern in (_TYPE_ERROR_RE, _VIBHAKTI_TYPE_ERROR_RE):
        match = pattern.search(message)
        if match:
            return match.group(1).strip(), match.group(2).strip(), match.group(3).strip()
    return None


def _extract_contradiction_from_error(message: str) -> Optional[tuple[str, str]]:
    match = _CONTRADICTION_RE.search(message)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None


def suggest_spelling(
    name: str,
    candidates: Set[str],
    *,
    max_distance: int = 3,
    max_count: int = 3,
) -> List[Suggestion]:
    scored: List[tuple[int, float, str]] = []
    for candidate in candidates:
        if candidate == name:
            continue
        distance = _levenshtein(name, candidate)
        if 0 < distance <= max_distance:
            confidence = round(1.0 - (distance / (max_distance + 1)), 2)
            scored.append((distance, confidence, candidate))
    scored.sort()
    return [
        Suggestion(
            kind="spelling",
            message_hi=f'क्या आप "{candidate}" लिखना चाहते थे?',
            message_en=f'Did you mean "{candidate}"?',
            fix=candidate,
            confidence=confidence,
        )
        for distance, confidence, candidate in scored[:max_count]
    ]


def suggest_confusable(
    name: str,
    candidates: Set[str],
    *,
    max_count: int = 3,
) -> List[Suggestion]:
    results: List[Suggestion] = []
    seen: Set[str] = set()
    characters = list(name)
    for index, character in enumerate(characters):
        for replacement in DEVANAGARI_CONFUSABLES.get(character, ()):
            candidate = "".join(characters[:index] + [replacement] + characters[index + 1 :])
            if candidate in candidates and candidate not in seen:
                seen.add(candidate)
                results.append(
                    Suggestion(
                        kind="confusable",
                        message_hi=(
                            f'देवनागरी भ्रम: "{character}" के स्थान पर "{replacement}" होना चाहिए। '
                            f'क्या आप "{candidate}" चाहते थे?'
                        ),
                        message_en=(
                            f'Devanagari confusable: "{character}" likely should be "{replacement}". '
                            f'Did you mean "{candidate}"?'
                        ),
                        fix=candidate,
                        confidence=0.85,
                    )
                )
            if len(results) >= max_count:
                return results
    return results


def suggest_type_conversion(context: str, expected: str, actual: str) -> List[Suggestion]:
    expected_norm = _TYPE_ALIASES.get(expected, expected.lower())
    actual_norm = _TYPE_ALIASES.get(actual, actual.lower())
    if expected_norm == actual_norm:
        return []
    hint = TYPE_CONVERSION_HINTS.get((expected_norm, actual_norm))
    if hint is None:
        return [
            Suggestion(
                kind="type_convert",
                message_hi=f'"{expected}" और "{actual}" सीधे संगत नहीं हैं',
                message_en=f'"{expected}" and "{actual}" are not directly compatible',
                fix=None,
                confidence=0.45,
            )
        ]
    fix, hi_reason, en_reason = hint
    return [
        Suggestion(
            kind="type_convert",
            message_hi=f'{context} के लिए {fix} आज़माएँ ({hi_reason})',
            message_en=f'Try {fix} for {context} ({en_reason})',
            fix=fix,
            confidence=0.9,
        )
    ]


def suggest_contradiction_fix(left: str, right: str) -> List[Suggestion]:
    suggestions = [
        Suggestion(
            kind="contradiction",
            message_hi=(
                f'विरोध: "{left}" और "{right}" एक साथ सत्य नहीं हो सकते। '
                "विरोधी दावा या नियम की समीक्षा करें।"
            ),
            message_en=(
                f'Contradiction: "{left}" and "{right}" cannot both hold. '
                "Review the conflicting assertion or rule."
            ),
            fix=None,
            confidence=1.0,
        )
    ]
    for prefix in ("NOT ", "न ", "नहीं "):
        if left.startswith(prefix) and left[len(prefix) :] == right:
            suggestions.append(
                Suggestion(
                    kind="contradiction",
                    message_hi=f'"{right}" और उसका निषेध दोनों दर्ज हैं; एक हटाएँ।',
                    message_en=f'Both "{right}" and its negation are asserted; remove one.',
                    fix=None,
                    confidence=1.0,
                )
            )
            break
        if right.startswith(prefix) and right[len(prefix) :] == left:
            suggestions.append(
                Suggestion(
                    kind="contradiction",
                    message_hi=f'"{left}" और उसका निषेध दोनों दर्ज हैं; एक हटाएँ।',
                    message_en=f'Both "{left}" and its negation are asserted; remove one.',
                    fix=None,
                    confidence=1.0,
                )
            )
            break
    return suggestions


def suggest_syntax_fix(message: str) -> List[Suggestion]:
    results: List[Suggestion] = []
    for pattern, message_hi, message_en, confidence in SYNTAX_FIX_PATTERNS:
        if re.search(pattern, message):
            results.append(
                Suggestion(
                    kind="syntax",
                    message_hi=message_hi,
                    message_en=message_en,
                    fix=None,
                    confidence=confidence,
                )
            )
    return results


class CognitiveFixer:
    """Analyze live Vak errors and produce actionable repair suggestions."""

    def _collect_available_names(self, context: Dict[str, Any]) -> Set[str]:
        names: Set[str] = set(KEYWORDS.keys())
        names.update(FALLBACK_BUILTIN_NAMES)

        builtins = context.get("builtins")
        if isinstance(builtins, dict):
            names.update(str(key) for key in builtins.keys())

        globals_dict = context.get("globals")
        if isinstance(globals_dict, dict):
            names.update(str(key) for key in globals_dict.keys())

        frame = context.get("frame")
        if frame is not None:
            bytecode = getattr(frame, "bytecode", None)
            var_names = getattr(bytecode, "var_names", None)
            if var_names:
                names.update(str(name) for name in var_names)
            functions = getattr(bytecode, "functions", None)
            if isinstance(functions, dict):
                names.update(str(name) for name in functions.keys())
            closure_env = getattr(frame, "closure_env", None)
            if isinstance(closure_env, dict):
                names.update(str(name) for name in closure_env.keys())

        return {
            name
            for name in names
            if name
            and not name.startswith("__")
            and not name.startswith("<")
            and name != "UNSET"
        }

    def analyze(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Suggestion]:
        if context is None:
            context = {}

        message = str(error)
        suggestions: List[Suggestion] = []

        name = _extract_name_from_error(message)
        if name:
            available_names = self._collect_available_names(context)
            suggestions.extend(suggest_confusable(name, available_names))
            suggestions.extend(suggest_spelling(name, available_names))

        type_info = _extract_type_info_from_error(message)
        if type_info:
            suggestions.extend(suggest_type_conversion(*type_info))

        contradiction = _extract_contradiction_from_error(message)
        if contradiction:
            suggestions.extend(suggest_contradiction_fix(*contradiction))

        mutation_match = _MUTATION_VIOLATION_RE.search(message)
        if mutation_match:
            param_name = mutation_match.group(1)
            suggestions.append(
                Suggestion(
                    kind="hint",
                    message_hi=(
                        f'विभक्ति नियम: "{param_name}" को परिवर्तित नहीं किया जा सकता। '
                        "यदि परिवर्तन चाहिए तो पैरामीटर की भूमिका बदलें।"
                    ),
                    message_en=(
                        f'Vibhakti rule: "{param_name}" is read-only. '
                        "Change the parameter role if mutation is required."
                    ),
                    fix=None,
                    confidence=0.95,
                )
            )

        too_many = _TOO_MANY_ARGS_RE.search(message)
        if too_many:
            expected_count, actual_count = too_many.groups()
            suggestions.append(
                Suggestion(
                    kind="hint",
                    message_hi=f"तर्क अधिक हैं: {expected_count} अपेक्षित, {actual_count} प्राप्त",
                    message_en=f"Too many arguments: expected {expected_count}, got {actual_count}",
                    fix=None,
                    confidence=0.9,
                )
            )

        suggestions.extend(suggest_syntax_fix(message))

        unique: List[Suggestion] = []
        seen: Set[tuple[str, Optional[str], str]] = set()
        for suggestion in suggestions:
            if suggestion.confidence < 0.4:
                continue
            key = (suggestion.kind, suggestion.fix, suggestion.message_hi)
            if key in seen:
                continue
            seen.add(key)
            unique.append(suggestion)
        unique.sort(key=lambda item: item.confidence, reverse=True)
        return unique[:5]


def format_suggestions(suggestions: List[Suggestion]) -> str:
    if not suggestions:
        return ""
    lines = ["   सुझाव (Suggestions):"]
    for suggestion in suggestions:
        marker = "✓" if suggestion.confidence >= 0.8 else "?"
        fix_text = f" -> {suggestion.fix}" if suggestion.fix else ""
        lines.append(f"    {marker} {suggestion.message_hi}{fix_text}")
    return "\n".join(lines)
