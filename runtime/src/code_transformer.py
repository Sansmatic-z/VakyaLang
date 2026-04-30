# वाक् भाषा - वाक्य-अनुवादक (Code Transformer)
# Transforms English Python-style source into live Vak syntax.

from __future__ import annotations

import ast
from dataclasses import dataclass
import re

from sanskrit_coder.core.translator import SanskritTranslator

from .deep_meaning import DeepMeaningMapper
from .lexer import Lexer, is_identifier_part, is_identifier_start
from .runtime_catalog import builtin_alias_map
from .tokens import KEYWORDS


_DEVANAGARI_KEYWORDS = {
    token for token in KEYWORDS
    if any('\u0900' <= ch <= '\u097F' for ch in token)
}

_DEVANAGARI_STATEMENT_MARKERS = {
    'चर', 'मान', 'स्थिर', 'कर्म', 'वर्ग', 'डेटा', 'यदि', 'अन्यत्', 'अन्यथा',
    'यावत्', 'प्रत्येक', 'प्रत्यागच्छ', 'मुद्रय', 'वैश्विक', 'अस्थानिक',
    'प्रयत्न', 'दोष', 'अन्ततः', 'उत्क्षिप', 'आयात', 'साथ', 'प्रत्यभिज्ञा',
    'अतुल्यकालिक', 'विराम', 'अग्रे',
}

_ENGLISH_MARKERS = {
    *SanskritTranslator.CODE_KEYWORD_DICTIONARY.keys(),
    *builtin_alias_map().keys(),
}

_ENGLISH_STATEMENT_PATTERNS = (
    re.compile(r'^from\s+\S+\s+import\b'),
    re.compile(r'^import\b'),
    re.compile(r'^async\s+(def|with|for)\b'),
    re.compile(r'^(def|class|if|elif|else|while|for|try|except|finally|with|return|global|nonlocal|raise|match|pass)\b'),
)


@dataclass(frozen=True)
class TransformResult:
    original_source: str
    source: str
    transformed: bool
    replacements: int = 0
    changed_lines: tuple[int, ...] = ()
    features: tuple[str, ...] = ()
    language: str = "unknown"
    confidence: float = 0.0
    blocked_reason: str | None = None
    blocked_line: int = 0


class _EnglishSubsetValidator(ast.NodeVisitor):
    """Reject Python features the token-level Vak transformer cannot preserve safely."""

    def __init__(self) -> None:
        self.blocked_reason: str | None = None
        self.blocked_line: int = 0

    def block(self, node: ast.AST, message: str) -> None:
        if self.blocked_reason is None:
            self.blocked_reason = f"वाक्य-अनुवाद असंभव: {message}"
            self.blocked_line = getattr(node, "lineno", 0) or 0

    def _guard_visit(self, node: ast.AST) -> bool:
        return self.blocked_reason is None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if len(node.bases) > 1:
            self.block(node, "multiple inheritance अभी समर्थित नहीं")
            return
        if node.keywords:
            self.block(node, "class keyword arguments अभी समर्थित नहीं")
            return
        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> None:
        self.block(node, "Python assert को सुरक्षित Vak रूप में नहीं बदला जा सकता")

    def visit_Delete(self, node: ast.Delete) -> None:
        self.block(node, "Python del अभी समर्थित नहीं")

    def visit_Yield(self, node: ast.Yield) -> None:
        self.generic_visit(node)

    def visit_YieldFrom(self, node: ast.YieldFrom) -> None:
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        if len(node.items) != 1:
            self.block(node, "एक साथ अनेक async context managers अभी समर्थित नहीं")
            return
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        if node.orelse:
            self.block(node, "Python try/else अभी समर्थित नहीं")
            return
        for handler in node.handlers:
            if isinstance(handler.type, ast.Tuple):
                self.block(handler, "एक ही except में अनेक exception प्रकार अभी समर्थित नहीं")
                return
        self.generic_visit(node)

    def visit_TryStar(self, node: ast.TryStar) -> None:  # type: ignore[attr-defined]
        self.block(node, "Python except* अभी समर्थित नहीं")

    def visit_With(self, node: ast.With) -> None:
        if len(node.items) != 1:
            self.block(node, "एक साथ अनेक context managers अभी समर्थित नहीं")
            return
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if any(alias.name == '*' for alias in node.names):
            self.block(node, "from ... import * अभी समर्थित नहीं")
            return
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if any(isinstance(arg, ast.Starred) for arg in node.args):
            self.block(node, "call-site *args unpacking अभी समर्थित नहीं")
            return
        if any(keyword.arg is None for keyword in node.keywords):
            self.block(node, "call-site **kwargs unpacking अभी समर्थित नहीं")
            return
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self.block(node, "set comprehension अभी समर्थित नहीं")

    def visit_Match(self, node: ast.Match) -> None:
        self.block(node, "Python match/case syntax का Vak रूप अभी पूर्ण नहीं है")

    def visit_Assign(self, node: ast.Assign) -> None:
        if any(self._contains_starred_target(target) for target in node.targets):
            self.block(node, "starred assignment target अभी समर्थित नहीं")
            return
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if self._contains_starred_target(node.target):
            self.block(node, "starred assignment target अभी समर्थित नहीं")
            return
        self.generic_visit(node)

    def generic_visit(self, node: ast.AST) -> None:
        if not self._guard_visit(node):
            return
        super().generic_visit(node)

    @staticmethod
    def _contains_starred_target(node: ast.AST) -> bool:
        if isinstance(node, ast.Starred):
            return True
        if isinstance(node, (ast.Tuple, ast.List)):
            return any(_EnglishSubsetValidator._contains_starred_target(elt) for elt in node.elts)
        return False


