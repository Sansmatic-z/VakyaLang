import contextlib
import io
import os
import sys
import tempfile
import time
import unittest
import contextlib
from pathlib import Path


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime.src.interpreter import VakInterpreter
from runtime.src.compiler import Compiler, CompileError
from runtime.src.lexer import Lexer
from runtime.src.parser import Parser
from runtime.src.vm import VakClass, VakVM


class RuntimeRegressionTests(unittest.TestCase):
    ZERO_DIVISION_MESSAGES = (
        "integer division or modulo by zero",
        "division by zero",
    )

    def run_source(self, source: str):
        buffer = io.StringIO()
        interpreter = VakInterpreter()
        with contextlib.redirect_stdout(buffer):
            result = interpreter.run(source)
        return result, buffer.getvalue()

    def assert_zero_division_output(self, output: str) -> None:
        self.assertTrue(
            any(message in output for message in self.ZERO_DIVISION_MESSAGES),
            msg=f"unexpected zero-division output: {output!r}",
        )

    def test_keyword_aliases_work_in_core_statements(self):
        source = """
मान x = ५
प्रति k में परास(३):
    बोलो k
प्रयास:
    १ // ०
पकड़ो e:
    बोलो ९९
यदि न असत्य:
    बोलो x
"""
        _, output = self.run_source(source)
        self.assertEqual(output.split(), ["0", "1", "2", "99", "5"])

    def test_builtin_name_can_share_keyword_spelling(self):
        source = """
आयात ganit_vistarit
मुद्रय वर्ग(५)
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "25")

    def test_from_import_binds_requested_name(self):
        source = """
आयात वर्ग से ganit_vistarit
मुद्रय वर्ग(६)
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "36")

    def test_multi_name_from_import_binds_all_requested_names(self):
        source = """
आयात स्टैक, कतार, बाइनरी_सर्च_ट्री से data_sangrah
मुद्रय नव स्टैक()
मुद्रय नव कतार()
मुद्रय नव बाइनरी_सर्च_ट्री()
"""
        _, output = self.run_source(source)
        self.assertEqual(
            output.splitlines(),
            ["<स्टैक वस्तु>", "<कतार वस्तु>", "<बाइनरी_सर्च_ट्री वस्तु>"],
        )

    def test_python_runtime_exceptions_are_catchable(self):
        source = """
प्रयत्न:
    मुद्रय १ // ०
दोष e:
    मुद्रय पाठ_कर(e)
"""
        _, output = self.run_source(source)
        self.assert_zero_division_output(output)

    def test_boolean_literal_argument_is_preserved(self):
        source = """
कर्म परीक्षण(x):
    मुद्रय x

परीक्षण(सत्य)
परीक्षण(असत्य)
"""
        _, output = self.run_source(source)
        self.assertEqual(output.split(), ["True", "False"])

    def test_lambda_and_inline_conditional_expression_work(self):
        source = """
मान दुगुना = lambda x: x * २
मान चयन = "बड़ा" यदि ५ > ३ अन्यथा "छोटा"
मुद्रय दुगुना(६)
मुद्रय चयन
"""
        _, output = self.run_source(source)
        self.assertEqual(output.split(), ["12", "बड़ा"])

    def test_lambda_name_can_still_be_used_as_identifier(self):
        source = """
कर्म छापो(lambda):
    मुद्रय lambda

छापो(७)
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "7")

    def test_break_exits_loop(self):
        source = """
मान क = ०
यावत् सत्य:
    यदि क == ३:
        विराम
    क = क + १

