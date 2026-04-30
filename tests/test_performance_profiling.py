import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from runtime.src.interpreter import VakInterpreter
from runtime.src.vm import VakVM


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PerformanceProfilingTests(unittest.TestCase):
    def test_interpreter_profile_source_collects_pipeline_stages(self):
        profile = VakInterpreter().profile_source(
            "मुद्रय १\n",
            filename="profile_test.vak",
            repeat=2,
            execute=False,
        )

        self.assertEqual(profile.mode, "source")
        self.assertEqual(profile.iterations, 2)
        stage_names = [stage.name for stage in profile.stages]
        self.assertEqual(stage_names[:4], ["prepare", "lex", "parse", "compile"])
        self.assertGreaterEqual(profile.total_ms, 0.0)

    def test_interpreter_profile_import_collects_import_profile(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            module_path = Path(temp_dir) / "गणना.vak"
            module_path.write_text(
                "कर्म उत्तर():\n"
                "    प्रत्यागच्छ ४२\n",
                encoding="utf-8",
            )
            main_path = Path(temp_dir) / "मुख्य.vak"
            profile = VakInterpreter().profile_import(
                "गणना",
                filename=str(main_path),
                repeat=2,
            )

        self.assertEqual(profile.mode, "import")
        stage_names = [stage.name for stage in profile.stages]
        self.assertIn("execute", stage_names)
        self.assertGreaterEqual(profile.total_ms, 0.0)

    def test_vm_profile_builtins_return_payload_and_text(self):
        vm = VakVM()
        payload = vm.builtins["प्रदर्शन_विवरण"](
            "मुद्रय १\n",
            "inline_profile.vak",
            1,
            False,
        )
        text = vm.builtins["प्रदर्शन_पाठ"](
            "मुद्रय १\n",
            "inline_profile.vak",
            1,
            False,
        )

        self.assertEqual(payload["mode"], "source")
        self.assertGreaterEqual(len(payload["stages"]), 4)
        self.assertIn("वाक् प्रदर्शन प्रोफ़ाइल", text)

    def test_vm_import_profile_builtin_uses_filename_context(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            module_path = Path(temp_dir) / "गणना.vak"
            module_path.write_text(
                "कर्म उत्तर():\n"
                "    प्रत्यागच्छ ४२\n",
                encoding="utf-8",
            )
            main_path = Path(temp_dir) / "मुख्य.vak"
            payload = VakVM().builtins["आयात_प्रदर्शन_विवरण"](
                "गणना",
                str(main_path),
                1,
            )

        self.assertEqual(payload["mode"], "import")
        self.assertTrue(any(stage["name"] == "execute" for stage in payload["stages"]))

    def test_profile_runtime_cli_emits_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "profile_cli.vak"
            source_path.write_text("मुद्रय १\n", encoding="utf-8")
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "utf-8"
            result = subprocess.run(
                [
                    sys.executable,
                    "runtime/tooling/profile_runtime.py",
                    str(source_path),
                    "--repeat",
                    "1",
                    "--json",
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
                timeout=120,
            )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["mode"], "source")
        self.assertGreaterEqual(len(payload["stages"]), 4)


if __name__ == "__main__":
    unittest.main()
