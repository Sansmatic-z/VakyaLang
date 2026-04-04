import unittest
from pathlib import Path

from runtime.src.rupantar import VakyaRupantar


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORPUS_ROOT = PROJECT_ROOT / "stress" / "rupantar_corpus"


class RupantarStressCorpusTests(unittest.TestCase):
    def test_repair_corpus_compiles_after_rupantar(self):
        cases = [
            ("ai_generated_old_syntax.vak", [], ("मुद्रय सूची",)),
            ("mixed_english_vak.vak", [], ("यावत् total < 3:",)),
            ("branch_chitra_drift.vak", ["chitrakala"], ("_chitra_canvas", "_chitra_line")),
            ("import_export_drift.vak", [], ("प्रतिज्ञा",)),
            ("adaptive_chitra_mix.vak", ["adaptive_rupantar", "chitrakala"], ("मुद्रय", "_chitra_canvas")),
        ]

        for filename, branches, snippets in cases:
            with self.subTest(filename=filename, branches=branches):
                source_path = CORPUS_ROOT / filename
                engine = VakyaRupantar(active_branches=branches)
                result = engine.transform_source(
                    source_path.read_text(encoding="utf-8"),
                    source_path=str(source_path),
                )
                self.assertTrue(result.syntax_valid, msg=result.report_text())
                self.assertTrue(result.compiled, msg=result.report_text())
                for snippet in snippets:
                    self.assertIn(snippet, result.source)


if __name__ == "__main__":
    unittest.main()
