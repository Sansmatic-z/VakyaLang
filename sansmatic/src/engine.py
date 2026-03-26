# सान्समैटिक — स्व-सत्यापन प्रमाण इन्जिन
# Sansmatic — Self-Verifying Proof Engine
#
# Local implementation notes:
# - Aligns with the public Sansmatic v0.1 repo direction:
#   proof-binding, proof obligations, forward chaining, contradiction rejection.
# - This is still not a full dependent-type kernel, but it is now a real
#   logic engine instead of a placeholder that returns True for everything.

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple
import copy
import hashlib
import json
import math
import re


Fact = Tuple[str, str, str]
Rule = Tuple[Fact, Fact]


class ProofError(Exception):
    """Raised when a proof assertion or verification fails."""


class SansmaticEngine:
    """
    Sansmatic proof engine.

    Core operations:
        परिभाषय (define)    - register a concept and its properties
        दावा (assert)       - assert a fact with proof-binding / obligation tracking
        नियम (rule)         - register an implication
        मूल्यांकन (evaluate) - report whether a fact is derivable and executable
        सिद्ध_है (is_provable) - boolean query

    The engine now enforces:
    - proof obligations for unsupported assertions
    - contradiction detection
    - forward chaining with variable substitution
    - verifiable proof certificates
    - a small extensible predicate layer for boolean proof goals
    """

    _RELATION_ALIASES = {
        "has": "HAS",
        "HAS": "HAS",
        "is": "IS",
        "IS": "IS",
        "है": "IS",
    }
    _NEGATION_PREFIXES = ("NOT ", "न ", "नहीं ")
    _ASCII_VAR_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")
    _CALL_RE = re.compile(r"^([^\s(]+)\((.*)\)$")

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.definitions: Dict[str, Set[str]] = {}
        self.facts: Set[Fact] = set()
        self.rules: List[Rule] = []
        self.proof_log: List[str] = []
        self._derived: Set[Fact] = set()
        self.obligations: List[Dict[str, Optional[str]]] = []
        self.contradictions: List[Tuple[str, str]] = []
        self.known_proofs: Dict[str, Set[str]] = {}
        self.issued_certificates: Dict[str, Dict[str, Any]] = {}
        self.predicates: Dict[str, Callable[..., bool]] = {}
        self._register_default_predicates()

    # ── Public API ──────────────────────────────────────────────────────────

    def clone(self, verbose: Optional[bool] = None) -> "SansmaticEngine":
        """Create a deep copy for sandboxed proof evaluation."""
        cloned = SansmaticEngine(self.verbose if verbose is None else verbose)
        cloned.definitions = {name: set(props) for name, props in self.definitions.items()}
        cloned.facts = set(self.facts)
        cloned.rules = list(self.rules)
        cloned.proof_log = list(self.proof_log)
        cloned._derived = set(self._derived)
        cloned.obligations = [dict(item) for item in self.obligations]
        cloned.contradictions = list(self.contradictions)
        cloned.known_proofs = {pid: set(stmts) for pid, stmts in self.known_proofs.items()}
        cloned.issued_certificates = {
            key: copy.deepcopy(payload) for key, payload in self.issued_certificates.items()
        }
        cloned.predicates = dict(self.predicates)
        return cloned

    def register_predicate(self, name: str, predicate: Callable[..., bool]) -> None:
        self.predicates[name] = predicate

    def register_proof(self, proof_id: str, statement: Any = None) -> None:
        """Register a trusted proof reference for one statement or many."""
        key = self._normalize_text(proof_id)
        supports: Set[str] = set()
        if statement is None:
            supports = set()
        elif isinstance(statement, (list, set, tuple)):
            if isinstance(statement, tuple) and len(statement) == 3:
                supports.add(self._fact_to_statement(self._normalize_fact(statement)))
            else:
                for item in statement:
                    supports.add(self._statement_to_key(item))
        else:
            supports.add(self._statement_to_key(statement))
        self.known_proofs[key] = supports

    def add_fact(
        self,
        entity: str,
        relation: str,
        property_: str,
        *,
        source: str = "known",
        proof_id: Optional[str] = None,
    ) -> Fact:
        """Add a fact directly to the knowledge base."""
        fact = self._normalize_fact((entity, relation, property_))
        self._register_fact(fact, source=source, proof_id=proof_id)
        return fact

    def define(self, name: str, properties: Any) -> str:
        """
        परिभाषय नाम = {गुण1, गुण2, ...}
        Define a named concept with a set of properties.
        """
        if isinstance(properties, dict):
            props = {self._normalize_text(key) for key in properties.keys()}
        elif isinstance(properties, (list, set, tuple)):
            props = {self._normalize_text(item) for item in properties}
        else:
            props = {self._normalize_text(properties)}

        concept = self._normalize_text(name)
        self.definitions[concept] = props

        for prop in props:
            self.add_fact(concept, "HAS", prop, source="definition")

        msg = f"[परिभाषा] {concept} = {{{', '.join(sorted(props))}}}"
        self._log(msg)
        return msg

    def assert_fact(
        self,
        entity: str,
        relation: str,
        property_: str,
        proof_id: Optional[str] = None,
    ) -> str:
        """
        दावा इकाई संबंध गुण [प्रमाण]

        If the fact is already known or derivable, assertion succeeds.
        If a valid proof reference supports it, assertion succeeds.
        Otherwise the assertion becomes a proof obligation and evaluation
        remains blocked until the obligation is discharged.
        """
        fact = self._normalize_fact((entity, relation, property_))
        statement = self._fact_to_statement(fact)
        proof_key = self._normalize_text(proof_id) if proof_id else None
        self._apply_rules()

        if self.contradictions:
            msg = f"[दावा✗] {statement}  (विरोध detected)"
            self._log(msg)
            raise ProofError(msg)

        if fact in self.facts or fact in self._derived:
            self._register_fact(fact, source="assert-known", proof_id=proof_key)
            note = f"(प्रमाण {proof_key} ✓)" if proof_key else "(✓ known)"
            msg = f"[दावा✔] {statement}  {note}"
            self._log(msg)
            return msg

        if proof_key and self._proof_supports(statement, proof_key):
            self._register_fact(fact, source="assert-proof", proof_id=proof_key)
            msg = f"[दावा✔] {statement}  (प्रमाण {proof_key} ✓)"
            self._log(msg)
            return msg

        self._record_obligation(statement, proof_key)
        if proof_key:
            msg = f"[दावा✗] {statement}  (प्रमाण {proof_key} अपर्याप्त)"
        else:
            msg = f"[दावा✗] {statement}  (अपूर्ण प्रमाण दायित्व)"
        self._log(msg)
        return msg

    def rule(self, premise: Any, conclusion: Any) -> str:
        """
        नियम premise ⇒ conclusion
        Declare an implication rule and forward-chain immediately.
        """
        premise_fact = self._coerce_rule_fact(premise)
        conclusion_fact = self._coerce_rule_fact(conclusion)
        rule = (premise_fact, conclusion_fact)
        if rule not in self.rules:
            self.rules.append(rule)
        self._apply_rules()

        msg = (
            f"[नियम] {self._fact_to_statement(premise_fact)} ⇒ "
            f"{self._fact_to_statement(conclusion_fact)}"
        )
        self._log(msg)
        return msg

    def evaluate(self, entity: str, relation: str, property_: str) -> str:
        """
        मूल्यांकन इकाई संबंध गुण
        Evaluate whether a statement is derivable and whether execution is allowed.
        """
        fact = self._normalize_fact((entity, relation, property_))
        statement = self._fact_to_statement(fact)
        self._apply_rules()

        if self.contradictions:
            msg = (
                f"[मूल्यांकन✗] {statement} — विरोध मिला; निष्पादन रोका गया "
                f"({len(self.contradictions)} contradiction)"
            )
            self._log(msg)
            return msg

        if self.obligations:
            msg = (
                f"[मूल्यांकन✗] {statement} — अपूर्ण प्रमाण दायित्व "
                f"({len(self.obligations)})"
            )
            self._log(msg)
            return msg

        if fact in self.facts or fact in self._derived:
            msg = f"[मूल्यांकन✔] {statement} — सिद्ध (derivable) ✓"
        else:
            msg = f"[मूल्यांकन✗] {statement} — असिद्ध (not derivable)"

        self._log(msg)
        return msg

    def evaluate_statement(self, statement: Any) -> str:
        """Evaluate a free-form statement string or fact triple."""
        parsed = self.parse_statement(statement)
        if parsed["kind"] == "fact":
            fact = parsed["fact"]
            return self.evaluate(*fact)

        self._apply_rules()
        if self.contradictions:
            msg = f"[मूल्यांकन✗] {parsed['text']} — विरोध मिला"
            self._log(msg)
            return msg
        if self.obligations:
            msg = (
                f"[मूल्यांकन✗] {parsed['text']} — अपूर्ण प्रमाण दायित्व "
                f"({len(self.obligations)})"
            )
            self._log(msg)
            return msg
        if self.verify_statement(statement):
            msg = f"[मूल्यांकन✔] {parsed['text']} — सिद्ध (derivable) ✓"
        else:
            msg = f"[मूल्यांकन✗] {parsed['text']} — असिद्ध (not derivable)"
        self._log(msg)
        return msg

    def is_provable(self, entity: str, relation: str, property_: str) -> bool:
        """Boolean fact query for use in वाक् conditions."""
        return self.verify_statement((entity, relation, property_))

    def verify_statement(self, statement: Any) -> bool:
        """Return True only for supported, contradiction-free, obligation-free goals."""
        self._apply_rules()
        if self.contradictions or self.obligations:
            return False

        parsed = self.parse_statement(statement)
        if parsed["kind"] == "fact":
            fact = parsed["fact"]
            return fact in self.facts or fact in self._derived

        if parsed["kind"] == "predicate":
            return self._evaluate_predicate(parsed["name"], parsed["args"])

        text = parsed["text"]
        if text in self._supported_statements():
            return True
        return False

    def issue_certificate(
        self,
        statement: Any,
        verified: bool,
        *,
        pramana: str,
        confidence: float,
        certificate_hint: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a verifiable proof certificate payload."""
        payload: Dict[str, Any] = {
            "kind": "sansmatic_certificate",
            "version": 1,
            "statement": self._statement_to_key(statement),
            "verified": bool(verified),
            "pramana": pramana,
            "confidence": round(float(confidence), 6),
            "certificate_hint": certificate_hint or "",
            "reason": reason or "",
            "facts": sorted(self._fact_to_statement(fact) for fact in self.facts),
            "derived": sorted(self._fact_to_statement(fact) for fact in self._derived),
            "rules": [
                {
                    "premise": self._fact_to_statement(premise),
                    "conclusion": self._fact_to_statement(conclusion),
                }
                for premise, conclusion in self.rules
            ],
            "obligations": [dict(item) for item in self.obligations],
            "contradictions": [list(item) for item in self.contradictions],
        }
        payload["hash"] = self._certificate_hash(payload)
        self.issued_certificates[payload["hash"]] = copy.deepcopy(payload)
        return payload

    @classmethod
    def verify_certificate(cls, certificate: Any) -> bool:
        """Validate a certificate payload or legacy string certificate."""
        if isinstance(certificate, str):
            return certificate.startswith("PROOF_") or certificate.startswith("AXIOMATIC_")

        if not isinstance(certificate, dict):
            return False

        if certificate.get("kind") != "sansmatic_certificate":
            return False
        expected_hash = certificate.get("hash")
        if not expected_hash:
            return False

        payload = {key: value for key, value in certificate.items() if key != "hash"}
        actual_hash = cls._certificate_hash(payload)
        return actual_hash == expected_hash and bool(certificate.get("verified"))

    def parse_statement(self, statement: Any) -> Dict[str, Any]:
        """Parse a statement into fact / predicate / raw text form."""
        if isinstance(statement, tuple) and len(statement) == 3:
            fact = self._normalize_fact(statement)
            return {"kind": "fact", "fact": fact, "text": self._fact_to_statement(fact)}

        text = self._normalize_text(statement)
        if not text:
            return {"kind": "text", "text": ""}

        match = self._CALL_RE.match(text)
        if match:
            name = self._normalize_text(match.group(1))
            args = [self._normalize_text(arg) for arg in self._split_args(match.group(2))]
            lowered = name.lower()
            if len(args) == 1 and lowered.startswith("has_"):
                fact = self._normalize_fact((args[0], "HAS", name[4:]))
                return {"kind": "fact", "fact": fact, "text": self._fact_to_statement(fact)}
            if len(args) == 1 and lowered.startswith("is_"):
                fact = self._normalize_fact((args[0], "IS", name[3:]))
                return {"kind": "fact", "fact": fact, "text": self._fact_to_statement(fact)}
            return {"kind": "predicate", "name": name, "args": args, "text": text}

        parts = text.split()
        if len(parts) == 2:
            fact = self._normalize_fact((parts[0], "IS", parts[1]))
            return {"kind": "fact", "fact": fact, "text": self._fact_to_statement(fact)}
        if len(parts) >= 3:
            fact = self._normalize_fact((parts[0], parts[1], " ".join(parts[2:])))
            return {"kind": "fact", "fact": fact, "text": self._fact_to_statement(fact)}

        return {"kind": "text", "text": text}

    def get_log(self) -> List[str]:
        return list(self.proof_log)

    def reset(self) -> None:
        self.definitions.clear()
        self.facts.clear()
        self.rules.clear()
        self.proof_log.clear()
        self._derived.clear()
        self.obligations.clear()
        self.contradictions.clear()
        self.known_proofs.clear()
        self.issued_certificates.clear()
        self.predicates.clear()
        self._register_default_predicates()

    # ── Internal: predicate support ─────────────────────────────────────────

    def _register_default_predicates(self) -> None:
        def _as_int(value: Any) -> int:
            coerced = self._coerce_atom(value)
            if isinstance(coerced, bool):
                return int(coerced)
            if isinstance(coerced, (int, float)):
                return int(coerced)
            raise ValueError(f"Cannot coerce {value!r} to int")

        def _is_prime(value: Any) -> bool:
            number = _as_int(value)
            if number < 2:
                return False
            if number == 2:
                return True
            if number % 2 == 0:
                return False
            limit = int(math.sqrt(number)) + 1
            for candidate in range(3, limit, 2):
                if number % candidate == 0:
                    return False
            return True

        self.register_predicate("अभाज्य_है", _is_prime)
        self.register_predicate("prime", _is_prime)
        self.register_predicate("is_prime", _is_prime)
        self.register_predicate("सम_है", lambda value: _as_int(value) % 2 == 0)
        self.register_predicate("even", lambda value: _as_int(value) % 2 == 0)
        self.register_predicate("विषम_है", lambda value: _as_int(value) % 2 == 1)
        self.register_predicate("odd", lambda value: _as_int(value) % 2 == 1)
        self.register_predicate("धनात्मक_है", lambda value: float(self._coerce_atom(value)) > 0)
        self.register_predicate("ऋणात्मक_है", lambda value: float(self._coerce_atom(value)) < 0)

    def _evaluate_predicate(self, name: str, args: List[str]) -> bool:
        predicate = self.predicates.get(name)
        if predicate is None:
            return False
        try:
            coerced_args = [self._coerce_atom(arg) for arg in args]
            return bool(predicate(*coerced_args))
        except Exception:
            return False

    # ── Internal: logic core ────────────────────────────────────────────────

    def _register_fact(
        self,
        fact: Fact,
        *,
        source: str,
        proof_id: Optional[str] = None,
    ) -> None:
        contradiction = self._find_contradiction(fact)
        if contradiction is not None:
            pair = (self._fact_to_statement(fact), self._fact_to_statement(contradiction))
            if pair not in self.contradictions:
                self.contradictions.append(pair)
            raise ProofError(
                f"Contradiction detected: {pair[0]} conflicts with {pair[1]}"
            )

        self.facts.add(fact)

        # An added fact can discharge a matching obligation.
        statement = self._fact_to_statement(fact)
        self.obligations = [
            item for item in self.obligations if item.get("statement") != statement
        ]

    def _record_obligation(self, statement: str, proof_id: Optional[str]) -> None:
        item = {"statement": statement, "proof_id": proof_id}
        if item not in self.obligations:
            self.obligations.append(item)

    def _proof_supports(self, statement: str, proof_id: str) -> bool:
        supports = self.known_proofs.get(proof_id)
        if supports is not None:
            return not supports or statement in supports

        certificate = self.issued_certificates.get(proof_id)
        if certificate:
            if not self.verify_certificate(certificate):
                return False
            if certificate.get("statement") == statement:
                return True

        if proof_id == "AUTO_PROVE":
            return self.verify_statement(statement)
        return False

    def _apply_rules(self) -> None:
        changed = True
        while changed:
            changed = False
            all_facts = list(self.facts | self._derived)
            for premise, conclusion in self.rules:
                for fact in all_facts:
                    bindings = self._match_pattern(premise, fact)
                    if bindings is None:
                        continue

                    derived = self._substitute_pattern(conclusion, bindings)
                    if derived in self.facts or derived in self._derived:
                        continue
                    if self._find_contradiction(derived) is not None:
                        pair = (
                            self._fact_to_statement(derived),
                            self._fact_to_statement(self._find_contradiction(derived)),
                        )
                        if pair not in self.contradictions:
                            self.contradictions.append(pair)
                        continue
                    self._derived.add(derived)
                    changed = True

    def _match_pattern(self, pattern: Fact, fact: Fact) -> Optional[Dict[str, str]]:
        bindings: Dict[str, str] = {}
        for index, (pattern_part, actual_part) in enumerate(zip(pattern, fact)):
            if pattern_part == "*":
                bindings.setdefault(f"*{index}", actual_part)
                continue

            if self._is_variable(pattern_part):
                bound = bindings.get(pattern_part)
                if bound is None:
                    bindings[pattern_part] = actual_part
                elif bound != actual_part:
                    return None
                continue

            if pattern_part != actual_part:
                return None

        return bindings

    def _substitute_pattern(self, pattern: Fact, bindings: Dict[str, str]) -> Fact:
        parts: List[str] = []
        for index, part in enumerate(pattern):
            if part == "*":
                parts.append(bindings.get(f"*{index}", part))
            elif self._is_variable(part):
                parts.append(bindings.get(part, part))
            else:
                parts.append(part)
        return self._normalize_fact(tuple(parts))

    def _find_contradiction(self, fact: Fact) -> Optional[Fact]:
        entity, relation, property_ = fact
        for alternative in self._contrary_properties(property_):
            candidate = (entity, relation, alternative)
            if candidate in self.facts or candidate in self._derived:
                return candidate
        return None

    def _contrary_properties(self, property_: str) -> List[str]:
        text = self._normalize_text(property_)
        for prefix in self._NEGATION_PREFIXES:
            if text.startswith(prefix):
                return [self._normalize_text(text[len(prefix):])]
        return [f"NOT {text}"]

    def _supported_statements(self) -> Set[str]:
        statements = {self._fact_to_statement(fact) for fact in self.facts | self._derived}
        for proof_id, supported in self.known_proofs.items():
            statements.update(supported)
        for payload in self.issued_certificates.values():
            if payload.get("verified"):
                statements.add(self._normalize_text(payload.get("statement")))
        return statements

    # ── Internal: parsing and normalization ────────────────────────────────

    def _coerce_rule_fact(self, value: Any) -> Fact:
        if isinstance(value, tuple) and len(value) == 3:
            return self._normalize_fact(value)

        parsed = self.parse_statement(value)
        if parsed["kind"] != "fact":
            raise ProofError(f"Rule must be a fact-like statement, got: {value!r}")
        return parsed["fact"]

    @classmethod
    def _normalize_fact(cls, fact: Tuple[Any, Any, Any]) -> Fact:
        entity, relation, property_ = fact
        normalized_relation = cls._normalize_relation(relation)
        return (
            cls._normalize_text(entity),
            normalized_relation,
            cls._normalize_text(property_),
        )

    @classmethod
    def _normalize_relation(cls, relation: Any) -> str:
        text = cls._normalize_text(relation)
        return cls._RELATION_ALIASES.get(text, text)

    @staticmethod
    def _normalize_text(value: Any) -> str:
        if value is None:
            return ""
        text = str(value).strip()
        while text.startswith("(") and text.endswith(")"):
            candidate = text[1:-1].strip()
            if candidate.count("(") == candidate.count(")"):
                text = candidate
            else:
                break
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\s*,\s*", ", ", text)
        return text

    @classmethod
    def _fact_to_statement(cls, fact: Fact) -> str:
        return f"{fact[0]} {fact[1]} {fact[2]}"

    def _statement_to_key(self, statement: Any) -> str:
        parsed = self.parse_statement(statement)
        if parsed["kind"] == "fact":
            return self._fact_to_statement(parsed["fact"])
        return parsed["text"]

    @staticmethod
    def _coerce_atom(value: Any) -> Any:
        if isinstance(value, (bool, int, float)):
            return value
        if value is None:
            return None

        text = str(value).strip()
        if not text:
            return ""
        if text in {"True", "true", "सत्य"}:
            return True
        if text in {"False", "false", "असत्य"}:
            return False
        if (text.startswith('"') and text.endswith('"')) or (
            text.startswith("'") and text.endswith("'")
        ):
            return text[1:-1]
        try:
            return int(text)
        except ValueError:
            pass
        try:
            return float(text)
        except ValueError:
            return text

    @staticmethod
    def _split_args(raw_args: str) -> List[str]:
        if not raw_args.strip():
            return []

        args: List[str] = []
        current: List[str] = []
        depth = 0
        quote: Optional[str] = None
        for char in raw_args:
            if quote:
                current.append(char)
                if char == quote:
                    quote = None
                continue

            if char in {"'", '"'}:
                quote = char
                current.append(char)
                continue

            if char in "([{":
                depth += 1
            elif char in ")]}":
                depth -= 1

            if char == "," and depth == 0:
                args.append("".join(current).strip())
                current = []
                continue

            current.append(char)

        tail = "".join(current).strip()
        if tail:
            args.append(tail)
        return args

    @classmethod
    def _is_variable(cls, token: str) -> bool:
        if token.startswith("?"):
            return True
        if token in cls._RELATION_ALIASES or token in cls._RELATION_ALIASES.values():
            return False
        return cls._ASCII_VAR_RE.match(token) is not None

    @classmethod
    def _certificate_hash(cls, payload: Dict[str, Any]) -> str:
        blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def _log(self, message: str) -> None:
        self.proof_log.append(message)
        if self.verbose:
            print(message)
