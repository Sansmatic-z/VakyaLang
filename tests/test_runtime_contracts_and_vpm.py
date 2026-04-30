import contextlib
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
import warnings
from pathlib import Path

from runtime.src.compiler import Compiler
from runtime.src.errors import CompileError, VMError, format_vak_error
from runtime.src.interpreter import VakInterpreter
from runtime.src.lexer import Lexer
from runtime.src.parser import Parser
from runtime.src.vm import VakVM
from vpm import VakPackageManager


class RuntimeContractsAndVpmTests(unittest.TestCase):
    def compile_source(self, source: str):
        return Compiler().compile(Parser(Lexer(source).tokenize()).parse())

    def test_runtime_enforces_dynamic_parameter_type_hints(self):
        source = """
कर्म संख्या_दोगुना(x: संख्या):
    प्रत्यागच्छ x * २

कर्म लागू(f, value):
    प्रत्यागच्छ f(value)

लागू(संख्या_दोगुना, "गलत")
"""
        with self.assertRaisesRegex(VMError, "parameter 'x'"):
            VakInterpreter().run(source)

    def test_runtime_enforces_dynamic_refinement_parameter_hints(self):
        source = """
कर्म अगला(x: परिशुद्ध[संख्या, धनात्मक_है]):
    प्रत्यागच्छ x + १

कर्म लागू(f, value):
    प्रत्यागच्छ f(value)

लागू(अगला, -१)
"""
        with self.assertRaisesRegex(VMError, "धनात्मक_है"):
            VakInterpreter().run(source)

    def test_runtime_enforces_dynamic_return_type_hints(self):
        source = """
कर्म नाम_बनाओ(value) → तार:
    प्रत्यागच्छ value

कर्म लागू(f, value):
    प्रत्यागच्छ f(value)

लागू(नाम_बनाओ, १)
"""
        with self.assertRaisesRegex(VMError, "return value of 'नाम_बनाओ'"):
            VakInterpreter().run(source)

    def test_runtime_rejects_missing_required_dynamic_argument(self):
        source = """
कर्म जोड़(x: संख्या, y: संख्या):
    प्रत्यागच्छ x + y

कर्म लागू(f, value):
    प्रत्यागच्छ f(value)

लागू(जोड़, १)
"""
        with self.assertRaisesRegex(VMError, "Missing required argument: y"):
            VakInterpreter().run(source)

    def test_runtime_rejects_extra_positional_dynamic_argument(self):
        source = """
कर्म जोड़(x: संख्या, y: संख्या):
    प्रत्यागच्छ x + y

कर्म लागू_त्रय(f, a, b, c):
    प्रत्यागच्छ f(a, b, c)

लागू_त्रय(जोड़, १, २, ३)
"""
        with self.assertRaisesRegex(VMError, "Too many positional arguments"):
            VakInterpreter().run(source)

    def test_package_install_from_archive_creates_importable_entrypoint(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = VakPackageManager(cwd=temp_dir)
            self.assertTrue(manager.init())

            pkg_dir = os.path.join(temp_dir, "pkgbuild", "demo")
            os.makedirs(pkg_dir, exist_ok=True)
            with open(os.path.join(pkg_dir, "vakya.json"), "w", encoding="utf-8") as manifest_file:
                json.dump(
                    {
                        "नाम": "demo",
                        "संस्करण": "1.0.0",
                        "विवरण": "demo package",
                        "फाइलें": ["demo.vak"],
                        "निर्भरताएँ": {},
                    },
                    manifest_file,
                    ensure_ascii=False,
                    indent=2,
                )
            with open(os.path.join(pkg_dir, "demo.vak"), "w", encoding="utf-8") as module_file:
                module_file.write("कर्म दुगुना(x):\n    प्रत्यागच्छ x * २\n")

            archive_path = os.path.join(temp_dir, "demo.tar.gz")
            with tarfile.open(archive_path, "w:gz") as archive:
                archive.add(pkg_dir, arcname="demo")

            self.assertTrue(manager.install_from_file(archive_path))
            self.assertTrue(os.path.exists(os.path.join(temp_dir, "वाक्_ग्रंथालय", "demo.vak")))

            source = "आयात demo\nमुद्रय demo.दुगुना(५)\n"
            buffer = io.StringIO()
            main_path = os.path.join(temp_dir, "main.vak")
            with contextlib.redirect_stdout(buffer):
                VakInterpreter().run(source, filename=main_path)
            self.assertEqual(buffer.getvalue().strip(), "10")

    def test_package_install_from_archive_avoids_tar_extract_deprecation_warning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = VakPackageManager(cwd=temp_dir)
            self.assertTrue(manager.init())

            pkg_dir = os.path.join(temp_dir, "pkgbuild", "demo")
            os.makedirs(pkg_dir, exist_ok=True)
            with open(os.path.join(pkg_dir, "vakya.json"), "w", encoding="utf-8") as manifest_file:
                json.dump(
                    {
                        "नाम": "demo",
                        "संस्करण": "1.0.0",
                        "विवरण": "demo package",
                        "फाइलें": ["demo.vak"],
                        "निर्भरताएँ": {},
                    },
                    manifest_file,
                    ensure_ascii=False,
                    indent=2,
                )
            with open(os.path.join(pkg_dir, "demo.vak"), "w", encoding="utf-8") as module_file:
                module_file.write('मुद्रय "demo"\n')

            archive_path = os.path.join(temp_dir, "demo.tar.gz")
            with tarfile.open(archive_path, "w:gz") as archive:
                archive.add(pkg_dir, arcname="demo")

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                self.assertTrue(manager.install_from_file(archive_path))

            self.assertFalse(
                any(item.category is DeprecationWarning for item in caught),
                msg=[str(item.message) for item in caught],
            )

    def test_lockfile_records_package_hashes_and_python_dependencies(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = VakPackageManager(cwd=temp_dir)
            self.assertTrue(manager.init())

            pkg_dir = os.path.join(temp_dir, "pkgbuild", "demo")
            os.makedirs(pkg_dir, exist_ok=True)
            with open(os.path.join(pkg_dir, "vakya.json"), "w", encoding="utf-8") as manifest_file:
                json.dump(
                    {
                        "नाम": "demo",
                        "संस्करण": "1.0.0",
                        "विवरण": "demo package",
                        "फाइलें": ["demo.vak"],
                        "निर्भरताएँ": {},
                    },
                    manifest_file,
                    ensure_ascii=False,
                    indent=2,
                )
            with open(os.path.join(pkg_dir, "demo.vak"), "w", encoding="utf-8") as module_file:
                module_file.write("मुद्रय १\n")

            archive_path = os.path.join(temp_dir, "demo.tar.gz")
            with tarfile.open(archive_path, "w:gz") as archive:
                archive.add(pkg_dir, arcname="demo")

            self.assertTrue(manager.install_from_file(archive_path))
            manager._save_python_dep("requests>=2")
            payload = manager.write_lockfile()

            self.assertEqual(payload["python_dependencies"], ["requests>=2"])
            self.assertEqual(len(payload["packages"]), 1)
            package = payload["packages"][0]
            self.assertEqual(package["नाम"], "demo")
            self.assertIn("manifest_sha256", package)
            self.assertEqual(package["files"][0]["path"], "demo.vak")
            self.assertIn("sha256", package["files"][0])

    def test_cache_info_and_clear_cache_report_cached_metadata_and_archives(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = VakPackageManager(cwd=temp_dir)
            self.assertTrue(manager.init())
            metadata = {
                "नाम": "demo",
                "संस्करण": "1.0.0",
                "विवरण": "cached demo",
                "फाइलें": ["demo.vak"],
                "निर्भरताएँ": {},
            }
            manager._cache_metadata("demo", metadata)
            archive_path = os.path.join(temp_dir, "demo.vakpkg")
            with open(archive_path, "wb") as archive_file:
                archive_file.write(b"vak archive payload")
            self.assertIsNotNone(manager._cache_archive(archive_path))

            info = manager.cache_info()
            self.assertEqual(info["metadata_files"], 1)
            self.assertEqual(info["archive_files"], 1)
            self.assertGreater(info["size_bytes"], 0)

            self.assertTrue(manager.clear_cache())
            cleared = manager.cache_info()
            self.assertEqual(cleared["metadata_files"], 0)
            self.assertEqual(cleared["archive_files"], 0)

    def test_package_update_refreshes_dependency_and_lockfile(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = VakPackageManager(cwd=temp_dir)
            self.assertTrue(manager.init())

            versions = {"demo": "1.0.0"}

            def fake_fetch(package_name, version=None):
                return {
                    "नाम": package_name,
                    "संस्करण": versions[package_name],
                    "विवरण": f"{package_name} package",
                    "फाइलें": [f"{package_name}.vak"],
                    "निर्भरताएँ": {},
                }

            def fake_download(package_name, metadata, package_path):
                os.makedirs(package_path, exist_ok=True)
                with open(os.path.join(package_path, "vakya.json"), "w", encoding="utf-8") as manifest_file:
                    json.dump(metadata, manifest_file, ensure_ascii=False, indent=2)
                with open(os.path.join(package_path, f"{package_name}.vak"), "w", encoding="utf-8") as module_file:
                    module_file.write(f'मुद्रय "{metadata["संस्करण"]}"\n')
                manager._sync_module_entrypoint(package_name, metadata, package_path)

            manager._fetch_package_metadata = fake_fetch  # type: ignore[method-assign]
            manager._download_package = fake_download  # type: ignore[method-assign]

            self.assertTrue(manager.install("demo"))
            self.assertEqual(manager._get_installed_version("demo"), "1.0.0")

            versions["demo"] = "2.0.0"
            self.assertTrue(manager.update("demo"))
            self.assertEqual(manager._get_installed_version("demo"), "2.0.0")

            with open(manager.lockfile_path, "r", encoding="utf-8") as lockfile:
                payload = json.load(lockfile)
            self.assertEqual(payload["packages"][0]["संस्करण"], "2.0.0")

    def test_remove_python_dependency_updates_lockfile(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = VakPackageManager(cwd=temp_dir)
            self.assertTrue(manager.init())
            manager._save_python_dep("requests>=2")
            manager._save_python_dep("rich>=13")
            manager.write_lockfile()

            self.assertTrue(manager.remove_python_dep("requests"))
            self.assertEqual(manager.list_python_deps(), ["rich>=13"])

            with open(manager.lockfile_path, "r", encoding="utf-8") as lockfile:
                payload = json.load(lockfile)
            self.assertEqual(payload["python_dependencies"], ["rich>=13"])

    def test_package_install_from_archive_requires_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = VakPackageManager(cwd=temp_dir)
            self.assertTrue(manager.init())

            archive_path = os.path.join(temp_dir, "missing-manifest.tar.gz")
            with tarfile.open(archive_path, "w:gz") as archive:
                payload = 'मुद्रय "oops"\n'.encode("utf-8")
                info = tarfile.TarInfo("demo/demo.vak")
                info.size = len(payload)
                archive.addfile(info, io.BytesIO(payload))

            self.assertFalse(manager.install_from_file(archive_path))

    def test_cli_run_passes_source_filename_for_package_resolution(self):
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        vak_cli = os.path.join(repo_root, "vak.py")

        with tempfile.TemporaryDirectory() as temp_dir:
            manager = VakPackageManager(cwd=temp_dir)
            manager.init()

            pkg_dir = os.path.join(temp_dir, "pkgbuild", "demo")
            os.makedirs(pkg_dir, exist_ok=True)
            with open(os.path.join(pkg_dir, "vakya.json"), "w", encoding="utf-8") as manifest_file:
                json.dump(
                    {
                        "नाम": "demo",
                        "संस्करण": "1.0.0",
                        "विवरण": "demo package",
                        "फाइलें": ["demo.vak"],
                        "निर्भरताएँ": {},
                    },
                    manifest_file,
                    ensure_ascii=False,
                    indent=2,
                )
            with open(os.path.join(pkg_dir, "demo.vak"), "w", encoding="utf-8") as module_file:
                module_file.write("कर्म दुगुना(x):\n    प्रत्यागच्छ x * २\n")

            archive_path = os.path.join(temp_dir, "demo.tar.gz")
            with tarfile.open(archive_path, "w:gz") as archive:
                archive.add(pkg_dir, arcname="demo")
            self.assertTrue(manager.install_from_file(archive_path))

            main_path = os.path.join(temp_dir, "main.vak")
            with open(main_path, "w", encoding="utf-8") as main_file:
                main_file.write("आयात demo\nमुद्रय demo.दुगुना(६)\n")

            completed = subprocess.run(
                [sys.executable, vak_cli, main_path],
                cwd=repo_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout.strip(), "12")

    def test_package_install_rejects_path_traversal_archive(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = VakPackageManager(cwd=temp_dir)
            manager.init()

            archive_path = os.path.join(temp_dir, "unsafe.tar.gz")
            with tarfile.open(archive_path, "w:gz") as archive:
                payload = b"escaped"
                info = tarfile.TarInfo("../evil.txt")
                info.size = len(payload)
                archive.addfile(info, io.BytesIO(payload))

            self.assertFalse(manager.install_from_file(archive_path))
            self.assertFalse(os.path.exists(os.path.join(temp_dir, "evil.txt")))

    def test_format_vak_error_uses_bilingual_categories(self):
        compile_error = CompileError("गलत", 3)
        runtime_error = VMError("boom")
        self.assertIn("संकलन त्रुटि (Compile Error)", format_vak_error(compile_error))
        self.assertIn("चालना त्रुटि (Runtime Error)", format_vak_error(runtime_error))

    def test_bundle_command_uses_runtime_stdlib_after_dev_quarantine(self):
        repo_root = Path(__file__).resolve().parents[1]
        vpm_cli = repo_root / "vpm.py"

        with tempfile.TemporaryDirectory() as temp_dir:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(vpm_cli),
                    "bundle",
                    "--lib",
                    "रंग_पुस्तकालय",
                    "--output",
                    temp_dir,
                ],
                cwd=repo_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(completed.returncode, 0, msg=completed.stderr or completed.stdout)
            package_path = Path(temp_dir) / "रंग_पुस्तकालय-1.0.0.tar.gz"
            self.assertTrue(package_path.exists(), msg=completed.stdout)


if __name__ == "__main__":
    unittest.main()
