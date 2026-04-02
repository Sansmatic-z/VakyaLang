import contextlib
import io
import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime.src.errors import format_vak_error
from runtime.src.interpreter import VakInterpreter


class AsyncStdlibModuleTests(unittest.TestCase):
    def run_source(self, source: str):
        buffer = io.StringIO()
        interpreter = VakInterpreter()
        with contextlib.redirect_stdout(buffer):
            result = interpreter.run(source)
        return result, buffer.getvalue()

    def test_promise_module_supports_then_all_and_race(self):
        source = """
आयात promise

चर व = नव promise.वादा()
कर्म सफलता(मान):
    मुद्रय "then: " + मान

व.तब(सफलता, शून्य)
व.पूर्ण_करो("ठीक")

चर यंत्र = नव promise.वादा_यंत्र()
चर अ = नव promise.वादा()
चर ब = नव promise.वादा()

कर्म सब_दिखाओ(सूची):
    मुद्रय "all: " + पाठ_कर(दीर्घता(सूची))

कर्म दौड़_दिखाओ(मान):
    मुद्रय "race: " + मान

यंत्र.सब([अ, ब]).तब(सब_दिखाओ, शून्य)
यंत्र.कोई_भी([अ, ब]).तब(दौड़_दिखाओ, शून्य)

ब.पूर्ण_करो("विजेता")
अ.पूर्ण_करो("दूसरा")
"""
        _, output = self.run_source(source)
        self.assertEqual(
            output.splitlines(),
            ["then: ठीक", "race: विजेता", "all: 2"],
        )

    def test_event_loop_and_task_group_run_in_stdlib_form(self):
        source = """
आयात event_loop
आयात task_group

चर लूप = नव event_loop.घटना_लूप()

कर्म प्रथम():
    प्रत्यागच्छ "१"

कर्म द्वितीय():
    प्रत्यागच्छ "२"

कर्म दिखाओ(सूची):
    मुद्रय "size: " + पाठ_कर(दीर्घता(सूची))
    मुद्रय सूची[०]
    मुद्रय सूची[१]

कर्म सूक्ष्म():
    मुद्रय "micro"

कर्म विलम्ब():
    मुद्रय "delay"

लूप.सूक्ष्म_कार्य_जोड़ो(सूक्ष्म)
लूप.विलम्ब_जोड़ो(विलम्ब, २)

चर समूह = नव task_group.कार्य_समूह(लूप)
समूह.जोड़ो(प्रथम)
समूह.जोड़ो(द्वितीय)
समूह.प्रतीक्षा_करो().तब(दिखाओ, शून्य)

लूप.चलाओ()
"""
        _, output = self.run_source(source)
        self.assertEqual(
            output.splitlines(),
            ["micro", "size: 2", "१", "२", "delay"],
        )

    def test_format_vak_error_handles_exception_groups(self):
        error = ExceptionGroup(
            "vak async group",
            [ValueError("bad"), RuntimeError("worse")],
        )
        rendered = format_vak_error(error)
        self.assertIn("समूह त्रुटि (Exception Group)", rendered)
        self.assertIn("[0] ValueError: bad", rendered)
        self.assertIn("[1] RuntimeError: worse", rendered)


if __name__ == "__main__":
    unittest.main()
