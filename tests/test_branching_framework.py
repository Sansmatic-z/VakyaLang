import contextlib
import io
import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from branches.registry import BranchRegistry, create_default_registry
from runtime.src.branching import BranchActivationError, BranchHookContext, VakBranch
from runtime.src.interpreter import VakInterpreter
from runtime.src.vm import VakVM


class BranchingFrameworkTests(unittest.TestCase):
    def test_registry_loads_tree_sentinel_branch(self):
        registry = create_default_registry()
        branch = registry.create("tree_sentinel")

        self.assertEqual(branch.name, "tree_sentinel")
        self.assertEqual(branch.kind, "validation")

    def test_registry_loads_adaptive_rupantar_branch(self):
        registry = create_default_registry()
        branch = registry.create("adaptive_rupantar")

        self.assertEqual(branch.name, "adaptive_rupantar")
        self.assertEqual(branch.kind, "experimental")

    def test_unknown_branch_raises_activation_error(self):
        registry = BranchRegistry()

        with self.assertRaises(BranchActivationError):
            registry.create("does_not_exist")

    def test_tree_sentinel_branch_collects_tree_metadata(self):
        interpreter = VakInterpreter(active_branches=["tree_sentinel"])
        bytecode = interpreter.compile_only("कर्म नमस्ते():\n    प्रत्यागच्छ १\n")
        report = interpreter.get_branch_report()

        self.assertIsNotNone(bytecode)
        self.assertIn("tree_sentinel", report)
        metadata = report["tree_sentinel"]["metadata"]
        self.assertEqual(metadata["root_type"], "Program")
        self.assertGreaterEqual(metadata["top_level_statements"], 1)
        self.assertIn("FuncDecl", metadata["node_counts"])
        self.assertGreater(metadata["bytecode_size"], 0)

    def test_branch_activation_does_not_change_program_output(self):
        source = 'मुद्रय "वृक्ष"\n'

        plain_output = io.StringIO()
        with contextlib.redirect_stdout(plain_output):
            VakInterpreter().run(source)

        branch_output = io.StringIO()
        with contextlib.redirect_stdout(branch_output):
            VakInterpreter(active_branches=["tree_sentinel"]).run(source)

        self.assertEqual(plain_output.getvalue(), branch_output.getvalue())

    def test_runtime_probe_branch_registers_additive_builtin(self):
        interpreter = VakInterpreter(active_branches=["runtime_probe"])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            interpreter.run('मुद्रय _branch_probe()\n')

        report = interpreter.get_branch_report()
        self.assertEqual(output.getvalue().strip(), "runtime-probe")
        self.assertEqual(
            report["runtime_probe"]["metadata"]["builtin_name"],
            "_branch_probe",
        )

    def test_interpreter_keeps_resolved_branch_registry_for_followup_helpers(self):
        interpreter = VakInterpreter(active_branches=["runtime_probe"])

        self.assertIsNotNone(interpreter.branch_registry)
        result = interpreter.rupantar_source("चर संख्या = १\n")

        self.assertIn("runtime_probe", result.active_branches)

    def test_runtime_branch_cannot_override_protected_builtin(self):
        class BadBuiltinOverrideBranch(VakBranch):
            name = "bad_builtin_override"
            kind = "validation"

            def extend_vm_builtins(
                self,
                builtins: dict[str, object],
                context: BranchHookContext,
            ) -> None:
                builtins["मुद्रय"] = lambda *args: None

        registry = create_default_registry()
        registry.register_branch_class(BadBuiltinOverrideBranch)

        with self.assertRaisesRegex(BranchActivationError, "override protected builtins"):
            VakVM(
                enable_jit=False,
                active_branches=["bad_builtin_override"],
                branch_registry=registry,
            )

    def test_chitrakala_branch_keeps_legacy_vm_builtin_surface(self):
        vm = VakVM(enable_jit=False)
        vm.suppress_output = True

        self.assertIn("_chitra_canvas", vm.builtins)
        canvas = vm.builtins["_chitra_canvas"](8, 8, "white")
        self.assertEqual(vm.builtins["_chitra_width"](canvas), 8)
        self.assertEqual(vm.builtins["_chitra_height"](canvas), 8)


if __name__ == "__main__":
    unittest.main()
