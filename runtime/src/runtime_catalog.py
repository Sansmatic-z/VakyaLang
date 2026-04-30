from __future__ import annotations

from dataclasses import dataclass, replace
import inspect
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class BuiltinSpec:
    name: str
    required_args: int = 0
    max_args: int | None = 0
    keyword_names: tuple[str, ...] = ()
    accepts_varargs: bool = False
    accepts_kwargs: bool = False
    aliases: tuple[str, ...] = ()
    category: str = "core"
    description: str = ""
    source: str = "builtin"
    branch: str | None = None


COMPILED_BUILTIN_ORDER: tuple[str, ...] = (
    "पाठ_कर",
    "str",
    "परास",
    "range",
    "दीर्घता",
    "len",
    "प्रकार",
    "type",
    "संख्या",
    "int",
    "दशमलव",
    "float",
    "मुद्रय",
    "print",
    "पठन",
    "लेखन",
    "खोलो",
    "अस्तित्व",
    "मिटाओ",
    "सूची_निर्देशिका",
    "बनाओ_निर्देशिका",
    "परिवेश_प्राप्त",
    "परिवेश_सेट",
    "प्रणाली_कमांड",
    "मंच",
    "कार्य_निर्देशिका",
    "संयोग",
    "विभाजन",
    "छाँटो",
    "उच्च",
    "निम्न",
    "पूर्णांक_कर",
    "क्रमबद्ध",
    "योग",
    "अधिकतम",
    "न्यूनतम",
    "कुंजियाँ",
    "मान",
    "वर्गमूल",
    "परम",
    "_math_cos",
    "_math_sin",
    "_math_tan",
    "_math_sqrt",
    "_math_abs",
    "_math_floor",
    "_math_ceil",
    "_math_round",
    "_math_degrees",
    "_math_radians",
    "जाल_लाओ",
    "जाल_भेजो",
    "जाल_डाउनलोड",
    "जाल_पुट",
    "जाल_हटाओ",
    "समय",
    "निद्रा",
    "धागा_शुरू",
    "सेट_टाइमआउट",
    "सेट_इंटरवल",
    "क्लियर_टाइमआउट",
    "async_sleep",
    "अतुल्य_अग्रिम",
    "async_next",
    "अतुल्य_समाप्त",
    "async_done",
    "रेगेक्स_खोज",
    "रेगेक्स_बदलो",
    "जेसन_लिखो",
    "जेसन_पढ़ो",
    "परिभाषय",
    "दावा",
    "नियम",
    "मूल्यांकन",
    "सिद्ध_है",
    "पश्च_सिद्ध_है",
    "प्रमाण_लॉग",
    "प्रमाण_सारांश",
    "प्रमाण_स्नैपशॉट",
    "प्रमाण_पुनर्स्थापय",
    "प्रमाण_रीसेट",
    "आत्म_मूल्य",
    "भाव_पढ़ो",
    "अवस्था_पढ़ो",
    "सभी_भाव",
    "सभी_अवस्था",
    "आत्म_इतिहास",
    "आत्म_है",
    "आत्म_भाव",
    "आत्म_अवस्था",
    "आत्म_मूल",
    "_chitra_canvas",
    "_chitra_fill",
    "_chitra_point",
    "_chitra_line",
    "_chitra_circle",
    "_chitra_rect",
    "_chitra_polygon",
    "_chitra_text",
    "_chitra_save",
    "_chitra_load",
    "_chitra_color",
    "_chitra_colors",
    "_chitra_width",
    "_chitra_height",
    "_chitra_pixel_get",
    "_chitra_pixel_set",
    "_chitra_clear",
    "_chitra_text_centered",
    "_chitra_gradient",
    "_chitra_rotate",
    "_chitra_mandala",
    "_chitra_kaleidoscope",
    "प्रदर्शन_विवरण",
    "प्रदर्शन_पाठ",
    "आयात_प्रदर्शन_विवरण",
    "आयात_प्रदर्शन_पाठ",
    "पायथन_आयात",
    "पायथन_चलाओ",
    "पायथन_मूल्यांकन",
    "अक्षर_मान",
)


