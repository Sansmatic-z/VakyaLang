# वाक् भाषा - गूढार्थ मोड (Deep Meaning Mode)
# Deterministic semantic renaming for English Python-style source.

from __future__ import annotations

import ast
from dataclasses import dataclass
import re

from sanskrit_coder.core.translator import SanskritTranslator
from sanskrit_coder.linguistics.kosa import KosaEngine
from sanskrit_coder.universal import UniversalAPI

from .tokens import KEYWORDS


_ENGLISH_IDENTIFIER_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
_WORD_RE = re.compile(r'[A-Za-z]+')
_CAMEL_SPLIT_RE = re.compile(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)|\d+')
_PUNCT_TOKEN_RE = re.compile(r'[A-Za-z]+|[^A-Za-z]+')

_IDENTIFIER_OVERRIDES: dict[str, str] = {
    'main': 'मुख्य',
    '__init__': 'प्रारम्भ',
    'add': 'जोड़ो',
    'sum': 'योग_करो',
    'subtract': 'घटाओ',
    'sub': 'घटाओ',
    'multiply': 'गुणय',
    'mul': 'गुणय',
    'divide': 'भागय',
    'div': 'भागय',
    'compute': 'गणय',
    'calculate': 'गणय',
    'build': 'बनाओ',
    'make': 'बनाओ',
    'create': 'बनाओ',
    'get': 'प्राप्त_करो',
    'set': 'स्थापय',
    'remove': 'हटाओ',
    'delete': 'हटाओ',
    'update': 'अद्यतन_करो',
    'check': 'जाँचो',
    'validate': 'सत्यापय',
    'find': 'खोजो',
    'search': 'खोजो',
    'show': 'दिखाओ',
    'draw': 'चित्रय',
    'render': 'प्रदर्शय',
    'translate': 'अनुवाद_करो',
    'parse': 'विश्लेषण_करो',
    'run': 'चलाओ',
    'start': 'आरम्भ_करो',
    'stop': 'रोको',
    'wait': 'प्रतीक्षा_करो',
    'read': 'पढ़ो',
    'write': 'लिखो',
    'save': 'सहेजो',
    'load': 'लोड_करो',
    'count': 'गणना',
    'total': 'कुल',
    'result': 'फल',
    'value': 'मूल्य',
    'name': 'नाम',
    'text': 'पाठ',
    'message': 'संदेश',
    'error': 'त्रुटि',
    'data': 'दत्तांश',
    'file': 'फाइल',
    'path': 'पथ',
    'item': 'पद',
    'index': 'अनुक्रमणिका',
    'size': 'आकार',
    'length': 'दीर्घता',
    'width': 'चौड़ाई',
    'height': 'ऊँचाई',
    'color': 'रंग',
    'box': 'पेटिका',
    'point': 'बिन्दु',
    'animal': 'पशु',
    'hello': 'नमस्कार',
    'world': 'विश्व',
}

_PARAMETER_OVERRIDES: dict[str, str] = {
    'a': 'क',
    'b': 'ख',
    'c': 'ग',
    'd': 'घ',
    'e': 'ङ',
    'f': 'च',
    'i': 'इ',
    'j': 'ज',
    'k': 'क',
    'm': 'म',
    'n': 'न',
    'x': 'क्ष',
    'y': 'य',
    'z': 'ज',
}

_STRING_OVERRIDES: dict[str, str] = {
    'hello': 'नमस्कार',
    'world': 'विश्व',
    'hello world': 'नमस्कार विश्व',
    'goodbye': 'पुनर्दर्शनाय',
    'error': 'त्रुटि',
    'warning': 'चेतावनी',
    'success': 'सफलता',
    'failed': 'विफल',
    'done': 'समाप्त',
    'name': 'नाम',
    'value': 'मूल्य',
    'result': 'फल',
    'count': 'गणना',
    'number': 'संख्या',
    'text': 'पाठ',
    'message': 'संदेश',
    'data': 'दत्तांश',
    'file': 'फाइल',
    'path': 'पथ',
}

_ROOT_FALLBACKS: dict[str, str] = {
    'be': 'भू',
    'know': 'ज्ञा',
    'go': 'गम्',
    'do': 'कृ',
}

_RISKY_STRING_RE = re.compile(r'[\\/]|https?://|[A-Za-z0-9_-]+\.[A-Za-z0-9]+')


@dataclass(frozen=True)
class DeepMeaningResult:
    source: str
    identifier_replacements: int = 0
    string_replacements: int = 0
    features: tuple[str, ...] = ()


