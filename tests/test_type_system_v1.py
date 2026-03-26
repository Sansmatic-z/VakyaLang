import contextlib
import io
import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime.src.compiler import Compiler, CompileError
from runtime.src.interpreter import VakInterpreter
from runtime.src.lexer import Lexer
from runtime.src.parser import Parser


class TypeSystemV1Tests(unittest.TestCase):
    def compile_source(self, source: str):
        ast = Parser(Lexer(source).tokenize()).parse()
        return Compiler().compile(ast)

    def run_source(self, source: str):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            VakInterpreter().run(source)
        return out.getvalue()

    def test_variable_annotation_mismatch_is_rejected(self):
        with self.assertRaisesRegex(CompileError, "संख्या"):
            self.compile_source('मान नाम: संख्या = "राज"')

    def test_function_return_type_mismatch_is_rejected(self):
        source = """
कर्म उत्तर() → संख्या:
    वापस "गलत"
"""
        with self.assertRaisesRegex(CompileError, "लौटाना"):
            self.compile_source(source)

    def test_function_call_argument_mismatch_is_rejected(self):
        source = """
कर्म जोड़(x: संख्या, y: संख्या) → संख्या:
    वापस x + y

मुद्रय जोड़("१", २)
"""
        with self.assertRaisesRegex(CompileError, "तर्क 'x'"):
            self.compile_source(source)

    def test_result_unwrap_flows_into_annotated_variable(self):
        source = """
मान मान: संख्या = फल_खोलो(सिद्ध(४२))
मुद्रय मान
"""
        self.assertEqual(self.run_source(source).strip(), "42")

    def test_match_result_pattern_narrows_success_branch(self):
        source = """
कर्म भाग(क: संख्या, ख: संख्या):
    यदि ख == ०:
        वापस असिद्ध("शून्य")
    वापस सिद्ध(क // ख)

प्रत्यभिज्ञा भाग(१०, २):
    सिद्ध(मान):
        मुद्रय मान + १
    असिद्ध(त्रुटि):
        मुद्रय त्रुटि
    _:
        मुद्रय "अज्ञात"
"""
        self.assertEqual(self.run_source(source).strip(), "6")

    def test_list_index_type_is_checked(self):
        with self.assertRaisesRegex(CompileError, "तार"):
            self.compile_source(
                """
मान संख्या_सूची = [१, २, ३]
मान शब्द: तार = संख्या_सूची[०]
"""
            )

    def test_bound_method_call_is_type_checked(self):
        source = """
वर्ग जोड़क:
    कर्म जोड़(स्वयं, x: संख्या) → संख्या:
        वापस x + १

मान obj = जोड़क()
मुद्रय obj.जोड़(४)
"""
        self.assertEqual(self.run_source(source).strip(), "5")

    def test_bound_method_argument_mismatch_is_rejected(self):
        source = """
वर्ग जोड़क:
    कर्म जोड़(स्वयं, x: संख्या) → संख्या:
        वापस x + १

मान obj = जोड़क()
मुद्रय obj.जोड़("गलत")
"""
        with self.assertRaisesRegex(CompileError, "तर्क 'x'"):
            self.compile_source(source)

    def test_generic_list_annotation_is_checked(self):
        source = """
मान संख्याएँ: सूची[संख्या] = [१, २, ३]
मुद्रय संख्याएँ[०]
"""
        self.assertEqual(self.run_source(source).strip(), "1")

    def test_generic_list_annotation_rejects_mixed_types(self):
        with self.assertRaisesRegex(CompileError, "सूची\\[संख्या\\]"):
            self.compile_source('मान संख्याएँ: सूची[संख्या] = [१, "दो"]')

    def test_generic_dict_annotation_is_checked(self):
        source = """
मान तालिका: शब्दकोश[तार, संख्या] = {"क": १, "ख": २}
मुद्रय तालिका["क"]
"""
        self.assertEqual(self.run_source(source).strip(), "1")

    def test_explicit_result_type_annotation_is_supported(self):
        source = """
मान उत्तर: फल[संख्या, तार] = सिद्ध(४२)
मुद्रय फल_खोलो(उत्तर)
"""
        self.assertEqual(self.run_source(source).strip(), "42")

    def test_union_annotation_accepts_null_and_number(self):
        source = """
मान शायद: संख्या | शून्य = शून्य
शायद = ७
मुद्रय शायद
"""
        self.assertEqual(self.run_source(source).strip(), "7")

    def test_union_annotation_rejects_incompatible_assignment(self):
        with self.assertRaisesRegex(CompileError, "संख्या \\| शून्य"):
            self.compile_source(
                """
मान शायद: संख्या | शून्य = शून्य
शायद = "गलत"
"""
            )

    def test_map_inference_produces_typed_list(self):
        source = """
मान दुगुना: सूची[संख्या] = map(lambda x: x * २, [१, २, ३])
मुद्रय दुगुना[१]
"""
        self.assertEqual(self.run_source(source).strip(), "4")

    def test_data_decl_variants_match_exhaustively_without_catchall(self):
        source = """
डेटा विकल्प:
    कुछ(संख्या)
    रिक्त

मान मान: विकल्प = कुछ(५)
प्रत्यभिज्ञा मान:
    कुछ(x):
        मुद्रय x
    रिक्त():
        मुद्रय ०
"""
        self.assertEqual(self.run_source(source).strip(), "5")

    def test_generic_data_decl_constructor_is_typed(self):
        source = """
डेटा विकल्प[T]:
    कुछ(T)
    रिक्त

मान मान: विकल्प[संख्या] = कुछ(५)
प्रत्यभिज्ञा मान:
    कुछ(x):
        मुद्रय x + १
    रिक्त():
        मुद्रय ०
"""
        self.assertEqual(self.run_source(source).strip(), "6")

    def test_non_exhaustive_data_match_is_rejected_without_catchall(self):
        source = """
डेटा विकल्प:
    कुछ(संख्या)
    रिक्त

मान मान: विकल्प = कुछ(५)
प्रत्यभिज्ञा मान:
    कुछ(x):
        मुद्रय x
"""
        with self.assertRaisesRegex(CompileError, "अपूर्ण प्रत्यभिज्ञा"):
            self.compile_source(source)

    def test_result_match_without_catchall_is_allowed_when_exhaustive(self):
        source = """
कर्म भाग(क: संख्या, ख: संख्या):
    यदि ख == ०:
        वापस असिद्ध("शून्य")
    वापस सिद्ध(क // ख)

प्रत्यभिज्ञा भाग(१०, ०):
    सिद्ध(मान):
        मुद्रय मान
    असिद्ध(त्रुटि):
        मुद्रय त्रुटि
"""
        self.assertEqual(self.run_source(source).strip(), "शून्य")


if __name__ == "__main__":
    unittest.main()
