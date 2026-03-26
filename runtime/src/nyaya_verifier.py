# वाक् भाषा - न्याय प्रमाण सत्यापन (Nyāya Proof Verification)
# Vak Language - Formal Nyāya Proof Verification System
#
# This verifier now performs actual proof checking against Sansmatic state.
# It still is not a full dependent-type kernel, but it no longer certifies
# arbitrary successful execution as a proof.

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum, auto
import time

from sansmatic.src.engine import SansmaticEngine, ProofError


class Pramana(Enum):
    """
    Valid sources of knowledge in Nyāya epistemology.

    1. प्रत्यक्ष (Perception)
    2. अनुमान (Inference)
    3. उपमान (Comparison)
    4. शब्द (Verbal testimony)
    """

    PRATYAKSHA = auto()
    ANUMANA = auto()
    UPAMANA = auto()
    SHABDA = auto()


@dataclass(frozen=True)
class Fact:
    """A fact in the knowledge base."""

    entity: str
    relation: str
    property_: str

    def __str__(self) -> str:
        return f"{self.entity} → {self.relation} → {self.property_}"


@dataclass(frozen=True)
class Rule:
    """An inference rule."""

    premise: str
    conclusion: str


@dataclass
class ProofCertificate:
    """
    Result of proof verification.
    """

    statement: str
    verified: bool
    pramana: Pramana
    confidence: float
    timestamp: float
    certificate_hash: str
    reason: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        status = "✓ सिद्ध" if self.verified else "✗ असिद्ध"
        if self.reason:
            return (
                f"[{status}] {self.statement} "
                f"(confidence: {self.confidence:.2f}, pramana: {self.pramana.name}, "
                f"reason: {self.reason})"
            )
        return (
            f"[{status}] {self.statement} "
            f"(confidence: {self.confidence:.2f}, pramana: {self.pramana.name})"
        )


@dataclass
class ProofResult:
    """Result of executing proof evidence in the sandbox."""

    success: bool
    value: Any = None
    error: Optional[str] = None
    trace: List[str] = field(default_factory=list)
    steps: int = 0
    environment: Dict[str, Any] = field(default_factory=dict)


class SandboxError(Exception):
    """Exception raised during sandboxed proof execution."""


class _SandboxReturn(Exception):
    def __init__(self, value: Any):
        self.value = value


class _SandboxBreak(Exception):
    pass


class _SandboxContinue(Exception):
    pass