मुद्रय क
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "3")

    def test_break_alias_and_for_loop_cleanup_work(self):
        source = """
कर्म खोजो():
    प्रत्येक चर i अन्तर्गत परास(४):
        प्रत्येक चर j अन्तर्गत परास(२):
            यदि "abcde"[i + j] != "cd"[j]:
                तोड़ो
            मुद्रय i
            मुद्रय j
    मुद्रय ९९

खोजो()
"""
        _, output = self.run_source(source)
        self.assertEqual(output.split(), ["2", "0", "2", "1", "99"])

    def test_continue_alias_jari_works(self):
        source = """
प्रति i में परास(४):
    यदि i == १:
        जारी
    मुद्रय i
"""
        _, output = self.run_source(source)
        self.assertEqual(output.split(), ["0", "2", "3"])

    def test_for_loop_tuple_unpacking_works_with_enumerate(self):
        source = """
प्रति क्रम, अक्षर में enumerate(["क", "ख"], १):
    मुद्रय क्रम
    मुद्रय अक्षर
"""
        _, output = self.run_source(source)
        self.assertEqual(output.splitlines(), ["1", "क", "2", "ख"])

    def test_try_stmt_supports_multiple_handlers_and_type_matching(self):
        source = """
प्रयत्न:
    मुद्रय १ // ०
पकड़ो ZeroDivisionError जैसे त्रुटि:
    मुद्रय पाठ_कर(त्रुटि)
पकड़ो TypeError:
    मुद्रय "wrong"
"""
        _, output = self.run_source(source)
        self.assert_zero_division_output(output)

    def test_try_stmt_falls_through_to_later_generic_handler(self):
        source = """
प्रयत्न:
    मुद्रय १ // ०
पकड़ो TypeError:
    मुद्रय "wrong"
पकड़ो त्रुटि:
    मुद्रय पाठ_कर(त्रुटि)
"""
        _, output = self.run_source(source)
        self.assert_zero_division_output(output)

    def test_anyaatha_yadi_spelling_works_as_elif(self):
        source = """
यदि असत्य:
    मुद्रय १
अन्यथा यदि सत्य:
    मुद्रय २
अन्यथा:
    मुद्रय ३
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "2")

    def test_if_true_branch_does_not_fall_through_to_else(self):
        source = """
यदि सत्य:
    मुद्रय १
अन्यथा यदि सत्य:
    मुद्रय २
अन्यथा:
    मुद्रय ३
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "1")

    def test_keyword_shaped_parameter_name_works_in_expression_position(self):
        source = """
कर्म छापो(मान):
    मुद्रय मान

छापो(११)
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "11")

    def test_legacy_char_global_syntax_updates_shared_state(self):
        source = """
मान पास = ०
कर्म गिनो():
    चर global पास
    पास = पास + १

गिनो()
गिनो()
मुद्रय पास
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "2")

    def test_vibhakti_word_can_be_plain_parameter_name(self):
        source = """
कर्म बताओ(कर्ता):
    मुद्रय कर्ता

बताओ("राम")
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "राम")

    def test_nonlocal_rebinds_nearest_enclosing_scope(self):
        source = """
कर्म बाहर():
    मान क = १०
    कर्म अंदर():
        अस्थानिक क
        क = २०
    अंदर()
    मुद्रय क

बाहर()
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "20")

    def test_local_assignment_does_not_read_outer_closure_binding(self):
        source = """
कर्म बाहर():
    मान क = १०
    कर्म अंदर():
        मुद्रय क
        क = २०
    अंदर()

बाहर()
"""
        with self.assertRaisesRegex(Exception, "before assignment"):
            self.run_source(source)

    def test_dead_branch_binding_still_marks_name_local(self):
        source = """
कर्म बाहर():
    यदि असत्य:
        मान छ = १
    मुद्रय छ

बाहर()
"""
        with self.assertRaisesRegex(Exception, "before assignment"):
            self.run_source(source)

    def test_nonlocal_requires_enclosing_binding(self):
        source = """
कर्म बाहर():
    कर्म अंदर():
        अस्थानिक क
        क = २०
"""
        with self.assertRaises(CompileError):
            Compiler().compile(Parser(Lexer(source).tokenize()).parse())

    def test_unreachable_code_after_return_is_not_emitted_into_function_bytecode(self):
        source = """
कर्म जल्दी():
    वापस १
    मुद्रय ९९
"""
        bytecode = Compiler().compile(Parser(Lexer(source).tokenize()).parse())
        func_bytecode = bytecode.functions["जल्दी"]
        self.assertNotIn(99, func_bytecode.constants)

    def test_method_inside_nested_class_keeps_outer_function_closure(self):
        source = """
कर्म बाहर():
    मान क = १०
    वर्ग डिब्बा:
        कर्म मान_दो(स्वयं):
            वापस क
    मुद्रय डिब्बा().मान_दो()

बाहर()
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "10")

    def test_scientific_notation_lexes_as_number(self):
        source = """
