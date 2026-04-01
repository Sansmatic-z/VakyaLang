from __future__ import annotations

from dataclasses import dataclass


class KernelTerm:
    """Base class for all trusted-kernel terms."""


@dataclass(frozen=True)
class Sort(KernelTerm):
    level: int = 0

    def __post_init__(self) -> None:
        if self.level < 0:
            raise ValueError("Sort level must be non-negative")

    def __str__(self) -> str:
        return f"Type{self.level}"


@dataclass(frozen=True)
class Var(KernelTerm):
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Pi(KernelTerm):
    param: str
    param_type: KernelTerm
    body_type: KernelTerm

    def __str__(self) -> str:
        return f"(Π {self.param}: {self.param_type}. {self.body_type})"


@dataclass(frozen=True)
class Sigma(KernelTerm):
    param: str
    param_type: KernelTerm
    body_type: KernelTerm

    def __str__(self) -> str:
        return f"(Σ {self.param}: {self.param_type}. {self.body_type})"


@dataclass(frozen=True)
class SumType(KernelTerm):
    left_type: KernelTerm
    right_type: KernelTerm

    def __str__(self) -> str:
        return f"(Sum {self.left_type} {self.right_type})"


@dataclass(frozen=True)
class Lam(KernelTerm):
    param: str
    param_type: KernelTerm
    body: KernelTerm

    def __str__(self) -> str:
        return f"(λ {self.param}: {self.param_type}. {self.body})"


@dataclass(frozen=True)
class App(KernelTerm):
    func: KernelTerm
    arg: KernelTerm

    def __str__(self) -> str:
        return f"({self.func} {self.arg})"


@dataclass(frozen=True)
class Pair(KernelTerm):
    first: KernelTerm
    second: KernelTerm

    def __str__(self) -> str:
        return f"(pair {self.first} {self.second})"


@dataclass(frozen=True)
class Inl(KernelTerm):
    value: KernelTerm
    right_type: KernelTerm

    def __str__(self) -> str:
        return f"(inl {self.value} {self.right_type})"


@dataclass(frozen=True)
class Inr(KernelTerm):
    left_type: KernelTerm
    value: KernelTerm

    def __str__(self) -> str:
        return f"(inr {self.left_type} {self.value})"


@dataclass(frozen=True)
class Fst(KernelTerm):
    pair: KernelTerm

    def __str__(self) -> str:
        return f"(fst {self.pair})"


@dataclass(frozen=True)
class Snd(KernelTerm):
    pair: KernelTerm

    def __str__(self) -> str:
        return f"(snd {self.pair})"


@dataclass(frozen=True)
class SumElim(KernelTerm):
    motive: KernelTerm
    left_case: KernelTerm
    right_case: KernelTerm
    target: KernelTerm

    def __str__(self) -> str:
        return f"(sum_elim {self.motive} {self.left_case} {self.right_case} {self.target})"


@dataclass(frozen=True)
class NatType(KernelTerm):
    def __str__(self) -> str:
        return "Nat"


@dataclass(frozen=True)
class NatLit(KernelTerm):
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("Nat literals must be non-negative")

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class NatSucc(KernelTerm):
    value: KernelTerm

    def __str__(self) -> str:
        return f"(succ {self.value})"


@dataclass(frozen=True)
class NatElim(KernelTerm):
    motive: KernelTerm
    base_case: KernelTerm
    step_case: KernelTerm
    target: KernelTerm

    def __str__(self) -> str:
        return f"(nat_elim {self.motive} {self.base_case} {self.step_case} {self.target})"


@dataclass(frozen=True)
class UnitType(KernelTerm):
    def __str__(self) -> str:
        return "Unit"


@dataclass(frozen=True)
class UnitIntro(KernelTerm):
    def __str__(self) -> str:
        return "unit"


@dataclass(frozen=True)
class EmptyType(KernelTerm):
    def __str__(self) -> str:
        return "Empty"


@dataclass(frozen=True)
class EqType(KernelTerm):
    type_term: KernelTerm
    left: KernelTerm
    right: KernelTerm

    def __str__(self) -> str:
        return f"(Eq {self.type_term} {self.left} {self.right})"


@dataclass(frozen=True)
class Refl(KernelTerm):
    value: KernelTerm

    def __str__(self) -> str:
        return f"(refl {self.value})"


@dataclass(frozen=True)
class Transport(KernelTerm):
    type_term: KernelTerm
    motive: KernelTerm
    left: KernelTerm
    right: KernelTerm
    equality_proof: KernelTerm
    value: KernelTerm

    def __str__(self) -> str:
        return (
            f"(transport {self.type_term} {self.motive} {self.left} "
            f"{self.right} {self.equality_proof} {self.value})"
        )


@dataclass(frozen=True)
class Absurd(KernelTerm):
    target_type: KernelTerm
    contradiction: KernelTerm

    def __str__(self) -> str:
        return f"(absurd {self.target_type} {self.contradiction})"


@dataclass(frozen=True)
class Ann(KernelTerm):
    term: KernelTerm
    annotation: KernelTerm

    def __str__(self) -> str:
        return f"({self.term} : {self.annotation})"


def free_vars(term: KernelTerm) -> set[str]:
    if isinstance(term, Var):
        return {term.name}
    if isinstance(term, (Sort, NatType, NatLit, UnitType, UnitIntro, EmptyType)):
        return set()
    if isinstance(term, NatSucc):
        return free_vars(term.value)
    if isinstance(term, App):
        return free_vars(term.func) | free_vars(term.arg)
    if isinstance(term, Pi):
        return free_vars(term.param_type) | (free_vars(term.body_type) - {term.param})
    if isinstance(term, Sigma):
        return free_vars(term.param_type) | (free_vars(term.body_type) - {term.param})
    if isinstance(term, SumType):
        return free_vars(term.left_type) | free_vars(term.right_type)
    if isinstance(term, Lam):
        return free_vars(term.param_type) | (free_vars(term.body) - {term.param})
    if isinstance(term, Pair):
        return free_vars(term.first) | free_vars(term.second)
    if isinstance(term, Inl):
        return free_vars(term.value) | free_vars(term.right_type)
    if isinstance(term, Inr):
        return free_vars(term.left_type) | free_vars(term.value)
    if isinstance(term, (Fst, Snd)):
        return free_vars(term.pair)
    if isinstance(term, SumElim):
        return (
            free_vars(term.motive)
            | free_vars(term.left_case)
            | free_vars(term.right_case)
            | free_vars(term.target)
        )
    if isinstance(term, EqType):
        return (
            free_vars(term.type_term)
            | free_vars(term.left)
            | free_vars(term.right)
        )
    if isinstance(term, Refl):
        return free_vars(term.value)
    if isinstance(term, Transport):
        return (
            free_vars(term.type_term)
            | free_vars(term.motive)
            | free_vars(term.left)
            | free_vars(term.right)
            | free_vars(term.equality_proof)
            | free_vars(term.value)
        )
    if isinstance(term, Absurd):
        return free_vars(term.target_type) | free_vars(term.contradiction)
    if isinstance(term, Ann):
        return free_vars(term.term) | free_vars(term.annotation)
    if isinstance(term, NatElim):
        return (
            free_vars(term.motive)
            | free_vars(term.base_case)
            | free_vars(term.step_case)
            | free_vars(term.target)
        )
    raise TypeError(f"Unsupported kernel term: {type(term).__name__}")


def fresh_name(base: str, used: set[str]) -> str:
    if base not in used:
        return base
    index = 1
    while f"{base}_{index}" in used:
        index += 1
    return f"{base}_{index}"
