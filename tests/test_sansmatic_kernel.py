import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sansmatic.src.kernel import (
    Absurd,
    Ann,
    App,
    EmptyType,
    EqType,
    Fst,
    Inl,
    Inr,
    KernelContext,
    KernelElaborator,
    KernelJudgment,
    KernelParser,
    KernelProofVerifier,
    KernelScopeError,
    KernelTypeChecker,
    KernelTypeError,
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
    Sort,
    Snd,
    Transport,
    UnitIntro,
    UnitType,
    Var,
    alpha_equivalent,
    convertible,
    normalize,
    substitute,
)


class SansmaticKernelTests(unittest.TestCase):
    def setUp(self):
        self.checker = KernelTypeChecker()
        self.parser = KernelParser()
        self.elaborator = KernelElaborator()

    def test_beta_normalization_reduces_lambda_application(self):
        term = App(Lam("x", NatType(), Var("x")), NatLit(3))

        self.assertEqual(normalize(term), NatLit(3))

    def test_alpha_equivalence_respects_binders(self):
        left = Lam("x", NatType(), Var("x"))
        right = Lam("y", NatType(), Var("y"))

        self.assertTrue(alpha_equivalent(left, right))

    def test_convertibility_uses_normal_forms(self):
        left = App(Lam("x", NatType(), Var("x")), NatLit(2))
        right = NatLit(2)

        self.assertTrue(convertible(left, right))

    def test_infer_nat_type_universe(self):
        self.assertEqual(self.checker.infer(NatType()), Sort(0))

    def test_infer_unit_and_empty_type_universe(self):
        self.assertEqual(self.checker.infer(UnitType()), Sort(0))
        self.assertEqual(self.checker.infer(EmptyType()), Sort(0))

    def test_infer_unit_intro_type(self):
        self.assertEqual(self.checker.infer(UnitIntro()), UnitType())

    def test_infer_identity_lambda_type(self):
        term = Lam("x", NatType(), Var("x"))

        self.assertEqual(self.checker.infer(term), Pi("x", NatType(), NatType()))

    def test_infer_equality_type_universe(self):
        term = EqType(NatType(), NatLit(2), NatLit(2))

        self.assertEqual(self.checker.infer(term), Sort(0))

    def test_infer_refl_produces_identity_type(self):
        term = Refl(NatLit(4))

        self.assertEqual(
            self.checker.infer(term),
            EqType(NatType(), NatLit(4), NatLit(4)),
        )

    def test_infer_application_result(self):
        identity = Lam("x", NatType(), Var("x"))
        term = App(identity, NatLit(5))

        self.assertEqual(self.checker.infer(term), NatType())

    def test_infer_sigma_type_universe(self):
        term = Sigma("x", NatType(), EqType(NatType(), Var("x"), Var("x")))

        self.assertEqual(self.checker.infer(term), Sort(0))

    def test_infer_sum_type_universe(self):
        term = SumType(NatType(), UnitType())

        self.assertEqual(self.checker.infer(term), Sort(0))

    def test_check_pair_against_dependent_sigma(self):
        term = Pair(NatLit(2), Refl(NatLit(2)))
        expected = Sigma("x", NatType(), EqType(NatType(), Var("x"), Var("x")))

        self.checker.check(term, expected)

    def test_pair_projection_normalizes(self):
        pair = Pair(NatLit(2), Refl(NatLit(2)))

        self.assertEqual(normalize(Fst(pair)), NatLit(2))
        self.assertEqual(normalize(Snd(pair)), Refl(NatLit(2)))

    def test_sum_injections_typecheck_against_sum(self):
        self.checker.check(Inl(NatLit(2), UnitType()), SumType(NatType(), UnitType()))
        self.checker.check(Inr(NatType(), UnitIntro()), SumType(NatType(), UnitType()))

    def test_projection_types_follow_sigma(self):
        pair = Ann(
            Pair(NatLit(3), Refl(NatLit(3))),
            Sigma("x", NatType(), EqType(NatType(), Var("x"), Var("x"))),
        )

        self.assertEqual(self.checker.infer(Fst(pair)), NatType())
        self.assertEqual(
            self.checker.infer(Snd(pair)),
            EqType(NatType(), NatLit(3), NatLit(3)),
        )

    def test_nat_succ_normalizes_literal_successor(self):
        self.assertEqual(normalize(NatSucc(NatLit(2))), NatLit(3))

    def test_nat_elim_checks_and_normalizes_identity_recursion(self):
        term = NatElim(
            Lam("n", NatType(), NatType()),
            NatLit(0),
            Lam("k", NatType(), Lam("ih", NatType(), NatSucc(Var("ih")))),
            NatLit(3),
        )

        self.assertEqual(self.checker.infer(term), NatType())
        self.assertEqual(normalize(term), NatLit(3))

    def test_transport_checks_and_normalizes_refl_case(self):
        term = Transport(
            NatType(),
            Lam("n", NatType(), EqType(NatType(), Var("n"), Var("n"))),
            NatLit(2),
            NatLit(2),
            Refl(NatLit(2)),
            Refl(NatLit(2)),
        )

        self.assertEqual(
            self.checker.infer(term),
            EqType(NatType(), NatLit(2), NatLit(2)),
        )
        self.assertEqual(normalize(term), Refl(NatLit(2)))

    def test_absurd_eliminates_empty_to_any_type(self):
        ctx = KernelContext().extend("contra", EmptyType())
        term = Absurd(NatType(), Var("contra"))

        self.assertEqual(self.checker.infer(term, ctx), NatType())
        self.assertEqual(normalize(term), Absurd(NatType(), Var("contra")))

    def test_sum_elim_checks_and_normalizes_left_branch(self):
        term = SumElim(
            Lam("s", SumType(NatType(), UnitType()), NatType()),
            Lam("x", NatType(), Var("x")),
            Lam("u", UnitType(), NatLit(0)),
            Inl(NatLit(4), UnitType()),
        )

        self.assertEqual(self.checker.infer(term), NatType())
        self.assertEqual(normalize(term), NatLit(4))

    def test_dependent_function_type_is_inferred(self):
        term = Lam("A", Sort(0), Lam("x", Var("A"), Var("x")))

        inferred = self.checker.infer(term)

        self.assertEqual(
            inferred,
            Pi("A", Sort(0), Pi("x", Var("A"), Var("A"))),
        )

    def test_check_accepts_lambda_against_pi_type(self):
        term = Lam("x", NatType(), Var("x"))
        expected = Pi("n", NatType(), NatType())

        self.checker.check(term, expected)

    def test_annotation_term_checks_and_infers_annotation(self):
        term = Ann(NatLit(3), NatType())

        self.assertEqual(self.checker.infer(term), NatType())
        self.assertEqual(normalize(term), NatLit(3))

    def test_check_accepts_refl_against_matching_identity_type(self):
        term = Refl(NatLit(2))
        expected = EqType(NatType(), NatLit(2), NatLit(2))

        self.checker.check(term, expected)

    def test_check_rejects_refl_against_nonmatching_identity_type(self):
        term = Refl(NatLit(2))
        expected = EqType(NatType(), NatLit(2), NatLit(3))

        with self.assertRaisesRegex(KernelTypeError, "right side"):
            self.checker.check(term, expected)

    def test_substitution_avoids_variable_capture(self):
        term = Lam("y", NatType(), Var("x"))
        substituted = substitute(term, "x", Var("y"))

        self.assertIsInstance(substituted, Lam)
        self.assertNotEqual(substituted.param, "y")
        self.assertEqual(substituted.body, Var("y"))

    def test_unbound_variable_is_rejected(self):
        with self.assertRaises(KernelScopeError):
            self.checker.infer(Var("missing"))

    def test_application_of_non_function_is_rejected(self):
        with self.assertRaisesRegex(KernelTypeError, "Pi type"):
            self.checker.infer(App(NatLit(1), NatLit(2)))

    def test_argument_type_mismatch_is_rejected(self):
        ctx = KernelContext().extend("X", Sort(0))
        identity = Lam("x", NatType(), Var("x"))

        with self.assertRaisesRegex(KernelTypeError, "Expected Nat"):
            self.checker.check(App(identity, Var("X")), NatType(), ctx)

    def test_parser_handles_lambda_pi_and_application(self):
        parsed = self.parser.parse_term("λ x: Nat. x")
        function_type = self.parser.parse_term("Π x: Nat. Nat")
        applied = self.parser.parse_term("(λ x: Nat. x) 3")

        self.assertEqual(parsed, Lam("x", NatType(), Var("x")))
        self.assertEqual(function_type, Pi("x", NatType(), NatType()))
        self.assertEqual(normalize(applied), NatLit(3))

    def test_parser_handles_identity_type_and_refl(self):
        eq_term = self.parser.parse_term("Eq Nat 2 2")
        refl_term = self.parser.parse_term("refl 2")

        self.assertEqual(eq_term, EqType(NatType(), NatLit(2), NatLit(2)))
        self.assertEqual(refl_term, Refl(NatLit(2)))

    def test_parser_handles_explicit_annotation(self):
        annotated = self.parser.parse_term("(3 : Nat)")

        self.assertEqual(annotated, Ann(NatLit(3), NatType()))

    def test_parser_handles_sigma_pair_and_projections(self):
        sigma_term = self.parser.parse_term("Σ x: Nat. Eq Nat x x")
        pair_term = self.parser.parse_term("pair 2 (refl 2)")
        fst_term = self.parser.parse_term("fst (pair 2 (refl 2))")
        snd_term = self.parser.parse_term("snd (pair 2 (refl 2))")

        self.assertEqual(sigma_term, Sigma("x", NatType(), EqType(NatType(), Var("x"), Var("x"))))
        self.assertEqual(pair_term, Pair(NatLit(2), Refl(NatLit(2))))
        self.assertEqual(normalize(fst_term), NatLit(2))
        self.assertEqual(normalize(snd_term), Refl(NatLit(2)))

    def test_parser_handles_nat_succ_and_eliminator(self):
        succ_term = self.parser.parse_term("succ 2")
        elim_term = self.parser.parse_term(
            "nat_elim (λ n: Nat. Nat) 0 (λ k: Nat. λ ih: Nat. succ ih) 2"
        )

        self.assertEqual(succ_term, NatSucc(NatLit(2)))
        self.assertEqual(normalize(elim_term), NatLit(2))

    def test_parser_handles_transport(self):
        transport_term = self.parser.parse_term(
            "transport Nat (λ n: Nat. Eq Nat n n) 2 2 (refl 2) (refl 2)"
        )

        self.assertEqual(
            transport_term,
            Transport(
                NatType(),
                Lam("n", NatType(), EqType(NatType(), Var("n"), Var("n"))),
                NatLit(2),
                NatLit(2),
                Refl(NatLit(2)),
                Refl(NatLit(2)),
            ),
        )
        self.assertEqual(normalize(transport_term), Refl(NatLit(2)))

    def test_parser_handles_unit_empty_and_absurd(self):
        unit_type = self.parser.parse_term("Unit")
        unit_value = self.parser.parse_term("unit")
        empty_type = self.parser.parse_term("Empty")
        absurd_term = self.parser.parse_term("absurd Nat contra")

        self.assertEqual(unit_type, UnitType())
        self.assertEqual(unit_value, UnitIntro())
        self.assertEqual(empty_type, EmptyType())
        self.assertEqual(absurd_term, Absurd(NatType(), Var("contra")))

    def test_parser_handles_sum_injections_and_eliminator(self):
        sum_type = self.parser.parse_term("Sum Nat Unit")
        inl_term = self.parser.parse_term("inl 3 Unit")
        inr_term = self.parser.parse_term("inr Nat unit")
        elim_term = self.parser.parse_term(
            "sum_elim (λ s: Sum Nat Unit. Nat) (λ x: Nat. x) (λ u: Unit. 0) (inl 3 Unit)"
        )

        self.assertEqual(sum_type, SumType(NatType(), UnitType()))
        self.assertEqual(inl_term, Inl(NatLit(3), UnitType()))
        self.assertEqual(inr_term, Inr(NatType(), UnitIntro()))
        self.assertEqual(normalize(elim_term), NatLit(3))

    def test_parser_desugars_arrow_to_pi(self):
        parsed = self.parser.parse_term("Nat -> Nat")

        self.assertEqual(parsed, Pi("_", NatType(), NatType()))

    def test_elaborator_builds_judgment_from_structured_spec(self):
        judgment = self.elaborator.elaborate_judgment(
            {
                "context": [{"name": "A", "type": "Type0"}],
                "term": {"kind": "lam", "param": "x", "param_type": "Nat", "body": "x"},
                "type": "Π x: Nat. Nat",
            }
        )

        self.assertIsInstance(judgment, KernelJudgment)
        self.assertEqual(judgment.context.lookup("A"), Sort(0))
        self.assertEqual(judgment.term, Lam("x", NatType(), Var("x")))

    def test_elaborator_builds_identity_terms(self):
        term = self.elaborator.elaborate_term(
            {
                "kind": "eq",
                "type_term": "Nat",
                "left": 2,
                "right": 2,
            }
        )
        proof = self.elaborator.elaborate_term(
            {
                "kind": "refl",
                "value": 2,
            }
        )

        self.assertEqual(term, EqType(NatType(), NatLit(2), NatLit(2)))
        self.assertEqual(proof, Refl(NatLit(2)))

    def test_elaborator_builds_annotation_term(self):
        term = self.elaborator.elaborate_term(
            {
                "kind": "ann",
                "term": 3,
                "annotation": "Nat",
            }
        )

        self.assertEqual(term, Ann(NatLit(3), NatType()))

    def test_elaborator_builds_sigma_and_pair_terms(self):
        sigma = self.elaborator.elaborate_term(
            {
                "kind": "sigma",
                "param": "x",
                "param_type": "Nat",
                "body_type": {"kind": "eq", "type_term": "Nat", "left": "x", "right": "x"},
            }
        )
        pair = self.elaborator.elaborate_term(
            {
                "kind": "pair",
                "first": 2,
                "second": {"kind": "refl", "value": 2},
            }
        )

        self.assertEqual(sigma, Sigma("x", NatType(), EqType(NatType(), Var("x"), Var("x"))))
        self.assertEqual(pair, Pair(NatLit(2), Refl(NatLit(2))))

    def test_elaborator_builds_nat_eliminator_terms(self):
        term = self.elaborator.elaborate_term(
            {
                "kind": "nat_elim",
                "motive": {"kind": "lam", "param": "n", "param_type": "Nat", "body": "Nat"},
                "base_case": 0,
                "step_case": {
                    "kind": "lam",
                    "param": "k",
                    "param_type": "Nat",
                    "body": {
                        "kind": "lam",
                        "param": "ih",
                        "param_type": "Nat",
                        "body": {"kind": "succ", "value": "ih"},
                    },
                },
                "target": 2,
            }
        )

        self.assertEqual(
            term,
            NatElim(
                Lam("n", NatType(), NatType()),
                NatLit(0),
                Lam("k", NatType(), Lam("ih", NatType(), NatSucc(Var("ih")))),
                NatLit(2),
            ),
        )

    def test_elaborator_builds_transport_terms(self):
        term = self.elaborator.elaborate_term(
            {
                "kind": "transport",
                "type_term": "Nat",
                "motive": {
                    "kind": "lam",
                    "param": "n",
                    "param_type": "Nat",
                    "body": {"kind": "eq", "type_term": "Nat", "left": "n", "right": "n"},
                },
                "left": 2,
                "right": 2,
                "equality_proof": {"kind": "refl", "value": 2},
                "value": {"kind": "refl", "value": 2},
            }
        )

        self.assertEqual(
            term,
            Transport(
                NatType(),
                Lam("n", NatType(), EqType(NatType(), Var("n"), Var("n"))),
                NatLit(2),
                NatLit(2),
                Refl(NatLit(2)),
                Refl(NatLit(2)),
            ),
        )

    def test_elaborator_builds_unit_empty_and_absurd_terms(self):
        unit_type = self.elaborator.elaborate_term({"kind": "unit_type"})
        unit_value = self.elaborator.elaborate_term({"kind": "unit"})
        empty_type = self.elaborator.elaborate_term({"kind": "empty_type"})
        absurd_term = self.elaborator.elaborate_term(
            {
                "kind": "absurd",
                "target_type": "Nat",
                "contradiction": {"kind": "var", "name": "contra"},
            }
        )

        self.assertEqual(unit_type, UnitType())
        self.assertEqual(unit_value, UnitIntro())
        self.assertEqual(empty_type, EmptyType())
        self.assertEqual(absurd_term, Absurd(NatType(), Var("contra")))

    def test_elaborator_builds_sum_terms(self):
        sum_type = self.elaborator.elaborate_term(
            {"kind": "sum", "left_type": "Nat", "right_type": "Unit"}
        )
        inl_term = self.elaborator.elaborate_term(
            {"kind": "inl", "value": 3, "right_type": "Unit"}
        )
        elim_term = self.elaborator.elaborate_term(
            {
                "kind": "sum_elim",
                "motive": {
                    "kind": "lam",
                    "param": "s",
                    "param_type": {"kind": "sum", "left_type": "Nat", "right_type": "Unit"},
                    "body": "Nat",
                },
                "left_case": {
                    "kind": "lam",
                    "param": "x",
                    "param_type": "Nat",
                    "body": "x",
                },
                "right_case": {
                    "kind": "lam",
                    "param": "u",
                    "param_type": "Unit",
                    "body": 0,
                },
                "target": {"kind": "inl", "value": 3, "right_type": "Unit"},
            }
        )

        self.assertEqual(sum_type, SumType(NatType(), UnitType()))
        self.assertEqual(inl_term, Inl(NatLit(3), UnitType()))
        self.assertEqual(
            elim_term,
            SumElim(
                Lam("s", SumType(NatType(), UnitType()), NatType()),
                Lam("x", NatType(), Var("x")),
                Lam("u", UnitType(), NatLit(0)),
                Inl(NatLit(3), UnitType()),
            ),
        )

    def test_kernel_verifier_issues_and_verifies_certificate(self):
        verifier = KernelProofVerifier()

        certificate = verifier.verify(
            {
                "term": "λ x: Nat. x",
                "type": "Π n: Nat. Nat",
            }
        )

        self.assertTrue(certificate.verified)
        self.assertEqual(certificate.payload["kind"], "sansmatic_kernel_certificate")
        self.assertTrue(verifier.verify_certificate(certificate.payload))

    def test_kernel_verifier_rejects_tampered_certificate(self):
        verifier = KernelProofVerifier()
        certificate = verifier.verify(
            {
                "term": "λ x: Nat. x",
                "type": "Π n: Nat. Nat",
            }
        )

        tampered = dict(certificate.payload)
        tampered["judgment"] = "⊢ tampered"

        self.assertFalse(verifier.verify_certificate(tampered))

    def test_kernel_verifier_reports_type_failure(self):
        verifier = KernelProofVerifier()
        certificate = verifier.verify(
            {
                "term": "3",
                "type": "Π x: Nat. Nat",
            }
        )

        self.assertFalse(certificate.verified)
        self.assertIn("Expected", certificate.reason)

    def test_kernel_verifier_handles_identity_judgment(self):
        verifier = KernelProofVerifier()
        certificate = verifier.verify(
            {
                "term": "refl 5",
                "type": "Eq Nat 5 5",
            }
        )

        self.assertTrue(certificate.verified)
        self.assertIn("Eq Nat 5 5", certificate.payload["expected_type"])

    def test_kernel_verifier_handles_sigma_witness_judgment(self):
        verifier = KernelProofVerifier()
        certificate = verifier.verify(
            {
                "term": "(pair 2 (refl 2) : Σ x: Nat. Eq Nat x x)",
                "type": "Σ x: Nat. Eq Nat x x",
            }
        )

        self.assertTrue(certificate.verified)
        self.assertIn("Σ x: Nat", certificate.payload["expected_type"])

    def test_kernel_verifier_handles_nat_elim_judgment(self):
        verifier = KernelProofVerifier()
        certificate = verifier.verify(
            {
                "term": "nat_elim (λ n: Nat. Nat) 0 (λ k: Nat. λ ih: Nat. succ ih) 2",
                "type": "Nat",
            }
        )

        self.assertTrue(certificate.verified)
        self.assertEqual(certificate.payload["normalized_term"], "2")

    def test_kernel_verifier_handles_transport_judgment(self):
        verifier = KernelProofVerifier()
        certificate = verifier.verify(
            {
                "term": "transport Nat (λ n: Nat. Eq Nat n n) 2 2 (refl 2) (refl 2)",
                "type": "Eq Nat 2 2",
            }
        )

        self.assertTrue(certificate.verified)
        self.assertEqual(certificate.payload["normalized_term"], "(refl 2)")

    def test_kernel_verifier_handles_absurd_judgment(self):
        verifier = KernelProofVerifier()
        certificate = verifier.verify(
            {
                "context": [{"name": "contra", "type": "Empty"}],
                "term": "absurd Nat contra",
                "type": "Nat",
            }
        )

        self.assertTrue(certificate.verified)
        self.assertEqual(certificate.payload["normalized_type"], "Nat")

    def test_kernel_verifier_handles_sum_elim_judgment(self):
        verifier = KernelProofVerifier()
        certificate = verifier.verify(
            {
                "term": "sum_elim (λ s: Sum Nat Unit. Nat) (λ x: Nat. x) (λ u: Unit. 0) (inl 3 Unit)",
                "type": "Nat",
            }
        )

        self.assertTrue(certificate.verified)
        self.assertEqual(certificate.payload["normalized_term"], "3")


if __name__ == "__main__":
    unittest.main()