मुद्रय 9.9843695780195716e-6
"""
        _, output = self.run_source(source)
        self.assertIn("9.984369578019", output)

    def test_na_can_be_used_as_variable_name(self):
        source = """
मान न = ५
मुद्रय न
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "5")

    def test_na_parameter_name_supports_recursion(self):
        source = """
कर्म क्रमगुणित(न):
    यदि न <= १:
        वापस १
    वापस न * क्रमगुणित(न - १)

मुद्रय क्रमगुणित(५)
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "120")

    def test_single_line_function_definition_works(self):
        source = """
कर्म दोगुना(क): वापस क * २
मुद्रय दोगुना(३)
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "6")

    def test_keyword_arguments_bind_by_name(self):
        source = """
कर्म परिचय(नाम, आयु):
    वापस नाम + ":" + पाठ_कर(आयु)

मुद्रय परिचय(आयु=२५, नाम="राज")
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "राज:25")

    def test_keyword_arguments_work_for_constructor_and_method(self):
        source = """
वर्ग व्यक्ति:
    कर्म __init__(स्वयं, नाम, आयु):
        स्वयं.नाम = नाम
        स्वयं.आयु = आयु

    कर्म विवरण(स्वयं, उपसर्ग, विराम):
        वापस उपसर्ग + स्वयं.नाम + ":" + पाठ_कर(स्वयं.आयु) + विराम

मान प = व्यक्ति(आयु=२५, नाम="राज")
मुद्रय प.विवरण(विराम="!", उपसर्ग=">>")
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), ">>राज:25!")

    def test_multiple_return_values_can_be_unpacked(self):
        source = """
कर्म मिनमैक्स(सूची):
    वापस न्यूनतम(सूची), अधिकतम(सूची)

मान न, म = मिनमैक्स([३, १, ५])
मुद्रय न
मुद्रय म
"""
        _, output = self.run_source(source)
        self.assertEqual(output.split(), ["1", "5"])

    def test_tuple_literal_can_be_indexed_and_printed(self):
        source = """
मान त = (१, २, ३)
मुद्रय त
मुद्रय त[१]
"""
        _, output = self.run_source(source)
        self.assertEqual(output.splitlines(), ["(1, 2, 3)", "2"])

    def test_dict_comprehension_works(self):
        source = """
मान द = {क: क * क प्रति क में परास(४)}
मुद्रय द
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "{0: 0, 1: 1, 2: 4, 3: 9}")

    def test_list_comprehension_filter_works(self):
        source = """
मान स = [क प्रति क में परास(६) यदि क % २ == ०]
मुद्रय स
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "[0, 2, 4]")

    def test_dict_comprehension_filter_works(self):
        source = """
मान द = {क: क * क प्रति क में परास(६) यदि क % २ == १}
मुद्रय द
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "{1: 1, 3: 9, 5: 25}")

    def test_with_statement_calls_enter_for_python_context_manager(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "builtin-open.txt").replace("\\", "\\\\")
            source = f"""
साथ खोलो("{file_path}", "w") जैसे फ़:
    फ़.write("hello")
मुद्रय पठन("{file_path}")
"""
            _, output = self.run_source(source)
            self.assertEqual(output.strip(), "hello")

    def test_bhasha_prasadan_trim_split_and_search_work(self):
        source = """