class VakCodeTransformer:
    """Translate English Python-style source into valid Vak source."""

    _identifier_re = r'[\w\u0900-\u097F]+'
    _module_re = r'[\w\u0900-\u097F\.]+'
    _from_import_re = re.compile(
        rf'^(?P<indent>[ \t]*)from\s+(?P<module>{_module_re})\s+import\s+(?P<names>.+?)\s*$'
    )
    _import_re = re.compile(
        r'^(?P<indent>[ \t]*)import\s+(?P<modules>.+?)\s*$'
    )

    def __init__(self, *, deep_meaning_mode: bool = False) -> None:
        self.translator = SanskritTranslator()
        self.deep_meaning_mode = deep_meaning_mode
        self.deep_meaning_mapper = DeepMeaningMapper() if deep_meaning_mode else None
        self.builtin_aliases = builtin_alias_map()

    def transform(self, source: str) -> TransformResult:
        """Return translated Vak source plus metadata."""
        language, confidence = self._detect_language(source)
        if language in ("vak", "unknown"):
            return TransformResult(
                original_source=source,
                source=source,
                transformed=False,
                language=language,
                confidence=confidence,
            )

        tree: ast.AST | None = None
        if language == "english":
            blocked_reason, blocked_line, tree = self._validate_english_subset(source)
            if blocked_reason is not None:
                return TransformResult(
                    original_source=source,
                    source=source,
                    transformed=False,
                    language=language,
                    confidence=confidence,
                    blocked_reason=blocked_reason,
                    blocked_line=blocked_line,
                )

        semantic_replacements = 0
        semantic_features: tuple[str, ...] = ()
        if language == "english" and self.deep_meaning_mode and self.deep_meaning_mapper is not None:
            deep_result = self.deep_meaning_mapper.transform_source(source, tree=tree)
            source = deep_result.source
            semantic_replacements = (
                deep_result.identifier_replacements + deep_result.string_replacements
            )
            semantic_features = deep_result.features

        transformed_lines: list[str] = []
        replacements = semantic_replacements
        in_multiline: str | None = None
        changed_lines: set[int] = set()
        features: set[str] = set(semantic_features)

        for line_no, raw_line in enumerate(source.splitlines(keepends=True), start=1):
            line = raw_line

            if in_multiline is not None:
                close_at = line.find(in_multiline)
                transformed_lines.append(line)
                if close_at != -1:
                    in_multiline = None
                continue

            rewritten, changed = self._rewrite_import_line(line)
            if changed:
                transformed_lines.append(rewritten)
                replacements += 1
                changed_lines.add(line_no)
                features.add("import_rewrite")
                continue

            translated, line_replacements, new_multiline, line_features = self._translate_line(line)
            transformed_lines.append(translated)
            replacements += line_replacements
            if line_replacements:
                changed_lines.add(line_no)
                features.update(line_features)
            in_multiline = new_multiline

        result_source = ''.join(transformed_lines)
        transformed = replacements > 0

        if transformed:
            # Validate that the translated source can be lexed by the live Vak lexer.
            Lexer(result_source).tokenize()

        return TransformResult(
            original_source=source,
            source=result_source,
            transformed=transformed,
            replacements=replacements,
            changed_lines=tuple(sorted(changed_lines)),
            features=tuple(sorted(features)),
            language=language,
            confidence=confidence,
        )

    def _detect_language(self, source: str) -> tuple[str, float]:
        if not source.strip():
            return "unknown", 0.0

        english_stmt_hits = 0
        for raw_line in source.splitlines():
            code, _ = self._split_comment(raw_line)
            stripped = code.lstrip()
            if not stripped:
                continue
            first_token, _ = self._peek_identifier(stripped, 0)
            if first_token in _DEVANAGARI_STATEMENT_MARKERS:
                return "vak", 1.0
            if any(pattern.match(stripped) for pattern in _ENGLISH_STATEMENT_PATTERNS):
                english_stmt_hits += 1

        if english_stmt_hits:
            confidence = min(1.0, 0.7 + (english_stmt_hits * 0.05))
            return "english", round(confidence, 2)

        english_score = 0

        for token in self._iter_identifiers(source):
            if token in _DEVANAGARI_KEYWORDS:
                return "vak", 1.0
            if token in _ENGLISH_MARKERS:
                english_score += 2

        if english_score:
            confidence = min(1.0, 0.5 + (english_score * 0.05))
            return "english", round(confidence, 2)
        return "unknown", 0.0

    @staticmethod
    def _iter_identifiers(source: str) -> list[str]:
        tokens: list[str] = []
        in_multiline: str | None = None

        for raw_line in source.splitlines():
            line = raw_line
            pos = 0
            length = len(line)

            if in_multiline is not None:
                close_at = line.find(in_multiline)
                if close_at == -1:
                    continue
                pos = close_at + len(in_multiline)
                in_multiline = None

            while pos < length:
                ch = line[pos]
                if ch == '#':
                    break
                if ch in ('"', "'"):
                    if pos + 2 < length and line[pos] == line[pos + 1] == line[pos + 2]:
                        quote = line[pos:pos + 3]
                        end_pos = line.find(quote, pos + 3)
                        if end_pos == -1:
                            in_multiline = quote
                            break
                        pos = end_pos + 3
                        continue

                    end_pos = pos + 1
                    while end_pos < length:
                        if line[end_pos] == '\\':
                            end_pos += 2
                            continue
                        if line[end_pos] == ch:
                            end_pos += 1
                            break
                        end_pos += 1
                    pos = end_pos
                    continue

                if is_identifier_start(ch):
                    start = pos
                    pos += 1
                    while pos < length and is_identifier_part(line[pos]):
                        pos += 1
                    tokens.append(line[start:pos])
                    continue

                pos += 1

        return tokens

    @staticmethod
    def _validate_english_subset(source: str) -> tuple[str | None, int, ast.AST | None]:
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            line = exc.lineno or 0
            return f"वाक्य-अनुवाद असंभव: Python वाक्यरचना त्रुटि", line, None

        validator = _EnglishSubsetValidator()
        validator.visit(tree)
        return validator.blocked_reason, validator.blocked_line, tree

    def _rewrite_import_line(self, line: str) -> tuple[str, bool]:
        newline = '\n' if line.endswith('\n') else ''
        base = line[:-1] if newline else line
        code, comment = self._split_comment(base)

        match = self._from_import_re.match(code)
        if match:
            indent = match.group('indent')
            module = match.group('module')
            names_part = match.group('names').strip()

            if names_part == '*':
                return line, False

            requested: list[str] = []
            alias_assignments: list[str] = []
            for item in self._comma_split(names_part):
                if not item:
                    continue
                alias_parts = re.match(
                    rf'^(?P<name>{self._identifier_re})\s+as\s+(?P<alias>{self._identifier_re})$',
                    item,
                )
                if alias_parts:
                    name = alias_parts.group('name')
                    alias = alias_parts.group('alias')
                    requested.append(name)
                    alias_assignments.append(f"चर {alias} = {name}")
                else:
                    requested.append(item)

            if not requested:
                return line, False

            statements = [f"आयात {', '.join(requested)} से {module}"]
            statements.extend(alias_assignments)
            rewritten = indent + '; '.join(statements)
            if comment:
                rewritten += comment
            return rewritten + newline, True

        match = self._import_re.match(code)
        if match:
            indent = match.group('indent')
            modules_part = match.group('modules').strip()
            statements: list[str] = []

            for item in self._comma_split(modules_part):
                if not item:
                    continue
                alias_parts = re.match(
                    rf'^(?P<module>{self._module_re})\s+as\s+(?P<alias>{self._identifier_re})$',
                    item,
                )
                if alias_parts:
                    module = alias_parts.group('module')
                    alias = alias_parts.group('alias')
                    statements.append(f"आयात {module}")
                    statements.append(f"चर {alias} = {module}")
                else:
                    statements.append(f"आयात {item}")

            if not statements:
                return line, False

            rewritten = indent + '; '.join(statements)
            if comment:
                rewritten += comment
            return rewritten + newline, True

        return line, False

    def _translate_line(self, line: str) -> tuple[str, int, str | None, list[str]]:
        result: list[str] = []
        replacements = 0
        features: list[str] = []
        pos = 0
        length = len(line)

        while pos < length:
            ch = line[pos]

            if ch == '#':
                result.append(line[pos:])
                break

            if ch in ('"', "'"):
                if pos + 2 < length and line[pos] == line[pos + 1] == line[pos + 2]:
                    quote = line[pos:pos + 3]
                    end_pos = line.find(quote, pos + 3)
                    if end_pos == -1:
                        result.append(line[pos:])
                        return ''.join(result), replacements, quote, features
                    result.append(line[pos:end_pos + 3])
                    pos = end_pos + 3
                    continue

                end_pos = pos + 1
                while end_pos < length:
                    if line[end_pos] == '\\':
                        end_pos += 2
                        continue
                    if line[end_pos] == ch:
                        end_pos += 1
                        break
                    end_pos += 1
                result.append(line[pos:end_pos])
                pos = end_pos
                continue

            if is_identifier_start(ch):
                start = pos
                pos += 1
                while pos < length and is_identifier_part(line[pos]):
                    pos += 1
                token = line[start:pos]
                if token.lower() == 'is':
                    lookahead_pos = self._skip_whitespace(line, pos)
                    next_token, next_end = self._peek_identifier(line, lookahead_pos)
                    if next_token is not None and next_token.lower() == 'not':
                        result.append('!=')
                        pos = next_end
                        replacements += 2
                        features.append('identity_compare')
                        continue
                    result.append('==')
                    replacements += 1
                    features.append('identity_compare')
                    continue

                replacement = self._translate_token(token)
                if replacement != token:
                    replacements += 1
                    features.append(f'keyword:{token.lower()}')
                result.append(replacement)
                continue

            result.append(ch)
            pos += 1

        return ''.join(result), replacements, None, features

    def _translate_token(self, token: str) -> str:
        if token == "yield":
            return "उपज"
        replacement = self.translator.english_code_to_sanskrit(token)
        if replacement is not None:
            return replacement
        alias = self.builtin_aliases.get(token) or self.builtin_aliases.get(token.lower())
        if alias is not None:
            return alias
        return token

    @staticmethod
    def _comma_split(text: str) -> list[str]:
        return [part.strip() for part in text.split(',')]

    @staticmethod
    def _split_comment(line: str) -> tuple[str, str]:
        in_single = False
        in_double = False
        escaped = False

        for index, ch in enumerate(line):
            if escaped:
                escaped = False
                continue
            if ch == '\\':
                escaped = True
                continue
            if ch == '"' and not in_single:
                in_double = not in_double
                continue
            if ch == "'" and not in_double:
                in_single = not in_single
                continue
            if ch == '#' and not in_single and not in_double:
                return line[:index], line[index:]

        return line, ''

    @staticmethod
    def _skip_whitespace(line: str, pos: int) -> int:
        length = len(line)
        while pos < length and line[pos] in (' ', '\t'):
            pos += 1
        return pos

    @staticmethod
    def _peek_identifier(line: str, pos: int) -> tuple[str | None, int]:
        if pos >= len(line) or not is_identifier_start(line[pos]):
            return None, pos
        start = pos
        pos += 1
        while pos < len(line) and is_identifier_part(line[pos]):
            pos += 1
        return line[start:pos], pos
