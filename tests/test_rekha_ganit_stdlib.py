import contextlib
import io
import os
import sys
import textwrap
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime.src.interpreter import VakInterpreter


class RekhaGanitStdlibTests(unittest.TestCase):
    def run_source(self, source: str, filename: str = "<test>"):
        buffer = io.StringIO()
        interpreter = VakInterpreter()
        with contextlib.redirect_stdout(buffer):
            result = interpreter.run(textwrap.dedent(source), filename=filename)
        return result, buffer.getvalue().splitlines()

    def test_vector_angle_returns_radians_not_cosine(self):
        _, output = self.run_source(
            """
            आयात rekha_ganit

            मुद्रय rekha_ganit.सदिश_कोण([१, ०], [०, १])
            मुद्रय rekha_ganit.सदिश_कोण([१, ०], [१, ०])
            मुद्रय rekha_ganit.सदिश_कोण([१, ०], [-१, ०])
            """
        )
        self.assertAlmostEqual(float(output[0]), 1.5707963267948966, places=9)
        self.assertAlmostEqual(float(output[1]), 0.0, places=9)
        self.assertAlmostEqual(float(output[2]), 3.141592653589793, places=9)

    def test_matrix_inverse_supports_three_by_three_case(self):
        _, output = self.run_source(
            """
            आयात rekha_ganit

            चर matrix = [
                [१, २, ३],
                [०, १, ४],
                [५, ६, ०]
            ]
            चर inverse = rekha_ganit.मैट्रिक्स_उल्टा(matrix)
            मुद्रय inverse[०][०]
            मुद्रय inverse[०][१]
            मुद्रय inverse[०][२]
            मुद्रय inverse[१][०]
            मुद्रय inverse[१][१]
            मुद्रय inverse[१][२]
            मुद्रय inverse[२][०]
            मुद्रय inverse[२][१]
            मुद्रय inverse[२][२]
            """
        )
        expected = [-24.0, 18.0, 5.0, 20.0, -15.0, -4.0, -5.0, 4.0, 1.0]
        self.assertEqual(len(output), len(expected))
        for actual, value in zip(output, expected):
            self.assertAlmostEqual(float(actual), value, places=9)


if __name__ == "__main__":
    unittest.main()
