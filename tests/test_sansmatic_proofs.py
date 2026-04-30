import contextlib
import copy
import io
import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sansmatic.src.config import SansmaticSettings
from sansmatic.src.engine import ProofError, SansmaticEngine
from runtime.src.compiler import CompileError
from runtime.src.interpreter import VakInterpreter
from runtime.src.macro_expander import SansmaticMacroEngine
from runtime.src.ast_nodes import Program
from runtime.src.errors import ParseError
from runtime.src.nyaya_verifier import NyayaProofVerifier
from runtime.src.vm import VakVM, VMError


class SansmaticProofTests(unittest.TestCase):
    def test_engine_rejects_unscoped_proof_registration_by_default(self):
        engine = SansmaticEngine(verbose=False)

        with self.assertRaisesRegex(ProofError, "Unscoped proof registration"):
            engine.register_proof("proof_unsafe")

    def test_engine_records_obligations_instead_of_proving_unknown_claims(self):
        engine = SansmaticEngine(verbose=False)

        message = engine.assert_fact("entity", "HAS", "growth")

        self.assertIn("अपूर्ण प्रमाण दायित्व", message)
        self.assertEqual(len(engine.obligations), 1)
        self.assertFalse(engine.is_provable("entity", "HAS", "growth"))

    def test_engine_derives_rule_conclusion_from_proven_fact(self):
        engine = SansmaticEngine(verbose=False)
        engine.register_proof("proof_001", ("entity", "HAS", "growth"))

        engine.assert_fact("entity", "HAS", "growth", "proof_001")
        engine.rule(("X", "HAS", "growth"), ("X", "IS", "Alive"))

        self.assertTrue(engine.is_provable("entity", "IS", "Alive"))

    def test_engine_summary_and_snapshot_restore_preserve_context(self):
        engine = SansmaticEngine(verbose=False)
        engine.register_proof("proof_001", ("entity", "HAS", "growth"))
        engine.assert_fact("entity", "HAS", "growth", "proof_001")
        engine.rule(("X", "HAS", "growth"), ("X", "IS", "Alive"))
        snapshot = engine.snapshot()

        summary = engine.summary()
        self.assertEqual(summary["facts"], 1)
        self.assertEqual(summary["rules"], 1)
        self.assertTrue(summary["consistent"])

        engine.add_fact("entity", "IS", "Dormant")
        self.assertTrue(engine.restore(snapshot))
        restored = engine.summary()
        self.assertEqual(restored["facts"], 1)
        self.assertEqual(restored["rules"], 1)
        self.assertIn("सान्समैटिक सारांश", engine.summary_text())

    def test_backward_chain_supports_goal_directed_queries(self):
        engine = SansmaticEngine(verbose=False)
        engine.register_proof("proof_001", ("entity", "HAS", "growth"))
        engine.assert_fact("entity", "HAS", "growth", "proof_001")
        engine.rule(("X", "HAS", "growth"), ("X", "IS", "Alive"))

        self.assertTrue(engine.backward_chain(("entity", "IS", "Alive")))

    def test_engine_exposes_rule_trace_and_proof_tree(self):
        engine = SansmaticEngine(verbose=False)
        engine.register_proof("proof_001", ("entity", "HAS", "growth"))
        engine.assert_fact("entity", "HAS", "growth", "proof_001")
        engine.rule(("X", "HAS", "growth"), ("X", "IS", "Alive"))

        trace = engine.trace()
        self.assertTrue(any(item["kind"] == "rule_fire" for item in trace))

        explanation = engine.explain(("entity", "IS", "Alive"))
        self.assertTrue(explanation["proved"])
        self.assertEqual(explanation["tree"]["status"], "proved_by_rule")
        self.assertEqual(explanation["tree"]["children"][0]["goal"], "entity HAS growth")
        self.assertIn("प्रमाण अनुक्रम", engine.trace_text())
        self.assertIn("प्रमाण वृक्ष", engine.proof_tree_text(("entity", "IS", "Alive")))
        self.assertIn("प्रमाण व्याख्या", engine.explain_text(("entity", "IS", "Alive")))

    def test_engine_explain_reports_obligation_blocker(self):
        engine = SansmaticEngine(verbose=False)
        engine.assert_fact("entity", "HAS", "growth")

        explanation = engine.explain(("entity", "HAS", "growth"))

        self.assertFalse(explanation["proved"])
        self.assertIn("obligation", explanation["blocked_by"])
        self.assertEqual(explanation["obligations"][0]["statement"], "entity HAS growth")
        self.assertIn("अवरोध: obligation", engine.explain_text(("entity", "HAS", "growth")))

    def test_engine_theorem_library_tracks_fact_and_rule_theorems(self):
        engine = SansmaticEngine(verbose=False)
        engine.register_proof("proof_001", ("entity", "HAS", "growth"))
        engine.assert_fact("entity", "HAS", "growth", "proof_001")
        fact_theorem = engine.register_theorem("वृद्धि_सत्य", ("entity", "HAS", "growth"))
        rule_theorem = engine.register_rule_theorem(
            "जीवित_नियम",
            ("X", "HAS", "growth"),
            ("X", "IS", "Alive"),
        )

        theorems = engine.list_theorems()
        self.assertEqual(fact_theorem["name"], "वृद्धि_सत्य")
        self.assertTrue(fact_theorem["proved"])
        self.assertEqual(rule_theorem["kind"], "rule")
        self.assertTrue(any(item["name"] == "वृद्धि_सत्य" for item in theorems))
        self.assertTrue(any(item["name"] == "जीवित_नियम" for item in theorems))

        detail = engine.theorem_details("जीवित_नियम")
        self.assertEqual(detail["conclusion"], "X IS Alive")

        explanation = engine.explain(("entity", "IS", "Alive"))
        self.assertIn("जीवित_नियम", explanation["matching_theorems"])

    def test_engine_theorem_library_supports_tags_and_snapshot_restore(self):
        engine = SansmaticEngine(verbose=False)
        engine.register_proof("proof_001", ("entity", "HAS", "growth"))
        engine.assert_fact("entity", "HAS", "growth", "proof_001")
        engine.register_theorem(
            "वृद्धि_प्रमेय",
            ("entity", "HAS", "growth"),
            tags=["जीवन", "वृद्धि"],
            note="जीवित प्रणाली वृद्धि दिखाती है",
        )
        snapshot = engine.snapshot()
        engine.reset()
        self.assertEqual(engine.list_theorems(), [])
        self.assertTrue(engine.restore(snapshot))

        tagged = engine.list_theorems("जीवन")
        self.assertEqual(len(tagged), 1)
        self.assertEqual(tagged[0]["name"], "वृद्धि_प्रमेय")
        detail = engine.theorem_details("वृद्धि_प्रमेय")
        self.assertIn("जीवन", detail["tags"])
        self.assertIn("वृद्धि", detail["tags"])
        self.assertEqual(detail["note"], "जीवित प्रणाली वृद्धि दिखाती है")

    def test_verifier_rejects_unproven_statement(self):
        verifier = NyayaProofVerifier()

        certificate = verifier.verify_proof("mountain has fire", 4)

        self.assertFalse(certificate.verified)
        self.assertIn("not derivable", certificate.reason)

    def test_verifier_rejects_predicate_claim_without_explicit_statement_expression(self):
        verifier = NyayaProofVerifier()

        certificate = verifier.verify_proof("अभाज्य_है(१७)", 4)

        self.assertFalse(certificate.verified)
        self.assertIn("statement expression", certificate.reason)

    def test_compile_time_proof_succeeds_for_derived_fact(self):
        source = """
सिद्धि: "पर्वत IS अग्नि"
    प्रमाण:
        परिभाषय("पर्वत", ["धूम"])
        नियम("*", "HAS", "धूम", "*", "IS", "अग्नि")
"""
        interpreter = VakInterpreter()
        bytecode = interpreter.compile_only(source)

        self.assertTrue(any(isinstance(item, dict) and item.get("kind") == "sansmatic_certificate"
                            for item in bytecode.constants))

    def test_compile_time_proof_rejects_unproven_fact(self):
        source = """
सिद्धि: "पर्वत IS अग्नि"
    प्रमाण:
        परिभाषय("पर्वत", ["जल"])
"""
        interpreter = VakInterpreter()

        with self.assertRaises(CompileError):
            interpreter.compile_only(source)

    def test_compile_time_predicate_proof_uses_statement_expression(self):
        source = """
सिद्धि: अभाज्य_है(१७)
    प्रमाण:
        मान x = २
        यावत् x < ५:
            यदि १७ % x == ०:
                उत्क्षिप "भाजक मिला"
            x = x + १
"""
        interpreter = VakInterpreter()
        bytecode = interpreter.compile_only(source)

        self.assertTrue(any(isinstance(item, dict) and item.get("verified") for item in bytecode.constants))
        certificate = next(
            item for item in bytecode.constants
            if isinstance(item, dict) and item.get("kind") == "sansmatic_certificate"
        )
        metadata = certificate.get("metadata", {})
        self.assertEqual(metadata.get("verified_by"), "NyayaProofVerifier")
        self.assertIn("policy", metadata)
        self.assertGreaterEqual(metadata.get("evidence_steps", 0), 1)

    def test_compile_time_predicate_proof_rejects_trivial_evidence_block(self):
        source = """
सिद्धि: अभाज्य_है(१७)
    प्रमाण:
        १
"""
        interpreter = VakInterpreter()

        with self.assertRaisesRegex(CompileError, "Predicate proof evidence is too weak"):
            interpreter.compile_only(source)

    def test_proof_declaration_requires_explicit_pramana_block(self):
        source = """
सिद्धि: अभाज्य_है(१७)
"""
        interpreter = VakInterpreter()

        with self.assertRaisesRegex(ParseError, "प्रमाण: ब्लॉक आवश्यक है"):
            interpreter.compile_only(source)

    def test_runtime_rejects_tampered_proof_certificate(self):
        source = """
सिद्धि: "पर्वत IS अग्नि"
    प्रमाण:
        परिभाषय("पर्वत", ["धूम"])
        नियम("*", "HAS", "धूम", "*", "IS", "अग्नि")
"""
        interpreter = VakInterpreter()
        bytecode = interpreter.compile_only(source)

        certificate_index = next(
            index for index, item in enumerate(bytecode.constants)
            if isinstance(item, dict) and item.get("kind") == "sansmatic_certificate"
        )
        tampered = copy.deepcopy(bytecode.constants[certificate_index])
        tampered["hash"] = "tampered"
        bytecode.constants[certificate_index] = tampered

        with self.assertRaises(VMError):
            VakVM().run(bytecode)

    def test_legacy_certificate_verification_remains_backward_compatible(self):
        engine = SansmaticEngine(verbose=False)
        certificate = engine.issue_certificate(
            "entity IS Alive",
            True,
            pramana="ANUMANA",
            confidence=0.9,
        )

        self.assertTrue(SansmaticEngine.verify_certificate(certificate))

    def test_hmac_certificate_verification_rejects_tampering(self):
        settings = SansmaticSettings(
            certificate_mode="hmac-sha256",
            certificate_secret="test-secret",
            allow_legacy_certificates=False,
        )
        engine = SansmaticEngine(verbose=False, settings=settings)
        certificate = engine.issue_certificate(
            "entity IS Alive",
            True,
            pramana="ANUMANA",
            confidence=0.9,
        )

        self.assertTrue(SansmaticEngine.verify_certificate(certificate, settings=settings))

        tampered = copy.deepcopy(certificate)
        tampered["statement"] = "entity IS Dead"
        self.assertFalse(SansmaticEngine.verify_certificate(tampered, settings=settings))

    def test_hmac_mode_rejects_unsigned_legacy_payloads_when_disabled(self):
        legacy_engine = SansmaticEngine(verbose=False)
        legacy_certificate = legacy_engine.issue_certificate(
            "entity IS Alive",
            True,
            pramana="ANUMANA",
            confidence=0.9,
        )
        strict_settings = SansmaticSettings(
            certificate_mode="hmac-sha256",
            certificate_secret="test-secret",
            allow_legacy_certificates=False,
        )

        self.assertFalse(
            SansmaticEngine.verify_certificate(legacy_certificate, settings=strict_settings)
        )

    def test_vak_runtime_exposes_sansmatic_summary_builtin(self):
        interpreter = VakInterpreter()
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            interpreter.run("मुद्रय प्रमाण_सारांश()[\"facts\"]")
        self.assertEqual(buffer.getvalue().splitlines(), ["0"])

    def test_vak_runtime_exposes_backward_chaining_builtin(self):
        vm = VakVM()
        vm.builtins["प्रमाण_रीसेट"]()
        vm.builtins["परिभाषय"]("entity", ["growth"])
        vm.builtins["नियम"]("X", "HAS", "growth", "X", "IS", "Alive")

        self.assertTrue(vm.builtins["पश्च_सिद्ध_है"]("entity", "IS", "Alive"))

    def test_vak_runtime_exposes_trace_and_explain_builtins(self):
        vm = VakVM()
        vm.builtins["प्रमाण_रीसेट"]()
        vm.builtins["परिभाषय"]("entity", ["growth"])
        vm.builtins["नियम"]("X", "HAS", "growth", "X", "IS", "Alive")
        vm.builtins["पश्च_सिद्ध_है"]("entity", "IS", "Alive")

        trace = vm.builtins["प्रमाण_अनुक्रम"]()
        explanation = vm.builtins["प्रमाण_व्याख्या"]("entity", "IS", "Alive")
        tree = vm.builtins["प्रमाण_वृक्ष"]("entity", "IS", "Alive")

        self.assertTrue(any(item["kind"] == "rule_fire" for item in trace))
        self.assertTrue(explanation["proved"])
        self.assertEqual(tree["status"], "proved_by_rule")

    def test_vak_runtime_exposes_text_and_theorem_builtins(self):
        vm = VakVM()
        vm.builtins["प्रमाण_रीसेट"]()
        vm.builtins["परिभाषय"]("entity", ["growth"])
        vm.builtins["प्रमेय_तथ्य"]("वृद्धि_तथ्य", "entity", "HAS", "growth")
        vm.builtins["प्रमेय_नियम"]("जीवन_नियम", "X", "HAS", "growth", "X", "IS", "Alive")

        summary_text = vm.builtins["प्रमाण_सारांश_पाठ"]()
        trace_text = vm.builtins["प्रमाण_अनुक्रम_पाठ"]()
        tree_text = vm.builtins["प्रमाण_वृक्ष_पाठ"]("entity", "IS", "Alive")
        explain_text = vm.builtins["प्रमाण_व्याख्या_पाठ"]("entity", "IS", "Alive")
        theorem_rows = vm.builtins["प्रमेय_सूची"]()
        theorem_detail = vm.builtins["प्रमेय_विवरण"]("जीवन_नियम")

        self.assertIn("सान्समैटिक सारांश", summary_text)
        self.assertIn("प्रमाण अनुक्रम", trace_text)
        self.assertIn("प्रमाण वृक्ष", tree_text)
        self.assertIn("मिलते प्रमेय: जीवन_नियम", explain_text)
        self.assertTrue(any(item["name"] == "वृद्धि_तथ्य" for item in theorem_rows))
        self.assertEqual(theorem_detail["kind"], "rule")

    def test_macro_validation_uses_sansmatic_preconditions(self):
        engine = SansmaticEngine(verbose=False)
        macro_engine = SansmaticMacroEngine(engine)
        ast = Program(body=[])

        validated = macro_engine.expand_with_proof(
            ast,
            {
                "facts": [("x", "IS", "Number")],
                "preconditions": ["x IS Number"],
                "type_constraints": {"x": "Number", "x_meta": "Any"},
                "x": {"type": "Number"},
                "x_meta": {"type": "Any"},
            },
        )

        self.assertIsInstance(validated, Program)

    def test_verifier_can_execute_registered_function_for_commutativity_checks(self):
        class _Param:
            def __init__(self, vibhakti):
                self.vibhakti = vibhakti

        class _Signature:
            params = [_Param("कर्म"), _Param("कर्म")]

        verifier = NyayaProofVerifier()
        verifier.register_function("योग", _Signature(), lambda a, b: a + b)

        self.assertTrue(verifier.check_commutativity("योग", [2, 3]))

    def test_verifier_can_issue_kernel_judgment_certificate(self):
        verifier = NyayaProofVerifier()

        certificate = verifier.verify_kernel_judgment(
            {
                "term": "(refl 4 : Eq Nat 4 4)",
                "type": "Eq Nat 4 4",
            }
        )

        self.assertTrue(certificate.verified)
        self.assertEqual(certificate.payload["kind"], "sansmatic_kernel_certificate")
        self.assertTrue(NyayaProofVerifier.verify_kernel_certificate_payload(certificate.payload))

    def test_certificate_payload_verifier_accepts_kernel_certificates(self):
        verifier = NyayaProofVerifier()
        certificate = verifier.verify_kernel_judgment(
            {
                "term": "refl 2",
                "type": "Eq Nat 2 2",
            }
        )

        self.assertTrue(NyayaProofVerifier.verify_certificate_payload(certificate.payload))

    def test_compile_time_proof_block_can_emit_kernel_judgment(self):
        source = """
सिद्धि: "kernel-eq"
    प्रमाण:
        प्रत्यागच्छ कर्नेल_निर्णय("refl 2", "Eq Nat 2 2")
"""
        interpreter = VakInterpreter()
        bytecode = interpreter.compile_only(source)

        certificate = next(
            item for item in bytecode.constants
            if isinstance(item, dict) and item.get("kind") == "sansmatic_kernel_certificate"
        )
        self.assertEqual(certificate.get("kernel"), "sansmatic-kernel-v1")
        self.assertIn("Eq Nat 2 2", certificate.get("normalized_type", ""))

    def test_compile_time_proof_block_rejects_invalid_kernel_judgment(self):
        source = """
सिद्धि: "kernel-bad"
    प्रमाण:
        प्रत्यागच्छ कर्नेल_निर्णय("refl 2", "Eq Nat 2 3")
"""
        interpreter = VakInterpreter()

        with self.assertRaisesRegex(CompileError, "सिद्धि असफल"):
            interpreter.compile_only(source)

    def test_compile_time_proof_block_accepts_explicit_kernel_section(self):
        source = """
सिद्धि: "kernel-section"
    कर्नेल:
        पद: "refl 2"
        प्रकार: "Eq Nat 2 2"
"""
        interpreter = VakInterpreter()
        bytecode = interpreter.compile_only(source)

        certificate = next(
            item for item in bytecode.constants
            if isinstance(item, dict) and item.get("kind") == "sansmatic_kernel_certificate"
        )
        self.assertTrue(certificate.get("verified"))
        self.assertIn("Eq Nat 2 2", certificate.get("normalized_type", ""))


if __name__ == "__main__":
    unittest.main()