आयात bhasha_prasadan
मुद्रय ट्रिम("  hello  ")
मुद्रय विभाजित("a,b,c", ",")
मुद्रय तार_खोजो("abcde", "cd")
"""
        _, output = self.run_source(source)
        self.assertEqual(output.splitlines(), ["hello", "['a', 'b', 'c']", "2"])

    def test_bhasha_prasadan_case_conversion_module_functions_work(self):
        source = """
आयात bhasha_prasadan
मुद्रय निम्न("HELLO")
मुद्रय उच्च("hello")
"""
        _, output = self.run_source(source)
        self.assertEqual(output.splitlines(), ["hello", "HELLO"])

    def test_sangrah_vistarit_sorts_do_not_mutate_input_and_exports_core_classes(self):
        source = """
आयात sangrah_vistarit
मान unsorted = [६४, ३४, २५, १२, २२, ११, ९०]
मुद्रय बुलबुला_क्रमबद्ध(unsorted)
मुद्रय द्रुत_क्रमबद्ध(unsorted)
मुद्रय unsorted
मान stack = नव स्टैक()
stack.धक्का(१०)
मुद्रय stack.पॉप()
"""
        _, output = self.run_source(source)
        self.assertEqual(
            output.splitlines(),
            [
                "[11, 12, 22, 25, 34, 64, 90]",
                "[11, 12, 22, 25, 34, 64, 90]",
                "[64, 34, 25, 12, 22, 11, 90]",
                "10",
            ],
        )

    def test_module_qualified_function_and_class_calls_work(self):
        source = """
आयात sangrah_vistarit
मुद्रय sangrah_vistarit.बुलबुला_क्रमबद्ध([३, १, २])
मान stack = नव sangrah_vistarit.स्टैक()
stack.धक्का(११)
मुद्रय stack.पॉप()
"""
        _, output = self.run_source(source)
        self.assertEqual(output.splitlines(), ["[1, 2, 3]", "11"])

    def test_whole_module_import_preserves_classes_and_hides_internal_bindings(self):
        source = "आयात sangrah_vistarit\n"
        bytecode = Compiler().compile(Parser(Lexer(source).tokenize()).parse())
        vm = VakVM()
        vm.run(bytecode)
        frame = vm.frames[0] if vm.frames else vm.current_frame
        module_obj = frame.locals[bytecode.var_names.index("sangrah_vistarit")]

        self.assertIsInstance(module_obj.attrs.get("स्टैक"), VakClass)
        self.assertIsInstance(module_obj.attrs.get("ग्राफ"), VakClass)
        self.assertNotIn("__imported_module_6", module_obj.attrs)

    def test_imported_class_methods_can_reference_sibling_module_classes(self):
        source = """
आयात sangrah_vistarit
मान bst = नव बाइनरी_सर्च_ट्री()
bst.जोड़ो(५०)
bst.जोड़ो(३०)
bst.जोड़ो(७०)
मुद्रय bst.खोजो(३०)
मुद्रय bst.खोजो(२०)
"""
        _, output = self.run_source(source)
        self.assertEqual(output.splitlines(), ["True", "False"])

    def test_imported_module_names_shadow_builtins(self):
        source = """
आयात sambhavana
मुद्रय परास([२, ४, ४, ४, ५, ५, ७, ९])
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "7")

    def test_sambhavana_median_uses_imported_sort_helper(self):
        source = """
आयात sambhavana
मुद्रय माध्यिका([२, ४, ४, ४, ५, ५, ७, ९])
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "4.5")

    def test_later_imported_module_name_wins_on_conflict(self):
        source = """
