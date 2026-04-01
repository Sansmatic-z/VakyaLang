from __future__ import annotations

from .syntax import (
    Absurd,
    Ann,
    App,
    EmptyType,
    EqType,
    Fst,
    Inl,
    Inr,
    KernelTerm,
    Lam,
    NatElim,
    NatLit,
    NatSucc,
    NatType,
    Pair,
    Pi,
    Refl,
    Sigma,
    SumElim,
    SumType,
    Snd,
    Sort,
    Transport,
    UnitIntro,
    UnitType,
    Var,
    free_vars,
    fresh_name,
)


def substitute(term: KernelTerm, name: str, replacement: KernelTerm) -> KernelTerm:
    if isinstance(term, Var):
        return replacement if term.name == name else term
    if isinstance(term, (Sort, NatType, NatLit, UnitType, UnitIntro, EmptyType)):
        return term
    if isinstance(term, NatSucc):
        return NatSucc(substitute(term.value, name, replacement))
    if isinstance(term, App):
        return App(
            substitute(term.func, name, replacement),
            substitute(term.arg, name, replacement),
        )
    if isinstance(term, Pi):
        param_type = substitute(term.param_type, name, replacement)
        if term.param == name:
            return Pi(term.param, param_type, term.body_type)
        binder, body_type = _substitute_under_binder(term.param, term.body_type, name, replacement)
        return Pi(binder, param_type, body_type)
    if isinstance(term, Sigma):
        param_type = substitute(term.param_type, name, replacement)
        if term.param == name:
            return Sigma(term.param, param_type, term.body_type)
        binder, body_type = _substitute_under_binder(term.param, term.body_type, name, replacement)
        return Sigma(binder, param_type, body_type)
    if isinstance(term, SumType):
        return SumType(
            substitute(term.left_type, name, replacement),
            substitute(term.right_type, name, replacement),
        )
    if isinstance(term, Lam):
        param_type = substitute(term.param_type, name, replacement)
        if term.param == name:
            return Lam(term.param, param_type, term.body)
        binder, body = _substitute_under_binder(term.param, term.body, name, replacement)
        return Lam(binder, param_type, body)
    if isinstance(term, Pair):
        return Pair(
            substitute(term.first, name, replacement),
            substitute(term.second, name, replacement),
        )
    if isinstance(term, Inl):
        return Inl(
            substitute(term.value, name, replacement),
            substitute(term.right_type, name, replacement),
        )
    if isinstance(term, Inr):
        return Inr(
            substitute(term.left_type, name, replacement),
            substitute(term.value, name, replacement),
        )
    if isinstance(term, Fst):
        return Fst(substitute(term.pair, name, replacement))
    if isinstance(term, Snd):
        return Snd(substitute(term.pair, name, replacement))
    if isinstance(term, SumElim):
        return SumElim(
            substitute(term.motive, name, replacement),
            substitute(term.left_case, name, replacement),
            substitute(term.right_case, name, replacement),
            substitute(term.target, name, replacement),
        )
    if isinstance(term, EqType):
        return EqType(
            substitute(term.type_term, name, replacement),
            substitute(term.left, name, replacement),
            substitute(term.right, name, replacement),
        )
    if isinstance(term, Refl):
        return Refl(substitute(term.value, name, replacement))
    if isinstance(term, Transport):
        return Transport(
            substitute(term.type_term, name, replacement),
            substitute(term.motive, name, replacement),
            substitute(term.left, name, replacement),
            substitute(term.right, name, replacement),
            substitute(term.equality_proof, name, replacement),
            substitute(term.value, name, replacement),
        )
    if isinstance(term, Absurd):
        return Absurd(
            substitute(term.target_type, name, replacement),
            substitute(term.contradiction, name, replacement),
        )
    if isinstance(term, Ann):
        return Ann(
            substitute(term.term, name, replacement),
            substitute(term.annotation, name, replacement),
        )
    if isinstance(term, NatElim):
        return NatElim(
            substitute(term.motive, name, replacement),
            substitute(term.base_case, name, replacement),
            substitute(term.step_case, name, replacement),
            substitute(term.target, name, replacement),
        )
    raise TypeError(f"Unsupported kernel term: {type(term).__name__}")


def _substitute_under_binder(
    binder: str,
    body: KernelTerm,
    target: str,
    replacement: KernelTerm,
) -> tuple[str, KernelTerm]:
    if binder not in free_vars(replacement):
        return binder, substitute(body, target, replacement)

    used = free_vars(body) | free_vars(replacement) | {target}
    fresh = fresh_name(binder, used)
    renamed_body = substitute(body, binder, Var(fresh))
    return fresh, substitute(renamed_body, target, replacement)


