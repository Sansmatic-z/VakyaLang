import contextlib
import io
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime.src.code_transformer import VakCodeTransformer
from runtime.src.errors import TranslationError
from runtime.src.interpreter import VakInterpreter
from sanskrit_coder.core.translator import SanskritTranslator


class CodeTransformerTests(unittest.TestCase):
    def run_source(self, source: str, filename: str = "<test>"):
        buffer = io.StringIO()
        interpreter = VakInterpreter()
        with contextlib.redirect_stdout(buffer):
            result = interpreter.run(textwrap.dedent(source), filename=filename)
        return interpreter, result, buffer.getvalue().splitlines()

    def test_sanskrit_translator_exposes_live_code_keyword_map(self):
        translator = SanskritTranslator()
        self.assertEqual(translator.english_code_to_sanskrit("def"), "कर्म")
        self.assertEqual(translator.english_code_to_sanskrit("await"), "प्रतीक्षा")
        self.assertEqual(translator.english_code_to_sanskrit("False"), "असत्य")

    def test_transformer_rewrites_python_keywords_and_from_import_order(self):
        transformer = VakCodeTransformer()
        result = transformer.transform(
            textwrap.dedent(
                """
                from data_sangrah import स्टैक as Stack
                def ready(flag):
                    if flag and not False:
                        return self
                    else:
                        return None
                """
            )
        )
        self.assertTrue(result.transformed)
        self.assertIn("आयात स्टैक से data_sangrah; चर Stack = स्टैक", result.source)
        self.assertIn("कर्म ready(flag):", result.source)
        self.assertIn("यदि flag और न असत्य:", result.source)
        self.assertIn("प्रत्यागच्छ स्वयं", result.source)
        self.assertIn("प्रत्यागच्छ शून्य", result.source)
        self.assertEqual(result.changed_lines, (2, 3, 4, 5, 6, 7))
        self.assertIn("import_rewrite", result.features)
        self.assertIn("keyword:def", result.features)
        self.assertEqual(result.language, "english")

    def test_transformer_skips_live_vak_source(self):
        transformer = VakCodeTransformer()
        result = transformer.transform(
            textwrap.dedent(
                """
                कर्म योग(संख्या):
                    प्रत्यागच्छ संख्या + १
                """
            )
        )
        self.assertFalse(result.transformed)
        self.assertEqual(result.language, "vak")
        self.assertEqual(result.source.strip().splitlines()[0], "कर्म योग(संख्या):")

    def test_deep_meaning_mode_semantically_renames_functions_and_parameters(self):
        transformer = VakCodeTransformer(deep_meaning_mode=True)
        result = transformer.transform(
            textwrap.dedent(
                """
                def add(a, b):
                    return a + b

                print(add(2, 3))
                """
            )
        )
        self.assertTrue(result.transformed)
        self.assertIn("कर्म जोड़ो(क, ख):", result.source)
        self.assertIn("प्रत्यागच्छ क + ख", result.source)
        self.assertIn("मुद्रय(जोड़ो(2, 3))", result.source)
        self.assertIn("deep_meaning", result.features)
        self.assertIn("deep_identifiers", result.features)

    def test_deep_meaning_mode_translates_human_strings(self):
        interpreter, _, output = self.run_source(
            """
            def greet():
                print("Hello World")

            greet()
            """
        )
        self.assertEqual(output, ["Hello World"])

        deep_interpreter = VakInterpreter(deep_meaning_mode=True)
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            deep_interpreter.run(
                textwrap.dedent(
                    """
                    def greet():
                        print("Hello World")

                    greet()
                    """
                )
            )
        self.assertEqual(buffer.getvalue().splitlines(), ["नमस्कार विश्व"])
        self.assertIn("deep_strings", deep_interpreter.last_transform_result.features)

    def test_deep_meaning_mode_does_not_translate_file_paths_or_modes(self):
        with tempfile.TemporaryDirectory() as tempdir:
            sample_path = (Path(tempdir) / "sample.txt").as_posix()
            interpreter = VakInterpreter(deep_meaning_mode=True)
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                interpreter.run(
                    textwrap.dedent(
                        f"""
                        with open("{sample_path}", "w") as handle:
                            handle.write("vak")

                        with open("{sample_path}", "r") as handle:
                            print(handle.read())
                        """
                    )
                )
            self.assertEqual(buffer.getvalue().splitlines(), ["vak"])

    def test_interpreter_executes_english_python_style_source(self):
        interpreter, _, output = self.run_source(
            """
            def fib(n):
                if n <= 1:
                    return n
                else:
                    return fib(n - 1) + fib(n - 2)

            for i in range(6):
                print(fib(i))
            """
        )
        self.assertEqual(output, ["0", "1", "1", "2", "3", "5"])
        self.assertEqual(interpreter.translation_status_message(), "वाक्य-अनुवाद सफल")

    def test_python_style_from_import_runs_after_translation(self):
        interpreter, _, output = self.run_source(
            """
            from ganit_vistarit import वर्ग
            print(वर्ग(6))
            """
        )
        self.assertEqual(output, ["36"])
        self.assertEqual(interpreter.translation_status_message(), "वाक्य-अनुवाद सफल")

    def test_transformer_handles_with_try_except_and_identity_comparisons(self):
        with tempfile.TemporaryDirectory() as tempdir:
            sample_path = (Path(tempdir) / "sample.txt").as_posix()
            interpreter, _, output = self.run_source(
                f"""
                with open("{sample_path}", "w") as handle:
                    handle.write("vak")

                with open("{sample_path}", "r") as handle:
                    print(handle.read())

                if None is None:
                    print("same")
                if 1 is not 2:
                    print("different")

                try:
                    print(1 // 0)
                except ZeroDivisionError as err:
                    print("caught")
                finally:
                    print("done")
                """
            )
            self.assertEqual(output, ["vak", "same", "different", "caught", "done"])
            self.assertIn("identity_compare", interpreter.last_transform_result.features)
            self.assertIn("keyword:open", interpreter.last_transform_result.features)

    def test_transformer_handles_async_and_class_self(self):
        interpreter, _, output = self.run_source(
            """
            class Box:
                def __init__(self, value):
                    self.value = value

                def get(self):
                    return self.value

            async def delayed():
                await async_sleep(0.01)
                return Box(9).get()

            print(await delayed())
            """
        )
        self.assertEqual(output, ["9"])
        self.assertIn("keyword:async", interpreter.last_transform_result.features)
        self.assertIn("keyword:self", interpreter.last_transform_result.features)

    def test_deep_meaning_mode_renames_methods_and_calls(self):
        interpreter = VakInterpreter(deep_meaning_mode=True)
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            interpreter.run(
                textwrap.dedent(
                    """
                    class Box:
                        def get(self):
                            return 9

                    print(Box().get())
                    """
                )
            )
        self.assertEqual(buffer.getvalue().splitlines(), ["9"])
        self.assertIn("वर्ग पेटिका:", interpreter.last_transform_result.source)
        self.assertIn("कर्म प्राप्त_करो(स्वयं):", interpreter.last_transform_result.source)
        self.assertIn("मुद्रय(पेटिका().प्राप्त_करो())", interpreter.last_transform_result.source)

    def test_transformer_supports_python_decorator_lines_when_vak_surface_supports_them(self):
        interpreter, _, output = self.run_source(
            textwrap.dedent(
                """
                def double(fn):
                    def wrapper(x):
                        return fn(x) * 2
                    return wrapper

                @double
                def inc(x):
                    return x + 1

                print(inc(4))
                """
            )
        )
        self.assertEqual(output, ["10"])
        self.assertIn("@double", interpreter.last_transform_result.source)

    def test_transformer_supports_python_yield_generators(self):
        interpreter, _, output = self.run_source(
            textwrap.dedent(
                """
                def count(limit):
                    i = 0
                    while i < limit:
                        yield i
                        i = i + 1

                for value in count(3):
                    print(value)
                """
            )
        )
        self.assertEqual(output, ["0", "1", "2"])
        self.assertIn("उपज i", interpreter.last_transform_result.source)

    def test_transformer_supports_python_yield_from_generators(self):
        interpreter, _, output = self.run_source(
            textwrap.dedent(
                """
                def base():
                    yield 1
                    yield 2

                def outer():
                    yield 0
                    yield from base()
                    yield 3

                for value in outer():
                    print(value)
                """
            )
        )
        self.assertEqual(output, ["0", "1", "2", "3"])
        self.assertIn("उपज से", interpreter.last_transform_result.source)

    def test_transformer_supports_python_async_for_generators(self):
        interpreter, _, output = self.run_source(
            textwrap.dedent(
                """
                async def count(limit):
                    i = 0
                    while i < limit:
                        await async_sleep(0.01)
                        yield i
                        i = i + 1

                async def main():
                    async for value in count(3):
                        print(value)

                await main()
                """
            )
        )
        self.assertEqual(output, ["0", "1", "2"])
        self.assertIn("अतुल्यकालिक प्रत्येक", interpreter.last_transform_result.source)

    def test_transformer_supports_python_async_with_context_managers(self):
        interpreter, _, output = self.run_source(
            textwrap.dedent(
                """
                class Stream:
                    def __init__(self):
                        self.events = []

                    async def __aenter__(self):
                        self.events.append("enter")
                        await async_sleep(0.01)
                        return "inside"

                    async def __aexit__(self, exc_type, exc, tb):
                        self.events.append("exit")
                        await async_sleep(0.01)
                        return False

                async def main():
                    stream = Stream()
                    async with stream as value:
                        print(value)
                    print(stream.events)

                await main()
                """
            )
        )
        self.assertEqual(output, ["inside", "['enter', 'exit']"])
        self.assertIn("अतुल्यकालिक साथ", interpreter.last_transform_result.source)

    def test_transformer_supports_python_generator_and_async_comprehensions(self):
        interpreter, _, output = self.run_source(
            textwrap.dedent(
                """
                async def count(limit):
                    i = 0
                    while i < limit:
                        await async_sleep(0.01)
                        yield i
                        i = i + 1

                def double_values():
                    return (value * 2 for value in [1, 2, 3])

                async def main():
                    items_out = [value * 2 async for value in count(4) if value > 0]
                    squares_out = {value: value * value async for value in count(4) if value > 1}
                    print(items_out)
                    print(squares_out)
                    for item in double_values():
                        print(item)

                await main()
                """
            )
        )
        self.assertEqual(output, ["[2, 4, 6]", "{2: 4, 3: 9}", "2", "4", "6"])
        self.assertIn("उपज", interpreter.last_transform_result.source)

    def test_transformer_rejects_lossy_python_features(self):
        interpreter = VakInterpreter()
        with self.assertRaises(TranslationError) as ctx:
            interpreter.run(
                textwrap.dedent(
                    """
                    async def broken(first, second):
                        async with first, second:
                            print(1)
                    """
                )
            )
        self.assertIn("वाक्य-अनुवाद असंभव", str(ctx.exception))
        self.assertIn("context managers", str(ctx.exception))

    def test_transformer_rejects_invalid_python_syntax_before_vak_parse(self):
        interpreter = VakInterpreter()
        with self.assertRaises(TranslationError) as ctx:
            interpreter.run(
                textwrap.dedent(
                    """
                    def broken(:
                        pass
                    """
                )
            )
        self.assertIn("वाक्य-अनुवाद असंभव", str(ctx.exception))
        self.assertIn("Python वाक्यरचना त्रुटि", str(ctx.exception))

    def test_cli_reports_translation_failure_for_unsupported_english_source(self):
        with tempfile.TemporaryDirectory() as tempdir:
            source_path = Path(tempdir) / "unsupported_english.vak"
            source_path.write_text(
                textwrap.dedent(
                    """
                    from data_sangrah import *
                    print(1)
                    """
                ),
                encoding="utf-8",
            )
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "utf-8"
            result = subprocess.run(
                [sys.executable, "vak.py", str(source_path)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
                timeout=60,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("वाक्य-अनुवाद असंभव", result.stderr)
            self.assertNotIn("वाक्यरचना त्रुटि (Parse Error)", result.stderr)

    def test_cli_gudhartha_flag_enables_deep_meaning_mode(self):
        with tempfile.TemporaryDirectory() as tempdir:
            source_path = Path(tempdir) / "deep_meaning_english.vak"
            source_path.write_text(
                textwrap.dedent(
                    """
                    def add(a, b):
                        return a + b

                    print("Hello World")
                    print(add(2, 3))
                    """
                ),
                encoding="utf-8",
            )
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "utf-8"
            result = subprocess.run(
                [sys.executable, "vak.py", "--गूढार्थ", str(source_path)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
                timeout=60,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("नमस्कार विश्व", result.stdout)
            self.assertIn("5", result.stdout)
            self.assertIn("वाक्य-अनुवाद सफल", result.stdout)

    def test_cli_shows_translation_success_for_english_source(self):
        with tempfile.TemporaryDirectory() as tempdir:
            source_path = Path(tempdir) / "english_style.vak"
            source_path.write_text(
                textwrap.dedent(
                    """
                    if True:
                        print(4)
                    """
                ),
                encoding="utf-8",
            )
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "utf-8"
            result = subprocess.run(
                [sys.executable, "vak.py", str(source_path)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
                timeout=60,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("वाक्य-अनुवाद सफल", result.stdout)
            self.assertIn("4", result.stdout)


if __name__ == "__main__":
    unittest.main()
