import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

from runtime.src.codex import build_default_codex
from runtime.src.codex.page import CodexPage
from runtime.src.errors import VMError
from runtime.src.interpreter import VakInterpreter
from runtime.src.vm import VakVM
from vpm import VakPackageManager


class AuditSecurityTests(unittest.TestCase):
    _audit_events: list[tuple[str, tuple[object, ...]]] = []
    _hook_installed = False

    @classmethod
    def setUpClass(cls):
        if not cls._hook_installed:
            def _hook(event, args):
                if isinstance(event, str) and event.startswith("vak."):
                    cls._audit_events.append((event, args))

            sys.addaudithook(_hook)
            cls._hook_installed = True

    def test_branch_runtime_creation_emits_audit_events(self):
        start = len(self._audit_events)
        VakInterpreter(active_branches=["chitrakala"])

        names = [event for event, _ in self._audit_events[start:]]
        self.assertIn("vak.branch.runtime.create", names)
        self.assertIn("vak.branch.activate", names)

    def test_vm_rejects_unsafe_module_name_and_audits_it(self):
        start = len(self._audit_events)
        with self.assertRaisesRegex(VMError, "Unsafe module name"):
            VakVM()._resolve_module_path("../evil", None)

        names = [event for event, _ in self._audit_events[start:]]
        self.assertIn("vak.import.reject", names)

    def test_duplicate_codex_page_name_is_rejected(self):
        class ConflictingVakPage(CodexPage):
            name = "vak"
            description = "conflicting page"
            capabilities = ("conflict",)

            def transform(self, source: str, *, filename: str | None = None):
                raise AssertionError("not expected to run")

        codex = build_default_codex()
        with self.assertRaisesRegex(ValueError, "Duplicate Codex page name"):
            codex.register_page(ConflictingVakPage())

    def test_package_install_from_file_emits_audit_events(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            start = len(self._audit_events)
            manager = VakPackageManager(cwd=temp_dir)
            self.assertTrue(manager.init())

            pkg_dir = Path(temp_dir) / "pkgbuild" / "demo"
            pkg_dir.mkdir(parents=True, exist_ok=True)
            (pkg_dir / "vakya.json").write_text(
                json.dumps(
                    {
                        "नाम": "demo",
                        "संस्करण": "1.0.0",
                        "विवरण": "demo package",
                        "फाइलें": ["demo.vak"],
                        "निर्भरताएँ": {},
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            (pkg_dir / "demo.vak").write_text('मुद्रय "demo"\n', encoding="utf-8")
            archive_path = Path(temp_dir) / "demo.tar.gz"
            with tarfile.open(archive_path, "w:gz") as archive:
                archive.add(pkg_dir, arcname="demo")

            self.assertTrue(manager.install_from_file(str(archive_path)))

            names = [event for event, _ in self._audit_events[start:]]
            self.assertIn("vak.package.install_file.start", names)
            self.assertIn("vak.package.install_file.complete", names)

    def test_missing_python_requirements_file_emits_audit_event(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            start = len(self._audit_events)
            manager = VakPackageManager(cwd=temp_dir)
            self.assertFalse(manager.install_python_deps_from_file(str(Path(temp_dir) / "missing.txt")))

            names = [event for event, _ in self._audit_events[start:]]
            self.assertIn("vak.package.python.install_file.error", names)


if __name__ == "__main__":
    unittest.main()
