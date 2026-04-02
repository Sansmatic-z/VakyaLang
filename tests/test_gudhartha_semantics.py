import contextlib
import io
import unittest

from runtime.src.interpreter import VakInterpreter
from runtime.src.semantic_guards import (
    build_karaka_signature,
    classify_padartha,
    create_dharma_spec,
    validate_dharma_value,
    validate_karaka_roles,
    validate_nyaya_syllogism,
)


class GudharthaSemanticTests(unittest.TestCase):
    def run_source(self, source: str) -> list[str]:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            VakInterpreter().run(source)
        return [line.strip() for line in buffer.getvalue().splitlines() if line.strip()]

    def test_dharma_validation_accepts_positive_even_number(self):
        spec = create_dharma_spec("धनात्मक_सम", "संख्या", ["धनात्मक", "सम"])
        report = validate_dharma_value(spec, 8)
        self.assertTrue(report["valid"])
        self.assertEqual(report["padartha"], "द्रव्य")

    def test_dharma_validation_reports_failed_property(self):
        spec = create_dharma_spec("धनात्मक", "संख्या", ["धनात्मक"])
        report = validate_dharma_value(spec, -2)
        self.assertFalse(report["valid"])
        self.assertEqual(report["failed_property"], "धनात्मक")

    def test_karaka_validation_reports_missing_required_role(self):
        signature = build_karaka_signature(
            "गमन",
            [
                {"नाम": "कर्ता", "भूमिका": "कर्ता", "आवश्यक": True},
                {"नाम": "गन्तव्य", "भूमिका": "अधिकरण", "आवश्यक": True},
            ],
        )
        report = validate_karaka_roles(signature, {"कर्ता": "राम"})
        self.assertFalse(report["valid"])
        self.assertIn("अधिकरण", report["missing_roles"])

    def test_nyaya_validation_requires_matching_conclusion(self):
        report = validate_nyaya_syllogism(
            "पर्वत अग्निमान् है",
            "क्योंकि धूमवान् है",
            "यथा रसोई",
            "पर्वत धूमवान् है",
            "पर्वत शीतल है",
        )
        self.assertFalse(report["valid"])
        self.assertIn("निगमन", report["message"])

    def test_padartha_classification_handles_none_and_functions(self):
        self.assertEqual(classify_padartha(None), "अभाव")
        self.assertEqual(classify_padartha(lambda value: value), "कर्म")

    def test_vak_runtime_exposes_semantic_builtins(self):
        source = """
चर धर्म = धर्म_निर्माण("धनात्मक", "संख्या", ["धनात्मक"])
यदि धर्म_मान्य_है(धर्म, ५):
    मुद्रय १
अन्यथा:
    मुद्रय ०
"""
        lines = self.run_source(source)
        self.assertEqual(lines[-1], "1")

    def test_vak_runtime_reports_missing_karaka_role(self):
        source = """
चर हस्ताक्षर = कारक_हस्ताक्षर("गमन", [
    {"नाम": "कर्ता", "भूमिका": "कर्ता", "आवश्यक": सत्य},
    {"नाम": "गन्तव्य", "भूमिका": "अधिकरण", "आवश्यक": सत्य},
])
चर रिपोर्ट = कारक_जाँच(हस्ताक्षर, {"कर्ता": "राम"})
यदि रिपोर्ट["मान्य"]:
    मुद्रय ०
अन्यथा:
    मुद्रय १
"""
        lines = self.run_source(source)
        self.assertEqual(lines[-1], "1")

    def test_gudhartha_stdlib_wrapper_is_importable(self):
        source = """
आयात gudhartha
यदि gudhartha.न्याय_मान्य(
    "पर्वत अग्निमान् है",
    "क्योंकि धूमवान् है",
    "यथा रसोई",
    "पर्वत धूमवान् है",
    "पर्वत अग्निमान् है"
):
    मुद्रय ९
अन्यथा:
    मुद्रय ०
"""
        lines = self.run_source(source)
        self.assertEqual(lines[-1], "9")


if __name__ == "__main__":
    unittest.main()
