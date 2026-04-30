import unittest
from pathlib import Path

from runtime.src.codex import build_default_codex


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORPUS_ROOT = PROJECT_ROOT / "stress" / "codex_corpus"


class CodexStressCorpusTests(unittest.TestCase):
    def test_codex_corpus_routes_and_validates(self):
        cases = [
            ("legacy_vak.vak", [], "vak_legacy", ("यावत् x < 3:",), "vak"),
            ("english_bridge.py", [], "python_vak", ("कर्म add(a, b):",), "python"),
            ("english_loop_bridge.py", [], "python_vak", ("यावत् (total < 2):", "मुद्रय(total)"), "python"),
            ("math_logic.logic", [], "math_logic", ("यदि न (a  और  b):",), "math_logic"),
            ("math_logic_nested.logic", [], "math_logic", ("अथवा",), "math_logic"),
            (
                "sanskrit_notation.svk",
                [],
                "sanskrit_notation",
                ("कर्म yoga(x, y):",),
                "sanskrit_notation",
            ),
            (
                "sanskrit_notation_loop.svk",
                [],
                "sanskrit_notation",
                ("यावत् total < 2:", "मुद्रय(total)"),
                "sanskrit_notation",
            ),
            ("sample.c", ["universal_codex_lab"], "c_subset", ("कर्म main():",), "c_subset"),
            ("sample.rs", ["universal_codex_lab"], "rust_subset", ("कर्म main():",), "rust_subset"),
            ("command.txt", ["universal_codex_lab"], "natural_language", ("यदि i % 2 == 0:",), "natural_language"),
            ("branch_repeat.txt", ["universal_codex_lab"], "natural_language", ("परास(0, 3)", "मुद्रय(7)"), "natural_language"),
        ]

        for filename, branches, expected_page, snippets, source_kind in cases:
            with self.subTest(filename=filename, branches=branches):
                source_path = CORPUS_ROOT / filename
                codex = build_default_codex(active_branches=branches)
                result = codex.transform_source(
                    source_path.read_text(encoding="utf-8"),
                    filename=str(source_path),
                )
                self.assertEqual(result.page, expected_page)
                self.assertEqual(result.source_kind, source_kind)
                self.assertTrue(result.validation is not None, msg=result.report_text())
                self.assertTrue(result.validation.syntax_valid, msg=result.report_text())
                self.assertTrue(result.validation.compiled, msg=result.report_text())
                self.assertTrue(result.validation_history, msg=result.report_text())
                for snippet in snippets:
                    self.assertIn(snippet, result.source)


if __name__ == "__main__":
    unittest.main()
