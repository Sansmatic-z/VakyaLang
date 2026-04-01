from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .context import KernelContext
from .parser import KernelParser
from .syntax import Absurd, Ann, App, EmptyType, EqType, Fst, Inl, Inr, KernelTerm, Lam, NatElim, NatLit, NatSucc, NatType, Pair, Pi, Refl, Sigma, SumElim, SumType, Snd, Sort, Transport, UnitIntro, UnitType, Var


@dataclass(frozen=True)
class KernelJudgment:
    context: KernelContext
    term: KernelTerm
    expected_type: KernelTerm | None = None

    def render(self) -> str:
        ctx = ", ".join(f"{entry.name}: {entry.value_type}" for entry in self.context.entries)
        turnstile = f"{ctx} ⊢ " if ctx else "⊢ "
        if self.expected_type is None:
            return f"{turnstile}{self.term}"
        return f"{turnstile}{self.term} : {self.expected_type}"


class KernelElaborator:
    """Elaborate simple textual or structured specifications into kernel objects."""

    def __init__(self, parser: KernelParser | None = None):
        self.parser = parser or KernelParser()

    def elaborate_term(self, spec: Any) -> KernelTerm:
        if isinstance(spec, KernelTerm):
            return spec
        if isinstance(spec, str):
            return self.parser.parse_term(spec)
        if isinstance(spec, int):
            return NatLit(spec)
        if isinstance(spec, dict):
            kind = spec.get("kind")
            if kind == "sort":
                return Sort(int(spec.get("level", 0)))
            if kind == "nat_type":
                return NatType()
            if kind == "unit_type":
                return UnitType()
            if kind == "empty_type":
                return EmptyType()
            if kind == "nat":
                return NatLit(int(spec["value"]))
            if kind == "unit":
                return UnitIntro()
            if kind == "succ":
                return NatSucc(self.elaborate_term(spec["value"]))
            if kind == "var":
                return Var(str(spec["name"]))
            if kind == "pi":
                return Pi(
                    str(spec["param"]),
                    self.elaborate_term(spec["param_type"]),
                    self.elaborate_term(spec["body_type"]),
                )
            if kind == "sigma":
                return Sigma(
                    str(spec["param"]),
                    self.elaborate_term(spec["param_type"]),
                    self.elaborate_term(spec["body_type"]),
                )
            if kind == "sum":
                return SumType(
                    self.elaborate_term(spec["left_type"]),
                    self.elaborate_term(spec["right_type"]),
                )
            if kind == "lam":
                return Lam(
                    str(spec["param"]),
                    self.elaborate_term(spec["param_type"]),
                    self.elaborate_term(spec["body"]),
                )
            if kind == "app":
                return App(
                    self.elaborate_term(spec["func"]),
                    self.elaborate_term(spec["arg"]),
                )
            if kind == "pair":
                return Pair(
                    self.elaborate_term(spec["first"]),
                    self.elaborate_term(spec["second"]),
                )
            if kind == "inl":
                return Inl(
                    self.elaborate_term(spec["value"]),
                    self.elaborate_term(spec["right_type"]),
                )
            if kind == "inr":
                return Inr(
                    self.elaborate_term(spec["left_type"]),
                    self.elaborate_term(spec["value"]),
                )
            if kind == "fst":
                return Fst(self.elaborate_term(spec["pair"]))
            if kind == "snd":
                return Snd(self.elaborate_term(spec["pair"]))
            if kind == "eq":
                return EqType(
                    self.elaborate_term(spec["type_term"]),
                    self.elaborate_term(spec["left"]),
                    self.elaborate_term(spec["right"]),
                )
            if kind == "refl":
                return Refl(self.elaborate_term(spec["value"]))
            if kind == "nat_elim":
                return NatElim(
                    self.elaborate_term(spec["motive"]),
                    self.elaborate_term(spec["base_case"]),
                    self.elaborate_term(spec["step_case"]),
                    self.elaborate_term(spec["target"]),
                )
            if kind == "sum_elim":
                return SumElim(
                    self.elaborate_term(spec["motive"]),
                    self.elaborate_term(spec["left_case"]),
                    self.elaborate_term(spec["right_case"]),
                    self.elaborate_term(spec["target"]),
                )
            if kind == "transport":
                return Transport(
                    self.elaborate_term(spec["type_term"]),
                    self.elaborate_term(spec["motive"]),
                    self.elaborate_term(spec["left"]),
                    self.elaborate_term(spec["right"]),
                    self.elaborate_term(spec["equality_proof"]),
                    self.elaborate_term(spec["value"]),
                )
            if kind == "absurd":
                return Absurd(
                    self.elaborate_term(spec["target_type"]),
                    self.elaborate_term(spec["contradiction"]),
                )
            if kind == "ann":
                return Ann(
                    self.elaborate_term(spec["term"]),
                    self.elaborate_term(spec["annotation"]),
                )
        raise TypeError(f"Unsupported kernel elaboration spec: {spec!r}")

    def elaborate_context(self, spec: Any) -> KernelContext:
        if spec is None:
            return KernelContext()
        if isinstance(spec, KernelContext):
            return spec

        ctx = KernelContext()
        for item in spec:
            if isinstance(item, tuple) and len(item) == 2:
                name, type_spec = item
            elif isinstance(item, dict):
                name, type_spec = item["name"], item["type"]
            else:
                raise TypeError(f"Unsupported kernel context item: {item!r}")
            ctx = ctx.extend(str(name), self.elaborate_term(type_spec))
        return ctx

    def elaborate_judgment(self, spec: Any) -> KernelJudgment:
        if isinstance(spec, KernelJudgment):
            return spec
        if not isinstance(spec, dict):
            raise TypeError("Kernel judgment spec must be a dict or KernelJudgment")
        return KernelJudgment(
            context=self.elaborate_context(spec.get("context")),
            term=self.elaborate_term(spec["term"]),
            expected_type=None if "type" not in spec else self.elaborate_term(spec["type"]),
        )
