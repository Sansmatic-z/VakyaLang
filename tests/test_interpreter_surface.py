import contextlib
import io
import os
import subprocess
import sys
import unittest
from unittest.mock import patch


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime.run import run_source
from runtime.src.interpreter import VakInterpreter


class InterpreterSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.python = sys.executable
        cls.project_root = PROJECT_ROOT

    def test_repl_read_source_accepts_viram_exit_word(self):
        interpreter = VakInterpreter()

        with patch("builtins.input", return_value="विराम"):
            self.assertIsNone(interpreter._read_repl_source())

    def test_runtime_runner_formats_suggestion_rich_errors(self):
        interpreter = VakInterpreter()
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            ok = run_source('मुद्रर("नमस्ते")\n', interpreter)

        self.assertFalse(ok)
        rendered = stderr.getvalue()
        self.assertIn("सुझाव (Suggestions)", rendered)
        self.assertIn("मुद्रय", rendered)

    def test_runtime_runner_includes_source_context_for_parse_errors(self):
        interpreter = VakInterpreter()
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            ok = run_source("यदि सत्य\n    मुद्रय १\n", interpreter, filename="broken.vak")

        self.assertFalse(ok)
        rendered = stderr.getvalue()
        self.assertIn("स्रोत: broken.vak:", rendered)
        self.assertIn("| यदि सत्य", rendered)

    def test_runtime_runner_renders_multiple_parse_errors_after_recovery(self):
        interpreter = VakInterpreter()
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            ok = run_source("मान x =\nस्थिर y =\n", interpreter, filename="broken_many.vak")

        self.assertFalse(ok)
        rendered = stderr.getvalue()
        self.assertIn("2 वाक्यरचना त्रुटियाँ", rendered)
        self.assertIn("स्थिर को मान चाहिए", rendered)

    def test_runtime_runner_recovers_inside_nested_try_blocks(self):
        interpreter = VakInterpreter()
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            ok = run_source(
                "प्रयत्न:\n    यदि सत्य\n        मुद्रय १\nअपवाद err:\n    मुद्रय err\n",
                interpreter,
                filename="broken_nested.vak",
            )

        self.assertFalse(ok)
        rendered = stderr.getvalue()
        self.assertIn("broken_nested.vak", rendered)
        self.assertIn("अपेक्षित COLON", rendered)

    def test_runtime_runner_lists_codex_chapters(self):
        completed = subprocess.run(
            [self.python, "runtime/run.py", "--codex-chapters"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("vak_core:", completed.stdout)
        self.assertIn("bridges:", completed.stdout)


if __name__ == "__main__":
    unittest.main()