आयात sangrah_vistarit
आयात sambhavana
मुद्रय बहुलक([२, ४, ४, ४, ५, ५, ७, ९])
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "[4]")

    def test_sambhavana_permutations_use_builtin_range_not_statistical_range(self):
        source = """
आयात sambhavana
मुद्रय क्रमचय(५, ३)
मुद्रय संचय(५, ३)
"""
        _, output = self.run_source(source)
        self.assertEqual(output.splitlines(), ["60", "10"])

    def test_upayogita_conversion_helpers_import_their_dependencies(self):
        source = """
आयात upayogita
मुद्रय दशमलव_से_द्विआधारी(१०)
मुद्रय द्विआधारी_से_दशमलव("1010")
मुद्रय रोमन_से_दशमलव("MMXXIV")
"""
        _, output = self.run_source(source)
        self.assertEqual(output.splitlines(), ["1010", "10", "2024"])

    def test_upayogita_simple_hash_handles_text_input(self):
        source = """
आयात upayogita
मुद्रय सरल_हैश("ABC")
"""
        _, output = self.run_source(source)
        self.assertTrue(output.strip().isdigit())

    def test_kootlekh_password_hash_and_verify_round_trip(self):
        source = """
आयात kootlekh
मान hashed = पासवर्ड_हैश("secret")
मुद्रय दीर्घता(hashed[०])
मुद्रय दीर्घता(hashed[१])
मुद्रय पासवर्ड_जाँच("secret", hashed[१], hashed[०])
मुद्रय पासवर्ड_जाँच("wrong", hashed[१], hashed[०])
"""
        _, output = self.run_source(source)
        self.assertEqual(output.splitlines(), ["64", "16", "True", "False"])

    def test_py_bridge_natural_log_maps_to_python_log(self):
        source = """
आयात py_bridge
मुद्रय प्राकृतिक_लघुगणक(ई())
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "1.0")

    def test_tasks_example_runs_and_persists_data_file(self):
        tasks_path = Path(PROJECT_ROOT) / "examples" / "tasks.vak"
        source = tasks_path.read_text(encoding="utf-8")

        buffer = io.StringIO()
        interpreter = VakInterpreter()
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                os.chdir(temp_dir)
                with contextlib.redirect_stdout(buffer):
                    interpreter.run(source, filename=os.path.join(temp_dir, "tasks.vak"))
            finally:
                os.chdir(original_cwd)

            data_path = Path(temp_dir) / "kaarya_soochi.txt"
            self.assertTrue(data_path.exists())
            self.assertIn("वाक् भाषा का अध्ययन करें", data_path.read_text(encoding="utf-8"))
            self.assertIn("यह एक वास्तविक सॉफ्टवेयर अनुप्रयोग है।", buffer.getvalue())

    def test_event_loop_does_not_run_sleeping_task_until_woken(self):
        from runtime.src.event_loop import EventLoop

        class FakeCoro:
            def __init__(self):
                self.completed = False
                self.suspended = True

        loop = EventLoop()
        task = loop.create_task(FakeCoro(), name="sleeping")
        called = []
        loop._run_task = lambda queued_task: called.append(queued_task.name)

        loop._run_once()
        self.assertEqual(called, [])

        loop._schedule_sleep(time.time() - 0.01, task)
        loop._process_sleeping_tasks()
        self.assertFalse(task.coro.suspended)

    def test_sutra_block_form_parses(self):
        source = """
सूत्र दोगुना(क):
    अनुवाद -> क + क
"""
        self.run_source(source)

    def test_apavada_overrides_general_sutra(self):
        source = """
सूत्र कर(क):
    अनुवाद -> क + क

अपवाद कर(०):
    अनुवाद -> ०

मुद्रय कर(०)
मुद्रय कर(३)
"""
        _, output = self.run_source(source)
        self.assertEqual(output.splitlines(), ["0", "6"])

    def test_scoped_sutras_can_coexist(self):
        source = """
सूत्र कर(क):
    अधिकार भारत
    अनुवाद -> क + १

सूत्र कर(क):
    अधिकार यूके
    अनुवाद -> क + २

सूत्र कर(क):
    अनुवाद -> क + ३

मुद्रय कर(५)
मुद्रय कर(५, अधिकार="भारत")
मुद्रय कर(५, अधिकार="यूके")
"""
        _, output = self.run_source(source)
        self.assertEqual(output.splitlines(), ["8", "6", "7"])

    def test_parinama_rewrites_to_fixed_point(self):
        source = """
