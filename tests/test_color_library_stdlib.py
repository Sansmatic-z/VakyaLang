import contextlib
import io
import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime.src.interpreter import VakInterpreter


class ColorLibraryStdlibTests(unittest.TestCase):
    def run_source(self, source: str, filename: str = "<test>"):
        buffer = io.StringIO()
        interpreter = VakInterpreter()
        with contextlib.redirect_stdout(buffer):
            result = interpreter.run(textwrap.dedent(source), filename=filename)
        return result, buffer.getvalue().splitlines()

    def test_lookup_and_conversion_helpers(self):
        _, output = self.run_source(
            """
            आयात रंग_पुस्तकालय

            मुद्रय रंग_पुस्तकालय.प्राप्त("नील")
            मुद्रय रंग_पुस्तकालय.प्राप्त("Blue")
            मुद्रय रंग_पुस्तकालय.rgb_से_hex(255, 87, 51)
            चर rgb = रंग_पुस्तकालय.hex_से_rgb("#FF5733")
            मुद्रय rgb["र"]
            मुद्रय rgb["ह"]
            मुद्रय rgb["नी"]
            मुद्रय रंग_पुस्तकालय.hsl_रंग(120, 100, 50)
            मुद्रय दीर्घता(रंग_पुस्तकालय.तापमान_रंग(1800))
            मुद्रय दीर्घता(रंग_पुस्तकालय.तरंगदैर्ध्य_रंग(500))
            """
        )
        self.assertEqual(output[0], "#0000CD")
        self.assertEqual(output[1], "#0000FF")
        self.assertEqual(output[2], "#FF5733")
        self.assertEqual(output[3:6], ["255", "87", "51"])
        self.assertEqual(output[6], "#00FF00")
        self.assertEqual(output[7], "7")
        self.assertEqual(output[8], "7")

    def test_palettes_and_contrast_helpers(self):
        _, output = self.run_source(
            """
            आयात रंग_पुस्तकालय

            चर श्रेणी = रंग_पुस्तकालय.रैखिक_ढाल("#000000", "#FFFFFF", 3)
            मुद्रय दीर्घता(श्रेणी)
            मुद्रय श्रेणी[0]
            मुद्रय श्रेणी[1]
            मुद्रय श्रेणी[2]
            मुद्रय रंग_पुस्तकालय.पूरक("#FF0000")
            मुद्रय रंग_पुस्तकालय.पाठ_रंग("#FFFFFF")
            मुद्रय दीर्घता(रंग_पुस्तकालय.त्रिशीर्षी("#FF0000"))
            मुद्रय दीर्घता(रंग_पुस्तकालय.समान_श्रेणी("#FF0000"))
            मुद्रय दीर्घता(रंग_पुस्तकालय.वर्ण_वर्णक्रम(5))
            मुद्रय दीर्घता(रंग_पुस्तकालय.स्पेक्ट्रम_ढाल(420, 520, 4))
            """
        )
        self.assertEqual(output[0], "3")
        self.assertEqual(output[1:4], ["#000000", "#808080", "#FFFFFF"])
        self.assertEqual(output[4], "#00FFFF")
        self.assertEqual(output[5], "#000000")
        self.assertEqual(output[6:], ["3", "3", "5", "4"])

    def test_svg_and_ppm_writers_generate_files(self):
        with tempfile.TemporaryDirectory() as tempdir:
            svg_path = (Path(tempdir) / "demo.svg").as_posix()
            ppm_path = (Path(tempdir) / "demo.ppm").as_posix()
            _, output = self.run_source(
                f"""
                आयात रंग_पुस्तकालय

                चर svg = रंग_पुस्तकालय.svg_आरम्भ(20, 10)
                svg = रंग_पुस्तकालय.svg_रेखीय_ढाल(svg, 0, 0, 1, 0, "नील", "पद्म", "g1")
                svg = रंग_पुस्तकालय.svg_आयत(svg, 0, 0, 20, 10, "नील", "none", 0)
                svg = रंग_पुस्तकालय.svg_पाठ(svg, 2, 6, "Vak", "श्वेत", 4)
                रंग_पुस्तकालय.svg_लिखो(svg, "{svg_path}")

                चर ppm = रंग_पुस्तकालय.ppm_आरम्भ(4, 4, "श्वेत")
                ppm = रंग_पुस्तकालय.ppm_आयत(ppm, 1, 1, 2, 2, "नील")
                ppm = रंग_पुस्तकालय.ppm_वृत्त(ppm, 2, 2, 1, "अरुण")
                रंग_पुस्तकालय.ppm_लिखो(ppm, "{ppm_path}")

                मुद्रय अस्तित्व("{svg_path}")
                मुद्रय अस्तित्व("{ppm_path}")
                """
            )
            self.assertEqual(output[-2:], ["True", "True"])
            self.assertTrue(Path(svg_path).exists())
            self.assertTrue(Path(ppm_path).exists())
            self.assertIn("<svg", Path(svg_path).read_text(encoding="utf-8"))
            ppm_text = Path(ppm_path).read_text(encoding="utf-8")
            self.assertTrue(ppm_text.startswith("P3\n"))

    def test_full_colour_lib_catalog_and_lookup_survive_import(self):
        _, output = self.run_source(
            """
            आयात colour_lib

            मुद्रय दीर्घता(कुंजियाँ(colour_lib.css_रंग))
            मुद्रय दीर्घता(कुंजियाँ(colour_lib.संस्कृत_रंग))
            मुद्रय दीर्घता(कुंजियाँ(colour_lib.tailwind_रंग))
            मुद्रय दीर्घता(कुंजियाँ(colour_lib.material_रंग))
            मुद्रय colour_lib.प्राप्त("Blue")
            मुद्रय colour_lib.प्राप्त("blue")
            मुद्रय colour_lib.प्राप्त("नील")
            मुद्रय colour_lib.पूरक("#191970")
            """
        )
        self.assertEqual(output[:4], ["141", "55", "242", "190"])
        self.assertEqual(output[4:7], ["#0000FF", "#0000FF", "#0000CD"])
        self.assertTrue(output[7].startswith("#"))
        self.assertEqual(len(output[7]), 7)

    def test_full_colour_lib_repaired_optional_signatures_work(self):
        with tempfile.TemporaryDirectory() as tempdir:
            svg_path = (Path(tempdir) / "full.svg").as_posix()
            _, output = self.run_source(
                f"""
                आयात colour_lib

                चर svg = colour_lib.svg_आरम्भ(10, 10)
                svg = colour_lib.svg_आयत(svg, 0, 0, 10, 10, "#FFFFFF")
                colour_lib.svg_लिखो(svg, "{svg_path}")
                मुद्रय दीर्घता(svg)
                मुद्रय अस्तित्व("{svg_path}")
                """
            )
            self.assertEqual(output[-2:], ["4", "True"])
            self.assertTrue(Path(svg_path).exists())
            self.assertIn("<rect", Path(svg_path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
