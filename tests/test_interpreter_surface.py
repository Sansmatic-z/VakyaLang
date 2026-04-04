import contextlib
import io
import os
import sys
import unittest
from unittest.mock import patch


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime.run import run_source
from runtime.src.interpreter import VakInterpreter


class InterpreterSurfaceTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