class ProofSandbox:
    """
    Sandboxed execution environment for proof evidence.

    Supports:
    - step limiting
    - pure expression evaluation
    - simple statement execution for proof blocks
    - Sansmatic logical builtins
    """

    def __init__(
        self,
        facts: Set[Fact],
        rules: Set[Rule],
        engine: Optional[SansmaticEngine] = None,
        initial_env: Optional[Dict[str, Any]] = None,
    ):
        self.engine = engine.clone(verbose=False) if engine is not None else SansmaticEngine(verbose=False)
        if engine is None:
            for fact in facts:
                self.engine.add_fact(
                    fact.entity,
                    fact.relation,
                    fact.property_,
                    source="sandbox-seed",
                )
            for rule in rules:
                self.engine.rule(rule.premise, rule.conclusion)

        self.execution_trace: List[str] = []
        self.max_steps = 10000
        self.step_count = 0
        self.env: Dict[str, Any] = dict(initial_env or {})
        self.builtins: Dict[str, Any] = {}
        self._install_builtins()

    def execute(self, evidence: Any) -> ProofResult:
        try:
            value = self._exec_or_eval(evidence)
            return ProofResult(
                success=True,
                value=value,
                trace=list(self.execution_trace),
                steps=self.step_count,
                environment=dict(self.env),
            )
        except _SandboxReturn as returned:
            return ProofResult(
                success=True,
                value=returned.value,
                trace=list(self.execution_trace),
                steps=self.step_count,
                environment=dict(self.env),
            )
        except (ProofError, SandboxError) as error:
            return ProofResult(
                success=False,
                error=str(error),
                trace=list(self.execution_trace),
                steps=self.step_count,
                environment=dict(self.env),
            )
        except Exception as error:
            return ProofResult(
                success=False,
                error=f"Unexpected error: {error}",
                trace=list(self.execution_trace),
                steps=self.step_count,
                environment=dict(self.env),
            )

    def evaluate_expression(self, expr: Any) -> Any:
        return self._eval(expr)

    # ── Builtins ────────────────────────────────────────────────────────────

    def _install_builtins(self) -> None:
        def _trace_print(*args: Any) -> None:
            rendered = " ".join(str(arg) for arg in args)
            self.execution_trace.append(f"PRINT {rendered}")
            return None

        self.builtins = {
            "परिभाषय": lambda name, props: self.engine.define(str(name), props),
            "दावा": lambda entity, relation, prop, proof_id=None: self.engine.assert_fact(
                str(entity), str(relation), str(prop), str(proof_id) if proof_id is not None else None
            ),
            "नियम": lambda a, b, c, d, e, f: self.engine.rule(
                (str(a), str(b), str(c)),
                (str(d), str(e), str(f)),
            ),
            "मूल्यांकन": lambda entity, relation, prop: self.engine.evaluate(
                str(entity), str(relation), str(prop)
            ),
            "सिद्ध_है": lambda entity, relation, prop: self.engine.is_provable(
                str(entity), str(relation), str(prop)
            ),
            "प्रमाण_लॉग": lambda: self.engine.get_log(),
            "प्रमाण_रीसेट": lambda: self.engine.reset(),
            "मुद्रय": _trace_print,
            "print": _trace_print,
            "पाठ_कर": str,
            "str": str,
            "परास": range,
            "range": range,
            "दीर्घता": len,
            "len": len,
            "संख्या": int,
            "int": int,
            "दशमलव": float,
            "float": float,
            "bool": bool,
            "list": list,
            "tuple": tuple,
            "dict": dict,
            "abs": abs,
            "round": round,
            "sum": sum,
            "min": min,
            "max": max,
            "sorted": sorted,
        }
        self.builtins.update(self.engine.predicates)

    # ── Execution core ──────────────────────────────────────────────────────

    def _step(self) -> None:
        self.step_count += 1
        if self.step_count > self.max_steps:
            raise SandboxError("Proof exceeded maximum steps")

    def _exec_or_eval(self, node: Any) -> Any:
        from .ast_nodes import Block

        if isinstance(node, Block):
            return self._exec_block(node)
        if isinstance(node, list):
            value = None
            for item in node:
                value = self._exec_or_eval(item)
            return value
        if self._is_statement_node(node):
            return self._exec_stmt(node)
        return self._eval(node)

    def _exec_block(self, block: Any) -> Any:
        value = None
        for stmt in getattr(block, "stmts", []):
            value = self._exec_stmt(stmt)
        return value

    def _exec_stmt(self, node: Any) -> Any:
        from .ast_nodes import (
            AssignExpr,
            Block,
            BreakStmt,
            ContinueStmt,
            ExprStmt,
            ForStmt,
            IfStmt,
            PrintStmt,
            ReturnStmt,
            ThrowStmt,
            TryStmt,
            VarDecl,
            WhileStmt,
        )

        self._step()

        if isinstance(node, Block):
            return self._exec_block(node)

        if isinstance(node, VarDecl):
            value = self._eval(node.value) if node.value is not None else None
            if len(node.names) == 1:
                self.env[node.names[0]] = value
            else:
                if not isinstance(value, (list, tuple)):
                    raise SandboxError("Cannot unpack non-sequence in proof sandbox")
                if len(value) != len(node.names):
                    raise SandboxError("Unpack arity mismatch in proof sandbox")
                for name, item in zip(node.names, value):
                    self.env[name] = item
            return value

        if isinstance(node, PrintStmt):
            values = [self._eval(item) for item in node.values]
            return self.builtins["मुद्रय"](*values)

        if isinstance(node, ExprStmt):
            return self._eval(node.expr)

        if isinstance(node, IfStmt):
            if self._truthy(self._eval(node.condition)):
                return self._exec_or_eval(node.then_body)
            for condition, body in node.elif_clauses:
                if self._truthy(self._eval(condition)):
                    return self._exec_or_eval(body)
            if node.else_body is not None:
                return self._exec_or_eval(node.else_body)
            return None

        if isinstance(node, WhileStmt):
            result = None
            while self._truthy(self._eval(node.condition)):
                try:
                    result = self._exec_or_eval(node.body)
                except _SandboxContinue:
                    continue
                except _SandboxBreak:
                    break
            return result

        if isinstance(node, ForStmt):
            result = None
            iterable = self._eval(node.iterable)
            for item in iterable:
                self._assign_loop_target(node.var_names, item)
                try:
                    result = self._exec_or_eval(node.body)
                except _SandboxContinue:
                    continue
                except _SandboxBreak:
                    break
            return result

        if isinstance(node, BreakStmt):
            raise _SandboxBreak()

        if isinstance(node, ContinueStmt):
            raise _SandboxContinue()

        if isinstance(node, ReturnStmt):
            raise _SandboxReturn(self._eval(node.value) if node.value is not None else None)

        if isinstance(node, ThrowStmt):
            raise SandboxError(str(self._eval(node.value)))

        if isinstance(node, TryStmt):
            try:
                return self._exec_or_eval(node.try_body)
            except Exception as error:
                for handler in node.handlers:
                    if self._matches_exception_handler(error, handler.match_name):
                        if handler.bind_name:
                            self.env[handler.bind_name] = error
                        return self._exec_or_eval(handler.body)
                raise
            finally:
                if node.finally_body is not None:
                    self._exec_or_eval(node.finally_body)

        if isinstance(node, AssignExpr):
            return self._eval(node)

        raise SandboxError(f"Unsupported proof statement: {type(node).__name__}")

    def _eval(self, node: Any) -> Any:
        from .ast_nodes import (
            AssignExpr,
            BinaryExpr,
            BoolLiteral,
            CallExpr,
            ConditionalExpr,
            DictComp,
            DictLiteral,
            FStringExpr,
            IdentifierExpr,
            IndexExpr,
            ListComp,
            ListLiteral,
            MemberExpr,
            NullLiteral,
            NumberLiteral,
            SetLiteral,
            SliceExpr,
            StringLiteral,
            TupleLiteral,
            UnaryExpr,
        )

        self._step()

        if isinstance(node, (int, float, str, bool)) or node is None:
            return node
        if isinstance(node, NumberLiteral):
            return node.value
        if isinstance(node, StringLiteral):
            return node.value
        if isinstance(node, BoolLiteral):
            return node.value
        if isinstance(node, NullLiteral):
            return None
        if isinstance(node, IdentifierExpr):
            if node.name in self.env:
                return self.env[node.name]
            if node.name in self.builtins:
                return self.builtins[node.name]
            raise SandboxError(f"Unknown identifier in proof sandbox: {node.name}")
        if isinstance(node, ListLiteral):
            return [self._eval(item) for item in node.elements]
        if isinstance(node, TupleLiteral):
            return tuple(self._eval(item) for item in node.elements)
        if isinstance(node, SetLiteral):
            return {self._eval(item) for item in node.elements}
        if isinstance(node, DictLiteral):
            return {self._eval(key): self._eval(value) for key, value in node.pairs}
        if isinstance(node, FStringExpr):
            parts: List[str] = []
            for part in node.parts:
                if isinstance(part, str):
                    parts.append(part)
                else:
                    parts.append(str(self._eval(part)))
            return "".join(parts)
        if isinstance(node, ConditionalExpr):
            if self._truthy(self._eval(node.condition)):
                return self._eval(node.then_expr)
            return self._eval(node.else_expr)
        if isinstance(node, UnaryExpr):
            operand = self._eval(node.operand)
            if node.op == "-":
                return -operand
            if node.op == "~":
                return ~operand
            if node.op == "न":
                return not self._truthy(operand)
            raise SandboxError(f"Unsupported unary operator: {node.op}")
        if isinstance(node, BinaryExpr):
            return self._eval_binary(node)
        if isinstance(node, MemberExpr):
            obj = self._eval(node.obj)
            if isinstance(obj, dict) and node.attr in obj:
                return obj[node.attr]
            return getattr(obj, node.attr)
        if isinstance(node, IndexExpr):
            return self._eval(node.obj)[self._eval(node.index)]
        if isinstance(node, SliceExpr):
            obj = self._eval(node.obj)
            start = self._eval(node.start) if node.start is not None else None
            stop = self._eval(node.stop) if node.stop is not None else None
            step = self._eval(node.step) if node.step is not None else None
            return obj[slice(start, stop, step)]
        if isinstance(node, AssignExpr):
            return self._eval_assign(node)
        if isinstance(node, CallExpr):
            callee = self._eval(node.callee)
            args = [self._eval(arg) for arg in node.args]
            kwargs = {key: self._eval(value) for key, value in node.kwargs.items()}
            if not callable(callee):
                raise SandboxError(f"Object is not callable in proof sandbox: {callee!r}")
            return callee(*args, **kwargs)
        if isinstance(node, ListComp):
            return self._eval_list_comp(node)
        if isinstance(node, DictComp):
            return self._eval_dict_comp(node)
        if isinstance(node, list):
            return [self._eval(item) for item in node]
        if isinstance(node, dict):
            return {key: self._eval(value) for key, value in node.items()}
        return node

    def _eval_binary(self, node: Any) -> Any:
        if node.op == "अथवा":
            left = self._eval(node.left)
            return left if self._truthy(left) else self._eval(node.right)
        if node.op == "और":
            left = self._eval(node.left)
            return self._eval(node.right) if self._truthy(left) else left

        left = self._eval(node.left)
        right = self._eval(node.right)
        op = node.op

        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            return left / right
        if op == "//":
            return left // right
        if op == "%":
            return left % right
        if op == "**":
            return left ** right
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == "<":
            return left < right
        if op == ">":
            return left > right
        if op == "<=":
            return left <= right
        if op == ">=":
            return left >= right
        if op == "|":
            return left | right
        if op == "^":
            return left ^ right
        if op == "&":
            return left & right
        if op == "<<":
            return left << right
        if op == ">>":
            return left >> right
        if op == "अन्तर्गत":
            return left in right
        if op == "not in":
            return left not in right
        raise SandboxError(f"Unsupported binary operator: {op}")

    def _eval_assign(self, node: Any) -> Any:
        value = self._eval(node.value)
        current = self._read_target(node.target) if node.op != "=" else None

        if node.op == "=":
            updated = value
        elif node.op == "+=":
            updated = current + value
        elif node.op == "-=":
            updated = current - value
        elif node.op == "*=":
            updated = current * value
        elif node.op == "/=":
            updated = current / value
        elif node.op == "//=":
            updated = current // value
        elif node.op == "%=":
            updated = current % value
        else:
            raise SandboxError(f"Unsupported assignment operator: {node.op}")

        self._write_target(node.target, updated)
        return updated

    def _eval_list_comp(self, node: Any) -> List[Any]:
        original = self.env.get(node.var_name)
        sentinel = object()
        if node.var_name not in self.env:
            original = sentinel

        result: List[Any] = []
        for item in self._eval(node.iterable):
            self.env[node.var_name] = item
            if node.filter_expr is not None and not self._truthy(self._eval(node.filter_expr)):
                continue
            result.append(self._eval(node.expr))

        if original is sentinel:
            self.env.pop(node.var_name, None)
        else:
            self.env[node.var_name] = original
        return result

    def _eval_dict_comp(self, node: Any) -> Dict[Any, Any]:
        original = self.env.get(node.var_name)
        sentinel = object()
        if node.var_name not in self.env:
            original = sentinel

        result: Dict[Any, Any] = {}
        for item in self._eval(node.iterable):
            self.env[node.var_name] = item
            if node.filter_expr is not None and not self._truthy(self._eval(node.filter_expr)):
                continue
            result[self._eval(node.key_expr)] = self._eval(node.value_expr)

        if original is sentinel:
            self.env.pop(node.var_name, None)
        else:
            self.env[node.var_name] = original
        return result

    def _read_target(self, target: Any) -> Any:
        from .ast_nodes import IdentifierExpr, IndexExpr, MemberExpr

        if isinstance(target, IdentifierExpr):
            if target.name in self.env:
                return self.env[target.name]
            raise SandboxError(f"Unknown assignment target: {target.name}")
        if isinstance(target, MemberExpr):
            obj = self._eval(target.obj)
            if isinstance(obj, dict):
                return obj.get(target.attr)
            return getattr(obj, target.attr)
        if isinstance(target, IndexExpr):
            obj = self._eval(target.obj)
            index = self._eval(target.index)
            return obj[index]
        raise SandboxError(f"Unsupported assignment target: {type(target).__name__}")

    def _write_target(self, target: Any, value: Any) -> None:
        from .ast_nodes import IdentifierExpr, IndexExpr, MemberExpr

        if isinstance(target, IdentifierExpr):
            self.env[target.name] = value
            return
        if isinstance(target, MemberExpr):
            obj = self._eval(target.obj)
            if isinstance(obj, dict):
                obj[target.attr] = value
            else:
                setattr(obj, target.attr, value)
            return
        if isinstance(target, IndexExpr):
            obj = self._eval(target.obj)
            index = self._eval(target.index)
            obj[index] = value
            return
        raise SandboxError(f"Unsupported assignment target: {type(target).__name__}")

    @staticmethod
    def _truthy(value: Any) -> bool:
        return bool(value)

    def _assign_loop_target(self, names: list[str], item: Any) -> None:
        if len(names) == 1:
            self.env[names[0]] = item
            return
        try:
            values = list(item)
        except TypeError as exc:
            raise SandboxError("For-loop unpacking requires an iterable value") from exc
        if len(values) != len(names):
            raise SandboxError(
                f"For-loop unpacking expected {len(names)} values, got {len(values)}"
            )
        for name, value in zip(names, values):
            self.env[name] = value

    @staticmethod
    def _matches_exception_handler(error: Exception, match_name: str | None) -> bool:
        if not match_name:
            return True
        try:
            import builtins as py_builtins

            candidate = getattr(py_builtins, str(match_name), None)
            if isinstance(candidate, type) and issubclass(candidate, BaseException):
                return isinstance(error, candidate)
        except Exception:
            pass
        match_text = str(match_name)
        if match_text.endswith(("Error", "Exception")):
            return any(cls.__name__ == match_text for cls in type(error).__mro__)
        return True

    @staticmethod
    def _is_statement_node(node: Any) -> bool:
        return hasattr(node, "__class__") and node.__class__.__name__.endswith("Stmt")