_MANUAL_SPECS: dict[str, BuiltinSpec] = {
    "मुद्रय": BuiltinSpec(
        "मुद्रय",
        required_args=0,
        max_args=None,
        accepts_varargs=True,
        aliases=("print",),
        category="core",
        description="Vak output printer",
    ),
    "दीर्घता": BuiltinSpec(
        "दीर्घता",
        required_args=1,
        max_args=1,
        aliases=("len",),
        category="core",
        description="Sequence or collection length",
    ),
    "परास": BuiltinSpec(
        "परास",
        required_args=1,
        max_args=3,
        aliases=("range",),
        category="core",
        description="Integer range builder",
    ),
    "प्रकार": BuiltinSpec(
        "प्रकार",
        required_args=1,
        max_args=1,
        aliases=("type",),
        category="core",
        description="Runtime type introspection",
    ),
    "पाठ_कर": BuiltinSpec(
        "पाठ_कर",
        required_args=1,
        max_args=1,
        aliases=("str",),
        category="core",
        description="Convert value to Vak text",
    ),
    "संख्या": BuiltinSpec(
        "संख्या",
        required_args=1,
        max_args=1,
        aliases=("int",),
        category="core",
        description="Convert value to integer",
    ),
    "दशमलव": BuiltinSpec(
        "दशमलव",
        required_args=1,
        max_args=1,
        aliases=("float",),
        category="core",
        description="Convert value to decimal",
    ),
    "खोलो": BuiltinSpec(
        "खोलो",
        required_args=1,
        max_args=2,
        keyword_names=("path", "mode"),
        aliases=("open",),
        category="io",
        description="Open a file handle",
    ),
    "क्रमबद्ध": BuiltinSpec(
        "क्रमबद्ध",
        required_args=1,
        max_args=1,
        aliases=("sorted",),
        category="core",
        description="Sorted copy of an iterable",
    ),
    "योग": BuiltinSpec(
        "योग",
        required_args=1,
        max_args=1,
        aliases=("sum",),
        category="core",
        description="Sum iterable values",
    ),
    "अधिकतम": BuiltinSpec(
        "अधिकतम",
        required_args=1,
        max_args=None,
        accepts_varargs=True,
        aliases=("max",),
        category="core",
        description="Maximum value",
    ),
    "न्यूनतम": BuiltinSpec(
        "न्यूनतम",
        required_args=1,
        max_args=None,
        accepts_varargs=True,
        aliases=("min",),
        category="core",
        description="Minimum value",
    ),
    "कुंजियाँ": BuiltinSpec(
        "कुंजियाँ",
        required_args=1,
        max_args=1,
        aliases=("keys",),
        category="collections",
        description="Dictionary keys",
    ),
    "मान": BuiltinSpec(
        "मान",
        required_args=1,
        max_args=1,
        aliases=("values",),
        category="collections",
        description="Dictionary values",
    ),
    "isinstance": BuiltinSpec(
        "isinstance",
        required_args=2,
        max_args=2,
        aliases=("उदाहरण_है",),
        category="core",
        description="Runtime isinstance check",
    ),
    "hasattr": BuiltinSpec(
        "hasattr",
        required_args=2,
        max_args=2,
        aliases=("गुण_है",),
        category="core",
        description="Attribute presence check",
    ),
    "getattr": BuiltinSpec(
        "getattr",
        required_args=2,
        max_args=3,
        aliases=("गुण_प्राप्त",),
        category="core",
        description="Attribute getter",
    ),
    "setattr": BuiltinSpec(
        "setattr",
        required_args=3,
        max_args=3,
        aliases=("गुण_नियत",),
        category="core",
        description="Attribute setter",
    ),
    "enumerate": BuiltinSpec(
        "enumerate",
        required_args=1,
        max_args=2,
        aliases=("गणना_सह",),
        category="collections",
        description="Enumerate iterable values",
    ),
    "zip": BuiltinSpec(
        "zip",
        required_args=1,
        max_args=None,
        accepts_varargs=True,
        aliases=("युग्मीकरण",),
        category="collections",
        description="Zip multiple iterables",
    ),
    "map": BuiltinSpec(
        "map",
        required_args=2,
        max_args=2,
        aliases=("मानचित्र",),
        category="collections",
        description="Map function over iterable",
    ),
    "filter": BuiltinSpec(
        "filter",
        required_args=2,
        max_args=2,
        aliases=("छलनी",),
        category="collections",
        description="Filter iterable values",
    ),
    "परिभाषय": BuiltinSpec(
        "परिभाषय",
        required_args=2,
        max_args=2,
        category="proof",
        description="Define a Sansmatic concept",
    ),
    "दावा": BuiltinSpec(
        "दावा",
        required_args=3,
        max_args=4,
        category="proof",
        description="Assert a proof fact",
    ),
    "नियम": BuiltinSpec(
        "नियम",
        required_args=6,
        max_args=6,
        category="proof",
        description="Register a Sansmatic implication rule",
    ),
    "मूल्यांकन": BuiltinSpec(
        "मूल्यांकन",
        required_args=3,
        max_args=3,
        category="proof",
        description="Evaluate proof derivability",
    ),
    "सिद्ध_है": BuiltinSpec(
        "सिद्ध_है",
        required_args=3,
        max_args=3,
        category="proof",
        description="Boolean forward proof query",
    ),
    "पश्च_सिद्ध_है": BuiltinSpec(
        "पश्च_सिद्ध_है",
        required_args=3,
        max_args=3,
        category="proof",
        description="Backward proof query",
    ),
    "प्रमाण_लॉग": BuiltinSpec(
        "प्रमाण_लॉग",
        required_args=0,
        max_args=0,
        category="proof",
        description="Full proof log",
    ),
    "प्रमाण_सारांश": BuiltinSpec(
        "प्रमाण_सारांश",
        required_args=0,
        max_args=0,
        category="proof",
        description="Structured proof summary",
    ),
    "प्रमाण_सारांश_पाठ": BuiltinSpec(
        "प्रमाण_सारांश_पाठ",
        required_args=0,
        max_args=0,
        category="proof",
        description="Formatted proof summary text",
    ),
    "प्रमाण_स्नैपशॉट": BuiltinSpec(
        "प्रमाण_स्नैपशॉट",
        required_args=0,
        max_args=0,
        category="proof",
        description="Capture proof state snapshot",
    ),
    "प्रमाण_पुनर्स्थापय": BuiltinSpec(
        "प्रमाण_पुनर्स्थापय",
        required_args=0,
        max_args=1,
        category="proof",
        description="Restore proof state snapshot",
    ),
    "प्रमाण_रीसेट": BuiltinSpec(
        "प्रमाण_रीसेट",
        required_args=0,
        max_args=0,
        category="proof",
        description="Clear proof state",
    ),
    "प्रमाण_अनुक्रम": BuiltinSpec(
        "प्रमाण_अनुक्रम",
        required_args=0,
        max_args=1,
        category="proof",
        description="Structured proof trace events",
    ),
    "प्रमाण_अनुक्रम_पाठ": BuiltinSpec(
        "प्रमाण_अनुक्रम_पाठ",
        required_args=0,
        max_args=1,
        category="proof",
        description="Formatted proof trace text",
    ),
    "प्रमाण_वृक्ष": BuiltinSpec(
        "प्रमाण_वृक्ष",
        required_args=3,
        max_args=3,
        category="proof",
        description="Proof tree for a target fact",
    ),
    "प्रमाण_वृक्ष_पाठ": BuiltinSpec(
        "प्रमाण_वृक्ष_पाठ",
        required_args=3,
        max_args=3,
        category="proof",
        description="Formatted proof tree text",
    ),
    "प्रमाण_व्याख्या": BuiltinSpec(
        "प्रमाण_व्याख्या",
        required_args=3,
        max_args=3,
        category="proof",
        description="Explain why a proof goal succeeded or failed",
    ),
    "प्रमाण_व्याख्या_पाठ": BuiltinSpec(
        "प्रमाण_व्याख्या_पाठ",
        required_args=3,
        max_args=3,
        category="proof",
        description="Formatted proof explanation text",
    ),
    "प्रमेय_सूची": BuiltinSpec(
        "प्रमेय_सूची",
        required_args=0,
        max_args=1,
        category="proof",
        description="List registered Sansmatic theorems",
    ),
    "प्रमेय_विवरण": BuiltinSpec(
        "प्रमेय_विवरण",
        required_args=1,
        max_args=1,
        category="proof",
        description="Return theorem details",
    ),
    "प्रमेय_तथ्य": BuiltinSpec(
        "प्रमेय_तथ्य",
        required_args=4,
        max_args=4,
        category="proof",
        description="Register a named fact theorem",
    ),
    "प्रमेय_नियम": BuiltinSpec(
        "प्रमेय_नियम",
        required_args=7,
        max_args=7,
        category="proof",
        description="Register a named rule theorem",
    ),
    "रूपान्तर": BuiltinSpec(
        "रूपान्तर",
        required_args=1,
        max_args=1,
        aliases=("rupantar",),
        category="repair",
        description="Transform Vak source into live runnable Vak",
    ),
    "रूपान्तर_रिपोर्ट": BuiltinSpec(
        "रूपान्तर_रिपोर्ट",
        required_args=1,
        max_args=1,
        aliases=("rupantar_report",),
        category="repair",
        description="Return textual repair report",
    ),
    "रूपान्तर_विवरण": BuiltinSpec(
        "रूपान्तर_विवरण",
        required_args=1,
        max_args=1,
        aliases=("rupantar_payload",),
        category="repair",
        description="Return structured repair payload",
    ),
    "कोडेक्स": BuiltinSpec(
        "कोडेक्स",
        required_args=1,
        max_args=3,
        aliases=("codex",),
        category="codex",
        description="Run Sanskrit Vakya Universal Codex and return Vak source",
    ),
    "कोडेक्स_रिपोर्ट": BuiltinSpec(
        "कोडेक्स_रिपोर्ट",
        required_args=1,
        max_args=3,
        aliases=("codex_report",),
        category="codex",
        description="Return textual Codex report",
    ),
    "कोडेक्स_विवरण": BuiltinSpec(
        "कोडेक्स_विवरण",
        required_args=1,
        max_args=3,
        aliases=("codex_payload",),
        category="codex",
        description="Return structured Codex payload",
    ),
    "कोडेक्स_पृष्ठ": BuiltinSpec(
        "कोडेक्स_पृष्ठ",
        required_args=0,
        max_args=0,
        aliases=("codex_pages",),
        category="codex",
        description="List available Codex pages",
    ),
    "कोडेक्स_अध्याय": BuiltinSpec(
        "कोडेक्स_अध्याय",
        required_args=0,
        max_args=0,
        aliases=("codex_chapters",),
        category="codex",
        description="List available Codex chapters",
    ),
    "कोडेक्स_उन्नयन": BuiltinSpec(
        "कोडेक्स_उन्नयन",
        required_args=1,
        max_args=2,
        aliases=("codex_promotion",),
        category="codex",
        description="Evaluate whether a Codex page is ready to graduate from branch to main",
    ),
    "प्रदर्शन_विवरण": BuiltinSpec(
        "प्रदर्शन_विवरण",
        required_args=1,
        max_args=4,
        aliases=("profile_payload",),
        category="tooling",
        description="Structured runtime performance profile for Vak source",
    ),
    "प्रदर्शन_पाठ": BuiltinSpec(
        "प्रदर्शन_पाठ",
        required_args=1,
        max_args=4,
        aliases=("profile_text",),
        category="tooling",
        description="Formatted runtime performance profile for Vak source",
    ),
    "आयात_प्रदर्शन_विवरण": BuiltinSpec(
        "आयात_प्रदर्शन_विवरण",
        required_args=1,
        max_args=3,
        aliases=("profile_import_payload",),
        category="tooling",
        description="Structured runtime performance profile for module imports",
    ),
    "आयात_प्रदर्शन_पाठ": BuiltinSpec(
        "आयात_प्रदर्शन_पाठ",
        required_args=1,
        max_args=3,
        aliases=("profile_import_text",),
        category="tooling",
        description="Formatted runtime performance profile for module imports",
    ),
    "अतुल्य_अग्रिम": BuiltinSpec(
        "अतुल्य_अग्रिम",
        required_args=1,
        max_args=1,
        aliases=("async_next",),
        category="async",
        description="Advance one awaited step of an async generator",
    ),
    "अतुल्य_समाप्त": BuiltinSpec(
        "अतुल्य_समाप्त",
        required_args=1,
        max_args=1,
        aliases=("async_done",),
        category="async",
        description="Check whether an async generator has completed",
    ),
}


