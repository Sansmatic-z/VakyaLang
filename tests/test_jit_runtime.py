import os
import unittest
from io import StringIO
from contextlib import redirect_stdout
from unittest import mock

from runtime.src.jit_compiler import JITCompiler
from runtime.src.interpreter import VakInterpreter
from runtime.src.vm import VakVM


class JitRuntimeTests(unittest.TestCase):
    def test_jit_defaults_to_observe_only_mode(self):
        jit = JITCompiler(threshold=2)

        jit.track_call("गर्म")
        jit.track_call("गर्म")
        status = jit.status()

        self.assertTrue(jit.is_hot("गर्म"))
        self.assertFalse(jit.runtime_enabled)
        self.assertFalse(jit.should_attempt_compile("गर्म"))
        self.assertEqual(status["mode"], "observe_only")
        self.assertIn("गर्म", status["hot_functions"])

    def test_jit_experimental_runtime_can_be_enabled_explicitly(self):
        jit = JITCompiler(threshold=2, experimental_runtime=True)

        jit.track_call("गर्म")
        jit.track_call("गर्म")

        self.assertTrue(jit.runtime_enabled)
        self.assertTrue(jit.should_attempt_compile("गर्म"))
        self.assertEqual(jit.status()["mode"], "experimental_runtime")

    def test_jit_respects_environment_flag_for_vm_instances(self):
        with mock.patch.dict(os.environ, {"VAK_EXPERIMENTAL_JIT": "1"}, clear=False):
            vm = VakVM(enable_jit=True)

        self.assertTrue(vm.jit.experimental_runtime)
        self.assertTrue(vm.jit.runtime_enabled)

    def test_jit_compiles_supported_compiler_generated_function(self):
        source = """
कर्म गुणा_योग(x, y):
    चर कुल = ०
    यावत् y > ०:
        कुल = कुल + x
        y = y - १
    प्रत्यागच्छ कुल
"""
        interpreter = VakInterpreter()
        bytecode = interpreter.compile_only(source, filename="jit_supported.vak")
        func_bc = bytecode.functions["गुणा_योग"]

        jit = JITCompiler(threshold=1, experimental_runtime=True)
        jit.track_call("गुणा_योग")
        compiled = jit.compile_function("गुणा_योग", func_bc, list(func_bc.constants))

        self.assertIsNotNone(compiled)
        self.assertEqual(compiled.execute({}, 3, 4), 12)
        self.assertIn("JUMP_IF_FALSE", jit.status()["supported_subset"])

    def test_jit_compiles_supported_dict_building_function(self):
        source = """
कर्म सार(x, y):
    प्रत्यागच्छ {"योग": x + y, "गुणन": x * y}
"""
        interpreter = VakInterpreter()
        bytecode = interpreter.compile_only(source, filename="jit_dict_supported.vak")
        func_bc = bytecode.functions["सार"]

        jit = JITCompiler(threshold=1, experimental_runtime=True)
        jit.track_call("सार")
        compiled = jit.compile_function("सार", func_bc, list(func_bc.constants))

        self.assertIsNotNone(compiled)
        self.assertEqual(compiled.execute({}, 2, 3), {"योग": 5, "गुणन": 6})

    def test_jit_benchmark_reports_parity_and_timings(self):
        source = """
कर्म गुणा_योग(x, y):
    चर कुल = ०
    यावत् y > ०:
        कुल = कुल + x
        y = y - १
    प्रत्यागच्छ कुल
"""
        interpreter = VakInterpreter()
        bytecode = interpreter.compile_only(source, filename="jit_benchmark.vak")
        func_bc = bytecode.functions["गुणा_योग"]

        def reference(x, y):
            कुल = 0
            while y > 0:
                कुल += x
                y -= 1
            return कुल

        jit = JITCompiler(threshold=1, experimental_runtime=True)
        jit.track_call("गुणा_योग")
        report = jit.benchmark_function(
            "गुणा_योग",
            func_bc,
            list(func_bc.constants),
            [(3, 4), (5, 6), (7, 8)],
            reference_callable=reference,
            iterations=50,
        )

        self.assertTrue(report["compiled"])
        self.assertTrue(report["parity_ok"])
        self.assertGreater(report["compiled_ms"], 0.0)
        self.assertGreater(report["baseline_ms"], 0.0)
        self.assertIn("गुणा_योग", jit.status()["benchmarked_functions"])
        self.assertIsNotNone(jit.get_stats("गुणा_योग")["benchmark"])

    def test_jit_rejects_unsupported_opcode_instead_of_silent_comment(self):
        source = """
कर्म दिखाओ(x):
    मुद्रय x
    प्रत्यागच्छ x
"""
        interpreter = VakInterpreter()
        bytecode = interpreter.compile_only(source, filename="jit_unsupported.vak")
        func_bc = bytecode.functions["दिखाओ"]

        jit = JITCompiler(threshold=1, experimental_runtime=True)
        jit.track_call("दिखाओ")
        compiled = jit.compile_function("दिखाओ", func_bc, list(func_bc.constants))

        self.assertIsNone(compiled)
        self.assertIn("दिखाओ", jit.status()["rejected_functions"])
        self.assertIn("unsupported opcode", jit.status()["rejected_functions"]["दिखाओ"])

    def test_vm_experimental_jit_executes_supported_function(self):
        source = """
कर्म गुणा_योग(x, y):
    चर कुल = ०
    यावत् y > ०:
        कुल = कुल + x
        y = y - १
    प्रत्यागच्छ कुल

मुद्रय गुणा_योग(३, ४)
"""
        interpreter = VakInterpreter()
        interpreter.vm.jit.call_threshold = 1
        interpreter.vm.jit.experimental_runtime = True

        output = StringIO()
        with redirect_stdout(output):
            interpreter.run(source, filename="jit_runtime.vak")

        self.assertEqual(output.getvalue().strip(), "12")
        self.assertIn("गुणा_योग", interpreter.vm.jit.get_compiled_functions())

    def test_vm_jit_runtime_failure_falls_back_to_vm(self):
        class BadCompiledFunction:
            def execute(self, globals_dict, *args, **kwargs):
                raise RuntimeError("boom")

        source = """
कर्म जोड़(x, y):
    प्रत्यागच्छ x + y

मुद्रय जोड़(२, ५)
"""
        interpreter = VakInterpreter()
        interpreter.vm.jit.call_threshold = 1
        interpreter.vm.jit.experimental_runtime = True
        interpreter.vm.jit.compiled_functions["जोड़"] = BadCompiledFunction()

        output = StringIO()
        with redirect_stdout(output):
            interpreter.run(source, filename="jit_fallback.vak")

        self.assertEqual(output.getvalue().strip(), "7")
        self.assertIn("जोड़", interpreter.vm.jit.status()["rejected_functions"])
        self.assertNotIn("जोड़", interpreter.vm.jit.get_compiled_functions())


if __name__ == "__main__":
    unittest.main()
