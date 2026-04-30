import os
import subprocess
import sys
import tempfile
import unittest
import hashlib
from pathlib import Path


class BootstrapCompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project_root = Path(__file__).resolve().parents[1]
        cls.python = sys.executable
        cls.env = os.environ.copy()
        cls.env.setdefault("PYTHONIOENCODING", "utf-8")

    def run_command(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self.python, *args],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=self.env,
        )

    def run_bootstrap_driver(
        self,
        driver_path: str,
        *,
        input_path: str,
        output_path: str,
        mode: str = "compile",
        second_output_path: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = self.env.copy()
        env["VAK_BOOTSTRAP_MODE"] = mode
        env["VAK_BOOTSTRAP_INPUT"] = input_path
        env["VAK_BOOTSTRAP_OUTPUT"] = output_path
        if second_output_path is not None:
            env["VAK_BOOTSTRAP_OUTPUT_SECOND"] = second_output_path
        return subprocess.run(
            [self.python, "vak.py", driver_path],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )

    def test_compiler_vak_lexer_demo_runs(self):
        result = self.run_command("vak.py", "compiler/compiler.vak")
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("लेक्सिकल विश्लेषण सफल", result.stdout)
        self.assertIn("<टोकन:", result.stdout)
        self.assertIn("Bootstrap compiler driver", result.stdout)

    def test_bootstrap_compiler_script_runs_without_console_encoding_failure(self):
        result = self.run_command("compiler/bootstrap_compiler.py")
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("Bootstrap Summary", result.stdout)
        self.assertIn("Bootstrap complete", result.stdout)
        self.assertIn("Reproducibility check passed", result.stdout)
        self.assertIn("bootstrap drivers matched Python compiler output", result.stdout)

    def test_source_bootstrap_driver_compiles_fixture_and_matches_python(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "fixture.vak"
            source_path.write_text(
                "\n".join(
                    [
                        "कर्म जोड़ो(अ, ब=३):",
                        "    प्रत्यागच्छ अ + ब",
                        "मुद्रय जोड़ो(७)",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            direct_result = self.run_command("vak.py", "--compile", str(source_path))
            self.assertEqual(direct_result.returncode, 0, msg=direct_result.stderr or direct_result.stdout)
            expected_vakc = source_path.with_suffix(".vakc")
            expected_meta = expected_vakc.with_suffix(expected_vakc.suffix + ".meta.json")

            output_vakc = Path(tmp) / "from_source_driver.vakc"
            result = self.run_bootstrap_driver(
                "compiler/compiler.vak",
                input_path=str(source_path),
                output_path=str(output_vakc),
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("BOOTSTRAP_COMPILE_OK", result.stdout)

            output_meta = output_vakc.with_suffix(output_vakc.suffix + ".meta.json")
            self.assertTrue(output_vakc.exists())
            self.assertTrue(output_meta.exists())
            self.assertEqual(hashlib.sha256(expected_vakc.read_bytes()).hexdigest(), hashlib.sha256(output_vakc.read_bytes()).hexdigest())
            self.assertEqual(hashlib.sha256(expected_meta.read_bytes()).hexdigest(), hashlib.sha256(output_meta.read_bytes()).hexdigest())

            run_result = self.run_command("vak.py", str(output_vakc))
            self.assertEqual(run_result.returncode, 0, msg=run_result.stderr or run_result.stdout)
            self.assertIn("10", run_result.stdout)

    def test_compiled_bootstrap_driver_can_self_compile_and_reproduce(self):
        compiler_source = self.project_root / "compiler" / "compiler.vak"
        direct_result = self.run_command("vak.py", "--compile", str(compiler_source))
        self.assertEqual(direct_result.returncode, 0, msg=direct_result.stderr or direct_result.stdout)
        canonical_vakc = compiler_source.with_suffix(".vakc")
        canonical_meta = canonical_vakc.with_suffix(canonical_vakc.suffix + ".meta.json")

        with tempfile.TemporaryDirectory() as tmp:
            output_vakc = Path(tmp) / "self_from_compiled_driver.vakc"
            result = self.run_bootstrap_driver(
                str(canonical_vakc),
                input_path=str(compiler_source),
                output_path=str(output_vakc),
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("BOOTSTRAP_COMPILE_OK", result.stdout)

            output_meta = output_vakc.with_suffix(output_vakc.suffix + ".meta.json")
            self.assertTrue(output_vakc.exists())
            self.assertTrue(output_meta.exists())
            self.assertEqual(hashlib.sha256(canonical_vakc.read_bytes()).hexdigest(), hashlib.sha256(output_vakc.read_bytes()).hexdigest())
            self.assertEqual(hashlib.sha256(canonical_meta.read_bytes()).hexdigest(), hashlib.sha256(output_meta.read_bytes()).hexdigest())

            repro_a = Path(tmp) / "repro_a.vakc"
            repro_b = Path(tmp) / "repro_b.vakc"
            repro_result = self.run_bootstrap_driver(
                str(canonical_vakc),
                input_path=str(compiler_source),
                output_path=str(repro_a),
                mode="repro",
                second_output_path=str(repro_b),
            )
            self.assertEqual(repro_result.returncode, 0, msg=repro_result.stderr or repro_result.stdout)
            self.assertIn("BOOTSTRAP_REPRO_OK", repro_result.stdout)
            self.assertEqual(hashlib.sha256(repro_a.read_bytes()).hexdigest(), hashlib.sha256(repro_b.read_bytes()).hexdigest())

    def test_vak_bootstrap_driver_assemble_mode_emits_runnable_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec_path = Path(tmp) / "assembly_spec.json"
            spec_path.write_text(
                """
{
  "name": "<module>",
  "constants": ["asm-ok"],
  "instructions": [
    {"op": "LOAD_CONST", "operand": 0, "width": 16},
    {"op": "PRINT"},
    {"op": "HALT"}
  ]
}
""".strip(),
                encoding="utf-8",
            )

            output_vakc = Path(tmp) / "assembled.vakc"
            env = self.env.copy()
            env["VAK_BOOTSTRAP_MODE"] = "assemble"
            env["VAK_BOOTSTRAP_SPEC"] = str(spec_path)
            env["VAK_BOOTSTRAP_OUTPUT"] = str(output_vakc)
            result = subprocess.run(
                [self.python, "vak.py", "compiler/compiler.vak"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("BOOTSTRAP_ASSEMBLE_OK", result.stdout)
            self.assertTrue(output_vakc.exists())
            self.assertTrue(output_vakc.with_suffix(output_vakc.suffix + ".meta.json").exists())

            run_result = self.run_command("vak.py", str(output_vakc))
            self.assertEqual(run_result.returncode, 0, msg=run_result.stderr or run_result.stdout)
            self.assertIn("asm-ok", run_result.stdout)

    def test_native_subset_source_driver_matches_python_for_supported_program(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "native_subset.vak"
            source_path.write_text(
                "\n".join(
                    [
                        "चर अ = २",
                        "चर ब = ३",
                        "चर योग = अ + ब",
                        'मुद्रय "native-subset"',
                        "मुद्रय योग",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            direct_result = self.run_command("vak.py", "--compile", str(source_path))
            self.assertEqual(direct_result.returncode, 0, msg=direct_result.stderr or direct_result.stdout)
            expected_vakc = source_path.with_suffix(".vakc")
            expected_meta = expected_vakc.with_suffix(expected_vakc.suffix + ".meta.json")

            output_vakc = Path(tmp) / "native_from_source.vakc"
            result = self.run_bootstrap_driver(
                "compiler/compiler.vak",
                input_path=str(source_path),
                output_path=str(output_vakc),
                mode="native_compile",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("BOOTSTRAP_NATIVE_COMPILE_OK", result.stdout)

            output_meta = output_vakc.with_suffix(output_vakc.suffix + ".meta.json")
            self.assertEqual(hashlib.sha256(expected_vakc.read_bytes()).hexdigest(), hashlib.sha256(output_vakc.read_bytes()).hexdigest())
            self.assertEqual(hashlib.sha256(expected_meta.read_bytes()).hexdigest(), hashlib.sha256(output_meta.read_bytes()).hexdigest())

            run_result = self.run_command("vak.py", str(output_vakc))
            self.assertEqual(run_result.returncode, 0, msg=run_result.stderr or run_result.stdout)
            self.assertIn("native-subset", run_result.stdout)
            self.assertIn("5", run_result.stdout)

    def test_native_subset_compiled_driver_and_repro_work(self):
        compiler_source = self.project_root / "compiler" / "compiler.vak"
        compile_result = self.run_command("vak.py", "--compile", str(compiler_source))
        self.assertEqual(compile_result.returncode, 0, msg=compile_result.stderr or compile_result.stdout)
        canonical_vakc = compiler_source.with_suffix(".vakc")

        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "native_subset_compiled.vak"
            source_path.write_text(
                "\n".join(
                    [
                        "चर क = ४",
                        "चर ख = ६",
                        "मुद्रय क + ख",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            output_vakc = Path(tmp) / "native_from_compiled_driver.vakc"
            result = self.run_bootstrap_driver(
                str(canonical_vakc),
                input_path=str(source_path),
                output_path=str(output_vakc),
                mode="native_compile",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("BOOTSTRAP_NATIVE_COMPILE_OK", result.stdout)

            run_result = self.run_command("vak.py", str(output_vakc))
            self.assertEqual(run_result.returncode, 0, msg=run_result.stderr or run_result.stdout)
            self.assertIn("10", run_result.stdout)

            repro_a = Path(tmp) / "native_repro_a.vakc"
            repro_b = Path(tmp) / "native_repro_b.vakc"
            repro_result = self.run_bootstrap_driver(
                str(canonical_vakc),
                input_path=str(source_path),
                output_path=str(repro_a),
                mode="native_repro",
                second_output_path=str(repro_b),
            )
            self.assertEqual(repro_result.returncode, 0, msg=repro_result.stderr or repro_result.stdout)
            self.assertIn("BOOTSTRAP_NATIVE_REPRO_OK", repro_result.stdout)
            self.assertEqual(hashlib.sha256(repro_a.read_bytes()).hexdigest(), hashlib.sha256(repro_b.read_bytes()).hexdigest())

    def test_native_subset_function_calls_match_python(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "native_function_subset.vak"
            source_path.write_text(
                "\n".join(
                    [
                        "कर्म जोड़ो(अ, ब):",
                        "    प्रत्यागच्छ अ + ब",
                        "मुद्रय जोड़ो(२, ३)",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            direct_result = self.run_command("vak.py", "--compile", str(source_path))
            self.assertEqual(direct_result.returncode, 0, msg=direct_result.stderr or direct_result.stdout)
            expected_vakc = source_path.with_suffix(".vakc")
            expected_meta = expected_vakc.with_suffix(expected_vakc.suffix + ".meta.json")

            output_vakc = Path(tmp) / "native_function_from_source.vakc"
            result = self.run_bootstrap_driver(
                "compiler/compiler.vak",
                input_path=str(source_path),
                output_path=str(output_vakc),
                mode="native_compile",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("BOOTSTRAP_NATIVE_COMPILE_OK", result.stdout)

            output_meta = output_vakc.with_suffix(output_vakc.suffix + ".meta.json")
            self.assertEqual(hashlib.sha256(expected_vakc.read_bytes()).hexdigest(), hashlib.sha256(output_vakc.read_bytes()).hexdigest())
            self.assertEqual(hashlib.sha256(expected_meta.read_bytes()).hexdigest(), hashlib.sha256(output_meta.read_bytes()).hexdigest())

            run_result = self.run_command("vak.py", str(output_vakc))
            self.assertEqual(run_result.returncode, 0, msg=run_result.stderr or run_result.stdout)
            self.assertIn("5", run_result.stdout)

    def test_native_subset_control_flow_matches_python(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "native_control_flow.vak"
            source_path.write_text(
                "\n".join(
                    [
                        "चर कुल = ०",
                        "चर i = ०",
                        "यावत् i < ४:",
                        "    यदि i == २:",
                        "        कुल = कुल + १०",
                        "    अन्यथा:",
                        "        कुल = कुल + i",
                        "    i = i + १",
                        "मुद्रय कुल",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            direct_result = self.run_command("vak.py", "--compile", str(source_path))
            self.assertEqual(direct_result.returncode, 0, msg=direct_result.stderr or direct_result.stdout)
            expected_vakc = source_path.with_suffix(".vakc")
            expected_meta = expected_vakc.with_suffix(expected_vakc.suffix + ".meta.json")

            output_vakc = Path(tmp) / "native_control_flow_from_source.vakc"
            result = self.run_bootstrap_driver(
                "compiler/compiler.vak",
                input_path=str(source_path),
                output_path=str(output_vakc),
                mode="native_compile",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("BOOTSTRAP_NATIVE_COMPILE_OK", result.stdout)

            output_meta = output_vakc.with_suffix(output_vakc.suffix + ".meta.json")
            self.assertEqual(hashlib.sha256(expected_vakc.read_bytes()).hexdigest(), hashlib.sha256(output_vakc.read_bytes()).hexdigest())
            self.assertEqual(hashlib.sha256(expected_meta.read_bytes()).hexdigest(), hashlib.sha256(output_meta.read_bytes()).hexdigest())

            run_result = self.run_command("vak.py", str(output_vakc))
            self.assertEqual(run_result.returncode, 0, msg=run_result.stderr or run_result.stdout)
            self.assertIn("14", run_result.stdout)

    def test_native_subset_recursive_function_matches_python(self):
        compiler_source = self.project_root / "compiler" / "compiler.vak"
        compile_result = self.run_command("vak.py", "--compile", str(compiler_source))
        self.assertEqual(compile_result.returncode, 0, msg=compile_result.stderr or compile_result.stdout)
        canonical_vakc = compiler_source.with_suffix(".vakc")

        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "native_recursive_subset.vak"
            source_path.write_text(
                "\n".join(
                    [
                        "कर्म फल(n):",
                        "    यदि n <= १:",
                        "        प्रत्यागच्छ १",
                        "    अन्यथा:",
                        "        प्रत्यागच्छ n * फल(n - १)",
                        "मुद्रय फल(५)",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            direct_result = self.run_command("vak.py", "--compile", str(source_path))
            self.assertEqual(direct_result.returncode, 0, msg=direct_result.stderr or direct_result.stdout)
            expected_vakc = source_path.with_suffix(".vakc")
            expected_meta = expected_vakc.with_suffix(expected_vakc.suffix + ".meta.json")

            output_vakc = Path(tmp) / "native_recursive_from_compiled_driver.vakc"
            result = self.run_bootstrap_driver(
                str(canonical_vakc),
                input_path=str(source_path),
                output_path=str(output_vakc),
                mode="native_compile",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("BOOTSTRAP_NATIVE_COMPILE_OK", result.stdout)

            output_meta = output_vakc.with_suffix(output_vakc.suffix + ".meta.json")
            self.assertEqual(hashlib.sha256(expected_vakc.read_bytes()).hexdigest(), hashlib.sha256(output_vakc.read_bytes()).hexdigest())
            self.assertEqual(hashlib.sha256(expected_meta.read_bytes()).hexdigest(), hashlib.sha256(output_meta.read_bytes()).hexdigest())

            repro_a = Path(tmp) / "native_recursive_repro_a.vakc"
            repro_b = Path(tmp) / "native_recursive_repro_b.vakc"
            repro_result = self.run_bootstrap_driver(
                str(canonical_vakc),
                input_path=str(source_path),
                output_path=str(repro_a),
                mode="native_repro",
                second_output_path=str(repro_b),
            )
            self.assertEqual(repro_result.returncode, 0, msg=repro_result.stderr or repro_result.stdout)
            self.assertIn("BOOTSTRAP_NATIVE_REPRO_OK", repro_result.stdout)
            self.assertEqual(hashlib.sha256(repro_a.read_bytes()).hexdigest(), hashlib.sha256(repro_b.read_bytes()).hexdigest())

            run_result = self.run_command("vak.py", str(output_vakc))
            self.assertEqual(run_result.returncode, 0, msg=run_result.stderr or run_result.stdout)
            self.assertIn("120", run_result.stdout)

    def test_native_subset_collection_iteration_and_indexing_match_python(self):
        compiler_source = self.project_root / "compiler" / "compiler.vak"
        compile_result = self.run_command("vak.py", "--compile", str(compiler_source))
        self.assertEqual(compile_result.returncode, 0, msg=compile_result.stderr or compile_result.stdout)
        canonical_vakc = compiler_source.with_suffix(".vakc")

        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "native_collection_subset.vak"
            source_path.write_text(
                "\n".join(
                    [
                        "चर items = [१, २, ३]",
                        "चर कुल = ०",
                        "प्रत्येक चर item अन्तर्गत items:",
                        "    कुल = कुल + item",
                        'चर mapping = {"योग": कुल, "स्थिर": ७}',
                        "चर tags = {१, २, ३}",
                        "चर tag_count = ०",
                        "प्रत्येक चर tag अन्तर्गत tags:",
                        "    tag_count = tag_count + १",
                        'मुद्रय mapping["योग"]',
                        "मुद्रय tag_count",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            direct_result = self.run_command("vak.py", "--compile", str(source_path))
            self.assertEqual(direct_result.returncode, 0, msg=direct_result.stderr or direct_result.stdout)
            expected_vakc = source_path.with_suffix(".vakc")
            expected_meta = expected_vakc.with_suffix(expected_vakc.suffix + ".meta.json")

            output_vakc = Path(tmp) / "native_collection_from_compiled_driver.vakc"
            result = self.run_bootstrap_driver(
                str(canonical_vakc),
                input_path=str(source_path),
                output_path=str(output_vakc),
                mode="native_compile",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("BOOTSTRAP_NATIVE_COMPILE_OK", result.stdout)

            output_meta = output_vakc.with_suffix(output_vakc.suffix + ".meta.json")
            self.assertEqual(hashlib.sha256(expected_vakc.read_bytes()).hexdigest(), hashlib.sha256(output_vakc.read_bytes()).hexdigest())
            self.assertEqual(hashlib.sha256(expected_meta.read_bytes()).hexdigest(), hashlib.sha256(output_meta.read_bytes()).hexdigest())

            repro_a = Path(tmp) / "native_collection_repro_a.vakc"
            repro_b = Path(tmp) / "native_collection_repro_b.vakc"
            repro_result = self.run_bootstrap_driver(
                str(canonical_vakc),
                input_path=str(source_path),
                output_path=str(repro_a),
                mode="native_repro",
                second_output_path=str(repro_b),
            )
            self.assertEqual(repro_result.returncode, 0, msg=repro_result.stderr or repro_result.stdout)
            self.assertIn("BOOTSTRAP_NATIVE_REPRO_OK", repro_result.stdout)
            self.assertEqual(hashlib.sha256(repro_a.read_bytes()).hexdigest(), hashlib.sha256(repro_b.read_bytes()).hexdigest())

            run_result = self.run_command("vak.py", str(output_vakc))
            self.assertEqual(run_result.returncode, 0, msg=run_result.stderr or run_result.stdout)
            self.assertIn("6", run_result.stdout)
            self.assertIn("3", run_result.stdout)

    def test_native_subset_collection_defaults_match_python(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "native_default_subset.vak"
            source_path.write_text(
                "\n".join(
                    [
                        "कर्म पढ़ो(ready=सत्य, missing=शून्य):",
                        "    यदि ready == सत्य:",
                        '        मुद्रय "ready"',
                        "    यदि missing == शून्य:",
                        '        मुद्रय "none"',
                        "पढ़ो()",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            direct_result = self.run_command("vak.py", "--compile", str(source_path))
            self.assertEqual(direct_result.returncode, 0, msg=direct_result.stderr or direct_result.stdout)
            expected_vakc = source_path.with_suffix(".vakc")
            expected_meta = expected_vakc.with_suffix(expected_vakc.suffix + ".meta.json")

            output_vakc = Path(tmp) / "native_default_from_source.vakc"
            result = self.run_bootstrap_driver(
                "compiler/compiler.vak",
                input_path=str(source_path),
                output_path=str(output_vakc),
                mode="native_compile",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("BOOTSTRAP_NATIVE_COMPILE_OK", result.stdout)

            output_meta = output_vakc.with_suffix(output_vakc.suffix + ".meta.json")
            self.assertEqual(hashlib.sha256(expected_vakc.read_bytes()).hexdigest(), hashlib.sha256(output_vakc.read_bytes()).hexdigest())
            self.assertEqual(hashlib.sha256(expected_meta.read_bytes()).hexdigest(), hashlib.sha256(output_meta.read_bytes()).hexdigest())

            run_result = self.run_command("vak.py", str(output_vakc))
            self.assertEqual(run_result.returncode, 0, msg=run_result.stderr or run_result.stdout)
            self.assertIn("ready", run_result.stdout)
            self.assertIn("none", run_result.stdout)

    def test_native_subset_import_and_member_access_match_python(self):
        compiler_source = self.project_root / "compiler" / "compiler.vak"
        compile_result = self.run_command("vak.py", "--compile", str(compiler_source))
        self.assertEqual(compile_result.returncode, 0, msg=compile_result.stderr or compile_result.stdout)
        canonical_vakc = compiler_source.with_suffix(".vakc")

        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "native_import_subset.vak"
            source_path.write_text(
                "\n".join(
                    [
                        "आयात रंग_पुस्तकालय",
                        "आयात css_रंग से रंग_पुस्तकालय",
                        'मुद्रय रंग_पुस्तकालय.संस्कृत_रंग["नील"]',
                        'मुद्रय css_रंग["red"]',
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            direct_result = self.run_command("vak.py", "--compile", str(source_path))
            self.assertEqual(direct_result.returncode, 0, msg=direct_result.stderr or direct_result.stdout)
            expected_vakc = source_path.with_suffix(".vakc")
            expected_meta = expected_vakc.with_suffix(expected_vakc.suffix + ".meta.json")

            output_vakc = Path(tmp) / "native_import_from_compiled_driver.vakc"
            result = self.run_bootstrap_driver(
                str(canonical_vakc),
                input_path=str(source_path),
                output_path=str(output_vakc),
                mode="native_compile",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("BOOTSTRAP_NATIVE_COMPILE_OK", result.stdout)

            output_meta = output_vakc.with_suffix(output_vakc.suffix + ".meta.json")
            self.assertEqual(hashlib.sha256(expected_vakc.read_bytes()).hexdigest(), hashlib.sha256(output_vakc.read_bytes()).hexdigest())
            self.assertEqual(hashlib.sha256(expected_meta.read_bytes()).hexdigest(), hashlib.sha256(output_meta.read_bytes()).hexdigest())

            run_result = self.run_command("vak.py", str(output_vakc))
            self.assertEqual(run_result.returncode, 0, msg=run_result.stderr or run_result.stdout)
            self.assertIn("#0000CD", run_result.stdout)
            self.assertIn("#FF0000", run_result.stdout)

    def test_native_subset_tuple_and_unpack_match_python(self):
        compiler_source = self.project_root / "compiler" / "compiler.vak"
        compile_result = self.run_command("vak.py", "--compile", str(compiler_source))
        self.assertEqual(compile_result.returncode, 0, msg=compile_result.stderr or compile_result.stdout)
        canonical_vakc = compiler_source.with_suffix(".vakc")

        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "native_tuple_unpack_subset.vak"
            source_path.write_text(
                "\n".join(
                    [
                        "चर युग्म = (७, ८)",
                        "मुद्रय युग्म[०]",
                        "मुद्रय युग्म[१]",
                        "चर पहला, दूसरा = युग्म",
                        "चर कुल = ०",
                        "चर जोड़े = [(१, १०), (२, २०)]",
                        "प्रत्येक चर क्रम, मूल्य अन्तर्गत जोड़े:",
                        "    कुल = कुल + क्रम + मूल्य",
                        "मुद्रय पहला",
                        "मुद्रय दूसरा",
                        "मुद्रय कुल",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            direct_result = self.run_command("vak.py", "--compile", str(source_path))
            self.assertEqual(direct_result.returncode, 0, msg=direct_result.stderr or direct_result.stdout)
            expected_vakc = source_path.with_suffix(".vakc")
            expected_meta = expected_vakc.with_suffix(expected_vakc.suffix + ".meta.json")

            output_vakc = Path(tmp) / "native_tuple_unpack_from_compiled_driver.vakc"
            result = self.run_bootstrap_driver(
                str(canonical_vakc),
                input_path=str(source_path),
                output_path=str(output_vakc),
                mode="native_compile",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("BOOTSTRAP_NATIVE_COMPILE_OK", result.stdout)

            output_meta = output_vakc.with_suffix(output_vakc.suffix + ".meta.json")
            self.assertEqual(hashlib.sha256(expected_vakc.read_bytes()).hexdigest(), hashlib.sha256(output_vakc.read_bytes()).hexdigest())
            self.assertEqual(hashlib.sha256(expected_meta.read_bytes()).hexdigest(), hashlib.sha256(output_meta.read_bytes()).hexdigest())

            run_result = self.run_command("vak.py", str(output_vakc))
            self.assertEqual(run_result.returncode, 0, msg=run_result.stderr or run_result.stdout)
            self.assertIn("7", run_result.stdout)
            self.assertIn("8", run_result.stdout)
            self.assertIn("33", run_result.stdout)

    def test_native_subset_class_keyword_calls_work_end_to_end(self):
        compiler_source = self.project_root / "compiler" / "compiler.vak"
        compile_result = self.run_command("vak.py", "--compile", str(compiler_source))
        self.assertEqual(compile_result.returncode, 0, msg=compile_result.stderr or compile_result.stdout)
        canonical_vakc = compiler_source.with_suffix(".vakc")

        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "native_class_kwargs.vak"
            source_path.write_text(
                "\n".join(
                    [
                        "वर्ग व्यक्ति:",
                        "    कर्म __init__(स्वयं, नाम, आयु=२५):",
                        "        स्वयं.नाम = नाम",
                        "        स्वयं.आयु = आयु",
                        "",
                        '    कर्म विवरण(स्वयं, उपसर्ग="", विराम="!"):',
                        "        प्रत्यागच्छ उपसर्ग + स्वयं.नाम + \":\" + पाठ_कर(स्वयं.आयु) + विराम",
                        "",
                        'चर प = व्यक्ति(नाम="राज")',
                        'मुद्रय प.विवरण(विराम="?", उपसर्ग=">>")',
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            output_vakc = Path(tmp) / "native_class_kwargs.vakc"
            result = self.run_bootstrap_driver(
                str(canonical_vakc),
                input_path=str(source_path),
                output_path=str(output_vakc),
                mode="native_compile",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("BOOTSTRAP_NATIVE_COMPILE_OK", result.stdout)

            run_result = self.run_command("vak.py", str(output_vakc))
            self.assertEqual(run_result.returncode, 0, msg=run_result.stderr or run_result.stdout)
            self.assertIn(">>राज:25?", run_result.stdout)

    def test_native_subset_closure_nonlocal_global_and_kwargs_capture_work(self):
        compiler_source = self.project_root / "compiler" / "compiler.vak"
        compile_result = self.run_command("vak.py", "--compile", str(compiler_source))
        self.assertEqual(compile_result.returncode, 0, msg=compile_result.stderr or compile_result.stdout)
        canonical_vakc = compiler_source.with_suffix(".vakc")

        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "native_closure_nonlocal.vak"
            source_path.write_text(
                "\n".join(
                    [
                        "चर कुल = १",
                        "कर्म बढ़ाओ_कुल():",
                        "    वैश्विक कुल",
                        "    कुल = कुल + ४",
                        "",
                        "कर्म काउंटर(आरम्भ=०, *बाकी, **विवरण):",
                        "    चर गिनती = आरम्भ",
                        "    कर्म बढ़ाओ(कदम=१):",
                        "        अस्थानिक गिनती",
                        "        गिनती = गिनती + कदम",
                        "        प्रत्यागच्छ गिनती",
                        '    मुद्रय विवरण["नाम"]',
                        "    मुद्रय बाकी[०]",
                        "    प्रत्यागच्छ बढ़ाओ",
                        "",
                        "बढ़ाओ_कुल()",
                        'चर अगला = काउंटर(२, ९, नाम="राज")',
                        "मुद्रय अगला()",
                        "मुद्रय अगला(कदम=३)",
                        "मुद्रय कुल",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            output_vakc = Path(tmp) / "native_closure_nonlocal.vakc"
            result = self.run_bootstrap_driver(
                str(canonical_vakc),
                input_path=str(source_path),
                output_path=str(output_vakc),
                mode="native_compile",
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("BOOTSTRAP_NATIVE_COMPILE_OK", result.stdout)

            repro_a = Path(tmp) / "native_closure_nonlocal_a.vakc"
            repro_b = Path(tmp) / "native_closure_nonlocal_b.vakc"
            repro_result = self.run_bootstrap_driver(
                str(canonical_vakc),
                input_path=str(source_path),
                output_path=str(repro_a),
                mode="native_repro",
                second_output_path=str(repro_b),
            )
            self.assertEqual(repro_result.returncode, 0, msg=repro_result.stderr or repro_result.stdout)
            self.assertIn("BOOTSTRAP_NATIVE_REPRO_OK", repro_result.stdout)
            self.assertEqual(hashlib.sha256(repro_a.read_bytes()).hexdigest(), hashlib.sha256(repro_b.read_bytes()).hexdigest())

            run_result = self.run_command("vak.py", str(output_vakc))
            self.assertEqual(run_result.returncode, 0, msg=run_result.stderr or run_result.stdout)
            self.assertEqual(run_result.stdout.splitlines(), ["राज", "9", "3", "6", "5"])

    def test_vakc_cli_disassembles_and_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "compiled_demo.vak"
            source_path.write_text('मुद्रय "compiled-ok"\n', encoding="utf-8")

            compile_result = self.run_command("vak.py", "--compile", str(source_path))
            self.assertEqual(
                compile_result.returncode,
                0,
                msg=compile_result.stderr or compile_result.stdout,
            )

            bytecode_path = source_path.with_suffix(".vakc")
            companion_path = bytecode_path.with_suffix(bytecode_path.suffix + ".meta.json")
            self.assertTrue(bytecode_path.exists())
            self.assertTrue(companion_path.exists())

            disassemble_result = self.run_command(
                "vak.py",
                str(bytecode_path),
                "--disassemble",
            )
            self.assertEqual(
                disassemble_result.returncode,
                0,
                msg=disassemble_result.stderr or disassemble_result.stdout,
            )
            self.assertIn("=== Bytecode:", disassemble_result.stdout)
            self.assertIn("LOAD_CONST", disassemble_result.stdout)

            run_result = self.run_command("vak.py", str(bytecode_path))
            self.assertEqual(
                run_result.returncode,
                0,
                msg=run_result.stderr or run_result.stdout,
            )
            self.assertIn("compiled-ok", run_result.stdout)

            runtime_run_result = self.run_command("runtime/run.py", str(bytecode_path))
            self.assertEqual(
                runtime_run_result.returncode,
                0,
                msg=runtime_run_result.stderr or runtime_run_result.stdout,
            )
            self.assertIn("compiled-ok", runtime_run_result.stdout)

            runtime_disassemble_result = self.run_command(
                "runtime/run.py",
                str(bytecode_path),
                "--disassemble",
            )
            self.assertEqual(
                runtime_disassemble_result.returncode,
                0,
                msg=runtime_disassemble_result.stderr or runtime_disassemble_result.stdout,
            )
            self.assertIn("=== Bytecode:", runtime_disassemble_result.stdout)

    def test_vakc_cli_hydrates_nested_functions_when_source_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "compiled_with_function.vak"
            source_path.write_text(
                "\n".join(
                    [
                        "कर्म नमस्ते():",
                        '    मुद्रय "nested-ok"',
                        "नमस्ते()",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            compile_result = self.run_command("vak.py", "--compile", str(source_path))
            self.assertEqual(
                compile_result.returncode,
                0,
                msg=compile_result.stderr or compile_result.stdout,
            )

            bytecode_path = source_path.with_suffix(".vakc")

            disassemble_result = self.run_command(
                "vak.py",
                str(bytecode_path),
                "--disassemble",
            )
            self.assertEqual(
                disassemble_result.returncode,
                0,
                msg=disassemble_result.stderr or disassemble_result.stdout,
            )
            self.assertIn("=== Nested Bytecode: नमस्ते ===", disassemble_result.stdout)

            runtime_disassemble_result = self.run_command(
                "runtime/run.py",
                str(bytecode_path),
                "--disassemble",
            )
            self.assertEqual(
                runtime_disassemble_result.returncode,
                0,
                msg=runtime_disassemble_result.stderr or runtime_disassemble_result.stdout,
            )
            self.assertIn("=== Nested Bytecode: नमस्ते ===", runtime_disassemble_result.stdout)

            run_result = self.run_command("vak.py", str(bytecode_path))
            self.assertEqual(
                run_result.returncode,
                0,
                msg=run_result.stderr or run_result.stdout,
            )
            self.assertIn("nested-ok", run_result.stdout)

            runtime_run_result = self.run_command("runtime/run.py", str(bytecode_path))
            self.assertEqual(
                runtime_run_result.returncode,
                0,
                msg=runtime_run_result.stderr or runtime_run_result.stdout,
            )
            self.assertIn("nested-ok", runtime_run_result.stdout)

            source_path.unlink()

            missing_source_run = self.run_command("vak.py", str(bytecode_path))
            self.assertEqual(
                missing_source_run.returncode,
                0,
                msg=missing_source_run.stderr or missing_source_run.stdout,
            )
            self.assertIn("nested-ok", missing_source_run.stdout)

            missing_source_runtime_run = self.run_command("runtime/run.py", str(bytecode_path))
            self.assertEqual(
                missing_source_runtime_run.returncode,
                0,
                msg=missing_source_runtime_run.stderr or missing_source_runtime_run.stdout,
            )
            self.assertIn("nested-ok", missing_source_runtime_run.stdout)

            companion_path = bytecode_path.with_suffix(bytecode_path.suffix + ".meta.json")
            companion_path.unlink()

            missing_source_run = self.run_command("vak.py", str(bytecode_path))
            self.assertNotEqual(missing_source_run.returncode, 0)
            self.assertIn("अंतः-बाइटकोड", missing_source_run.stderr or missing_source_run.stdout)

            missing_source_runtime_run = self.run_command("runtime/run.py", str(bytecode_path))
            self.assertNotEqual(missing_source_runtime_run.returncode, 0)
            self.assertIn(
                "अंतः-बाइटकोड",
                missing_source_runtime_run.stderr or missing_source_runtime_run.stdout,
            )

    def test_compiler_artifact_is_reproducible(self):
        compiler_source = self.project_root / "compiler" / "compiler.vak"
        bytecode_path = compiler_source.with_suffix(".vakc")
        companion_path = bytecode_path.with_suffix(bytecode_path.suffix + ".meta.json")

        first = self.run_command("vak.py", "--compile", str(compiler_source))
        self.assertEqual(first.returncode, 0, msg=first.stderr or first.stdout)
        self.assertTrue(bytecode_path.exists())
        self.assertTrue(companion_path.exists())
        first_hash = hashlib.sha256(bytecode_path.read_bytes()).hexdigest()
        first_meta_hash = hashlib.sha256(companion_path.read_bytes()).hexdigest()

        second = self.run_command("vak.py", "--compile", str(compiler_source))
        self.assertEqual(second.returncode, 0, msg=second.stderr or second.stdout)
        second_hash = hashlib.sha256(bytecode_path.read_bytes()).hexdigest()
        second_meta_hash = hashlib.sha256(companion_path.read_bytes()).hexdigest()

        self.assertEqual(first_hash, second_hash)
        self.assertEqual(first_meta_hash, second_meta_hash)
