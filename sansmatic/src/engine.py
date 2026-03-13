# सान्समैटिक — स्व-सत्यापन प्रमाण इन्जिन
# Sansmatic — Self-Verifying Proof Engine
# Original concept: Raj Mitra (Sansmatic repo, Aug 2025)
# Integrated into VakyaLang unified ecosystem: Mar 2026
#
# A program can now DEFINE facts, ASSERT them against proofs,
# declare RULES, and EVALUATE logical consequences.
# Inspired by Pāṇini's rule-based grammar as a proof system.

from typing import Any, Dict, List, Optional, Set, Tuple


class ProofError(Exception):
    """Raised when a proof assertion fails."""
    pass


class SansmaticEngine:
    """
    The Sansmatic proof engine.

    Four operations (mapped to Sanskrit वाक् keywords):
        परिभाषय (define)   — establish a named set of properties
        दावा     (assert)   — claim a fact, verified against known proofs
        नियम     (rule)     — declare an implication (if X then Y)
        मूल्यांकन (evaluate) — derive whether a statement is provable

    Sanskrit output markers (matching original Sansmatic format):
        [परिभाषा]    ← DEFINE
        [दावा✔]     ← ASSERT (verified)
        [दावा✗]     ← ASSERT (failed)
        [नियम]      ← RULE
        [मूल्यांकन✔] ← EVALUATE (derivable)
        [मूल्यांकन✗] ← EVALUATE (not derivable)
    """

    def __init__(self, verbose: bool = True):
        self.verbose      = verbose
        self.definitions : Dict[str, Set]         = {}  # name → {prop1, prop2}
        self.facts        : Set[Tuple]             = set()  # (entity, relation, prop)
        self.rules        : List[Tuple]            = []  # (premise, conclusion)
        self.proof_log    : List[str]              = []
        self._derived     : Set[Tuple]             = set()

    # ── Core Operations ───────────────────────────────────────────────────────

    def define(self, name: str, properties: Any) -> str:
        """
        परिभाषय नाम = {गुण1, गुण2, ...}
        Define a named concept with a set of properties.
        """
        if isinstance(properties, (list, set)):
            props = set(str(p) for p in properties)
        elif isinstance(properties, dict):
            props = set(properties.keys())
        else:
            props = {str(properties)}

        self.definitions[name] = props

        # Auto-register facts: name HAS each property
        for prop in props:
            self.facts.add((name, "HAS", prop))

        msg = f"[परिभाषा] {name} = {{{', '.join(sorted(props))}}}"
        self._log(msg)
        return msg

    def assert_fact(self, entity: str, relation: str,
                    property_: str, proof_id: Optional[str] = None) -> str:
        """
        दावा इकाई संबंध गुण
        Assert a fact. Verifies it is known or provable.
        """
        fact = (str(entity), str(relation), str(property_))
        verified = fact in self.facts or fact in self._derived

        if verified:
            proof_note = f"(प्रमाण {proof_id} ✓)" if proof_id else "(✓ known)"
            msg = f"[दावा✔] {entity} {relation} {property_}  {proof_note}"
            self._log(msg)
            return msg
        else:
            msg = f"[दावा✗] {entity} {relation} {property_}  (अज्ञात — unknown)"
            self._log(msg)
            raise ProofError(msg)

    def rule(self, premise: Tuple, conclusion: Tuple) -> str:
        """
        नियम (entity, relation, prop) → (entity, relation, prop)
        Declare an implication rule.
        """
        self.rules.append((premise, conclusion))
        # Apply immediately to known facts
        self._apply_rules()

        p_str = f"{premise[0]} {premise[1]} {premise[2]}"
        c_str = f"{conclusion[0]} {conclusion[1]} {conclusion[2]}"
        msg = f"[नियम] {p_str} ⇒ {c_str}"
        self._log(msg)
        return msg

    def evaluate(self, entity: str, relation: str, property_: str) -> str:
        """
        मूल्यांकन इकाई संबंध गुण
        Evaluate whether a statement is derivable from known facts + rules.
        """
        self._apply_rules()  # ensure all derivations are fresh
        fact = (str(entity), str(relation), str(property_))
        derivable = fact in self.facts or fact in self._derived

        if derivable:
            msg = f"[मूल्यांकन✔] {entity} {relation} {property_} — सिद्ध (derivable) ✓"
        else:
            msg = f"[मूल्यांकन✗] {entity} {relation} {property_} — असिद्ध (not derivable)"

        self._log(msg)
        return msg

    def is_provable(self, entity: str, relation: str, property_: str) -> bool:
        """Returns True/False — for use in वाक् if conditions."""
        self._apply_rules()
        fact = (str(entity), str(relation), str(property_))
        return fact in self.facts or fact in self._derived

    # ── Internal ──────────────────────────────────────────────────────────────

    def _apply_rules(self):
        """Forward-chain all rules until no new facts are derived."""
        changed = True
        while changed:
            changed = False
            for premise, conclusion in self.rules:
                # premise is a pattern: (entity, relation, prop) — entity can be wildcard '*'
                matched_entities = self._match_premise(premise)
                for entity in matched_entities:
                    # Substitute entity into conclusion
                    conc = (
                        entity if conclusion[0] == '*' else conclusion[0],
                        conclusion[1],
                        conclusion[2]
                    )
                    if conc not in self.facts and conc not in self._derived:
                        self._derived.add(conc)
                        changed = True

    def _match_premise(self, premise: Tuple) -> List[str]:
        """Find all entities matching a premise pattern."""
        p_entity, p_rel, p_prop = premise
        matched = []
        all_facts = self.facts | self._derived
        if p_entity == '*':
            for (e, r, p) in all_facts:
                if r == p_rel and p == p_prop:
                    matched.append(e)
        else:
            if (p_entity, p_rel, p_prop) in all_facts:
                matched.append(p_entity)
        return matched

    def _log(self, msg: str):
        self.proof_log.append(msg)
        if self.verbose:
            print(msg)

    def get_log(self) -> List[str]:
        return list(self.proof_log)

    def reset(self):
        """Clear all state — start fresh."""
        self.definitions.clear()
        self.facts.clear()
        self.rules.clear()
        self.proof_log.clear()
        self._derived.clear()