पारिणाम सरल_करो:
    जोड़(क, ०) -> क
    जोड़(०, क) -> क
    गुण(क, १) -> क
    गुण(क, ०) -> ०
    गुण(०, क) -> ०
    गुण(क, संख्या(०)) -> संख्या(०)
    गुण(संख्या(०), क) -> संख्या(०)
    जोड़(संख्या(क), संख्या(ख)) -> संख्या(क + ख)

मान परिणाम = सरल_करो(गुण(जोड़(संख्या(३), संख्या(४)), संख्या(०)))
मुद्रय परिणाम
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "0")

    def test_runtime_parinama_call_works_when_function_is_declared_before_rule(self):
        source = """
कर्म प्रयोग():
    मुद्रय सरल(जोड़(५, ०))

पारिणाम सरल:
    जोड़(क, ०) -> क

प्रयोग()
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "5")

    def test_imported_runtime_parinama_is_callable_via_term_builder(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            rules_path = os.path.join(temp_dir, "rules.vak")
            main_path = os.path.join(temp_dir, "main.vak")
            with open(rules_path, "w", encoding="utf-8") as rules_file:
                rules_file.write(
                    "पारिणाम सरल:\n"
                    "    जोड़(क, ०) -> क\n"
                    "    जोड़(०, क) -> क\n"
                )

            source = "आयात rules\nमुद्रय rules.सरल(पद(जोड़(५, ०)))\n"
            buffer = io.StringIO()
            interpreter = VakInterpreter()
            with contextlib.redirect_stdout(buffer):
                interpreter.run(source, filename=main_path)
            self.assertEqual(buffer.getvalue().strip(), "5")

    def test_yadricha_module_and_bridge_aliases_work(self):
        source = """
आयात यादृच्छा
आयात पायथन_ब्रिज
यादृच्छा_बीज(१२३)
मुद्रय यादृच्छा_पूर्णांक(१, १)
मुद्रय पायथन_ब्रिज.यादृच्छा_पूर्णांक(१, १)
"""
        _, output = self.run_source(source)
        self.assertEqual(output.splitlines()[-2:], ["1", "1"])

    def test_pipeline_operator_supports_multiline_chains(self):
        source = """
मान परिणाम = "  vak  "
    |> छाँटो
    |> उच्च

मुद्रय परिणाम
मुद्रय ५ |> अधिकतम(३)
"""
        _, output = self.run_source(source)
        self.assertEqual(output.splitlines(), ["VAK", "5"])

    def test_pratyabhijna_matches_sequence_patterns(self):
        source = """
मान परिणाम = [१, २, ३]
प्रत्यभिज्ञा परिणाम:
    []:
        मुद्रय "खाली"
    [पहला, ...]:
        मुद्रय पहला
    _:
        मुद्रय "अज्ञात"
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "1")

    def test_pratyabhijna_supports_call_patterns_and_result_values(self):
        source = """
कर्म भाग(क, ख):
    यदि ख == ०:
        वापस असिद्ध("शून्य")
    वापस सिद्ध(क // ख)

प्रत्यभिज्ञा भाग(१०, ०):
    सिद्ध(मान):
        मुद्रय मान
    असिद्ध(त्रुटि):
        मुद्रय त्रुटि
    _:
        मुद्रय "अज्ञात"
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "शून्य")

    def test_pratyabhijna_case_guards_work(self):
        source = """