def _builtin_category(name: str) -> str:
    if name.startswith("_chitra_"):
        return "graphics"
    if name in {
        "परिभाषय",
        "दावा",
        "नियम",
        "मूल्यांकन",
        "सिद्ध_है",
        "पश्च_सिद्ध_है",
        "प्रमाण_लॉग",
        "प्रमाण_सारांश",
        "प्रमाण_सारांश_पाठ",
        "प्रमाण_स्नैपशॉट",
        "प्रमाण_पुनर्स्थापय",
        "प्रमाण_रीसेट",
        "प्रमाण_अनुक्रम",
        "प्रमाण_अनुक्रम_पाठ",
        "प्रमाण_वृक्ष",
        "प्रमाण_वृक्ष_पाठ",
        "प्रमाण_व्याख्या",
        "प्रमाण_व्याख्या_पाठ",
        "प्रमेय_सूची",
        "प्रमेय_विवरण",
        "प्रमेय_तथ्य",
        "प्रमेय_नियम",
    }:
        return "proof"
    if name in {"रूपान्तर", "रूपान्तर_रिपोर्ट", "रूपान्तर_विवरण"}:
        return "repair"
    if name in {"कोडेक्स", "कोडेक्स_रिपोर्ट", "कोडेक्स_विवरण", "कोडेक्स_पृष्ठ", "कोडेक्स_अध्याय", "कोडेक्स_उन्नयन"}:
        return "codex"
    if name in {"प्रदर्शन_विवरण", "प्रदर्शन_पाठ", "आयात_प्रदर्शन_विवरण", "आयात_प्रदर्शन_पाठ"}:
        return "tooling"
    if name in {"पठन", "लेखन", "खोलो", "अस्तित्व", "मिटाओ", "सूची_निर्देशिका", "बनाओ_निर्देशिका"}:
        return "io"
    if name.startswith("जाल_"):
        return "network"
    if name in {"समय", "निद्रा", "धागा_शुरू", "सेट_टाइमआउट", "सेट_इंटरवल", "क्लियर_टाइमआउट", "async_sleep", "अतुल्य_अग्रिम", "async_next", "अतुल्य_समाप्त", "async_done"}:
        return "async"
    return "core"


