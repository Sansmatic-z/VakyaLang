import contextlib
import io
import os
import sys
import unittest
from unittest import mock


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import vak_test_tree


class VakTestTreeTests(unittest.TestCase):
    def test_tree_contains_critical_subsystems(self):
        tree = vak_test_tree.build_test_tree()
        paths = {"/".join(path) for path, _ in vak_test_tree.iter_leaves(tree)}

        self.assertIn("vak-tree/python/unittest-discover", paths)
        self.assertIn("vak-tree/python/month2-3-script", paths)
        self.assertIn("vak-tree/vak/runtime-examples", paths)
        self.assertIn("vak-tree/ecosystem/master-audit", paths)
        self.assertIn("vak-tree/native/rust-tests", paths)

    def test_tree_paths_are_unique_and_valid(self):
        tree = vak_test_tree.build_test_tree()
        vak_test_tree.validate_tree(tree)
        paths = ["/".join(path) for path, _ in vak_test_tree.iter_leaves(tree)]

        self.assertEqual(len(paths), len(set(paths)))
        self.assertGreaterEqual(len(paths), 10)

    def test_find_leaf_supports_full_and_suffix_paths(self):
        tree = vak_test_tree.build_test_tree()

        full_match = vak_test_tree.find_leaf(tree, "vak-tree/python/unittest-discover")
        suffix_match = vak_test_tree.find_leaf(tree, "python/unittest-discover")

        self.assertIsNotNone(full_match)
        self.assertIsNotNone(suffix_match)
        self.assertEqual(full_match[0], suffix_match[0])

    def test_command_specs_use_repo_relative_workdirs(self):
        tree = vak_test_tree.build_test_tree()

        for _, leaf in vak_test_tree.iter_leaves(tree):
            self.assertIsNotNone(leaf.command)
            self.assertTrue(str(leaf.command.cwd).startswith(PROJECT_ROOT))
            self.assertGreaterEqual(len(leaf.command.argv), 1)

    def test_native_leaf_uses_platform_appropriate_cargo_invocation(self):
        tree = vak_test_tree.build_test_tree()
        _, leaf = vak_test_tree.find_leaf(tree, "vak-tree/native/rust-tests")

        self.assertIsNotNone(leaf)
        if vak_test_tree.os.name == "nt":
            self.assertIn("+stable-x86_64-pc-windows-gnu", leaf.command.argv)
        else:
            self.assertNotIn("+stable-x86_64-pc-windows-gnu", leaf.command.argv)

    def test_run_leaf_marks_missing_executable_as_skipped(self):
        leaf = vak_test_tree.TestNode(
            name="missing-tool",
            description="Synthetic missing executable leaf",
            command=vak_test_tree.CommandSpec(
                argv=("missing-executable",),
                cwd=vak_test_tree.REPO_ROOT,
            ),
        )

        with mock.patch("vak_test_tree.subprocess.run", side_effect=FileNotFoundError("missing-executable")):
            with contextlib.redirect_stdout(io.StringIO()):
                result = vak_test_tree._run_leaf(("vak-tree", "synthetic", "missing-tool"), leaf)

        self.assertTrue(result["skipped"])
        self.assertFalse(result["passed"])
        self.assertEqual(result["returncode"], None)


if __name__ == "__main__":
    unittest.main()
