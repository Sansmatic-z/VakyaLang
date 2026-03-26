import copy
import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sansmatic.src.engine import SansmaticEngine
from runtime.src.compiler import CompileError
from runtime.src.interpreter import VakInterpreter
from runtime.src.macro_expander import SansmaticMacroEngine
from runtime.src.ast_nodes import Program
from runtime.src.nyaya_verifier import NyayaProofVerifier
from runtime.src.vm import VakVM, VMError


class SansmaticProofTests(unittest.TestCase):
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

    def test_verifier_rejects_unproven_statement(self):
        verifier = NyayaProofVerifier()

        certificate = verifier.verify_proof("mountain has fire", 4)

        self.assertFalse(certificate.verified)
        self.assertIn("not derivable", certificate.reason)

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


if __name__ == "__main__":
    unittest.main()
