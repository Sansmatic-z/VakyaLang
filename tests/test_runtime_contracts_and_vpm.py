import contextlib
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest

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


if __name__ == "__main__":
    unittest.main()
