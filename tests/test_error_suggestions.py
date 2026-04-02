import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime.src.errors import ParseError, VMError, format_vak_error_with_suggestions
from runtime.src.interpreter import VakInterpreter


class ErrorSuggestionTests(unittest.TestCase):
    def test_runtime_name_error_suggests_close_builtin(self):
        interpreter = VakInterpreter()
        source = 'मुद्रर("नमस्ते")\n'

        with self.assertRaises(Exception) as error_ctx:
            interpreter.run(source, filename="<memory>")

        rendered = format_vak_error_with_suggestions(
            error_ctx.exception,
            interpreter.error_context(),
        )
        self.assertIn("सुझाव (Suggestions)", rendered)
        self.assertIn("मुद्रय", rendered)

    def test_type_error_suggests_live_conversion_expression(self):
        rendered = format_vak_error_with_suggestions(
            VMError("प्रकार त्रुटि: मान के लिए 'संख्या' अपेक्षित था, लेकिन 'str' मिला")
        )
        self.assertIn("संख्या(मान)", rendered)

    def test_contradiction_error_gets_resolution_hint(self):
        rendered = format_vak_error_with_suggestions(
            Exception("Contradiction detected: अग्नि conflicts with NOT अग्नि")
        )
        self.assertIn("विरोध", rendered)
        self.assertIn("एक हटाएँ", rendered)

    def test_parse_error_adds_proof_block_hint(self):
        rendered = format_vak_error_with_suggestions(
            ParseError("सिद्धि के लिए प्रमाण: ब्लॉक आवश्यक है", 7)
        )
        self.assertIn("प्रमाण: ब्लॉक", rendered)


if __name__ == "__main__":
    unittest.main()
