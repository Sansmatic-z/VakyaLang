"""
Phase 4: Grammar Engine Codex Page.

Provides grammar definition and parser generation tools:
- EBNF/PEG grammar parsing and validation
- Grammar visualization and analysis
- Parser code generation from grammar definitions
- Grammar transformation and optimization
"""
from __future__ import annotations

from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from ..engines.grammar_parser import GrammarParser, GrammarRule, ParseError
from ..engines.code_generator import CodeGenerator, GenerationContext
from .utils import _overall_confidence
from ..vak_surface import normalize_vak_surface


class GrammarEngineCodexPage(CodexPage):
    """Grammar definition and parser generation from EBNF/PEG."""
    name = "grammar_engine"
    description = "Grammar definition page (EBNF/PEG → Parser generator)"
    priority = 60
    kind = "python"
    chapter = "language_tools"
    chapter_title = "Language Creation Tools"
    chapter_order = 40
    capabilities = ("grammar", "ebnf", "peg", "parser_generation", "grammar_analysis")
    emits_vak = True
    extensions = ("grammar", "ebnf", "peg", "g4", "yacc", "y")
    max_fixpoint_passes = 2

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._grammar_parser = GrammarParser()
        self._generator = CodeGenerator()
        self._diagnostics: list[CodexDiagnostic] = []
        self._detected_constructs: list[str] = []
        self._register_templates()

    def _register_templates(self) -> None:
        self._generator.register_template("parser_skeleton", """# Parser: {grammar_name}
# Dialect: {dialect}
# Rules: {rules_count}

वर्ग {parser_name}Parser {{
    चर tokens = []
    चर position = 0

{parse_methods}
}}""")

        self._generator.register_template("parse_method", """    कर्म parse_{rule_name}() {{
        # Rule: {rule_name} = {rule_body}
        # Alternatives: {alternatives_count}
        चर node = शून्य
        प्रत्यागच्छ node
    }}""")

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------
    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        indicators = [
            "=", ";", "<-",  # Grammar syntax
            "grammar", "rule", "production", "terminal", "nonterminal",
            "EBNF", "PEG", "BNF", "grammar",
            "|",  # Alternative separator in grammars
        ]
        score = 0
        for indicator in indicators:
            count = source.count(indicator)
            score += min(count * 2, 15)

        if filename and filename.endswith((".grammar", ".ebnf", ".peg", ".g4", ".yacc", ".y")):
            score += 40

        # Check if it looks like a grammar definition
        if ";" in source and "=" in source:
            score += 20
        if "<-" in source:
            score += 20

        if score >= 20:
            return CodexPageProbe(self.name, min(score, 90), f"Grammar definition detected ({score} indicators)")
        return CodexPageProbe(self.name, 0, "not a grammar candidate")

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------
    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        self._diagnostics = []
        self._detected_constructs = []

        try:
            # Determine dialect
            dialect = "peg" if "<-" in source else "ebnf"

            # Parse the grammar
            rules = self._grammar_parser.parse(source, dialect=dialect)

            if not rules:
                return self._no_transform(source, "No valid grammar rules found")

            # Analyze the grammar
            self._analyze_grammar(rules)

            # Generate parser code
            vak_code = self._generate_parser(source, rules, dialect)

            return CodexResult(
                page=self.name,
                original_source=source,
                source=vak_code,
                transformed=True,
                confidence=_overall_confidence(self._diagnostics, True),
                diagnostics=tuple(self._diagnostics),
                manifest=self.manifest(),
                metadata={
                    "source_kind": "grammar_definition",
                    "dialect": dialect,
                    "rules_count": len(rules),
                    "rule_names": [r.name for r in rules],
                    "terminals": [r.name for r in rules if r.is_terminal],
                    "nonterminals": [r.name for r in rules if not r.is_terminal],
                },
            )
        except ParseError as exc:
            return self._no_transform(source, f"Grammar parse error: {exc}")
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
            metadata={"source_kind": "grammar_definition", "error": reason},
        )

    # ------------------------------------------------------------------
    # Grammar analysis
    # ------------------------------------------------------------------
    def _analyze_grammar(self, rules: tuple[GrammarRule, ...]) -> None:
        """Analyze grammar properties and report diagnostics."""
        terminals = [r for r in rules if r.is_terminal]
        nonterminals = [r for r in rules if not r.is_terminal]

        self._detected_constructs.append(f"terminals:{len(terminals)}")
        self._detected_constructs.append(f"nonterminals:{len(nonterminals)}")

        self._diagnostics.append(CodexDiagnostic(
            page=self.name, level="info",
            message=f"Grammar: {len(terminals)} terminals, {len(nonterminals)} non-terminals",
            confidence="safe_auto_fix",
        ))

        # Check for left recursion (simple check)
        for rule in nonterminals:
            for alt in rule.alternatives:
                if alt.startswith(rule.name):
                    self._diagnostics.append(CodexDiagnostic(
                        page=self.name, level="warning",
                        message=f"Potential left recursion in rule: {rule.name}",
                        confidence="suggest_only",
                    ))

    # ------------------------------------------------------------------
    # Code generation
    # ------------------------------------------------------------------
    def _generate_parser(self, source: str, rules: tuple[GrammarRule, ...], dialect: str) -> str:
        parser_name = "Language"
        if rules:
            parser_name = rules[0].name.capitalize().replace("_", "")

        # Generate parse methods for each rule
        parse_methods: list[str] = []
        for rule in rules:
            rule_body = " | ".join(rule.alternatives)
            vak = self._generator.generate(
                template_name="parse_method",
                rule_name=rule.name.lower(),
                rule_body=rule_body,
                alternatives_count=len(rule.alternatives),
            )
            parse_methods.append(vak)

        vak = self._generator.generate(
            template_name="parser_skeleton",
            grammar_name=parser_name,
            dialect=dialect,
            rules_count=len(rules),
            parser_name=parser_name,
            parse_methods="\n\n".join(parse_methods),
        )

        return normalize_vak_surface(vak)
