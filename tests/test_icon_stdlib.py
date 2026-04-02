import contextlib
import io
import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime.src.interpreter import VakInterpreter


class IconStdlibTests(unittest.TestCase):
    def run_source(self, source: str):
        buffer = io.StringIO()
        interpreter = VakInterpreter()
        with contextlib.redirect_stdout(buffer):
            result = interpreter.run(source)
        lines = [line.rstrip() for line in buffer.getvalue().splitlines()]
        return result, lines

    def test_split_icon_module_exports_direct_constants(self):
        source = """
आयात icon_status

मुद्रय icon_status.सफल
मुद्रय icon_status.स्थिति_संग्रह["सफल"]
"""
        _, lines = self.run_source(source)
        self.assertEqual(lines, ["✅", "✅"])

    def test_icon_facade_supports_lookup_search_and_counts(self):
        source = """
आयात icon

मुद्रय icon.सफल
मुद्रय icon.प्राप्त("स्थिति", "सफल")
मुद्रय icon.प्राप्त("अमान्य", "सफल")
मुद्रय icon.श्रेणी_गिनती("स्थिति")
मुद्रय icon.श्रेणी_गिनती("अमान्य")
मुद्रय दीर्घता(icon.खोज("सूर्य"))
मुद्रय icon.श्रेणी_रजिस्टर["स्थिति"]["सफल"]
"""
        _, lines = self.run_source(source)
        self.assertEqual(lines[0], "✅")
        self.assertEqual(lines[1], "✅")
        self.assertEqual(lines[2], "None")
        self.assertEqual(lines[3], "37")
        self.assertEqual(lines[4], "0")
        self.assertEqual(lines[5], "1")
        self.assertEqual(lines[6], "✅")

    def test_icon_facade_ui_helpers_render(self):
        source = """
आयात icon

icon.शीर्षक_बनाओ("चिह्न परीक्षण")
icon.विभाजक_रेखा(10, "भारी")
icon.स्थिति_दिखाओ("कार्य पूरा", "सफल")
icon.प्रगति_पट्टी(75, 12)
"""
        _, lines = self.run_source(source)
        self.assertEqual(lines[1], "║  चिह्न परीक्षण  ║")
        self.assertEqual(lines[3], "══════════")
        self.assertEqual(lines[4], "  ✅ कार्य पूरा")
        self.assertEqual(lines[5], "[█████████░░░]  75%")


if __name__ == "__main__":
    unittest.main()