def normalize(term: KernelTerm) -> KernelTerm:
    if isinstance(term, (Sort, Var, NatType, NatLit, UnitType, UnitIntro, EmptyType)):
        return term
    if isinstance(term, NatSucc):
        value = normalize(term.value)
        if isinstance(value, NatLit):
            return NatLit(value.value + 1)
        return NatSucc(value)
    if isinstance(term, Pi):
        return Pi(
            term.param,
            normalize(term.param_type),
            normalize(term.body_type),
        )
    if isinstance(term, Sigma):
        return Sigma(
            term.param,
            normalize(term.param_type),
            normalize(term.body_type),
        )
    if isinstance(term, SumType):
        return SumType(
            normalize(term.left_type),
            normalize(term.right_type),
        )
    if isinstance(term, Lam):
        return Lam(
            term.param,
            normalize(term.param_type),
            normalize(term.body),
        )
    if isinstance(term, App):
        func = normalize(term.func)
        arg = normalize(term.arg)
        if isinstance(func, Lam):
            return normalize(substitute(func.body, func.param, arg))
        return App(func, arg)
    if isinstance(term, Pair):
        return Pair(
            normalize(term.first),
            normalize(term.second),
        )
    if isinstance(term, Inl):
        return Inl(
            normalize(term.value),
            normalize(term.right_type),
        )
    if isinstance(term, Inr):
        return Inr(
            normalize(term.left_type),
            normalize(term.value),
        )
    if isinstance(term, Fst):
        pair = normalize(term.pair)
        if isinstance(pair, Pair):
            return normalize(pair.first)
        return Fst(pair)
    if isinstance(term, Snd):
        pair = normalize(term.pair)
        if isinstance(pair, Pair):
            return normalize(pair.second)
        return Snd(pair)
    if isinstance(term, SumElim):
        motive = normalize(term.motive)
        left_case = normalize(term.left_case)
        right_case = normalize(term.right_case)
        target = normalize(term.target)
        if isinstance(target, Inl):
            return normalize(App(left_case, target.value))
        if isinstance(target, Inr):
            return normalize(App(right_case, target.value))
        return SumElim(motive, left_case, right_case, target)
    if isinstance(term, EqType):
        return EqType(
            normalize(term.type_term),
            normalize(term.left),
            normalize(term.right),
        )
    if isinstance(term, Refl):
        return Refl(normalize(term.value))
    if isinstance(term, Transport):
        type_term = normalize(term.type_term)
        motive = normalize(term.motive)
        left = normalize(term.left)
        right = normalize(term.right)
        equality_proof = normalize(term.equality_proof)
        value = normalize(term.value)
        if isinstance(equality_proof, Refl):
            return value
        return Transport(type_term, motive, left, right, equality_proof, value)
    if isinstance(term, Absurd):
        return Absurd(
            normalize(term.target_type),
            normalize(term.contradiction),
        )
    if isinstance(term, Ann):
        return normalize(term.term)
    if isinstance(term, NatElim):
        motive = normalize(term.motive)
        base_case = normalize(term.base_case)
        step_case = normalize(term.step_case)
        target = normalize(term.target)
        if isinstance(target, NatLit):
            if target.value == 0:
                return base_case
            predecessor = NatLit(target.value - 1)
            recursive = normalize(NatElim(motive, base_case, step_case, predecessor))
            return normalize(App(App(step_case, predecessor), recursive))
        return NatElim(motive, base_case, step_case, target)
    raise TypeError(f"Unsupported kernel term: {type(term).__name__}")


