import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime.src.codex import build_default_codex
from runtime.src.interpreter import VakInterpreter


class UniversalCodexTests(unittest.TestCase):
    def test_codex_lists_shipped_pages(self):
        codex = build_default_codex()
        pages = {item["name"]: item for item in codex.list_pages()}
        self.assertIn("vak_legacy", pages)
        self.assertIn("vak", pages)
        self.assertIn("math_logic", pages)
        self.assertIn("sanskrit_notation", pages)
        self.assertIn("english_vak", pages)
        self.assertIn("python_vak", pages)
        self.assertIn("javascript_vak", pages)
        self.assertIn("pseudocode_vak", pages)
        self.assertIn("vak_native", pages)
        self.assertIn("vak_legacy_native", pages)
        self.assertIn("math_logic_native", pages)
        self.assertIn("sanskrit_notation_native", pages)
        self.assertIn("english_vak_native", pages)
        self.assertEqual(pages["vak"]["kind"], "python")
        self.assertEqual(pages["vak_native"]["kind"], "vak_module")
        self.assertEqual(pages["vak"]["chapter"], "vak_core")
        self.assertEqual(pages["english_vak"]["chapter"], "bridges")
        self.assertEqual(pages["python_vak"]["chapter"], "bridges")
        self.assertIn("normalize", pages["vak_native"]["capabilities"])
        self.assertTrue(pages["vak_native"]["emits_vak"])
        self.assertGreaterEqual(pages["vak"]["max_fixpoint_passes"], 2)

    def test_codex_lists_chapters(self):
        codex = build_default_codex(active_branches=["universal_codex_lab"])
        chapters = {item["name"]: item for item in codex.list_chapters()}
        self.assertIn("vak_core", chapters)
        self.assertIn("bridges", chapters)
        self.assertIn("math_logic", chapters)
        self.assertIn("sanskrit_notation", chapters)
        self.assertIn("vak_native", chapters)
        self.assertIn("experimental_systems", chapters)
        self.assertIn("experimental_language", chapters)
        self.assertIn("vak", chapters["vak_core"]["pages"])
        self.assertIn("english_vak", chapters["bridges"]["pages"])

    def test_codex_vak_page_normalizes_legacy_vak(self):
        codex = build_default_codex()
        result = codex.transform_source(
            textwrap.dedent(
                """
                चर x = 0
                जबतक x < 2:
                    x = x + 1
                """
            ),
            filename="legacy.vak",
        )
        self.assertEqual(result.page, "vak_legacy")
        self.assertIn("यावत् x < 2:", result.source)
        self.assertEqual(result.confidence, "safe_auto_fix")
        self.assertIsNotNone(result.manifest)
        self.assertEqual(result.manifest.name, "vak_legacy")
        self.assertIsNotNone(result.validation)
        self.assertTrue(result.validation.syntax_valid)
        self.assertTrue(result.validation.compiled)
        self.assertEqual(result.source_kind, "vak")
        self.assertTrue(result.applied_rules)
        self.assertTrue(result.validation_history)

    def test_codex_vak_page_normalizes_augmented_assignment_drift(self):
        codex = build_default_codex()
        result = codex.transform_source(
            textwrap.dedent(
                """
                चर कुल = ०
                कुल += ३
                चर सूचक = ०
                सूचक++
                """
            ),
            filename="drift.vak",
            page="vak",
        )
        self.assertEqual(result.page, "vak")
        self.assertIn("कुल = कुल + ३", result.source)
        self.assertIn("सूचक = सूचक + १", result.source)
        self.assertIsNotNone(result.validation)
        self.assertTrue(result.validation.compiled)

    def test_codex_vak_page_normalizes_python_order_import_drift(self):
        codex = build_default_codex()
        with tempfile.TemporaryDirectory() as tempdir:
            temp_root = Path(tempdir)
            (temp_root / "demo.vak").write_text(
                "कर्म प्रतिज्ञा():\n    प्रत्यागच्छ ११\n",
                encoding="utf-8",
            )
            main_path = temp_root / "main.vak"
            result = codex.transform_source(
                "from demo import प्रतिग्ञा\nमुद्रय प्रतिग्ञा()\n",
                filename=str(main_path),
                page="vak",
            )
            self.assertEqual(result.page, "vak")
            self.assertIn("आयात प्रतिज्ञा से demo", result.source)
            self.assertIn("मुद्रय प्रतिज्ञा()", result.source)
            self.assertIsNotNone(result.validation)
            self.assertTrue(result.validation.compiled)

    def test_codex_vak_page_normalizes_legacy_generator_surface(self):
        codex = build_default_codex()
        result = codex.transform_source(
            textwrap.dedent(
                """
                श्रेणी गणक {
                    परिवर्तनी गुणक = २
                    कार्य दुगुना(स्वयं, x) {
                        लौटाओ x * स्वयं.गुणक
                    }
                }
                """
            ),
            filename="generated.vak",
            page="vak",
        )
        self.assertEqual(result.page, "vak")
        self.assertIn("वर्ग गणक:", result.source)
        self.assertIn("कर्म दुगुना(स्वयं, x):", result.source)
        self.assertIn("प्रत्यागच्छ x * स्वयं.गुणक", result.source)
        self.assertIsNotNone(result.validation)
        self.assertTrue(result.validation.compiled)

    def test_codex_vak_page_normalizes_generated_control_flow_surface(self):
        codex = build_default_codex()
        result = codex.transform_source(
            textwrap.dedent(
                """
                चर items = [१, २]
                foreach item in items {
                    मुद्रय item
                }
                if सत्य {
                    मुद्रय १
                } else {
                    मुद्रय २
                }
                """
            ),
            filename="generated_control.vak",
            page="vak",
        )
        self.assertEqual(result.page, "vak")
        self.assertIn("प्रत्येक चर item अन्तर्गत items:", result.source)
        self.assertIn("यदि सत्य:", result.source)
        self.assertIn("अन्यथा:", result.source)
        self.assertIsNotNone(result.validation)
        self.assertTrue(result.validation.compiled)

    def test_codex_vak_page_removes_branch_pseudomodule_import(self):
        codex = build_default_codex()
        result = codex.transform_source(
            "आयात चित्रकला\nचर क = चित्रकला.कैनवास_निर्माण(१०, १०)\nचित्रकला.रेखा(क, ०, ०, ९, ९)\n",
            filename="branch_import.vak",
            page="vak",
        )
        self.assertEqual(result.page, "vak")
        self.assertNotIn("आयात चित्रकला", result.source)
        self.assertIn("_chitra_canvas", result.source)
        self.assertIn("_chitra_line", result.source)
        self.assertIsNotNone(result.validation)
        self.assertTrue(result.validation.compiled)

    def test_codex_python_page_translates_to_vak(self):
        codex = build_default_codex()
        result = codex.transform_source(
            textwrap.dedent(
                """
                def add(a, b):
                    return a + b
                """
            ),
            filename="sample.py",
        )
        self.assertEqual(result.page, "python_vak")
        self.assertIn("कर्म add(a, b):", result.source)
        self.assertIn("प्रत्यागच्छ (a + b)", result.source)
        self.assertEqual(result.confidence, "safe_auto_fix")
        self.assertIsNotNone(result.validation)
        self.assertTrue(result.validation.compiled)

    def test_codex_english_page_remains_force_selectable(self):
        codex = build_default_codex()
        result = codex.transform_source(
            textwrap.dedent(
                """
                def add(a, b):
                    return a + b
                """
            ),
            filename="sample.py",
            page="english_vak",
        )
        self.assertEqual(result.page, "english_vak")
        self.assertIn("कर्म add(a, b):", result.source)
        self.assertIn("प्रत्यागच्छ a + b", result.source)

    def test_codex_promoted_javascript_page_translates_without_branch(self):
        codex = build_default_codex()
        result = codex.transform_source(
            "function greet() { return 'hi'; }\n",
            filename="sample.js",
        )
        self.assertEqual(result.page, "javascript_vak")
        self.assertIn("कर्म greet():", result.source)
        self.assertIn("प्रत्यागच्छ 'hi'", result.source)
        self.assertIsNotNone(result.validation)
        self.assertTrue(result.validation.compiled)

    def test_codex_promoted_pseudocode_page_translates_without_branch(self):
        codex = build_default_codex()
        result = codex.transform_source(
            "set x = 1\nif x > 0 then\nreturn x\n",
            filename="sample.pseudo",
        )
        self.assertEqual(result.page, "pseudocode_vak")
        self.assertIn("चर x = 1", result.source)
        self.assertIn("यदि (x > 0):", result.source)
        self.assertIn("प्रत्यागच्छ x", result.source)
        self.assertIsNotNone(result.validation)
        self.assertTrue(result.validation.compiled)

    def test_codex_legacy_page_wins_on_old_vak_markers(self):
        codex = build_default_codex()
        result = codex.transform_source(
            "चर x = 0\nजबतक x < 1:\n    x = x + 1\n",
            filename="old_style.vak",
        )
        self.assertEqual(result.page, "vak_legacy")
        self.assertIn("यावत् x < 1:", result.source)

    def test_codex_math_logic_page_normalizes_symbolic_logic(self):
        codex = build_default_codex()
        result = codex.transform_source(
            "यदि ¬(a ∧ b):\n    मुद्रय(⊤)\n",
            filename="logic.logic",
        )
        self.assertEqual(result.page, "math_logic")
        self.assertIn("यदि न (a  और  b):", result.source)
        self.assertIn("मुद्रय(सत्य)", result.source)
        self.assertEqual(result.source_kind, "math_logic")
        self.assertIn("¬", result.detected_constructs)

    def test_codex_sanskrit_notation_page_normalizes_transliteration(self):
        codex = build_default_codex()
        result = codex.transform_source(
            "karma add(x, y):\n    pratyagaccha x + y\n",
            filename="roman.svk",
        )
        self.assertEqual(result.page, "sanskrit_notation")
        self.assertIn("कर्म add(x, y):", result.source)
        self.assertIn("प्रत्यागच्छ x + y", result.source)
        self.assertEqual(result.source_kind, "sanskrit_notation")

    def test_codex_vak_native_page_runs_real_vak_page_module(self):
        codex = build_default_codex()
        result = codex.transform_source(
            textwrap.dedent(
                """
                चर x = 0
                जबतक x < 2:
                    x = x + 1
                """
            ),
            filename="legacy.vak",
            page="vak_native",
        )
        self.assertEqual(result.page, "vak_native")
        self.assertIn("यावत् x < 2:", result.source)
        self.assertEqual(result.metadata["page_kind"], "vak_module")
        self.assertTrue(str(result.metadata["vak_page_path"]).endswith("vak_native.vak"))
        self.assertIsNotNone(result.manifest)
        self.assertEqual(result.manifest.kind, "vak_module")
        self.assertEqual(result.manifest.capabilities, ("vak", "normalize", "repair"))
        self.assertIsNotNone(result.validation)
        self.assertTrue(result.validation.compiled)

    def test_codex_other_vak_native_page_wrappers_are_force_selectable(self):
        codex = build_default_codex()
        result = codex.transform_source(
            "karma add(x, y):\n    pratyagaccha x + y\n",
            filename="roman.svk",
            page="sanskrit_notation_native",
        )
        self.assertEqual(result.page, "sanskrit_notation_native")
        self.assertIn("कर्म add(x, y):", result.source)
        self.assertIsNotNone(result.validation)
        self.assertTrue(result.validation.compiled)

    def test_codex_invalid_manual_page_is_downgraded_by_core_validation(self):
        codex = build_default_codex()
        result = codex.transform_source(
            "def broken(:\n    return 1\n",
            filename="broken.py",
            page="english_vak",
        )
        self.assertEqual(result.confidence, "do_not_touch")
        self.assertIsNotNone(result.validation)
        self.assertFalse(result.validation.syntax_valid)
        self.assertTrue(any(item.confidence == "do_not_touch" for item in result.diagnostics))
        self.assertTrue(result.rejected_rules)

    def test_branch_codex_pages_are_discovered(self):
        codex = build_default_codex(active_branches=["universal_codex_lab"])
        pages = {item["name"] for item in codex.list_pages()}
        self.assertIn("c_subset", pages)
        self.assertIn("rust_subset", pages)
        self.assertIn("natural_language", pages)
        self.assertIn("python_to_vak_experimental", pages)
        self.assertIn("javascript_to_vak_experimental", pages)
        self.assertIn("pseudocode_to_vak_experimental", pages)

    def test_branch_full_codex_system_pack_is_discovered(self):
        codex = build_default_codex(active_branches=["universal_codex_lab"])
        pages = {item["name"] for item in codex.list_pages()}
        codex_system_pages = {name for name in pages if name.startswith("codex_system_")}
        self.assertGreaterEqual(len(codex_system_pages), 25)
        self.assertIn("codex_system_python_to_vak", codex_system_pages)
        self.assertIn("codex_system_api_generator", codex_system_pages)
        self.assertIn("codex_system_grammar_engine", codex_system_pages)
        self.assertIn("codex_system_knowledge_graph", codex_system_pages)
        self.assertIn("codex_system_bytecode_decoder", codex_system_pages)
        self.assertIn("codex_system_vak_native", codex_system_pages)

    def test_branch_python_translator_page_handles_python_source(self):
        codex = build_default_codex(active_branches=["universal_codex_lab"])
        result = codex.transform_source(
            "def add(a, b):\n    return a + b\n",
            filename="sample.py",
            page="python_to_vak_experimental",
        )
        self.assertEqual(result.page, "python_to_vak_experimental")
        self.assertIn("कर्म add(a, b):", result.source)
        self.assertIn("प्रत्यागच्छ (a + b)", result.source)
        self.assertIsNotNone(result.validation)
        self.assertTrue(result.validation.compiled)

    def test_branch_javascript_translator_page_handles_simple_function(self):
        codex = build_default_codex(active_branches=["universal_codex_lab"])
        result = codex.transform_source(
            "function greet() { return 'hi'; }\n",
            filename="sample.js",
            page="javascript_to_vak_experimental",
        )
        self.assertEqual(result.page, "javascript_to_vak_experimental")
        self.assertIn("कर्म greet():", result.source)
        self.assertIn("प्रत्यागच्छ 'hi'", result.source)
        self.assertIsNotNone(result.validation)
        self.assertTrue(result.validation.compiled)

    def test_branch_pseudocode_translator_page_handles_basic_flow(self):
        codex = build_default_codex(active_branches=["universal_codex_lab"])
        result = codex.transform_source(
            "set x = 1\nif x > 0 then\nreturn x\n",
            filename="sample.pseudo",
            page="pseudocode_to_vak_experimental",
        )
        self.assertEqual(result.page, "pseudocode_to_vak_experimental")
        self.assertIn("चर x = 1", result.source)
        self.assertIn("यदि (x > 0):", result.source)
        self.assertIn("प्रत्यागच्छ x", result.source)
        self.assertIsNotNone(result.validation)
        self.assertTrue(result.validation.compiled)

    def test_branch_codex_system_python_page_is_force_selectable(self):
        codex = build_default_codex(active_branches=["universal_codex_lab"])
        result = codex.transform_source(
            "def add(a, b):\n    return a + b\n",
            filename="sample.py",
            page="codex_system_python_to_vak",
        )
        self.assertEqual(result.page, "codex_system_python_to_vak")
        self.assertIn("कर्म", result.source)
        self.assertIn("प्रत्यागच्छ", result.source)
        self.assertEqual(result.metadata["integration_pack"], "codex_system_full")
        self.assertEqual(result.metadata["vendor_page"], "python_to_vak")
        self.assertIsNotNone(result.validation)
        self.assertTrue(result.validation.compiled)

    def test_branch_codex_system_api_generator_page_is_force_selectable(self):
        codex = build_default_codex(active_branches=["universal_codex_lab"])
        spec = """
        {
            "type": "rest",
            "name": "TestAPI",
            "endpoints": [
                {"method": "GET", "path": "/items"},
                {"method": "POST", "path": "/items"}
            ],
            "models": [
                {"name": "Item", "fields": ["id: int", "name: string"]}
            ]
        }
        """
        result = codex.transform_source(
            textwrap.dedent(spec),
            filename="api.json",
            page="codex_system_api_generator",
        )
        self.assertEqual(result.page, "codex_system_api_generator")
        self.assertIn("कर्म", result.source)
        self.assertIn("वर्ग", result.source)
        self.assertIsNotNone(result.validation)
        self.assertTrue(result.validation.compiled)

    def test_branch_codex_system_vak_native_page_is_force_selectable(self):
        codex = build_default_codex(active_branches=["universal_codex_lab"])
        result = codex.transform_source(
            "चर x = 0\nजबतक x < 1:\n    x = x + 1\n",
            filename="legacy.vak",
            page="codex_system_vak_native",
        )
        self.assertEqual(result.page, "codex_system_vak_native")
        self.assertIn("यावत् x < 1:", result.source)
        self.assertEqual(result.metadata["integration_pack"], "codex_system_full")
        self.assertEqual(result.metadata["vendor_page"], "vak_native")
        self.assertIsNotNone(result.validation)
        self.assertTrue(result.validation.compiled)

    def test_branch_c_subset_page_translates_simple_c(self):
        codex = build_default_codex(active_branches=["universal_codex_lab"])
        result = codex.transform_source(
            textwrap.dedent(
                """
                int main() {
                    int x = 1;
                    printf("%d", x);
                    return 0;
                }
                """
            ),
            filename="sample.c",
        )
        self.assertEqual(result.page, "c_subset")
        self.assertIn("कर्म main():", result.source)
        self.assertIn("चर x = 1", result.source)
        self.assertIn("मुद्रय(x)", result.source)

    def test_branch_c_subset_page_translates_simple_for_loop(self):
        codex = build_default_codex(active_branches=["universal_codex_lab"])
        result = codex.transform_source(
            textwrap.dedent(
                """
                int main() {
                    for (int i = 0; i < 3; i++) {
                        printf("%d", i);
                    }
                    return 0;
                }
                """
            ),
            filename="loop.c",
        )
        self.assertEqual(result.page, "c_subset")
        self.assertIn("प्रत्येक चर i अन्तर्गत परास(0, 3):", result.source)
        self.assertIn("मुद्रय(i)", result.source)

    def test_branch_rust_subset_page_translates_simple_rust(self):
        codex = build_default_codex(active_branches=["universal_codex_lab"])
        result = codex.transform_source(
            textwrap.dedent(
                """
                fn main() {
                    let mut x = 1;
                    println!("{}", x);
                }
                """
            ),
            filename="sample.rs",
        )
        self.assertEqual(result.page, "rust_subset")
        self.assertIn("कर्म main():", result.source)
        self.assertIn("चर x = 1", result.source)
        self.assertIn("मुद्रय(x)", result.source)

    def test_branch_rust_subset_page_translates_range_for_loop(self):
        codex = build_default_codex(active_branches=["universal_codex_lab"])
        result = codex.transform_source(
            textwrap.dedent(
                """
                fn main() {
                    for i in 1..=3 {
                        println!("{}", i);
                    }
                }
                """
            ),
            filename="loop.rs",
        )
        self.assertEqual(result.page, "rust_subset")
        self.assertIn("प्रत्येक चर i अन्तर्गत परास(1, (3) + 1):", result.source)
        self.assertIn("मुद्रय(i)", result.source)

    def test_branch_natural_language_page_handles_simple_command(self):
        codex = build_default_codex(active_branches=["universal_codex_lab"])
        result = codex.transform_source(
            "print even numbers from 1 to 5",
            filename="command.txt",
        )
        self.assertEqual(result.page, "natural_language")
        self.assertIn("यदि i % 2 == 0:", result.source)
        self.assertEqual(result.confidence, "suggest_only")

    def test_branch_natural_language_page_handles_repeat_print_command(self):
        codex = build_default_codex(active_branches=["universal_codex_lab"])
        result = codex.transform_source(
            'repeat 3 times print "जय"',
            filename="repeat.txt",
        )
        self.assertEqual(result.page, "natural_language")
        self.assertIn("प्रत्येक चर", result.source)
        self.assertIn('मुद्रय("जय")', result.source)
        self.assertEqual(result.confidence, "suggest_only")

    def test_interpreter_exposes_codex_source(self):
        interpreter = VakInterpreter()
        result = interpreter.codex_source("जबतक सत्य:\n    विराम\n", filename="sample.vak")
        self.assertEqual(result.page, "vak_legacy")
        self.assertIn("यावत् सत्य:", result.source)

    def test_codex_builtins_are_callable_from_runtime(self):
        interpreter = VakInterpreter()
        pages = interpreter.vm.builtins["कोडेक्स_पृष्ठ"]()
        chapters = interpreter.vm.builtins["कोडेक्स_अध्याय"]()
        self.assertTrue(any(item["name"] == "vak" for item in pages))
        self.assertTrue(any(item["name"] == "vak_core" for item in chapters))
        payload = interpreter.vm.builtins["कोडेक्स_विवरण"](
            "जबतक सत्य:\n    विराम\n",
            "vak_legacy",
            "sample.vak",
        )
        self.assertEqual(payload["page"], "vak_legacy")
        self.assertEqual(payload["source_kind"], "vak")
        self.assertTrue(payload["validation"]["compiled"])

    def test_codex_promotion_report_and_builtin_reflect_experimental_gate(self):
        with tempfile.TemporaryDirectory() as tempdir:
            corpus_root = Path(tempdir)
            sample = corpus_root / "sample.c"
            sample.write_text(
                textwrap.dedent(
                    """
                    int main() {
                        int x = 1;
                        printf("%d", x);
                        return 0;
                    }
                    """
                ),
                encoding="utf-8",
            )
            codex = build_default_codex(active_branches=["universal_codex_lab"])
            report = codex.promotion_report("c_subset", corpus_root=corpus_root)
            self.assertEqual(report.page, "c_subset")
            self.assertEqual(report.total_cases, 1)
            self.assertFalse(report.ready_for_main)
            self.assertTrue(any(gate.name == "deterministic_support" and not gate.passed for gate in report.gates))

            interpreter = VakInterpreter(active_branches=["universal_codex_lab"])
            payload = interpreter.vm.builtins["कोडेक्स_उन्नयन"]("c_subset", str(corpus_root))
            self.assertEqual(payload["page"], "c_subset")
            self.assertEqual(payload["total_cases"], 1)
            self.assertFalse(payload["ready_for_main"])

    def test_cli_codex_writes_output(self):
        with tempfile.TemporaryDirectory() as tempdir:
            input_path = Path(tempdir) / "legacy.vak"
            output_path = Path(tempdir) / "legacy_fixed.vak"
            input_path.write_text(
                textwrap.dedent(
                    """
                    चर x = 0
                    जबतक x < 1:
                        x = x + 1
                    """
                ),
                encoding="utf-8",
            )
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "utf-8"
            result = subprocess.run(
                [
                    sys.executable,
                    "vak.py",
                    "--कोडेक्स",
                    str(input_path),
                    str(output_path),
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
                timeout=60,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(output_path.exists())
            self.assertIn("यावत् x < 1:", output_path.read_text(encoding="utf-8"))
            self.assertIn("संस्कृत-वाक्य यूनिवर्सल कोडेक्स रिपोर्ट", result.stdout)

    def test_cli_lists_codex_pages(self):
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            [sys.executable, "vak.py", "--codex-pages"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("vak:", result.stdout)
        self.assertIn("english_vak:", result.stdout)
        self.assertIn("vak_native:", result.stdout)

    def test_cli_lists_codex_chapters(self):
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        result = subprocess.run(
            [sys.executable, "vak.py", "--codex-chapters"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("vak_core:", result.stdout)
        self.assertIn("bridges:", result.stdout)


if __name__ == "__main__":
    unittest.main()
