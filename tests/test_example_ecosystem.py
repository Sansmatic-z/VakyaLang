import contextlib
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

from runtime.src.interpreter import VakInterpreter
from vpm import VakPackageManager


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ExampleEcosystemTests(unittest.TestCase):
    def _run_example(self, relative_path: str) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(
            [sys.executable, "vak.py", relative_path],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            timeout=120,
        )

    def test_ecosystem_full_stack_example_passes(self):
        result = self._run_example("examples/ecosystem_full_stack.vak")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Vak Full Stack Ecosystem Demo", result.stdout)
        self.assertIn("कोडेक्स पृष्ठ:", result.stdout)
        self.assertIn("रंग compatibility:", result.stdout)
        self.assertIn("प्रदर्शन चरण:", result.stdout)
        self.assertIn("पूर्ण: ecosystem_full_stack", result.stdout)

    def test_tooling_diagnostics_showcase_example_passes(self):
        result = self._run_example("examples/tooling_diagnostics_showcase.vak")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Vak Tooling Diagnostics Showcase", result.stdout)
        self.assertIn("legacy page:", result.stdout)
        self.assertIn("उन्नयन मामले:", result.stdout)
        self.assertIn("वाक् प्रदर्शन प्रोफ़ाइल", result.stdout)
        self.assertIn("पूर्ण: tooling_diagnostics_showcase", result.stdout)

    def test_mission_control_showcase_example_passes(self):
        result = self._run_example("examples/mission_control_showcase.vak")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Vak Mission Control Showcase", result.stdout)
        self.assertIn("सेवा सूची:", result.stdout)
        self.assertIn("कोडेक्स पृष्ठ:", result.stdout)
        self.assertIn("रूपान्तर संकलित:", result.stdout)
        self.assertIn("चित्र सहेजा:", result.stdout)
        self.assertIn("पूर्ण: mission_control_showcase", result.stdout)

    def test_temp_package_flow_works_with_codex_and_rupantar(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = VakPackageManager(cwd=temp_dir)
            self.assertTrue(manager.init())

            pkg_dir = Path(temp_dir) / "pkgbuild" / "demo"
            pkg_dir.mkdir(parents=True, exist_ok=True)
            (pkg_dir / "vakya.json").write_text(
                json.dumps(
                    {
                        "नाम": "demo",
                        "संस्करण": "1.0.0",
                        "विवरण": "demo package",
                        "फाइलें": ["demo.vak"],
                        "निर्भरताएँ": {},
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            (pkg_dir / "demo.vak").write_text(
                "कर्म दुगुना(x):\n"
                "    प्रत्यागच्छ x * २\n",
                encoding="utf-8",
            )

            archive_path = Path(temp_dir) / "demo.tar.gz"
            with tarfile.open(archive_path, "w:gz") as archive:
                archive.add(pkg_dir, arcname="demo")

            self.assertTrue(manager.install_from_file(str(archive_path)))

            source = (
                "आयात demo\n"
                "चर codex_payload = कोडेक्स_विवरण(\"def add(a, b):\\n    return a + b\\n\", \"english_vak\", \"demo.py\")\n"
                "चर repair_payload = रूपान्तर_विवरण(\"चर सूची = []\\nसूची.apend(१)\\n\")\n"
                "प्रमाण_रीसेट()\n"
                "परिभाषय(\"वस्तु\", [\"गुण\"])\n"
                "दावा(\"वस्तु\", \"HAS\", \"गुण\")\n"
                "नियम(\"*\", \"HAS\", \"गुण\", \"*\", \"IS\", \"ज्ञात\")\n"
                "मुद्रय demo.दुगुना(६)\n"
                "मुद्रय codex_payload[\"validation\"][\"compiled\"]\n"
                "मुद्रय repair_payload[\"compiled\"]\n"
                "मुद्रय पश्च_सिद्ध_है(\"वस्तु\", \"IS\", \"ज्ञात\")\n"
            )
            main_path = Path(temp_dir) / "main.vak"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                VakInterpreter().run(source, filename=str(main_path))

            lines = output.getvalue().splitlines()
            self.assertIn("12", lines)
            self.assertIn("True", lines)


if __name__ == "__main__":
    unittest.main()