class _SemanticPlanBuilder(ast.NodeVisitor):
    def __init__(self, mapper: "DeepMeaningMapper") -> None:
        self.mapper = mapper
        self.renames: dict[str, str] = {}
        self.callable_names: set[str] = set()
        self.excluded_names: set[str] = set()
        self.used_names: set[str] = set(KEYWORDS)

    def build(self, tree: ast.AST) -> tuple[dict[str, str], set[str]]:
        self.visit(tree)
        return self.renames, self.callable_names

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.excluded_names.add(alias.asname or alias.name.split('.')[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            self.excluded_names.add(alias.asname or alias.name)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.callable_names.add(node.name)
        self._register(node.name, "function")
        self._register_args(node.args)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.callable_names.add(node.name)
        self._register(node.name, "function")
        self._register_args(node.args)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._register(node.name, "class")
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self._register_target(target, "variable")
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._register_target(node.target, "variable")
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self._register_target(node.target, "variable")
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._register_target(node.target, "variable")
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            if item.optional_vars is not None:
                self._register_target(item.optional_vars, "variable")
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name:
            self._register(node.name, "variable")
        self.generic_visit(node)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        self._register_target(node.target, "variable")
        self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self._register_comprehensions(node.generators)
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self._register_comprehensions(node.generators)
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self._register_comprehensions(node.generators)
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self._register_comprehensions(node.generators)
        self.generic_visit(node)

    def _register_args(self, args: ast.arguments) -> None:
        for arg in [*args.posonlyargs, *args.args, *args.kwonlyargs]:
            self._register(arg.arg, "parameter")
        if args.vararg is not None:
            self._register(args.vararg.arg, "parameter")
        if args.kwarg is not None:
            self._register(args.kwarg.arg, "parameter")

    def _register_comprehensions(self, generators: list[ast.comprehension]) -> None:
        for generator in generators:
            self._register_target(generator.target, "variable")

    def _register_target(self, node: ast.AST, kind: str) -> None:
        if isinstance(node, ast.Name):
            self._register(node.id, kind)
        elif isinstance(node, (ast.Tuple, ast.List)):
            for elt in node.elts:
                self._register_target(elt, kind)

    def _register(self, name: str, kind: str) -> None:
        if name in self.excluded_names or name in self.renames:
            return
        if not _ENGLISH_IDENTIFIER_RE.fullmatch(name):
            return
        if name.startswith("__") and name.endswith("__") and name != "__init__":
            return

        candidate = self.mapper.translate_identifier(name, kind=kind)
        if candidate == name:
            return

        safe = candidate
        if safe in KEYWORDS:
            safe = f"{candidate}_नाम"
        suffix = 2
        while safe in self.used_names:
            safe = f"{candidate}_{suffix}"
            suffix += 1
        self.used_names.add(safe)
        self.renames[name] = safe


class _DeepMeaningAstTransformer(ast.NodeTransformer):
    def __init__(self, mapper: "DeepMeaningMapper", renames: dict[str, str], callable_names: set[str]) -> None:
        self.mapper = mapper
        self.renames = renames
        self.callable_names = callable_names
        self.string_replacements = 0

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        node.name = self.renames.get(node.name, node.name)
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        node.name = self.renames.get(node.name, node.name)
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        node.name = self.renames.get(node.name, node.name)
        self.generic_visit(node)
        return node

    def visit_arg(self, node: ast.arg) -> ast.AST:
        node.arg = self.renames.get(node.arg, node.arg)
        return node

    def visit_Name(self, node: ast.Name) -> ast.AST:
        node.id = self.renames.get(node.id, node.id)
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        self.generic_visit(node)
        if node.attr in self.renames and node.attr in self.callable_names:
            node.attr = self.renames[node.attr]
        return node

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> ast.AST:
        if node.name:
            node.name = self.renames.get(node.name, node.name)
        self.generic_visit(node)
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        if isinstance(node.value, str):
            translated = self.mapper.translate_string(node.value)
            if translated != node.value:
                self.string_replacements += 1
                node.value = translated
        return node


class DeepMeaningMapper:
    """Opt-in semantic Sanskritization for English Python-style code."""

    def __init__(self) -> None:
        self.translator = SanskritTranslator()
        self.kosa = KosaEngine()
        self.universal = UniversalAPI()
        self.sutra_count = len(self.universal.ashtadhyayi.sutras)

    def transform_source(self, source: str, tree: ast.AST | None = None) -> DeepMeaningResult:
        working_tree = ast.parse(source) if tree is None else tree
        planner = _SemanticPlanBuilder(self)
        renames, callable_names = planner.build(working_tree)
        transformer = _DeepMeaningAstTransformer(self, renames, callable_names)
        new_tree = transformer.visit(working_tree)
        ast.fix_missing_locations(new_tree)
        transformed_source = ast.unparse(new_tree)
        if source.endswith("\n") and not transformed_source.endswith("\n"):
            transformed_source += "\n"

        features: list[str] = ["deep_meaning", f"ashtadhyayi:{self.sutra_count}"]
        if renames:
            features.append("deep_identifiers")
        if transformer.string_replacements:
            features.append("deep_strings")

        return DeepMeaningResult(
            source=transformed_source,
            identifier_replacements=len(renames),
            string_replacements=transformer.string_replacements,
            features=tuple(features),
        )

    def translate_identifier(self, name: str, *, kind: str) -> str:
        lowered = name.lower()

        if kind == "parameter" and lowered in _PARAMETER_OVERRIDES:
            return _PARAMETER_OVERRIDES[lowered]

        exact = _IDENTIFIER_OVERRIDES.get(lowered)
        if exact:
            return exact

        parts = self._split_identifier(name)
        if not parts:
            return name

        translated_parts: list[str] = []
        for index, part in enumerate(parts):
            translated = self._translate_identifier_part(
                part,
                prefer_verb=(kind == "function" and index == 0),
            )
            if translated is None:
                return name
            translated_parts.append(translated)

        return "_".join(translated_parts)

    def translate_string(self, text: str) -> str:
        lowered = text.strip().lower()
        if lowered in _STRING_OVERRIDES:
            return _STRING_OVERRIDES[lowered]
        if not self._should_translate_string(text):
            return text

        pieces: list[str] = []
        changed = False
        for token in _PUNCT_TOKEN_RE.findall(text):
            if token.isalpha():
                translated = self._translate_text_word(token)
                if translated is not None and translated != token:
                    pieces.append(translated)
                    changed = True
                else:
                    pieces.append(token)
            else:
                pieces.append(token)
        if changed:
            return "".join(pieces)
        return text

    def _translate_identifier_part(self, part: str, *, prefer_verb: bool) -> str | None:
        lowered = part.lower()

        if lowered in _PARAMETER_OVERRIDES:
            return _PARAMETER_OVERRIDES[lowered]

        override = _IDENTIFIER_OVERRIDES.get(lowered)
        if override is not None:
            return override

        translated = self.translator.english_to_sanskrit(lowered)
        if translated and translated != lowered:
            return translated

        kosa_match = self._lookup_kosa(lowered)
        if kosa_match is not None:
            return kosa_match

        if prefer_verb:
            root = _ROOT_FALLBACKS.get(lowered)
            if root is not None:
                derived = self.universal.generate(root)
                if derived and "(unknown)" not in derived:
                    return derived

        return None

    def _translate_text_word(self, token: str) -> str | None:
        lowered = token.lower()
        if lowered in _STRING_OVERRIDES:
            return _STRING_OVERRIDES[lowered]

        translated = self.translator.english_to_sanskrit(lowered)
        if translated and translated != lowered:
            return translated

        kosa_match = self._lookup_kosa(lowered)
        if kosa_match is not None:
            return kosa_match
        return None

    def _lookup_kosa(self, query: str) -> str | None:
        results = self.kosa.search(query, field="meaning")
        if not results:
            return None

        exact_matches: list[str] = []
        partial_matches: list[str] = []
        for result in results:
            meaning = result.get("meaning", "").lower()
            word = result.get("word")
            if not word:
                continue
            meaning_words = set(_WORD_RE.findall(meaning))
            if query in meaning_words:
                exact_matches.append(word)
            elif query in meaning:
                partial_matches.append(word)

        if exact_matches:
            return sorted(exact_matches, key=len)[0]
        if partial_matches:
            return sorted(partial_matches, key=len)[0]
        return None

    @staticmethod
    def _split_identifier(name: str) -> list[str]:
        if "_" in name:
            parts = [part for part in name.split("_") if part]
            return parts
        return [part for part in _CAMEL_SPLIT_RE.findall(name) if part]

    @staticmethod
    def _should_translate_string(text: str) -> bool:
        if not any('A' <= ch <= 'Z' or 'a' <= ch <= 'z' for ch in text):
            return False
        if _RISKY_STRING_RE.search(text):
            return False
        words = _WORD_RE.findall(text)
        if not words:
            return False
        if len(words) == 1 and words[0].islower():
            return False
        return True