class NyayaProofVerifier:
    """
    Formal Nyāya proof verifier backed by Sansmatic.
    """

    def __init__(self):
        self.engine = SansmaticEngine(verbose=False)
        self.facts: Set[Fact] = set()
        self.rules: Set[Rule] = set()
        self.proofs: Dict[str, ProofCertificate] = {}
        self.function_signatures: Dict[str, Any] = {}

    def add_fact(self, entity: str, relation: str, property_: str) -> None:
        fact = Fact(entity, relation, property_)
        self.facts.add(fact)
        self.engine.add_fact(entity, relation, property_, source="verifier")

    def add_rule(self, premise: str, conclusion: str) -> None:
        rule = Rule(premise, conclusion)
        self.rules.add(rule)
        self.engine.rule(premise, conclusion)

    def verify_proof(
        self,
        statement: str,
        evidence: Any,
        *,
        statement_expr: Any = None,
        certificate_hint: Optional[str] = None,
    ) -> ProofCertificate:
        sandbox = ProofSandbox(self.facts, self.rules, engine=self.engine)
        result = sandbox.execute(evidence)

        verified, reason = self._check_statement(statement, statement_expr, result, sandbox)
        pramana = self._determine_pramana(statement, result, sandbox)
        confidence = self._calculate_confidence(verified, pramana, result, sandbox)
        payload = sandbox.engine.issue_certificate(
            statement,
            verified,
            pramana=pramana.name,
            confidence=confidence,
            certificate_hint=certificate_hint,
            reason=reason,
        )
        cert = ProofCertificate(
            statement=statement,
            verified=verified,
            pramana=pramana,
            confidence=confidence,
            timestamp=time.time(),
            certificate_hash=payload["hash"],
            reason=reason,
            payload=payload,
        )
        self.proofs[statement] = cert
        return cert

    def _check_statement(
        self,
        statement: str,
        statement_expr: Any,
        result: ProofResult,
        sandbox: ProofSandbox,
    ) -> tuple[bool, Optional[str]]:
        if not result.success:
            return False, result.error or "Proof execution failed"

        if sandbox.engine.contradictions:
            return False, "Contradiction detected in proof context"

        if sandbox.engine.obligations:
            return False, f"Unmet proof obligations: {len(sandbox.engine.obligations)}"

        if statement_expr is not None:
            try:
                evaluated = sandbox.evaluate_expression(statement_expr)
                if isinstance(evaluated, bool):
                    return evaluated, None if evaluated else "Statement expression evaluated to false"
            except Exception as error:
                return False, f"Statement expression could not be evaluated: {error}"

        if sandbox.engine.verify_statement(statement):
            return True, None

        parsed = sandbox.engine.parse_statement(statement)
        if parsed["kind"] == "predicate" and sandbox.engine.verify_statement(statement):
            return True, None

        return False, "Statement is not derivable from facts, rules, and evidence"

    def _determine_pramana(
        self,
        statement: str,
        result: ProofResult,
        sandbox: ProofSandbox,
    ) -> Pramana:
        parsed = sandbox.engine.parse_statement(statement)
        if parsed["kind"] == "fact":
            fact = parsed["fact"]
            base_fact = Fact(*fact)
            if base_fact in self.facts:
                return Pramana.PRATYAKSHA
            if fact in sandbox.engine._derived:
                return Pramana.ANUMANA
        if parsed["kind"] == "predicate":
            return Pramana.ANUMANA
        if any("like" in trace.lower() for trace in result.trace):
            return Pramana.UPAMANA
        return Pramana.SHABDA

    def _calculate_confidence(
        self,
        verified: bool,
        pramana: Pramana,
        result: ProofResult,
        sandbox: ProofSandbox,
    ) -> float:
        if not verified:
            return 0.0
        if sandbox.engine.obligations or sandbox.engine.contradictions:
            return 0.0

        base_confidence = {
            Pramana.PRATYAKSHA: 1.0,
            Pramana.ANUMANA: 0.9,
            Pramana.UPAMANA: 0.7,
            Pramana.SHABDA: 0.6,
        }[pramana]

        if result.steps > 0:
            step_penalty = min(0.15, result.steps / 2000.0)
            return max(0.0, base_confidence - step_penalty)
        return base_confidence

    def check_commutativity(self, func_name: str, args: List[Any]) -> bool:
        """
        Check if function is commutative based on Vibhakti roles.
        """
        sig = self._get_function_signature(func_name)
        if not sig or len(args) != 2:
            return False

        if hasattr(sig, "params") and len(sig.params) == 2:
            p1, p2 = sig.params
            if hasattr(p1, "vibhakti") and hasattr(p2, "vibhakti"):
                if p1.vibhakti == p2.vibhakti:
                    result1 = self._call_function(func_name, args)
                    result2 = self._call_function(func_name, [args[1], args[0]])
                    return result1 == result2

        return False

    def _get_function_signature(self, func_name: str) -> Optional[Any]:
        return self.function_signatures.get(func_name)

    def _call_function(self, func_name: str, args: List[Any]) -> Any:
        return None

    def register_function(self, func_name: str, signature: Any) -> None:
        self.function_signatures[func_name] = signature

    @staticmethod
    def verify_certificate_payload(payload: Any) -> bool:
        return SansmaticEngine.verify_certificate(payload)


__all__ = [
    "NyayaProofVerifier",
    "ProofSandbox",
    "ProofCertificate",
    "ProofResult",
    "Fact",
    "Rule",
    "Pramana",
    "SandboxError",
]
