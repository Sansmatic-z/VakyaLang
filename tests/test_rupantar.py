import contextlib
import io
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

from runtime.src.interpreter import VakInterpreter
from runtime.src.rupantar import VakyaRupantar


class VakyaRupantarTests(unittest.TestCase):
    def test_rupantar_normalizes_deprecated_keywords_and_type_pattern(self):
        engine = VakyaRupantar()
        result = engine.transform_source(
            textwrap.dedent(
                """
                जबतक संख्या < ३:
                    विराम
                यदि रंग के प्रकार == dict:
                    मुद्रय रंग
                यदि क < १ या क > ३:
                    मुद्रय क
                """
            )
        )
        self.assertTrue(result.transformed)
        self.assertIn("यावत् संख्या < ३:", result.source)
        self.assertIn('यदि प्रकार(रंग) == "शब्दकोश":', result.source)
        self.assertIn("यदि क < १ अथवा क > ३:", result.source)
        self.assertTrue(result.syntax_valid)
        self.assertTrue(result.compiled)

    def test_rupantar_normalizes_identifier_digits_and_member_aliases(self):
        engine = VakyaRupantar()
        result = engine.transform_source(
            textwrap.dedent(
                """
                चर सूची = []
                सूची.append(१)
                चर टी₁ = ३
                मुद्रय टी₁
                """
            )
        )
        self.assertIn("सूची.जोड़ो(१)", result.source)
        self.assertIn("चर टी१ = ३", result.source)
        self.assertIn("मुद्रय टी१", result.source)
        self.assertTrue(result.syntax_valid)
        self.assertTrue(result.compiled)

    def test_rupantar_normalizes_augmented_assignments_and_increment_syntax(self):
        engine = VakyaRupantar()
        result = engine.transform_source(
            textwrap.dedent(
                """
                चर कुल = ०
                कुल += ३
                कुल *= २
                चर सूचक = ०
                सूचक++
                --सूचक
                मुद्रय कुल
                मुद्रय सूचक
                """
            )
        )
        self.assertIn("कुल = कुल + ३", result.source)
        self.assertIn("कुल = कुल * २", result.source)
        self.assertIn("सूचक = सूचक + १", result.source)
        self.assertIn("सूचक = सूचक - १", result.source)
        self.assertTrue(result.syntax_valid)
        self.assertTrue(result.compiled)

    def test_rupantar_normalizes_python_order_import_syntax(self):
        engine = VakyaRupantar()
        with tempfile.TemporaryDirectory() as tempdir:
            temp_root = Path(tempdir)
            module_path = temp_root / "demo.vak"
            main_path = temp_root / "main.vak"
            module_path.write_text(
                textwrap.dedent(
                    """
                    कर्म प्रतिज्ञा():
                        प्रत्यागच्छ ११
                    """
                ),
                encoding="utf-8",
            )
            source = "from demo import प्रतिग्ञा\nमुद्रय प्रतिग्ञा()\n"
            result = engine.transform_source(source, source_path=str(main_path))
            self.assertIn("आयात प्रतिज्ञा से demo", result.source)
            self.assertIn("मुद्रय प्रतिज्ञा()", result.source)
            self.assertTrue(result.syntax_valid)
            self.assertTrue(result.compiled)

    def test_rupantar_normalizes_legacy_generator_surface_blocks(self):
        engine = VakyaRupantar()
        result = engine.transform_source(
            textwrap.dedent(
                """
                श्रेणी गणक {
                    परिवर्तनी गुणक = २
                    कार्य दुगुना(स्वयं, x) {
                        लौटाओ x * स्वयं.गुणक
                    }
                }

                चर g = नव गणक()
                मुद्रय g.दुगुना(४)
                """
            )
        )
        self.assertIn("वर्ग गणक:", result.source)
        self.assertIn("चर गुणक = २", result.source)
        self.assertIn("कर्म दुगुना(स्वयं, x):", result.source)
        self.assertIn("प्रत्यागच्छ x * स्वयं.गुणक", result.source)
        self.assertNotIn("{", result.source)
        self.assertTrue(result.syntax_valid)
        self.assertTrue(result.compiled)

    def test_rupantar_normalizes_generated_foreach_and_else_blocks(self):
        engine = VakyaRupantar()
        result = engine.transform_source(
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
            )
        )
        self.assertIn("प्रत्येक चर item अन्तर्गत items:", result.source)
        self.assertIn("यदि सत्य:", result.source)
        self.assertIn("अन्यथा:", result.source)
        self.assertNotIn("{", result.source)
        self.assertTrue(result.syntax_valid)
        self.assertTrue(result.compiled)

    def test_rupantar_removes_branch_pseudomodule_import_when_branch_builtins_exist(self):
        engine = VakyaRupantar()
        result = engine.transform_source(
            textwrap.dedent(
                """
                आयात चित्रकला
                चर क = चित्रकला.कैनवास_निर्माण(१०, १०)
                चित्रकला.रेखा(क, ०, ०, ९, ९)
                """
            )
        )
        self.assertNotIn("आयात चित्रकला", result.source)
        self.assertIn("_chitra_canvas", result.source)
        self.assertIn("_chitra_line", result.source)
        self.assertTrue(result.syntax_valid)
        self.assertTrue(result.compiled)

    def test_rupantar_renames_reserved_keyword_identifiers_in_block_scope(self):
        engine = VakyaRupantar()
        result = engine.transform_source(
            textwrap.dedent(
                """
                कर्म नमूना():
                    चर डेटा = []
                    डेटा.जोड़ो(१)
                    प्रत्यागच्छ {"डेटा": डेटा}
                """
            )
        )
        self.assertIn("चर डेटा_मान = []", result.source)
        self.assertIn("डेटा_मान.जोड़ो(१)", result.source)
        self.assertIn('प्रत्यागच्छ {"डेटा": डेटा_मान}', result.source)
        self.assertTrue(result.syntax_valid)
        self.assertTrue(result.compiled)

    def test_rupantar_corrects_module_name_against_live_stdlib(self):
        engine = VakyaRupantar()
        result = engine.transform_source(
            textwrap.dedent(
                """
                आयात promiss
                मुद्रय १
                """
            )
        )
        self.assertIn("आयात promise", result.source)
        self.assertTrue(result.compiled)

    def test_rupantar_corrects_imported_name_against_module_exports(self):
        engine = VakyaRupantar()
        with tempfile.TemporaryDirectory() as tempdir:
            temp_root = Path(tempdir)
            module_path = temp_root / "demo.vak"
            main_path = temp_root / "main.vak"
            module_path.write_text(
                textwrap.dedent(
                    """
                    कर्म प्रतिज्ञा():
                        प्रत्यागच्छ ७
                    """
                ),
                encoding="utf-8",
            )
            source = 'आयात प्रतिग्ञा से demo\nमुद्रय प्रतिग्ञा()\n'
            result = engine.transform_source(source, source_path=str(main_path))
            self.assertIn("आयात प्रतिज्ञा से demo", result.source)
            self.assertIn("मुद्रय प्रतिज्ञा()", result.source)

            interpreter = VakInterpreter()
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                interpreter.run(result.source, filename=str(main_path))
            self.assertIn("7", buffer.getvalue())

    def test_rupantar_corrects_module_member_against_module_exports(self):
        engine = VakyaRupantar()
        with tempfile.TemporaryDirectory() as tempdir:
            temp_root = Path(tempdir)
            module_path = temp_root / "demo.vak"
            main_path = temp_root / "main.vak"
            module_path.write_text(
                textwrap.dedent(
                    """
                    कर्म प्रतिज्ञा():
                        प्रत्यागच्छ ९
                    """
                ),
                encoding="utf-8",
            )
            source = 'आयात demo\nमुद्रय demo.प्रतिग्ञा()\n'
            result = engine.transform_source(source, source_path=str(main_path))
            self.assertIn("मुद्रय demo.प्रतिज्ञा()", result.source)

            interpreter = VakInterpreter()
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                interpreter.run(result.source, filename=str(main_path))
            self.assertIn("9", buffer.getvalue())

    def test_rupantar_ast_normalizes_typed_member_typos_in_mainline(self):
        engine = VakyaRupantar()
        result = engine.transform_source(
            textwrap.dedent(
                """
                चर सूची = []
                सूची.apend(१)
                """
            )
        )
        self.assertIn("सूची.जोड़ो(१)", result.source)
        self.assertTrue(result.compiled)
        self.assertTrue(any(event.stage == "ast-normalization:typed-members" for event in result.validation_events))

    def test_rupantar_is_branch_aware_for_chitrakala_aliases(self):
        engine = VakyaRupantar()
        result = engine.transform_source(
            textwrap.dedent(
                """
                चर क = चित्रकला.कैनवास_निर्माण(१०, १०)
                चित्रकला.रेखा(क, ०, ०, ९, ९)
                """
            )
        )
        self.assertIn("_chitra_canvas", result.source)
        self.assertIn("_chitra_line", result.source)
        self.assertIn("chitrakala", result.active_branches)

    def test_rupantar_feeds_english_like_source_into_existing_translator(self):
        engine = VakyaRupantar()
        result = engine.transform_source(
            textwrap.dedent(
                """
                while True:
                    break
                """
            )
        )
        self.assertTrue(result.translation_used)
        self.assertIn("यावत् सत्य:", result.source)
        self.assertIn("विराम", result.source)
        self.assertTrue(result.compiled)

    def test_adaptive_rupantar_branch_fuzzy_repairs_builtin_and_member_typos(self):
        engine = VakyaRupantar(active_branches=["adaptive_rupantar"])
        result = engine.transform_source(
            textwrap.dedent(
                """
                चर सूची = []
                सूची.apend(१)
                मुद्रर सूची
                """
            )
        )
        self.assertIn("सूची.जोड़ो(१)", result.source)
        self.assertIn("मुद्रय सूची", result.source)
        self.assertIn("adaptive_rupantar", result.active_branches)
        self.assertTrue(result.syntax_valid)
        self.assertTrue(result.compiled)

    def test_adaptive_rupantar_promotes_null_guarded_param_to_real_default(self):
        engine = VakyaRupantar(active_branches=["adaptive_rupantar"])
        result = engine.transform_source(
            textwrap.dedent(
                """
                कर्म रंग_पट्टी_दिखाओ(रंग_सूची, ब्लॉक_आकार):
                    यदि ब्लॉक_आकार == शून्य:
                        ब्लॉक_आकार = ४
                    मुद्रय ब्लॉक_आकार

                रंग_पट्टी_दिखाओ([])
                """
            )
        )
        self.assertIn("कर्म रंग_पट्टी_दिखाओ(रंग_सूची, ब्लॉक_आकार = शून्य):", result.source)
        self.assertTrue(result.syntax_valid)
        self.assertTrue(result.compiled)

    def test_adaptive_rupantar_infers_missing_null_guarded_optional_param(self):
        engine = VakyaRupantar(active_branches=["adaptive_rupantar"])
        result = engine.transform_source(
            textwrap.dedent(
                """
                कर्म svg_आयत(निर्माता, x, y, चौड़ाई, ऊंचाई, भरण, सीमा):
                    यदि सीमा == शून्य:
                        सीमा = "none"
                    यदि सीमा_चौड़ाई == शून्य:
                        सीमा_चौड़ाई = ०
                    प्रत्यागच्छ पाठ_कर(सीमा_चौड़ाई)
                """
            )
        )
        self.assertIn("कर्म svg_आयत(निर्माता, x, y, चौड़ाई, ऊंचाई, भरण, सीमा = शून्य, सीमा_चौड़ाई = शून्य):", result.source)
        self.assertNotIn("अपरिभाषित नाम 'सीमा_चौड़ाई'", "\n".join(result.warnings))
        self.assertTrue(result.syntax_valid)
        self.assertTrue(result.compiled)

    def test_adaptive_rupantar_repairs_common_cross_script_identifier_drift(self):
        engine = VakyaRupantar(active_branches=["adaptive_rupantar"])
        result = engine.transform_source(
            textwrap.dedent(
                """
                कर्म rgb_मान():
                    चर r = १२
                    चर g = ३४
                    प्रत्यागच्छ {"र": र, "ह": ग}
                """
            )
        )
        self.assertIn('प्रत्यागच्छ {"र": r, "ह": g}', result.source)
        self.assertTrue(result.syntax_valid)
        self.assertTrue(result.compiled)

    def test_adaptive_rupantar_uses_compile_validated_candidate_search(self):
        engine = VakyaRupantar(active_branches=["adaptive_rupantar"])
        result = engine.transform_source(
            textwrap.dedent(
                """
                कर्म चित्र(क):
                    प्रत्यागच्छ क

                कर्म चित्रा(क, ख):
                    प्रत्यागच्छ क + ख

                मुद्रय चितर(१)
                """
            )
        )
        self.assertIn("मुद्रय चित्र(१)", result.source)
        self.assertNotIn("मुद्रय चित्रा(१)", result.source)
        self.assertTrue(result.compiled)

    def test_rupantar_error_driven_repair_uses_compile_failure_line(self):
        engine = VakyaRupantar()
        result = engine.transform_source(
            textwrap.dedent(
                """
                कर्म चित्र(रंग, सीमा):
                    यदि सीमा == शून्य:
                        सीमा = "none"
                    प्रत्यागच्छ सीमा

                मुद्रय चित्र("नील")
                """
            )
        )
        self.assertIn("कर्म चित्र(रंग, सीमा = शून्य):", result.source)
        self.assertTrue(result.compiled)
        payload = result.report_payload()
        stages = [item["stage"] for item in payload["validation_events"]]
        self.assertIn("initial", stages)
        self.assertTrue(any(stage.startswith("error-driven:") for stage in stages))
        self.assertIn("सत्यापन चरण:", result.report_text())

    def test_rupantar_error_driven_repair_fixes_unknown_keyword_argument(self):
        engine = VakyaRupantar()
        result = engine.transform_source(
            textwrap.dedent(
                """
                कर्म चित्र(रंग, सीमा_चौड़ाई = शून्य):
                    प्रत्यागच्छ सीमा_चौड़ाई

                मुद्रय चित्र("नील", सीमा_चोडाई = २)
                """
            )
        )
        self.assertIn('मुद्रय चित्र("नील", सीमा_चौड़ाई = २)', result.source)
        self.assertTrue(result.compiled)
        self.assertTrue(any(event.stage.startswith("error-driven:") for event in result.validation_events))

    def test_rupantar_reports_structured_signature_suggestions(self):
        engine = VakyaRupantar()
        result = engine.transform_source("खोलो()\n")
        self.assertTrue(result.syntax_valid)
        self.assertTrue(result.compiled)
        self.assertTrue(any(item.confidence == "suggest_only" for item in result.suggestions))
        self.assertTrue(any("खोलो" in item.message for item in result.suggestions))
        payload = result.report_payload()
        self.assertIn("suggestions", payload)

    def test_rupantar_error_driven_repair_fixes_unambiguous_unresolved_name(self):
        engine = VakyaRupantar()
        result = engine.transform_source("मुद्रर १\n")
        self.assertIn("मुद्रय १", result.source)
        self.assertTrue(result.compiled)

    def test_rupantar_report_tracks_rejected_fixes(self):
        engine = VakyaRupantar()
        result = engine.transform_source(
            textwrap.dedent(
                """
                चर सूची = []
                सूची.appendd(१)
                """
            )
        )
        payload = result.report_payload()
        self.assertIn("rejected_fixes", payload)

    def test_rupantar_report_exposes_original_source_and_diff(self):
        engine = VakyaRupantar()
        source = "चर सूची = []\nसूची.apend(१)\n"
        result = engine.transform_source(source)
        payload = result.report_payload()
        self.assertEqual(payload["original_source"], source)
        self.assertTrue(payload["diff"])
        self.assertIn("सूची.apend(१)", "\n".join(payload["diff"]))
        self.assertIn("सूची.जोड़ो(१)", "\n".join(payload["diff"]))
        self.assertIn("अंतर:", result.report_text())

    def test_rupantar_marks_blocked_translation_as_do_not_touch(self):
        engine = VakyaRupantar()
        result = engine.transform_source(
            textwrap.dedent(
                """
                async def broken(first, second):
                    async with first, second:
                        print(item)
                """
            )
        )
        self.assertFalse(result.translation_used)
        self.assertTrue(any(item.confidence == "do_not_touch" for item in result.suggestions))
        self.assertTrue(any("वाक्य-अनुवाद असंभव" in item.message for item in result.suggestions))

    def test_cli_rupantar_accepts_branch_selection(self):
        with tempfile.TemporaryDirectory() as tempdir:
            input_path = Path(tempdir) / "adaptive.vak"
            output_path = Path(tempdir) / "adaptive_fixed.vak"
            input_path.write_text(
                textwrap.dedent(
                    """
                    चर सूची = []
                    सूची.apend(१)
                    मुद्रर सूची
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
                    "--branch",
                    "adaptive_rupantar",
                    "--रूपान्तर",
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
            rewritten = output_path.read_text(encoding="utf-8")
            self.assertIn("सूची.जोड़ो(१)", rewritten)
            self.assertIn("मुद्रय सूची", rewritten)

    def test_vak_builtin_rupantar_is_callable_from_source(self):
        interpreter = VakInterpreter()
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            interpreter.run('मुद्रय रूपान्तर("यदि रंग के प्रकार == dict:")')
        self.assertIn('यदि प्रकार(रंग) == "शब्दकोश":', buffer.getvalue())

    def test_cli_rupantar_writes_output_and_report(self):
        with tempfile.TemporaryDirectory() as tempdir:
            input_path = Path(tempdir) / "legacy.vak"
            output_path = Path(tempdir) / "legacy_fixed.vak"
            input_path.write_text(
                textwrap.dedent(
                    """
                    जबतक सत्य:
                        विराम
                    """
                ),
                encoding="utf-8",
            )
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "utf-8"
            result = subprocess.run(
                [sys.executable, "vak.py", "--रूपान्तर", str(input_path), str(output_path)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
                timeout=60,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(output_path.exists())
            self.assertIn("यावत् सत्य:", output_path.read_text(encoding="utf-8"))
            self.assertIn("वाक्य-रूपान्तर रिपोर्ट", result.stdout)


if __name__ == "__main__":
    unittest.main()