def _introspect_builtin_spec(
    name: str,
    func: Any,
    *,
    fallback: BuiltinSpec | None = None,
) -> BuiltinSpec:
    if fallback is None:
        fallback = BuiltinSpec(
            name=name,
            category=_builtin_category(name),
            description=f"{name} builtin",
        )
    try:
        signature = inspect.signature(func)
    except (TypeError, ValueError):
        return fallback

    required = 0
    positional = 0
    keyword_names: list[str] = []
    accepts_varargs = False
    accepts_kwargs = False
    for parameter in signature.parameters.values():
        if parameter.kind == inspect.Parameter.VAR_POSITIONAL:
            accepts_varargs = True
            continue
        if parameter.kind == inspect.Parameter.VAR_KEYWORD:
            accepts_kwargs = True
            continue
        if parameter.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            positional += 1
            if parameter.default is inspect._empty:
                required += 1
        if parameter.kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        ):
            keyword_names.append(parameter.name)

    return replace(
        fallback,
        required_args=required,
        max_args=None if accepts_varargs else positional,
        keyword_names=tuple(keyword_names),
        accepts_varargs=accepts_varargs,
        accepts_kwargs=accepts_kwargs,
    )


def build_builtin_catalog(
    vm_builtins: dict[str, Any] | None = None,
    *,
    active_branches: Iterable[str] = (),
) -> dict[str, BuiltinSpec]:
    specs = {name: spec for name, spec in _MANUAL_SPECS.items()}

    for name in COMPILED_BUILTIN_ORDER:
        specs.setdefault(
            name,
            BuiltinSpec(
                name=name,
                category=_builtin_category(name),
                description=f"{name} builtin",
            ),
        )

    if vm_builtins is not None:
        for name, func in vm_builtins.items():
            specs[name] = _introspect_builtin_spec(name, func, fallback=specs.get(name))

    branch_names = set(active_branches)
    for name, spec in list(specs.items()):
        if spec.branch is None and name.startswith("_chitra_"):
            specs[name] = replace(spec, branch="chitrakala", category="graphics")
        elif spec.branch is None and name == "_branch_probe":
            specs[name] = replace(spec, branch="runtime_probe", category="diagnostic")
        elif spec.branch is not None and spec.branch not in branch_names and vm_builtins is None:
            continue

    return specs


