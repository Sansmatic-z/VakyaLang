import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from branches.registry import BranchRegistry, create_default_registry
from runtime.src.branching import BranchActivationError


class BranchAdmissionTests(unittest.TestCase):
    def test_default_registry_discovers_registered_branch_manifests(self):
        registry = create_default_registry()
        report = registry.branch_report()

        self.assertIn("chitrakala", report)
        self.assertEqual(report["chitrakala"]["state"], "registered")
        self.assertEqual(report["chitrakala"]["manifest"]["entrypoint"], "branches.chitrakala")

    def test_default_branch_names_come_from_verified_manifests(self):
        registry = create_default_registry()

        self.assertEqual(registry.default_branch_names(), ("chitrakala",))

    def test_invalid_manifest_is_quarantined(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            branch_root = Path(temp_dir)
            bad_dir = branch_root / "bad_branch"
            bad_dir.mkdir()
            (bad_dir / "__init__.py").write_text("", encoding="utf-8")
            (bad_dir / "branch.json").write_text(
                json.dumps(
                    {
                        "name": "bad_branch",
                        "version": "1.0.0",
                        "api_version": "999",
                        "kind": "runtime",
                        "entrypoint": "branches.bad_branch",
                        "capabilities": ["vm_builtins"],
                    }
                ),
                encoding="utf-8",
            )

            registry = BranchRegistry(branch_root=branch_root)
            report = registry.branch_report()

            self.assertEqual(report["bad_branch"]["state"], "quarantined")
            self.assertTrue(report["bad_branch"]["issues"])
            with self.assertRaisesRegex(BranchActivationError, "quarantined"):
                registry.create("bad_branch")

    def test_resolve_names_adds_verified_dependencies(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            branch_root = Path(temp_dir)
            self._write_branch_manifest(branch_root, "base")
            self._write_branch_manifest(branch_root, "dependent", depends_on=["base"])

            registry = BranchRegistry(branch_root=branch_root)

            self.assertEqual(registry.resolve_names(["dependent"]), ["base", "dependent"])

    def test_resolve_names_rejects_conflicting_branches(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            branch_root = Path(temp_dir)
            self._write_branch_manifest(branch_root, "left", conflicts_with=["right"])
            self._write_branch_manifest(branch_root, "right")

            registry = BranchRegistry(branch_root=branch_root)

            with self.assertRaisesRegex(BranchActivationError, "conflicts with active branches"):
                registry.resolve_names(["left", "right"])

    def test_dependency_cycle_is_quarantined(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            branch_root = Path(temp_dir)
            self._write_branch_manifest(branch_root, "alpha", depends_on=["beta"])
            self._write_branch_manifest(branch_root, "beta", depends_on=["alpha"])

            registry = BranchRegistry(branch_root=branch_root)
            report = registry.branch_report()

            self.assertEqual(report["alpha"]["state"], "quarantined")
            self.assertEqual(report["beta"]["state"], "quarantined")
            with self.assertRaisesRegex(BranchActivationError, "quarantined"):
                registry.resolve_names(["alpha"])

    def _write_branch_manifest(
        self,
        branch_root: Path,
        name: str,
        *,
        kind: str = "runtime",
        depends_on: list[str] | None = None,
        conflicts_with: list[str] | None = None,
        default_activation: bool = False,
    ) -> None:
        branch_dir = branch_root / name
        branch_dir.mkdir()
        (branch_dir / "__init__.py").write_text("", encoding="utf-8")
        (branch_dir / "branch.json").write_text(
            json.dumps(
                {
                    "name": name,
                    "version": "1.0.0",
                    "api_version": "1",
                    "kind": kind,
                    "entrypoint": f"branches.{name}",
                    "capabilities": ["vm_builtins"] if kind == "runtime" else [],
                    "depends_on": depends_on or [],
                    "conflicts_with": conflicts_with or [],
                    "default_activation": default_activation,
                }
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
