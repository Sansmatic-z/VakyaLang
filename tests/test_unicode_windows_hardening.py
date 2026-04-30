import contextlib
import io
import json
import os
import tarfile
import tempfile
import unittest
from pathlib import Path

from runtime.src.interpreter import VakInterpreter
from runtime.tooling.lsp_server import VakLanguageServer
from vpm import VakPackageManager


class UnicodeWindowsHardeningTests(unittest.TestCase):
    def test_lsp_file_uri_decodes_windows_style_devanagari_paths(self):
        server = VakLanguageServer(in_stream=io.BytesIO(), out_stream=io.BytesIO())
        uri = "file:///C:/Temp/%E0%A4%AA%E0%A4%B0%E0%A5%80%E0%A4%95%E0%A5%8D%E0%A4%B7%E0%A4%BE/%E0%A4%A8%E0%A4%AE%E0%A5%82%E0%A4%A8%E0%A4%BE.vak"
        resolved = server._path_from_uri(uri)

        self.assertIn("C:", resolved)
        self.assertTrue(resolved.endswith("नमूना.vak"))

    def test_interpreter_handles_devanagari_module_paths_and_mixed_script_identifiers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            helper_path = temp_root / "सहायक.vak"
            helper_path.write_text(
                "कर्म say_संख्या(x):\n"
                "    प्रत्यागच्छ x * २\n",
                encoding="utf-8",
            )
            main_path = temp_root / "मुख्य.vak"
            source = "आयात सहायक\nमुद्रय सहायक.say_संख्या(३)\n"
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                VakInterpreter().run(source, filename=str(main_path))

            self.assertEqual(buffer.getvalue().strip(), "6")

    def test_vpm_archive_install_supports_devanagari_package_and_module_names(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = VakPackageManager(cwd=temp_dir)
            self.assertTrue(manager.init())

            pkg_dir = Path(temp_dir) / "pkgbuild" / "प्रदर्शन"
            pkg_dir.mkdir(parents=True, exist_ok=True)
            (pkg_dir / "vakya.json").write_text(
                json.dumps(
                    {
                        "नाम": "प्रदर्शन",
                        "संस्करण": "1.0.0",
                        "विवरण": "देवनागरी पैकेज",
                        "फाइलें": ["प्रदर्शन.vak"],
                        "निर्भरताएँ": {},
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            (pkg_dir / "प्रदर्शन.vak").write_text(
                "कर्म नमस्ते():\n"
                "    प्रत्यागच्छ \"देवनागरी\"\n",
                encoding="utf-8",
            )

            archive_path = Path(temp_dir) / "प्रदर्शन.tar.gz"
            with tarfile.open(archive_path, "w:gz") as archive:
                archive.add(pkg_dir, arcname="प्रदर्शन")

            self.assertTrue(manager.install_from_file(str(archive_path)))
            alias_path = Path(temp_dir) / "वाक्_ग्रंथालय" / "प्रदर्शन.vak"
            self.assertTrue(alias_path.exists())

            main_path = Path(temp_dir) / "मुख्य.vak"
            source = "आयात प्रदर्शन\nमुद्रय प्रदर्शन.नमस्ते()\n"
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                VakInterpreter().run(source, filename=str(main_path))
            self.assertEqual(buffer.getvalue().strip(), "देवनागरी")


if __name__ == "__main__":
    unittest.main()
