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
        self.assertIn("vak_native", pages)
        self.assertIn("vak_legacy_native", pages)
        self.assertIn("math_logic_native", pages)
        self.assertIn("sanskrit_notation_native", pages)
        self.assertIn("english_vak_native", pages)
        self.assertEqual(pages["vak"]["kind"], "python")
        self.assertEqual(pages["vak_native"]["kind"], "vak_module")
        self.assertEqual(pages["vak"]["chapter"], "vak_core")
        self.assertEqual(pages["english_vak"]["chapter"], "bridges")
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

    def test_codex_english_page_translates_to_vak(self):
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
        self.assertEqual(result.page, "english_vak")
        self.assertIn("कर्म add(a, b):", result.source)
        self.assertIn("प्रत्यागच्छ a + b", result.source)
        self.assertEqual(result.confidence, "safe_auto_fix")
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

    def test_branch_natural_language_page_handles_simple_command(self):
        codex = build_default_codex(active_branches=["universal_codex_lab"])
        result = codex.transform_source(
            "print even numbers from 1 to 5",
            filename="command.txt",
        )
        self.assertEqual(result.page, "natural_language")
        self.assertIn("यदि i % 2 == 0:", result.source)
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
