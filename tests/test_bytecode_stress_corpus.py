import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORPUS_ROOT = PROJECT_ROOT / "stress" / "bytecode_corpus"


class BytecodeStressCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.python = sys.executable
        cls.env = os.environ.copy()
        cls.env.setdefault("PYTHONIOENCODING", "utf-8")

    def run_command(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [self.python, *args],
            cwd=cwd or PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=self.env,
        )

    def test_bytecode_corpus_compiles_and_runs_from_compiled_artifacts(self):
        cases = [
            ("nested_closure.vak", "5", True),
            ("class_and_method.vak", "9", True),
            ("देवनागरी_संकलित.vak", "देवनागरी-संकलन", False),
        ]

        for filename, expected, remove_source in cases:
            with self.subTest(filename=filename, remove_source=remove_source):
                with tempfile.TemporaryDirectory() as temp_dir:
                    workdir = Path(temp_dir)
                    source_path = workdir / filename
                    source_path.write_text(
                        (CORPUS_ROOT / filename).read_text(encoding="utf-8"),
                        encoding="utf-8",
                    )

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

                    disassemble_result = self.run_command("vak.py", str(bytecode_path), "--disassemble")
                    self.assertEqual(
                        disassemble_result.returncode,
                        0,
                        msg=disassemble_result.stderr or disassemble_result.stdout,
                    )
                    self.assertIn("=== Bytecode:", disassemble_result.stdout)

                    if remove_source:
                        source_path.unlink()

                    run_result = self.run_command("vak.py", str(bytecode_path))
                    self.assertEqual(
                        run_result.returncode,
                        0,
                        msg=run_result.stderr or run_result.stdout,
                    )
                    self.assertIn(expected, run_result.stdout)

                    runtime_result = self.run_command("runtime/run.py", str(bytecode_path))
                    self.assertEqual(
                        runtime_result.returncode,
                        0,
                        msg=runtime_result.stderr or runtime_result.stdout,
                    )
                    self.assertIn(expected, runtime_result.stdout)


if __name__ == "__main__":
    unittest.main()
