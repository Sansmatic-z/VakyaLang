import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from runtime.export_abi import compile_file


class RustVmSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cargo = Path(r"C:\Users\Admin\.cargo\bin\cargo.exe")
        assert cargo.exists(), "cargo.exe not found"

        cls.crate_dir = PROJECT_ROOT / "native" / "vakvm-rs"
        subprocess.run(
            [str(cargo), "+stable-x86_64-pc-windows-gnu", "build"],
            cwd=cls.crate_dir,
            check=True,
            capture_output=True,
            text=True,
        )

        cls.exe_path = cls.crate_dir / "target" / "debug" / "vakvm_exec.exe"
        assert cls.exe_path.exists(), "vakvm_exec.exe not built"

    def _run_vak(self, source: str, extra_files: dict[str, str] | None = None) -> list[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "program.vak"
            source_path.write_text(source, encoding="utf-8")

            for relative_path, contents in (extra_files or {}).items():
                file_path = Path(temp_dir) / relative_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(contents, encoding="utf-8")

            abi_path = Path(temp_dir) / "program.abi.json"
            abi_path.write_text(compile_file(source_path), encoding="utf-8")

            env = os.environ.copy()
            env["VAK_PROJECT_ROOT"] = str(PROJECT_ROOT)
            env["VAK_PYTHON"] = sys.executable

            completed = subprocess.run(
                [str(self.exe_path), str(abi_path)],
                cwd=self.crate_dir,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
            )

        return completed.stdout.splitlines()

    def test_rust_vm_executes_exported_vak_smoke_program(self):
        lines = self._run_vak(
            "मान सूची = [१, २, ३]\nयदि ५ > २:\n    मुद्रय ७ * ६\nमुद्रय सूची\nमुद्रय २ + ३\n"
        )
        self.assertEqual(lines, ["42", "[1, 2, 3]", "5"])

    def test_rust_vm_executes_functions_defaults_and_kwargs(self):
        lines = self._run_vak(
            "कर्म गुणा_जोड़(क, ख=२, ग=१):\n"
            "    वापस क * ख + ग\n"
            "मुद्रय गुणा_जोड़(५)\n"
            "मुद्रय गुणा_जोड़(५, ग=३)\n"
            "मुद्रय गुणा_जोड़(क=४, ख=३, ग=२)\n"
        )
        self.assertEqual(lines, ["11", "13", "14"])

    def test_rust_vm_executes_loops_and_comprehensions(self):
        lines = self._run_vak(
            "मान कुल = ०\n"
            "प्रति क में परास(५):\n"
            "    मान कुल = कुल + क\n"
            "मुद्रय कुल\n"
            "मान वर्ग = [क * क प्रति क में परास(५) यदि क > १]\n"
            "मुद्रय वर्ग\n"
            "मान मानचित्र = {पाठ_कर(क): क * क प्रति क में परास(५) यदि क > २}\n"
            "मुद्रय मानचित्र[\"3\"]\n"
            "मुद्रय दीर्घता(मानचित्र)\n"
        )
        self.assertEqual(lines, ["10", "[4, 9, 16]", "9", "2"])

    def test_rust_vm_executes_classes_methods_and_attributes(self):
        lines = self._run_vak(
            "वर्ग जन:\n"
            "    कर्म __init__(स्वयं, नाम):\n"
            "        स्वयं.नाम = नाम\n"
            "    कर्म बोलो(स्वयं):\n"
            "        वापस स्वयं.नाम\n"
            "मान ज = जन(\"राम\")\n"
            "मुद्रय ज.नाम\n"
            "मुद्रय ज.बोलो()\n"
        )
        self.assertEqual(lines, ["राम", "राम"])

    def test_rust_vm_executes_try_catch_and_with_cleanup(self):
        lines = self._run_vak(
            "वर्ग द्वार:\n"
            "    कर्म __enter__(स्वयं):\n"
            "        वापस स्वयं\n"
            "    कर्म __exit__(स्वयं, a, b, c):\n"
            "        मुद्रय \"बंद\"\n"
            "प्रयास:\n"
            "    १ // ०\n"
            "पकड़ो e:\n"
            "    मुद्रय पाठ_कर(e)\n"
            "मान द = द्वार()\n"
            "साथ द जैसे x:\n"
            "    मुद्रय \"भीतर\"\n"
        )
        self.assertEqual(lines, ["division by zero", "भीतर", "बंद"])

    def test_rust_vm_executes_imports_via_native_bridge(self):
        lines = self._run_vak(
            "आयात गणित_विस्तारित\n"
            "आयात सहायक\n"
            "मुद्रय गणित_विस्तारित.वर्ग(५)\n"
            "मुद्रय सहायक.दोगुना(७)\n"
            "मुद्रय सहायक.नाम\n",
            extra_files={
                "सहायक.vak": (
                    "मान नाम = \"सहायक\"\n"
                    "कर्म दोगुना(x):\n"
                    "    वापस x * २\n"
                )
            },
        )
        self.assertEqual(lines[-3:], ["25", "14", "सहायक"])


if __name__ == "__main__":
    unittest.main()