प्रत्यभिज्ञा [१, २]:
    [x, y] यदि x + y == ४:
        मुद्रय "गलत"
    [x, y] यदि x + y == ३:
        मुद्रय "ठीक"
    _:
        मुद्रय "अज्ञात"
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "ठीक")

    def test_pratyabhijna_requires_catchall_case(self):
        source = """
प्रत्यभिज्ञा [१]:
    []:
        मुद्रय "खाली"
"""
        with self.assertRaises(CompileError):
            Compiler().compile(Parser(Lexer(source).tokenize()).parse())

    def test_result_helpers_are_available(self):
        source = """
मान s = सिद्ध(४२)
मान e = असिद्ध("त्रुटि")
मुद्रय फल_सफल_है(s)
मुद्रय फल_विफल_है(e)
मुद्रय फल_खोलो(s)
मुद्रय फल_त्रुटि(e)
"""
        _, output = self.run_source(source)
        self.assertEqual(output.splitlines(), ["True", "True", "42", "त्रुटि"])

    def test_vibhakti_compile_time_rejects_karana_mutation(self):
        source = """
कर्म चलाओ(करण औजार):
    औजार = [९]
"""
        with self.assertRaises(CompileError):
            Compiler().compile(Parser(Lexer(source).tokenize()).parse())

    def test_vibhakti_runtime_rejects_null_karta(self):
        source = """
कर्म योग(कर्ता x: संख्या, कर्म y: संख्या):
    मुद्रय x + y

योग(शून्य, २)
"""
        with self.assertRaisesRegex(Exception, "कर्ता"):
            self.run_source(source)

    def test_vibhakti_runtime_rejects_mutating_karana_object(self):
        source = """
कर्म प्रयोग(करण औजार):
    मान दूसरा = औजार
    दूसरा[०] = ९

प्रयोग([१, २])
"""
        with self.assertRaisesRegex(Exception, "करण"):
            self.run_source(source)

    def test_python_style_builtin_helpers_are_available(self):
        source = """
मुद्रय दीर्घता(set([१, १, २]))
मुद्रय map(lambda x: x * २, [१, २, ३])
मुद्रय filter(lambda x: x > १, [१, २, ३])
मुद्रय enumerate(["क", "ख"], १)
मुद्रय zip([१, २], ["a", "b"])
"""
        _, output = self.run_source(source)
        self.assertEqual(
            output.splitlines(),
            ["2", "[2, 4, 6]", "[2, 3]", "[(1, 'क'), (2, 'ख')]", "[(1, 'a'), (2, 'b')]"],
        )

    def test_python_style_introspection_builtins_work_for_vak_objects(self):
        source = """
वर्ग रंग:
    कर्म __init__(स्वयं):
        स्वयं.नाम = "लाल"

मान r = रंग()
मुद्रय isinstance(r, रंग)
मुद्रय hasattr(r, "नाम")
मुद्रय all([सत्य, २ > १])
मुद्रय any([असत्य, ३ > २])
"""
        _, output = self.run_source(source)
        self.assertEqual(output.splitlines(), ["True", "True", "True", "True"])

    def test_paath_kar_uses_custom_str(self):
        source = """
वर्ग रंग:
    कर्म __init__(स्वयं, नाम):
        स्वयं.नाम = नाम
    कर्म __str__(स्वयं):
        वापस स्वयं.नाम

मान ल = रंग("लाल")
मुद्रय पाठ_कर(ल)
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "लाल")

    def test_devanagari_import_alias_loads_stdlib_module(self):
        source = """
आयात गणित
मुद्रय वर्गफल(४)
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "16")

    def test_ganit_module_exposes_ascii_pi_alias(self):
        source = """
आयात ganit
मुद्रय ganit.pi
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "3.141592653589793")

    def test_runtime_root_module_import_works(self):
        source = """
आयात core_builtins
मुद्रय पूर्णांक_कर("42")
मुद्रय पाठ_कर(असत्य)
"""
        _, output = self.run_source(source)
        self.assertEqual(output.splitlines(), ["42", "असत्य"])

    def test_bool_and_int_constants_remain_distinct(self):
        source = """
