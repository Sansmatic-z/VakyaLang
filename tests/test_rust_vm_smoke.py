import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from runtime.export_abi import compile_file
from runtime.src.interpreter import VakInterpreter


class RustVmSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cargo_path = shutil.which("cargo") or r"C:\Users\Admin\.cargo\bin\cargo.exe"
        cargo = Path(cargo_path)
        if not cargo.exists():
            raise unittest.SkipTest("cargo.exe not found")

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

    def _run_rust_vak(self, source: str, extra_files: dict[str, str] | None = None) -> list[str]:
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

    def _run_python_vak(self, source: str, extra_files: dict[str, str] | None = None) -> list[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "program.vak"
            source_path.write_text(source, encoding="utf-8")

            for relative_path, contents in (extra_files or {}).items():
                file_path = Path(temp_dir) / relative_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(contents, encoding="utf-8")

            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                VakInterpreter().run(source, filename=str(source_path))
            return buffer.getvalue().splitlines()

    def _assert_python_rust_parity(
        self,
        source: str,
        *,
        extra_files: dict[str, str] | None = None,
        expected: list[str] | None = None,
    ) -> None:
        rust_lines = self._run_rust_vak(source, extra_files=extra_files)
        python_lines = self._run_python_vak(source, extra_files=extra_files)
        self.assertEqual(rust_lines, python_lines)
        if expected is not None:
            self.assertEqual(rust_lines, expected)

    def test_rust_vm_executes_exported_vak_smoke_program(self):
        self._assert_python_rust_parity(
            "मान सूची = [१, २, ३]\nयदि ५ > २:\n    मुद्रय ७ * ६\nमुद्रय सूची\nमुद्रय २ + ३\n",
            expected=["42", "[1, 2, 3]", "5"],
        )

    def test_rust_vm_executes_functions_defaults_and_kwargs(self):
        self._assert_python_rust_parity(
            "कर्म गुणा_जोड़(क, ख=२, ग=१):\n"
            "    वापस क * ख + ग\n"
            "मुद्रय गुणा_जोड़(५)\n"
            "मुद्रय गुणा_जोड़(५, ग=३)\n"
            "मुद्रय गुणा_जोड़(क=४, ख=३, ग=२)\n",
            expected=["11", "13", "14"],
        )

    def test_rust_vm_executes_loops_and_comprehensions(self):
        self._assert_python_rust_parity(
            "मान कुल = ०\n"
            "प्रति क में परास(५):\n"
            "    मान कुल = कुल + क\n"
            "मुद्रय कुल\n"
            "मान वर्ग = [क * क प्रति क में परास(५) यदि क > १]\n"
            "मुद्रय वर्ग\n"
            "मान मानचित्र = {पाठ_कर(क): क * क प्रति क में परास(५) यदि क > २}\n"
            "मुद्रय मानचित्र[\"3\"]\n"
            "मुद्रय दीर्घता(मानचित्र)\n",
            expected=["10", "[4, 9, 16]", "9", "2"],
        )

    def test_rust_vm_executes_classes_methods_and_attributes(self):
        self._assert_python_rust_parity(
            "वर्ग जन:\n"
            "    कर्म __init__(स्वयं, नाम):\n"
            "        स्वयं.नाम = नाम\n"
            "    कर्म बोलो(स्वयं):\n"
            "        वापस स्वयं.नाम\n"
            "मान ज = जन(\"राम\")\n"
            "मुद्रय ज.नाम\n"
            "मुद्रय ज.बोलो()\n",
            expected=["राम", "राम"],
        )

    def test_rust_vm_executes_try_catch_and_with_cleanup(self):
        self._assert_python_rust_parity(
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
            "    मुद्रय \"भीतर\"\n",
            expected=["division by zero", "भीतर", "बंद"],
        )

    def test_rust_vm_executes_imports_via_native_bridge(self):
        self._assert_python_rust_parity(
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
            expected=["25", "14", "सहायक"],
        )

    def test_rust_vm_executes_set_contains_and_slicing(self):
        self._assert_python_rust_parity(
            "मान वस्तु = {१, २, २, ३}\n"
            "मुद्रय २ in वस्तु\n"
            "मुद्रय ८ in वस्तु\n"
            "मुद्रय [१, २, ३, ४][१:४:२]\n"
            "मुद्रय \"vakya\"[१:५:२]\n",
            expected=["True", "False", "[2, 4]", "ay"],
        )

    def test_rust_vm_supports_runtime_type_introspection_builtins(self):
        self._assert_python_rust_parity(
            "वर्ग जन:\n"
            "    कर्म __init__(स्वयं):\n"
            "        स्वयं.नाम = \"राम\"\n"
            "मान ज = जन()\n"
            "मुद्रय hasattr(ज, \"नाम\")\n"
            "मुद्रय hasattr(ज, \"गायब\")\n"
            "मुद्रय isinstance(ज, \"जन\")\n"
            "मुद्रय isinstance([१, २], \"list\")\n"
            "मुद्रय any([असत्य, सत्य])\n"
            "मुद्रय all([सत्य, सत्य])\n",
            expected=["True", "False", "True", "True", "True", "True"],
        )


if __name__ == "__main__":
    unittest.main()
