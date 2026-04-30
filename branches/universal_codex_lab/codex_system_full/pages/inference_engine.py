"""
Phase 5: Inference Engine Codex Page.

Derives new facts from existing knowledge using logical inference:
- Modus Ponens, Modus Tollens, Hypothetical Syllogism
- Forward chaining and backward chaining
- Rule-based inference with confidence scoring
- Outputs valid Vak code representing derived facts
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from ..engines.code_generator import CodeGenerator, GenerationContext
from .utils import _overall_confidence


@dataclass
class Fact:
    """A single fact in the knowledge base."""
    key: str
    value: Any
    confidence: float = 1.0
    derived: bool = False
    source: str = "asserted"  # "asserted" or "inferred"


@dataclass
class Rule:
    """An inference rule."""
    name: str
    premise: str
    conclusion: str
    rule_type: str  # "modus_ponens", "modus_tollens", "syllogism", "forward_chain", "backward_chain"


class InferenceEngineCodexPage(CodexPage):
    """Derives new facts from existing knowledge using logical inference."""
    name = "inference_engine"
    description = "Inference engine page (derive new facts from existing knowledge)"
    priority = 71
    kind = "python"
    chapter = "knowledge_engine"
    chapter_title = "Domain-Specific Knowledge Engine"
    chapter_order = 51
    capabilities = ("inference", "logic", "modus_ponens", "chaining", "rule_based")
    emits_vak = True
    extensions = ("rules", "logic", "inf")
    max_fixpoint_passes = 3

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._facts: dict[str, Fact] = {}
        self._rules: list[Rule] = []
        self._derived_facts: list[Fact] = []
        self._generator = CodeGenerator()
        self._diagnostics: list[CodexDiagnostic] = []
        self._detected_constructs: list[str] = []
        self._load_default_rules()

    def _load_default_rules(self) -> None:
        """Load default inference rules."""
        self._rules.extend([
            Rule("modus_ponens", "P, P → Q", "Q", "modus_ponens"),
            Rule("modus_tollens", "¬Q, P → Q", "¬P", "modus_tollens"),
            Rule("hypothetical_syllogism", "P → Q, Q → R", "P → R", "syllogism"),
            Rule("disjunctive_syllogism", "P ∨ Q, ¬P", "Q", "disjunctive_syllogism"),
            Rule("forward_chain", "If premises match, derive conclusion", "Conclusion", "forward_chain"),
            Rule("backward_chain", "To prove goal, find matching rule", "Sub-goals", "backward_chain"),
        ])

    # ------------------------------------------------------------------
    # Inference operations
    # ------------------------------------------------------------------
    def assert_fact(self, key: str, value: Any, confidence: float = 1.0) -> Fact:
        """Assert a new fact."""
        fact = Fact(key=key, value=value, confidence=confidence)
        self._facts[key] = fact
        return fact

    def infer_modus_ponens(self, premise_key: str, implication: tuple[str, str]) -> Fact | None:
        """
        Apply modus ponens: If P is true and P → Q, then Q is true.

        Parameters
        ----------
        premise_key : str
            The key of the known fact (P).
        implication : tuple[str, str]
            The implication (P, Q) meaning P → Q.

        Returns
        -------
        Fact | None
            The derived fact Q, or None if premise not found.
        """
        p_key, q_key = implication
        if premise_key in self._facts:
            fact = self._facts[premise_key]
            derived = Fact(
                key=q_key, value=True,
                confidence=fact.confidence * 0.9,
                derived=True, source="modus_ponens",
            )
            self._derived_facts.append(derived)
            return derived
        return None

    def forward_chain(self, max_iterations: int = 10) -> list[Fact]:
        """
        Perform forward chaining inference.

        Starting from known facts, apply all matching rules
        to derive new facts until no new facts can be derived.
        """
        derived: list[Fact] = []
        for _ in range(max_iterations):
            new_facts = False
            for rule in self._rules:
                if rule.rule_type == "forward_chain":
                    # Check if premise matches any known fact
                    for fact_key, fact in self._facts.items():
                        if rule.premise.lower() in fact_key.lower():
                            new_key = f"inferred_{rule.name}_{fact_key}"
                            if new_key not in self._facts:
                                new_fact = Fact(
                                    key=new_key, value=fact.value,
                                    confidence=fact.confidence * 0.8,
                                    derived=True, source="forward_chain",
                                )
                                self._facts[new_key] = new_fact
                                derived.append(new_fact)
                                new_facts = True
            if not new_facts:
                break
        return derived

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------
    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        indicators = [
            "infer", "derive", "conclude", "therefore", "hence",
            "modus ponens", "modus tollens", "syllogism",
            "forward chain", "backward chain", "rule",
            "if.*then", "implies", "→", "therefore",
        ]
        score = 0
        for indicator in indicators:
            if indicator in source.lower():
                score += 12

        if score >= 12:
            return CodexPageProbe(self.name, min(score, 85), f"Inference request detected ({score} indicators)")
        return CodexPageProbe(self.name, 10, "Inference engine chapter (default)")

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------
    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        self._diagnostics = []
        self._detected_constructs = []

        # Parse inference request
        derived = self._process_inference(source)

        # Generate Vak output
        vak_output = self._generate_inference_output(derived)

        transformed = len(derived) > 0

        return CodexResult(
            page=self.name,
            original_source=source,
            source=vak_output,
            transformed=transformed,
            confidence=_overall_confidence(self._diagnostics, transformed),
            diagnostics=tuple(self._diagnostics),
            manifest=self.manifest(),
            metadata={
                "source_kind": "inference_request",
                "derived_facts_count": len(derived),
                "total_facts_count": len(self._facts),
                "rules_count": len(self._rules),
            },
        )

    def _process_inference(self, source: str) -> list[Fact]:
        """Process an inference request from natural language."""
        import re
        source_lower = source.lower().strip()
        derived: list[Fact] = []

        # Assert facts: "X is Y" or "X = Y"
        m = re.match(r"(\w+)\s+(?:is|=)\s+(.+)", source_lower)
        if m:
            key, value = m.group(1), m.group(2).strip()
            fact = self.assert_fact(key, value)
            derived.append(fact)
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="info",
                message=f"Asserted fact: {key} = {value}",
                confidence="safe_auto_fix",
            ))
            return derived

        # Forward chain
        if "forward" in source_lower or "chain" in source_lower:
            derived = self.forward_chain()
            for fact in derived:
                self._diagnostics.append(CodexDiagnostic(
                    page=self.name, level="info",
                    message=f"Derived via forward chaining: {fact.key}",
                    confidence="safe_auto_fix" if fact.confidence > 0.7 else "suggest_only",
                ))
            return derived

        # Modus ponens: "if P then Q, P is true, therefore Q"
        m = re.search(r"if\s+(\w+)\s+then\s+(\w+)", source_lower)
        if m:
            p_key = m.group(1)
            q_key = m.group(2)
            result = self.infer_modus_ponens(p_key, (p_key, q_key))
            if result:
                derived.append(result)
                self._diagnostics.append(CodexDiagnostic(
                    page=self.name, level="info",
                    message=f"Modus ponens: {p_key} → {q_key}",
                    confidence="safe_auto_fix",
                ))
            return derived

        return derived

    def _generate_inference_output(self, derived: list[Fact]) -> str:
        """Generate Vak code representing derived facts."""
        lines: list[str] = []
        lines.append("# Inference Engine Results")
        lines.append(f"# Derived facts: {len(derived)}")
        lines.append("")

        for fact in derived:
            source_label = "derived" if fact.derived else "asserted"
            lines.append(f"# Fact ({source_label}, confidence: {fact.confidence:.2f})")
            lines.append(f"परिवर्तनी {fact.key} = {fact.value!r}")
            lines.append("")

        if not derived:
            lines.append("# No new facts derived from input")
            lines.append("परिवर्तनी inference_result = अपरिभाषित")

        return "\n".join(lines)
