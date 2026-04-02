import contextlib
import io
import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime.src.interpreter import VakInterpreter


class SalvagedStdlibModuleTests(unittest.TestCase):
    def run_source(self, source: str):
        buffer = io.StringIO()
        interpreter = VakInterpreter()
        with contextlib.redirect_stdout(buffer):
            result = interpreter.run(source)
        return result, [line.rstrip() for line in buffer.getvalue().splitlines()]

    def test_contracts_config_and_id_generation(self):
        source = """
आयात अनुबंध
आयात विन्यास
आयात क्रम_निर्माता

चर पथ = "salvaged_config_test.cfg"
विन्यास.विन्यास_लिखो({"नाम": "वाक्", "mode": "debug"}, पथ)
चर cfg = विन्यास.विन्यास_पढ़ो(पथ)
मुद्रय विन्यास.विन्यास_प्राप्त(cfg, "नाम", "x")
मुद्रय विन्यास.विन्यास_प्राप्त(cfg, "अनुपस्थित", "fallback")
मुद्रय क्रम_निर्माता.अगला_क्रम()
मुद्रय क्रम_निर्माता.उपसर्ग_बनाओ("vak")
मुद्रय दीर्घता(क्रम_निर्माता.छोटा_यूयुआईडी())
मुद्रय क्रम_निर्माता.स्लग_बनाओ("vak lang")
अनुबंध.सीमा_जाँच(५, १, १०, "मान")
मिटाओ(पथ)
मुद्रय अस्तित्व(पथ)
"""
        _, lines = self.run_source(source)
        self.assertEqual(lines[0], "वाक्")
        self.assertEqual(lines[1], "fallback")
        self.assertEqual(lines[2], "1")
        self.assertEqual(lines[3], "vak_2")
        self.assertEqual(lines[4], "8")
        self.assertEqual(lines[5], "vak-lang-4")
        self.assertEqual(lines[6], "False")

    def test_state_events_and_deep_compare(self):
        source = """
आयात अवस्था_यंत्र
आयात घटना_चक्र
आयात तुलना

चर मशीन = अवस्था_यंत्र.अवस्था_यंत्र_बनाओ("idle")
अवस्था_यंत्र.संक्रमण_जोड़ो(मशीन, "idle", "start", "run")
अवस्था_यंत्र.संक्रमण_जोड़ो(मशीन, "run", "stop", "idle")
मुद्रय अवस्था_यंत्र.घटना_भेजो(मशीन, "start")
मुद्रय अवस्था_यंत्र.वर्तमान_अवस्था(मशीन)
मुद्रय दीर्घता(अवस्था_यंत्र.अवस्था_इतिहास(मशीन))

चर emitter = घटना_चक्र.उत्सर्जक_बनाओ()
चर state = {"total": ०}
कर्म add_one(value):
    state["total"] += value
घटना_चक्र.सुनो(emitter, "tick", add_one)
मुद्रय घटना_चक्र.उत्सर्जित_करो(emitter, "tick", ३)
मुद्रय state["total"]
मुद्रय तुलना.गहरा_बराबर({"a": [१, २]}, {"a": [१, २]})
मुद्रय तुलना.गहरा_बराबर({"a": [१, २]}, {"a": [२, १]})
"""
        _, lines = self.run_source(source)
        self.assertEqual(lines, ["True", "run", "2", "1", "3", "True", "False"])

    def test_text_canvas_spinner_and_validation(self):
        source = """
आयात अक्षर_चित्र
आयात चक्रवात
आयात प्रमाणीकरण

चर canvas = अक्षर_चित्र.कैनवास_बनाओ(८, ४, ".")
अक्षर_चित्र.कैनवास_आयत(canvas, १, १, ५, २, "#", असत्य)
अक्षर_चित्र.कैनवास_पाठ(canvas, २, २, "vak")
मुद्रय अक्षर_चित्र.कैनवास_स्ट्रिंग(canvas)
मुद्रय चक्रवात.चक्र_प्राप्त(३)
मुद्रय चक्रवात.बिंदु_प्रगति(१०, ७, १०)
मुद्रय प्रमाणीकरण.ईमेल_वैध("vak@example.com")
मुद्रय प्रमाणीकरण.फोन_वैध("9876543210")
मुद्रय प्रमाणीकरण.संकेत_शक्ति("Vak12345")
मुद्रय प्रमाणीकरण.संख्यात्मक_है("-१२.५")
"""
        _, lines = self.run_source(source)
        self.assertEqual(lines[0], "........")
        self.assertEqual(lines[1], ".#####..")
        self.assertEqual(lines[2], ".#vak#..")
        self.assertEqual(lines[3], "........")
        self.assertEqual(lines[4], "⠸")
        self.assertEqual(lines[5], "[███████░░░]  70%")
        self.assertEqual(lines[6], "True")
        self.assertEqual(lines[7], "True")
        self.assertEqual(lines[8], "मजबूत")
        self.assertEqual(lines[9], "True")


if __name__ == "__main__":
    unittest.main()
