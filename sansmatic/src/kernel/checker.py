from __future__ import annotations

from .context import KernelContext
from .errors import KernelTypeError
from .normalize import convertible, normalize, substitute
from .syntax import Absurd, Ann, App, EmptyType, EqType, Fst, Inl, Inr, KernelTerm, Lam, NatElim, NatLit, NatSucc, NatType, Pair, Pi, Refl, Sigma, SumElim, SumType, Snd, Sort, Transport, UnitIntro, UnitType, Var


class KernelTypeChecker:
    """
    Minimal trusted Sansmatic kernel.

    This stage provides a small auditable core:
    - universes via Sort(level)
    - dependent function types via Pi
    - dependent pair types via Sigma
    - lambdas and application
    - Nat and nat literals
    - identity types via Eq and refl
    """

    def infer(self, term: KernelTerm, ctx: KernelContext | None = None) -> KernelTerm:
        context = ctx or KernelContext()

        if isinstance(term, Sort):
            return Sort(term.level + 1)
        if isinstance(term, NatType):
            return Sort(0)
        if isinstance(term, UnitType):
            return Sort(0)
        if isinstance(term, EmptyType):
            return Sort(0)
        if isinstance(term, NatLit):
            return NatType()
        if isinstance(term, UnitIntro):
            return UnitType()
        if isinstance(term, NatSucc):
            self.check(term.value, NatType(), context)
            return NatType()
        if isinstance(term, Ann):
            self._expect_sort(self.infer(term.annotation, context), term.annotation)
            self.check(term.term, term.annotation, context)
            return term.annotation
        if isinstance(term, EqType):
            term_sort = self._expect_sort(self.infer(term.type_term, context), term.type_term)
            self.check(term.left, term.type_term, context)
            self.check(term.right, term.type_term, context)
            return Sort(term_sort.level)
        if isinstance(term, Refl):
            value_type = self.infer(term.value, context)
            return EqType(value_type, term.value, term.value)
        if isinstance(term, Transport):
            self._expect_sort(self.infer(term.type_term, context), term.type_term)
            motive_type = normalize(self.infer(term.motive, context))
            if not isinstance(motive_type, Pi):
                raise KernelTypeError(f"transport motive must have a Pi type, got {motive_type}")
            if not convertible(motive_type.param_type, term.type_term):
                raise KernelTypeError(
                    f"transport motive domain must match {term.type_term}, got {motive_type.param_type}"
                )
            self._expect_sort(motive_type.body_type, term.motive)
            self.check(term.left, term.type_term, context)
            self.check(term.right, term.type_term, context)
            self.check(
                term.equality_proof,
                EqType(term.type_term, term.left, term.right),
                context,
            )
            left_value_type = normalize(App(term.motive, term.left))
            self._expect_sort(self.infer(left_value_type, context), left_value_type)
            self.check(term.value, left_value_type, context)
            return normalize(App(term.motive, term.right))
        if isinstance(term, Absurd):
            self._expect_sort(self.infer(term.target_type, context), term.target_type)
            self.check(term.contradiction, EmptyType(), context)
            return term.target_type
        if isinstance(term, Var):
            return context.lookup(term.name)
        if isinstance(term, Pi):
            domain_sort = self._expect_sort(self.infer(term.param_type, context), term.param_type)
            body_ctx = context.extend(term.param, term.param_type)
            codomain_sort = self._expect_sort(self.infer(term.body_type, body_ctx), term.body_type)
            return Sort(max(domain_sort.level, codomain_sort.level))
        if isinstance(term, Sigma):
            domain_sort = self._expect_sort(self.infer(term.param_type, context), term.param_type)
            body_ctx = context.extend(term.param, term.param_type)
            codomain_sort = self._expect_sort(self.infer(term.body_type, body_ctx), term.body_type)
            return Sort(max(domain_sort.level, codomain_sort.level))
        if isinstance(term, SumType):
            left_sort = self._expect_sort(self.infer(term.left_type, context), term.left_type)
            right_sort = self._expect_sort(self.infer(term.right_type, context), term.right_type)
            return Sort(max(left_sort.level, right_sort.level))
        if isinstance(term, Lam):
            self._expect_sort(self.infer(term.param_type, context), term.param_type)
            body_ctx = context.extend(term.param, term.param_type)
            body_type = self.infer(term.body, body_ctx)
            return Pi(term.param, term.param_type, body_type)
        if isinstance(term, Pair):
            first_type = self.infer(term.first, context)
            second_type = self.infer(term.second, context)
            return Sigma("_", first_type, second_type)
        if isinstance(term, Inl):
            left_type = self.infer(term.value, context)
            self._expect_sort(self.infer(term.right_type, context), term.right_type)
            return SumType(left_type, term.right_type)
        if isinstance(term, Inr):
            self._expect_sort(self.infer(term.left_type, context), term.left_type)
            right_type = self.infer(term.value, context)
            return SumType(term.left_type, right_type)
        if isinstance(term, NatElim):
            motive_type = normalize(self.infer(term.motive, context))
            if not isinstance(motive_type, Pi):
                raise KernelTypeError(f"nat_elim motive must have a Pi type, got {motive_type}")
            if not convertible(motive_type.param_type, NatType()):
                raise KernelTypeError(f"nat_elim motive domain must be Nat, got {motive_type.param_type}")
            self._expect_sort(motive_type.body_type, term.motive)
            self.check(term.target, NatType(), context)

            zero_case_type = normalize(App(term.motive, NatLit(0)))
            self._expect_sort(self.infer(zero_case_type, context), zero_case_type)
            self.check(term.base_case, zero_case_type, context)

            step_expected = Pi(
                "k",
                NatType(),
                Pi(
                    "ih",
                    normalize(App(term.motive, Var("k"))),
                    normalize(App(term.motive, NatSucc(Var("k")))),
                ),
            )
            self.check(term.step_case, step_expected, context)
            return normalize(App(term.motive, term.target))
        if isinstance(term, SumElim):
            target_type = normalize(self.infer(term.target, context))
            if not isinstance(target_type, SumType):
                raise KernelTypeError(f"sum_elim target must have a Sum type, got {target_type}")
            motive_type = normalize(self.infer(term.motive, context))
            if not isinstance(motive_type, Pi):
                raise KernelTypeError(f"sum_elim motive must have a Pi type, got {motive_type}")
            if not convertible(motive_type.param_type, target_type):
                raise KernelTypeError(
                    f"sum_elim motive domain must match {target_type}, got {motive_type.param_type}"
                )
            self._expect_sort(motive_type.body_type, term.motive)
            left_target = Inl(Var("x"), target_type.right_type)
            left_expected = Pi(
                "x",
                target_type.left_type,
                normalize(App(term.motive, left_target)),
            )
            right_target = Inr(target_type.left_type, Var("y"))
            right_expected = Pi(
                "y",
                target_type.right_type,
                normalize(App(term.motive, right_target)),
            )
            self.check(term.left_case, left_expected, context)
            self.check(term.right_case, right_expected, context)
            return normalize(App(term.motive, term.target))
        if isinstance(term, App):
            func_type = normalize(self.infer(term.func, context))
            if not isinstance(func_type, Pi):
                raise KernelTypeError(f"Application requires a Pi type, got {func_type}")
            self.check(term.arg, func_type.param_type, context)
            return normalize(substitute(func_type.body_type, func_type.param, term.arg))
        if isinstance(term, Fst):
            pair_type = normalize(self.infer(term.pair, context))
            if not isinstance(pair_type, Sigma):
                raise KernelTypeError(f"fst requires a Sigma type, got {pair_type}")
            return pair_type.param_type
        if isinstance(term, Snd):
            pair_type = normalize(self.infer(term.pair, context))
            if not isinstance(pair_type, Sigma):
                raise KernelTypeError(f"snd requires a Sigma type, got {pair_type}")
            return normalize(substitute(pair_type.body_type, pair_type.param, Fst(term.pair)))
        raise KernelTypeError(f"Unsupported kernel term: {type(term).__name__}")

    def check(
        self,
        term: KernelTerm,
        expected_type: KernelTerm,
        ctx: KernelContext | None = None,
    ) -> None:
        context = ctx or KernelContext()
        expected_nf = normalize(expected_type)

        if isinstance(term, Refl) and isinstance(expected_nf, EqType):
            self.infer(expected_nf, context)
            self.check(term.value, expected_nf.type_term, context)
            if not convertible(term.value, expected_nf.left):
                raise KernelTypeError(
                    f"refl value {term.value} does not match equality left side {expected_nf.left}"
                )
            if not convertible(term.value, expected_nf.right):
                raise KernelTypeError(
                    f"refl value {term.value} does not match equality right side {expected_nf.right}"
                )
            return

        if isinstance(term, Pair) and isinstance(expected_nf, Sigma):
            self.infer(expected_nf, context)
            self.check(term.first, expected_nf.param_type, context)
            second_expected = normalize(substitute(expected_nf.body_type, expected_nf.param, term.first))
            self.check(term.second, second_expected, context)
            return

        if isinstance(term, Inl) and isinstance(expected_nf, SumType):
            self.infer(expected_nf, context)
            self.check(term.value, expected_nf.left_type, context)
            self._expect_sort(self.infer(term.right_type, context), term.right_type)
            if not convertible(term.right_type, expected_nf.right_type):
                raise KernelTypeError(
                    f"inl annotation {term.right_type} does not match expected right type {expected_nf.right_type}"
                )
            return

        if isinstance(term, Inr) and isinstance(expected_nf, SumType):
            self.infer(expected_nf, context)
            self._expect_sort(self.infer(term.left_type, context), term.left_type)
            if not convertible(term.left_type, expected_nf.left_type):
                raise KernelTypeError(
                    f"inr annotation {term.left_type} does not match expected left type {expected_nf.left_type}"
                )
            self.check(term.value, expected_nf.right_type, context)
            return

        if isinstance(term, Lam) and isinstance(expected_nf, Pi):
            self._expect_sort(self.infer(term.param_type, context), term.param_type)
            if not convertible(term.param_type, expected_nf.param_type):
                raise KernelTypeError(
                    f"Lambda annotation {term.param_type} does not match expected domain {expected_nf.param_type}"
                )
            body_ctx = context.extend(term.param, expected_nf.param_type)
            body_expected = normalize(substitute(expected_nf.body_type, expected_nf.param, Var(term.param)))
            self.check(term.body, body_expected, body_ctx)
            return

        actual_type = self.infer(term, context)
        if not convertible(actual_type, expected_type):
            raise KernelTypeError(f"Expected {expected_type}, got {actual_type}")

    @staticmethod
    def _expect_sort(term_type: KernelTerm, origin: KernelTerm) -> Sort:
        normalized = normalize(term_type)
        if not isinstance(normalized, Sort):
            raise KernelTypeError(f"Expected a universe for {origin}, got {normalized}")
        return normalized
