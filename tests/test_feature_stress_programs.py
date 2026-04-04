import os
import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VAK_CLI = PROJECT_ROOT / "vak.py"
STRESS_DIR = PROJECT_ROOT / "stress"


class FeatureStressProgramTests(unittest.TestCase):
    maxDiff = None

    def run_program(self, relative_path: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.setdefault("PYTHONIOENCODING", "utf-8")
        return subprocess.run(
            [sys.executable, str(VAK_CLI), str(STRESS_DIR / relative_path)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            check=False,
        )

    def tearDown(self) -> None:
        for pattern in ("stress_visual_matrix_*.png", "stress_runtime_data_*.json"):
            for path in PROJECT_ROOT.glob(pattern):
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass

    def assertSucceeded(self, result: subprocess.CompletedProcess[str]) -> None:
        if result.returncode != 0:
            self.fail(
                "stress program failed\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )

    def test_core_language_matrix(self):
        result = self.run_program("core_language_matrix.vak")
        self.assertSucceeded(result)
        output = result.stdout
        self.assertIn("सूत्र: 6", output)
        self.assertIn("closure: 15", output)
        self.assertIn("pipeline: VAK CORE", output)
        self.assertIn("result: 4", output)
        self.assertIn("data: 10", output)
        self.assertIn("STRESS CORE OK", output)

    def test_modules_io_matrix(self):
        result = self.run_program("modules_io_matrix.vak")
        self.assertSucceeded(result)
        output = result.stdout
        self.assertIn("title: VAK I/O MATRIX", output)
        self.assertIn("number: 21", output)
        self.assertIn("format: sanskrit_stack", output)
        self.assertIn("binary: 1010", output)
        self.assertIn("replace-full: VAK", output)
        self.assertIn("hash-len: 64", output)
        self.assertIn("sqrt: 9", output)
        self.assertIn("exists: True", output)
        self.assertIn("cleanup: False", output)
        self.assertIn("STRESS IO OK", output)
        self.assertNotIn("TextIOWrapper", output)
        self.assertFalse(any(PROJECT_ROOT.glob("stress_runtime_data_*.json")))

    def test_semantics_proofs_matrix(self):
        result = self.run_program("semantics_proofs_matrix.vak")
        self.assertSucceeded(result)
        output = result.stdout
        self.assertIn("refinement: 19", output)
        self.assertIn("proof: True", output)
        self.assertIn("proof-odd: True", output)
        self.assertIn("dharma: True", output)
        self.assertIn("karaka: True", output)
        self.assertIn("nyaya: True", output)
        self.assertIn("result: 9", output)
        self.assertIn("STRESS SEMANTICS OK", output)

    def test_visual_matrix(self):
        for path in PROJECT_ROOT.glob("stress_visual_matrix_*.png"):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        result = self.run_program("visual_matrix.vak")
        self.assertSucceeded(result)
        output = result.stdout
        self.assertIn("visual-size: 480 480", output)
        self.assertIn("visual-center: ChitraColor(255, 255, 255, 255)", output)
        self.assertIn("STRESS VISUAL OK", output)

    def test_advanced_runtime_probe(self):
        result = self.run_program("advanced_runtime_probe.vak")
        self.assertSucceeded(result)
        self.assertEqual(result.stdout.splitlines(), ["ADVANCED RUNTIME PROBE", "7"])

    def test_async_timer_probe(self):
        result = self.run_program("async_timer_probe.vak")
        self.assertSucceeded(result)
        self.assertEqual(
            result.stdout.splitlines(),
            ["ASYNC TIMER PROBE", "timer-fired", "11"],
        )

    def test_json_wrapper_probe(self):
        result = self.run_program("json_wrapper_probe.vak")
        self.assertSucceeded(result)
        self.assertIn("JSON WRAPPER PROBE", result.stdout)
        self.assertIn('{"क": 1}', result.stdout)


if __name__ == "__main__":
    unittest.main()