def alpha_equivalent(
    left: KernelTerm,
    right: KernelTerm,
    left_env: dict[str, int] | None = None,
    right_env: dict[str, int] | None = None,
    depth: int = 0,
) -> bool:
    left_env = {} if left_env is None else left_env
    right_env = {} if right_env is None else right_env

    if type(left) is not type(right):
        return False

    if isinstance(left, Sort):
        return left.level == right.level
    if isinstance(left, NatType):
        return True
    if isinstance(left, NatLit):
        return left.value == right.value
    if isinstance(left, UnitType):
        return True
    if isinstance(left, UnitIntro):
        return True
    if isinstance(left, EmptyType):
        return True
    if isinstance(left, NatSucc):
        return alpha_equivalent(left.value, right.value, left_env, right_env, depth)
    if isinstance(left, Var):
        left_bound = left.name in left_env
        right_bound = right.name in right_env
        if left_bound or right_bound:
            return left_env.get(left.name) == right_env.get(right.name)
        return left.name == right.name
    if isinstance(left, App):
        return alpha_equivalent(left.func, right.func, left_env, right_env, depth) and alpha_equivalent(
            left.arg, right.arg, left_env, right_env, depth
        )
    if isinstance(left, Pair):
        return (
            alpha_equivalent(left.first, right.first, left_env, right_env, depth)
            and alpha_equivalent(left.second, right.second, left_env, right_env, depth)
        )
    if isinstance(left, Inl):
        return (
            alpha_equivalent(left.value, right.value, left_env, right_env, depth)
            and alpha_equivalent(left.right_type, right.right_type, left_env, right_env, depth)
        )
    if isinstance(left, Inr):
        return (
            alpha_equivalent(left.left_type, right.left_type, left_env, right_env, depth)
            and alpha_equivalent(left.value, right.value, left_env, right_env, depth)
        )
    if isinstance(left, Fst):
        return alpha_equivalent(left.pair, right.pair, left_env, right_env, depth)
    if isinstance(left, Snd):
        return alpha_equivalent(left.pair, right.pair, left_env, right_env, depth)
    if isinstance(left, SumElim):
        return (
            alpha_equivalent(left.motive, right.motive, left_env, right_env, depth)
            and alpha_equivalent(left.left_case, right.left_case, left_env, right_env, depth)
            and alpha_equivalent(left.right_case, right.right_case, left_env, right_env, depth)
            and alpha_equivalent(left.target, right.target, left_env, right_env, depth)
        )
    if isinstance(left, EqType):
        return (
            alpha_equivalent(left.type_term, right.type_term, left_env, right_env, depth)
            and alpha_equivalent(left.left, right.left, left_env, right_env, depth)
            and alpha_equivalent(left.right, right.right, left_env, right_env, depth)
        )
    if isinstance(left, Refl):
        return alpha_equivalent(left.value, right.value, left_env, right_env, depth)
    if isinstance(left, Transport):
        return (
            alpha_equivalent(left.type_term, right.type_term, left_env, right_env, depth)
            and alpha_equivalent(left.motive, right.motive, left_env, right_env, depth)
            and alpha_equivalent(left.left, right.left, left_env, right_env, depth)
            and alpha_equivalent(left.right, right.right, left_env, right_env, depth)
            and alpha_equivalent(
                left.equality_proof, right.equality_proof, left_env, right_env, depth
            )
            and alpha_equivalent(left.value, right.value, left_env, right_env, depth)
        )
    if isinstance(left, Absurd):
        return (
            alpha_equivalent(left.target_type, right.target_type, left_env, right_env, depth)
            and alpha_equivalent(left.contradiction, right.contradiction, left_env, right_env, depth)
        )
    if isinstance(left, Ann):
        return (
            alpha_equivalent(left.term, right.term, left_env, right_env, depth)
            and alpha_equivalent(left.annotation, right.annotation, left_env, right_env, depth)
        )
    if isinstance(left, NatElim):
        return (
            alpha_equivalent(left.motive, right.motive, left_env, right_env, depth)
            and alpha_equivalent(left.base_case, right.base_case, left_env, right_env, depth)
            and alpha_equivalent(left.step_case, right.step_case, left_env, right_env, depth)
            and alpha_equivalent(left.target, right.target, left_env, right_env, depth)
        )
    if isinstance(left, Pi):
        if not alpha_equivalent(left.param_type, right.param_type, left_env, right_env, depth):
            return False
        return alpha_equivalent(
            left.body_type,
            right.body_type,
            {**left_env, left.param: depth},
            {**right_env, right.param: depth},
            depth + 1,
        )
    if isinstance(left, Sigma):
        if not alpha_equivalent(left.param_type, right.param_type, left_env, right_env, depth):
            return False
        return alpha_equivalent(
            left.body_type,
            right.body_type,
            {**left_env, left.param: depth},
            {**right_env, right.param: depth},
            depth + 1,
        )
    if isinstance(left, SumType):
        return (
            alpha_equivalent(left.left_type, right.left_type, left_env, right_env, depth)
            and alpha_equivalent(left.right_type, right.right_type, left_env, right_env, depth)
        )
    if isinstance(left, Lam):
        if not alpha_equivalent(left.param_type, right.param_type, left_env, right_env, depth):
            return False
        return alpha_equivalent(
            left.body,
            right.body,
            {**left_env, left.param: depth},
            {**right_env, right.param: depth},
            depth + 1,
        )
    raise TypeError(f"Unsupported kernel term: {type(left).__name__}")


def convertible(left: KernelTerm, right: KernelTerm) -> bool:
    return alpha_equivalent(normalize(left), normalize(right))