def builtin_alias_map(
    vm_builtins: dict[str, Any] | None = None,
    *,
    active_branches: Iterable[str] = (),
) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for spec in build_builtin_catalog(vm_builtins, active_branches=active_branches).values():
        for alias in spec.aliases:
            aliases[alias] = spec.name
            aliases.setdefault(alias.lower(), spec.name)
    return aliases


def builtin_names(
    vm_builtins: dict[str, Any] | None = None,
    *,
    active_branches: Iterable[str] = (),
) -> set[str]:
    return set(build_builtin_catalog(vm_builtins, active_branches=active_branches).keys())


def compiled_builtin_index(name: str) -> int:
    try:
        return COMPILED_BUILTIN_ORDER.index(name)
    except ValueError:
        return 0


def format_builtin_help(
    vm_builtins: dict[str, Any] | None = None,
    *,
    active_branches: Iterable[str] = (),
    category: str | None = None,
    limit: int = 16,
) -> str:
    specs = build_builtin_catalog(vm_builtins, active_branches=active_branches)
    rows: list[str] = []
    for name in sorted(specs):
        spec = specs[name]
        if category is not None and spec.category != category:
            continue
        suffix = ""
        if spec.aliases:
            suffix = f" | aliases: {', '.join(spec.aliases)}"
        rows.append(f"{name} [{spec.category}] - {spec.description}{suffix}")
        if len(rows) >= limit:
            break
    if not rows:
        return "कोई builtin नहीं मिला"
    return "\n".join(rows)
