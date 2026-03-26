import contextlib
import io
import os
import sys
import tempfile
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime.export_abi import compile_file
from runtime.src.bytecode import ABI_FORMAT, ABI_VERSION, Bytecode
from runtime.src.interpreter import VakInterpreter
from runtime.src.vm import VakVM


class BytecodeAbiTests(unittest.TestCase):
    def compile_source(self, source: str, filename: str = "<test>") -> Bytecode:
        interpreter = VakInterpreter()
        return interpreter.compile_only(source, filename=filename)

    def run_bytecode(self, bytecode: Bytecode) -> tuple[object, str]:
        vm = VakVM()
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            result = vm.run(bytecode)
        return result, buffer.getvalue()

    def test_abi_roundtrip_preserves_nested_functions_and_defaults(self):
        source = """
कर्म बनाओ(a):
    कर्म भीतर(b):
        वापस a + b
    वापस भीतर

मान plus = बनाओ(१०)
मुद्रय plus(५)

मान दुगुना = lambda n: n * २
मुद्रय दुगुना(७)

कर्म जोड़ो(a, b=३):
    वापस a + b

मुद्रय जोड़ो(१)
"""
        bytecode = self.compile_source(source)
        roundtripped = Bytecode.from_abi_json(bytecode.to_abi_json())

        _, original_output = self.run_bytecode(bytecode)
        _, roundtrip_output = self.run_bytecode(roundtripped)

        self.assertEqual(roundtrip_output, original_output)
        self.assertEqual(roundtrip_output.splitlines(), ["15", "14", "4"])

    def test_abi_dict_contains_versioned_envelope_and_metadata(self):
        source = """
कर्म योग(a, b):
    वापस a + b
"""
        bytecode = self.compile_source(source, filename="examples/demo.vak")
        abi = bytecode.to_abi_dict()

        self.assertEqual(abi["format"], ABI_FORMAT)
        self.assertEqual(abi["version"], ABI_VERSION)
        self.assertEqual(abi["bytecode"]["source_path"], "examples/demo.vak")
        self.assertIn("योग", abi["bytecode"]["functions"])

    def test_abi_keeps_booleans_distinct_from_integers(self):
        source = """
मुद्रय १
मुद्रय सत्य
मुद्रय ०
मुद्रय असत्य
"""
        bytecode = self.compile_source(source)
        constants = bytecode.to_abi_dict()["bytecode"]["constants"]
        kinds = [item["kind"] for item in constants]

        self.assertGreaterEqual(kinds.count("int"), 2)
        self.assertGreaterEqual(kinds.count("bool"), 2)

    def test_export_abi_cli_helper_writes_valid_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = os.path.join(temp_dir, "prog.vak")
            with open(source_path, "w", encoding="utf-8") as source_file:
                source_file.write("मुद्रय २ + ३\n")

            abi_json = compile_file(source_path)
            roundtripped = Bytecode.from_abi_json(abi_json)
            _, output = self.run_bytecode(roundtripped)
            self.assertEqual(output.strip(), "5")


if __name__ == "__main__":
    unittest.main()