मान values = [१, सत्य, ०, असत्य]
मुद्रय प्रकार(values[०])
मुद्रय प्रकार(values[१])
मुद्रय प्रकार(values[२])
मुद्रय प्रकार(values[३])
"""
        _, output = self.run_source(source)
        self.assertEqual(
            output.splitlines(),
            ["संख्या", "बूलियन", "संख्या", "बूलियन"],
        )

    def test_relative_import_uses_calling_file_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            helper_path = os.path.join(temp_dir, "helper.vak")
            main_path = os.path.join(temp_dir, "main.vak")
            with open(helper_path, "w", encoding="utf-8") as helper_file:
                helper_file.write("कर्म दुगुना(x):\n    प्रत्यागच्छ x * २\n")

            source = "आयात helper\nमुद्रय दुगुना(५)\n"
            buffer = io.StringIO()
            interpreter = VakInterpreter()
            with contextlib.redirect_stdout(buffer):
                interpreter.run(source, filename=main_path)
            self.assertEqual(buffer.getvalue().strip(), "10")

    def test_dotted_import_resolves_package_style_module_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            package_dir = os.path.join(temp_dir, "pkg")
            os.makedirs(package_dir, exist_ok=True)
            with open(os.path.join(package_dir, "tools.vak"), "w", encoding="utf-8") as module_file:
                module_file.write("कर्म तिगुना(x):\n    प्रत्यागच्छ x * ३\n")

            source = "आयात pkg.tools\nमुद्रय तिगुना(७)\n"
            buffer = io.StringIO()
            interpreter = VakInterpreter()
            with contextlib.redirect_stdout(buffer):
                interpreter.run(source, filename=os.path.join(temp_dir, "main.vak"))
            self.assertEqual(buffer.getvalue().strip(), "21")

    def test_dunder_init_constructor_sets_instance_attributes(self):
        source = """
वर्ग पशु:
    कर्म __init__(स्वयं, नाम):
        स्वयं.नाम = नाम

चर क = पशु("dog")
मुद्रय क.नाम
"""
        _, output = self.run_source(source)
        self.assertEqual(output.strip(), "dog")

    def test_with_statement_works_with_file_module_without_import_noise(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "sample.txt").replace("\\", "\\\\")
            source = f"""
आयात file
चर f = नव file.संचिका("{file_path}")
साथ f जैसे fh:
    fh.लिखो("hello")
मुद्रय पठन("{file_path}")
"""
            _, output = self.run_source(source)
            self.assertEqual(output.strip(), "hello")

    def test_chitra_effect_builtins_have_real_vm_implementations(self):
        vm = VakVM(enable_jit=False)
        vm.suppress_output = True

        canvas = vm.builtins["_chitra_canvas"](32, 24, "white")
        vm.builtins["_chitra_line"](canvas, 0, 0, 31, 23, "black")
        centered = vm.builtins["_chitra_text_centered"](canvas, 4, "vak", "black", 1)
        rotated = vm.builtins["_chitra_rotate"](canvas, 45, 16, 12)
        mandala = vm.builtins["_chitra_mandala"](
            canvas,
            16,
            12,
            8,
            6,
            [vm.builtins["_chitra_color"]("black"), vm.builtins["_chitra_color"]("white")],
        )
        kaleidoscope = vm.builtins["_chitra_kaleidoscope"](canvas, 6)

        self.assertIs(centered, canvas)
        self.assertIs(mandala, canvas)
        self.assertEqual(rotated.width, canvas.width)
        self.assertEqual(rotated.height, canvas.height)
        self.assertEqual(kaleidoscope.width, canvas.width)
        self.assertEqual(kaleidoscope.height, canvas.height)

    def test_http_download_builtin_writes_destination_file(self):
        vm = VakVM(enable_jit=False)
        vm.suppress_output = True

        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = os.path.join(temp_dir, "source.txt")
            target_path = os.path.join(temp_dir, "copied.txt")
            with open(source_path, "w", encoding="utf-8") as handle:
                handle.write("vakya-download")

            source_url = Path(source_path).resolve().as_uri()
            result_path = vm.builtins["जाल_डाउनलोड"](source_url, target_path)

            self.assertTrue(os.path.exists(target_path))
            with open(target_path, "r", encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "vakya-download")
            self.assertTrue(str(result_path).endswith("copied.txt"))


if __name__ == "__main__":
    unittest.main()
