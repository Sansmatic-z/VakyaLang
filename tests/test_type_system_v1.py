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

    def test_function_with_declared_return_must_return_on_all_paths(self):
        source = """
कर्म उत्तर() → संख्या:
    मान x = १
"""
        with self.assertRaisesRegex(CompileError, "सभी मार्गों में"):
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

    def test_if_condition_requires_bool(self):
        with self.assertRaisesRegex(CompileError, "यदि की शर्त"):
            self.compile_source(
                """
यदि १:
    मुद्रय १
"""
            )

    def test_while_condition_requires_bool(self):
        with self.assertRaisesRegex(CompileError, "यावत् की शर्त"):
            self.compile_source(
                """
यावत् "हाँ":
    विराम
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

    def test_instance_field_assignment_uses_inferred_init_type(self):
        source = """
वर्ग बक्सा:
    कर्म __init__(स्वयं):
        स्वयं.मान = १

मान box = बक्सा()
box.मान = "गलत"
"""
        with self.assertRaisesRegex(CompileError, "सदस्य 'मान'"):
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

    def test_refinement_annotation_accepts_compile_time_proven_literal(self):
        source = """
मान अभाज्य: परिशुद्ध[संख्या, अभाज्य_है] = १७
मुद्रय अभाज्य + १
"""
        self.assertEqual(self.run_source(source).strip(), "18")

    def test_refinement_annotation_rejects_value_that_fails_predicate(self):
        with self.assertRaisesRegex(CompileError, "अभाज्य_है"):
            self.compile_source('मान अभाज्य: परिशुद्ध[संख्या, अभाज्य_है] = १८')

    def test_refinement_annotation_requires_compile_time_proof(self):
        source = """
कर्म पहचान(x: संख्या) → संख्या:
    वापस x

मान अभाज्य: परिशुद्ध[संख्या, अभाज्य_है] = पहचान(१७)
"""
        with self.assertRaisesRegex(CompileError, "compile-time सिद्ध"):
            self.compile_source(source)

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

    def test_refinement_parameter_is_enforced_at_call_site(self):
        source = """
कर्म अगला(x: परिशुद्ध[संख्या, धनात्मक_है]) → संख्या:
    वापस x + १

मुद्रय अगला(५)
"""
        self.assertEqual(self.run_source(source).strip(), "6")

    def test_refinement_parameter_rejects_non_matching_argument(self):
        source = """
कर्म अगला(x: परिशुद्ध[संख्या, धनात्मक_है]) → संख्या:
    वापस x + १

मुद्रय अगला(-१)
"""
        with self.assertRaisesRegex(CompileError, "धनात्मक_है"):
            self.compile_source(source)

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

    def test_refinement_return_type_is_enforced(self):
        source = """
कर्म अभाज्य() → परिशुद्ध[संख्या, अभाज्य_है]:
    वापस १९

मुद्रय अभाज्य() + १
"""
        self.assertEqual(self.run_source(source).strip(), "20")

    def test_refinement_return_type_rejects_invalid_value(self):
        source = """
कर्म अभाज्य() → परिशुद्ध[संख्या, अभाज्य_है]:
    वापस २०
"""
        with self.assertRaisesRegex(CompileError, "अभाज्य_है"):
            self.compile_source(source)

    def test_map_inference_produces_typed_list(self):
        source = """
मान दुगुना: सूची[संख्या] = map(lambda x: x * २, [१, २, ३])
मुद्रय दुगुना[१]
"""
        self.assertEqual(self.run_source(source).strip(), "4")

    def test_default_value_type_mismatch_is_rejected(self):
        source = """
कर्म जोड़(x: संख्या = "१") → संख्या:
    वापस x
"""
        with self.assertRaisesRegex(CompileError, "डिफ़ॉल्ट मान"):
            self.compile_source(source)

    def test_duplicate_positional_and_keyword_argument_is_rejected(self):
        source = """
कर्म जोड़(x: संख्या, y: संख्या) → संख्या:
    वापस x + y

मुद्रय जोड़(१, x=२, y=३)
"""
        with self.assertRaisesRegex(CompileError, "बार-बार"):
            self.compile_source(source)

    def test_conditional_expression_requires_bool_condition(self):
        with self.assertRaisesRegex(CompileError, "शर्तीय अभिव्यक्ति"):
            self.compile_source('मान x = १ यदि २ अन्यथा ३')

    def test_list_comprehension_filter_requires_bool(self):
        with self.assertRaisesRegex(CompileError, "सूची comprehension filter"):
            self.compile_source('मान x = [क प्रति क में [१, २] यदि ५]')

    def test_match_guard_requires_bool(self):
        with self.assertRaisesRegex(CompileError, "प्रत्यभिज्ञा guard"):
            self.compile_source(
                """
प्रत्यभिज्ञा १:
    x यदि ५:
        मुद्रय x
    _:
        मुद्रय ०
"""
            )

    def test_list_index_assignment_checks_element_type(self):
        with self.assertRaisesRegex(CompileError, "सूची तत्व"):
            self.compile_source(
                """
मान xs: सूची[संख्या] = [१, २]
xs[०] = "गलत"
"""
            )

    def test_refinement_assignment_is_rechecked_on_update(self):
        with self.assertRaisesRegex(CompileError, "धनात्मक_है"):
            self.compile_source(
                """
मान x: परिशुद्ध[संख्या, धनात्मक_है] = ५
x = -२
"""
            )

    def test_list_index_assignment_enforces_refinement_element_type(self):
        with self.assertRaisesRegex(CompileError, "धनात्मक_है"):
            self.compile_source(
                """
मान xs: सूची[परिशुद्ध[संख्या, धनात्मक_है]] = [१, २]
xs[०] = -१
"""
            )

    def test_dict_index_assignment_checks_value_type(self):
        with self.assertRaisesRegex(CompileError, "शब्दकोश मान"):
            self.compile_source(
                """
मान d: शब्दकोश[तार, संख्या] = {"क": १}
d["क"] = "गलत"
"""
            )

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
