import contextlib
import io
import os
import sys
import tempfile
import unittest


if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime.src.interpreter import VakInterpreter
from runtime.src.vibhakti import VibhaktiCase, VibhaktiProof


class ProductionReadinessTests(unittest.TestCase):
    _audit_events = []
    _hook_installed = False

    @classmethod
    def setUpClass(cls):
        if not cls._hook_installed:
            def _hook(event, args):
                if isinstance(event, str) and event.startswith("vak."):
                    cls._audit_events.append((event, args))

            sys.addaudithook(_hook)
            cls._hook_installed = True

    def run_source(self, source: str, filename: str | None = None):
        interpreter = VakInterpreter()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = interpreter.run(source, filename=filename)
        return result, output.getvalue()

    def test_vibhakti_proof_requires_matching_roles(self):
        valid = VibhaktiProof(
            function_name="योग",
            proof_type="commutativity",
            roles_involved=[VibhaktiCase.KARMA, VibhaktiCase.KARMA],
            proof_evidence="same semantic role on both operands",
        )
        invalid = VibhaktiProof(
            function_name="दान",
            proof_type="commutativity",
            roles_involved=[VibhaktiCase.KARTA, VibhaktiCase.KARMA],
            proof_evidence="mixed roles cannot commute",
        )

        self.assertTrue(valid.verify())
        self.assertIsNotNone(valid.certificate)
        self.assertFalse(invalid.verify())
        self.assertIsNotNone(invalid.certificate_payload)

    def test_audit_events_are_emitted_for_file_and_import_activity(self):
        start = len(self._audit_events)

        with tempfile.TemporaryDirectory() as temp_dir:
            module_path = os.path.join(temp_dir, "गणना.vak")
            with open(module_path, "w", encoding="utf-8") as handle:
                handle.write('कर्म उत्तर():\n    वापस ४२\n')

            data_path = os.path.join(temp_dir, "data.txt")
            vak_data_path = data_path.replace("\\", "/")
            source = f'''
लेखन("{vak_data_path}", "नमस्ते")
मुद्रय पठन("{vak_data_path}")
आयात गणना
मुद्रय गणना.उत्तर()
'''
            _, output = self.run_source(source, filename=os.path.join(temp_dir, "main.vak"))
            self.assertIn("नमस्ते", output)
            self.assertIn("42", output)

        events = self._audit_events[start:]
        event_names = [name for name, _ in events]
        self.assertIn("vak.file.write", event_names)
        self.assertIn("vak.file.read", event_names)
        self.assertIn("vak.import.module", event_names)
        self.assertIn("vak.interpreter.run.start", event_names)
        self.assertIn("vak.interpreter.run.complete", event_names)

    def test_proof_audit_events_are_emitted_for_compile_time_verification(self):
        start = len(self._audit_events)
        interpreter = VakInterpreter()
        source = """
सिद्धि: अभाज्य_है(१७)
    प्रमाण:
        मान x = २
        यावत् x < ५:
            यदि १७ % x == ०:
                उत्क्षिप "भाजक मिला"
            x = x + १
"""
        bytecode = interpreter.compile_only(source, filename="proof_test.vak")
        self.assertIsNotNone(bytecode)

        events = self._audit_events[start:]
        event_names = [name for name, _ in events]
        self.assertIn("vak.proof.verify.start", event_names)
        self.assertIn("vak.proof.verify.complete", event_names)

    def test_pyproject_includes_runtime_dependency_packages_and_resources(self):
        pyproject_path = os.path.join(PROJECT_ROOT, "pyproject.toml")
        with open(pyproject_path, "rb") as handle:
            data = tomllib.load(handle)

        package_include = data["tool"]["setuptools"]["packages"]["find"]["include"]
        package_data = data["tool"]["setuptools"]["package-data"]
        dev_deps = data["project"]["optional-dependencies"]["dev"]

        self.assertIn("sansmatic*", package_include)
        self.assertIn("atmalipi*", package_include)
        self.assertIn("stdlib/*.vak", package_data["runtime"])
        self.assertTrue(any(dep.startswith("build") for dep in dev_deps))
        self.assertTrue(any(dep.startswith("twine") for dep in dev_deps))

    def test_production_scaffolding_files_exist(self):
        required_paths = [
            ".env.example",
            "Dockerfile",
            "docker-compose.yml",
            os.path.join(".github", "workflows", "sansmatic-production.yml"),
            os.path.join("docs", "sansmatic_production_architecture.md"),
            os.path.join("docs", "sansmatic_api.md"),
        ]

        for relative_path in required_paths:
            self.assertTrue(
                os.path.exists(os.path.join(PROJECT_ROOT, relative_path)),
                relative_path,
            )


if __name__ == "__main__":
    unittest.main()
