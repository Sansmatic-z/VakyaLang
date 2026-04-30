#!/usr/bin/env python3
# वाक् कंपाइलर बूटस्ट्रैप — Bootstrap the Self-Hosting Compiler
#
# ═══════════════════════════════════════════════════════════════════════════
# Signature: Visionary RM (Raj Mitra) ⚡
# "Bootstrapping the Self-Hosting Compiler" 🔥
# ═══════════════════════════════════════════════════════════════════════════
#
# Month 2-3 Advanced Features: Self-Hosting Compiler
# 
# Stage 1: Python compiler compiles compiler.vak → compiler.vakc
# Stage 2: compiler.vakc can now compile itself
#
# © 2026 Raj Mitra (Visionary RM)

import subprocess
import sys
import os
import hashlib
import tempfile
import shutil
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))
vaklan_root = os.path.dirname(script_dir)
python_executable = sys.executable or "python"


def _subprocess_env():
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def _run_subprocess(args, *, cwd, env=None):
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env or _subprocess_env(),
        cwd=cwd,
    )


def _file_hash(path: str | Path) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _run_bootstrap_driver(
    vak_py: str,
    driver_path: str,
    input_path: str,
    output_path: str,
    *,
    mode: str = "compile",
    second_output_path: str | None = None,
):
    env = _subprocess_env()
    env["VAK_BOOTSTRAP_MODE"] = mode
    env["VAK_BOOTSTRAP_INPUT"] = str(input_path)
    env["VAK_BOOTSTRAP_OUTPUT"] = str(output_path)
    if second_output_path is not None:
        env["VAK_BOOTSTRAP_OUTPUT_SECOND"] = str(second_output_path)
    return _run_subprocess([python_executable, vak_py, driver_path], cwd=vaklan_root, env=env)


def _run_bootstrap_repro(vak_py: str, driver_path: str, input_path: str, output_a: str, output_b: str):
    env = _subprocess_env()
    env["VAK_BOOTSTRAP_MODE"] = "repro"
    env["VAK_BOOTSTRAP_INPUT"] = str(input_path)
    env["VAK_BOOTSTRAP_OUTPUT"] = str(output_a)
    env["VAK_BOOTSTRAP_OUTPUT_SECOND"] = str(output_b)
    return _run_subprocess([python_executable, vak_py, driver_path], cwd=vaklan_root, env=env)


def _compile_with_python(vak_py: str, input_path: str):
    return _run_subprocess([python_executable, vak_py, "--compile", input_path], cwd=vaklan_root)


def _assert_matching_artifacts(left_path: str | Path, right_path: str | Path):
    left_path = Path(left_path)
    right_path = Path(right_path)
    left_meta = Path(str(left_path) + ".meta.json")
    right_meta = Path(str(right_path) + ".meta.json")
    if not left_path.exists() or not right_path.exists():
        raise AssertionError("Compiled artifact missing during bootstrap verification")
    if not left_meta.exists() or not right_meta.exists():
        raise AssertionError("Metadata artifact missing during bootstrap verification")
    left_hash = _file_hash(left_path)
    right_hash = _file_hash(right_path)
    left_meta_hash = _file_hash(left_meta)
    right_meta_hash = _file_hash(right_meta)
    if left_hash != right_hash:
        raise AssertionError(f"Compiled bytecode hash mismatch: {left_hash} != {right_hash}")
    if left_meta_hash != right_meta_hash:
        raise AssertionError(
            f"Compiled metadata hash mismatch: {left_meta_hash} != {right_meta_hash}"
        )
    return {
        "byte_hash": left_hash,
        "meta_hash": left_meta_hash,
    }


def bootstrap():
    """
    Bootstrap the VakyaLang compiler.
    
    This script:
    1. Uses the Python-based VakyaLang compiler to compile compiler.vak
    2. Verifies the compiled bytecode and metadata
    3. Compares source execution vs compiled execution
    4. Verifies reproducible compiler output
    """
    print("═" * 70)
    print("   Bootstrapping VakyaLang Compiler")
    print("   © 2026 Raj Mitra (Visionary RM)")
    print("═" * 70)
    
    # Check if vak.py exists
    vak_py = os.path.join(vaklan_root, "vak.py")
    if not os.path.exists(vak_py):
        print(f"❌ Error: vak.py not found at {vak_py}")
        sys.exit(1)
    
    # Check if compiler.vak exists
    compiler_vak = os.path.join(script_dir, "compiler.vak")
    if not os.path.exists(compiler_vak):
        print(f"❌ Error: compiler.vak not found at {compiler_vak}")
        sys.exit(1)
    
    # ──────────────────────────────────────────────────────────────────────
    # Stage 1: Use Python compiler to compile compiler.vak
    # ──────────────────────────────────────────────────────────────────────
    print("\n📌 Stage 1: Compiling compiler.vak with Python...")
    print(f"   Command: {python_executable} {vak_py} --compile {compiler_vak}")
    
    result = _compile_with_python(vak_py, compiler_vak)
    
    if result.returncode != 0:
        print(f"❌ Compilation failed:")
        print(f"   STDOUT: {result.stdout}")
        print(f"   STDERR: {result.stderr}")
        sys.exit(1)
    
    compiler_vakc = os.path.join(script_dir, "compiler.vakc")
    compiler_meta = compiler_vakc + ".meta.json"
    if not os.path.exists(compiler_vakc):
        print("❌ No .vakc file generated")
        sys.exit(1)

    print("✓ compiler.vakc generated")
    print(f"   Found compiled bytecode: {compiler_vakc}")
    first_hash = _file_hash(compiler_vakc)
    print(f"   SHA256: {first_hash}")
    first_meta_hash = _file_hash(compiler_meta)
    print(f"   META SHA256: {first_meta_hash}")
    if os.path.exists(compiler_meta):
        print(f"   Found metadata sidecar: {compiler_meta}")

    # ──────────────────────────────────────────────────────────────────────
    # Stage 2: Verify the compiled bytecode
    # ──────────────────────────────────────────────────────────────────────
    print("\n📌 Stage 2: Verifying compiled bytecode...")

    result = _run_subprocess(
        [python_executable, vak_py, compiler_vakc, "--disassemble"],
        cwd=vaklan_root,
    )

    if result.returncode != 0:
        print(f"❌ Disassembly failed:")
        print(f"   STDERR: {result.stderr}")
        sys.exit(1)

    print("✓ Bytecode disassembly successful")
    print("\n--- Disassembly Output ---")
    print(result.stdout[:500])

    # ──────────────────────────────────────────────────────────────────────
    # Stage 3: Run the compiler.vak directly and use it as a bootstrap driver
    # ──────────────────────────────────────────────────────────────────────
    print("\n📌 Stage 3: Running compiler.vak directly...")

    result = _run_subprocess([python_executable, vak_py, compiler_vak], cwd=vaklan_root)

    if result.returncode != 0:
        print("❌ Source execution failed:")
        print(f"   STDERR: {result.stderr[:500]}")
        sys.exit(1)

    source_output = result.stdout
    print("✓ Source execution successful")
    print("\n--- Compiler Output ---")
    print(source_output)

    # ──────────────────────────────────────────────────────────────────────
    # Stage 4: Use compiler.vak and compiler.vakc as bootstrap drivers
    # ──────────────────────────────────────────────────────────────────────
    print("\n📌 Stage 4: Verifying source/compiled bootstrap driver compilation...")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        sample_source = temp_root / "bootstrap_sample.vak"
        sample_source.write_text(
            "\n".join(
                [
                    "कर्म जोड़ो(अ, ब=३):",
                    "    प्रत्यागच्छ अ + ब",
                    "मुद्रय जोड़ो(७)",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        expected_sample = temp_root / "expected_sample.vakc"
        expected_self = temp_root / "expected_self.vakc"
        expected_native = temp_root / "expected_native.vakc"
        source_sample = temp_root / "source_sample.vakc"
        source_self = temp_root / "source_self.vakc"
        source_native = temp_root / "source_native.vakc"
        compiled_sample = temp_root / "compiled_sample.vakc"
        compiled_self = temp_root / "compiled_self.vakc"
        compiled_native = temp_root / "compiled_native.vakc"
        native_repro_a = temp_root / "native_repro_a.vakc"
        native_repro_b = temp_root / "native_repro_b.vakc"
        source_repro_a = temp_root / "source_repro_a.vakc"
        source_repro_b = temp_root / "source_repro_b.vakc"
        compiled_repro_a = temp_root / "compiled_repro_a.vakc"
        compiled_repro_b = temp_root / "compiled_repro_b.vakc"
        native_source = temp_root / "native_control_sample.vak"

        expected_sample_result = _compile_with_python(vak_py, str(sample_source))
        if expected_sample_result.returncode != 0:
            print("❌ Direct Python compile failed for sample source:")
            print(expected_sample_result.stderr or expected_sample_result.stdout)
            sys.exit(1)
        shutil.copyfile(sample_source.with_suffix(".vakc"), expected_sample)
        shutil.copyfile(
            sample_source.with_suffix(".vakc.meta.json"),
            Path(str(expected_sample) + ".meta.json"),
        )

        expected_self_result = _compile_with_python(vak_py, compiler_vak)
        if expected_self_result.returncode != 0:
            print("❌ Direct Python compile failed for compiler.vak:")
            print(expected_self_result.stderr or expected_self_result.stdout)
            sys.exit(1)
        shutil.copyfile(Path(compiler_vakc), expected_self)
        shutil.copyfile(Path(compiler_meta), Path(str(expected_self) + ".meta.json"))

        native_source.write_text(
            "\n".join(
                [
                    "कर्म फल(n):",
                    "    यदि n <= १:",
                    "        प्रत्यागच्छ १",
                    "    अन्यथा:",
                    "        प्रत्यागच्छ n * फल(n - १)",
                    "चर युग्म = (७, ८)",
                    "चर पहला, दूसरा = युग्म",
                    "चर items = [१, २, ३]",
                    "चर कुल = ०",
                    "प्रत्येक चर item अन्तर्गत items:",
                    "    कुल = कुल + item",
                    "चर जोड़े = [(१, १०), (२, २०)]",
                    "प्रत्येक चर क्रम, मूल्य अन्तर्गत जोड़े:",
                    "    कुल = कुल + क्रम + मूल्य",
                    'चर mapping = {"फल": फल(५), "योग": कुल}',
                    "चर tags = {१, २, ३}",
                    "चर tag_count = ०",
                    "प्रत्येक चर tag अन्तर्गत tags:",
                    "    tag_count = tag_count + १",
                    "मुद्रय पहला",
                    "मुद्रय दूसरा",
                    'मुद्रय mapping["फल"]',
                    'मुद्रय mapping["योग"]',
                    "मुद्रय tag_count",
                    "मुद्रय कुल",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        expected_native_result = _compile_with_python(vak_py, str(native_source))
        if expected_native_result.returncode != 0:
            print("❌ Direct Python compile failed for native subset sample:")
            print(expected_native_result.stderr or expected_native_result.stdout)
            sys.exit(1)
        shutil.copyfile(native_source.with_suffix(".vakc"), expected_native)
        shutil.copyfile(
            native_source.with_suffix(".vakc.meta.json"),
            Path(str(expected_native) + ".meta.json"),
        )

        source_driver_sample = _run_bootstrap_driver(vak_py, compiler_vak, str(sample_source), str(source_sample))
        if source_driver_sample.returncode != 0:
            print("❌ Source bootstrap driver failed for sample:")
            print(source_driver_sample.stderr or source_driver_sample.stdout)
            sys.exit(1)
        source_driver_self = _run_bootstrap_driver(vak_py, compiler_vak, compiler_vak, str(source_self))
        if source_driver_self.returncode != 0:
            print("❌ Source bootstrap driver failed for compiler.vak:")
            print(source_driver_self.stderr or source_driver_self.stdout)
            sys.exit(1)

        sample_match = _assert_matching_artifacts(expected_sample, source_sample)
        self_match = _assert_matching_artifacts(expected_self, source_self)
        print("✓ Source bootstrap driver matched Python compiler")
        print(f"   sample hash: {sample_match['byte_hash']}")
        print(f"   self hash:   {self_match['byte_hash']}")

        compiled_driver_sample = _run_bootstrap_driver(vak_py, compiler_vakc, str(sample_source), str(compiled_sample))
        if compiled_driver_sample.returncode != 0:
            print("❌ Compiled bootstrap driver failed for sample:")
            print(compiled_driver_sample.stderr or compiled_driver_sample.stdout)
            sys.exit(1)
        compiled_driver_self = _run_bootstrap_driver(vak_py, compiler_vakc, compiler_vak, str(compiled_self))
        if compiled_driver_self.returncode != 0:
            print("❌ Compiled bootstrap driver failed for compiler.vak:")
            print(compiled_driver_self.stderr or compiled_driver_self.stdout)
            sys.exit(1)

        compiled_sample_match = _assert_matching_artifacts(expected_sample, compiled_sample)
        compiled_self_match = _assert_matching_artifacts(expected_self, compiled_self)
        print("✓ Compiled bootstrap driver matched Python compiler")
        print(f"   sample hash: {compiled_sample_match['byte_hash']}")
        print(f"   self hash:   {compiled_self_match['byte_hash']}")

        source_native_result = _run_bootstrap_driver(
            vak_py,
            compiler_vak,
            str(native_source),
            str(source_native),
            mode="native_compile",
        )
        if source_native_result.returncode != 0:
            print("❌ Source native bootstrap driver failed:")
            print(source_native_result.stderr or source_native_result.stdout)
            sys.exit(1)
        compiled_native_result = _run_bootstrap_driver(
            vak_py,
            compiler_vakc,
            str(native_source),
            str(compiled_native),
            mode="native_compile",
        )
        if compiled_native_result.returncode != 0:
            print("❌ Compiled native bootstrap driver failed:")
            print(compiled_native_result.stderr or compiled_native_result.stdout)
            sys.exit(1)
        native_source_match = _assert_matching_artifacts(expected_native, source_native)
        native_compiled_match = _assert_matching_artifacts(expected_native, compiled_native)
        native_repro_result = _run_bootstrap_driver(
            vak_py,
            compiler_vakc,
            str(native_source),
            str(native_repro_a),
            mode="native_repro",
            second_output_path=str(native_repro_b),
        )
        if native_repro_result.returncode != 0:
            print("❌ Native subset reproducibility failed:")
            print(native_repro_result.stderr or native_repro_result.stdout)
            sys.exit(1)
        _assert_matching_artifacts(native_repro_a, native_repro_b)
        print("✓ Native subset bootstrap drivers matched Python compiler")
        print(f"   source hash:   {native_source_match['byte_hash']}")
        print(f"   compiled hash: {native_compiled_match['byte_hash']}")

    # ──────────────────────────────────────────────────────────────────────
    # Stage 5: Recompile and verify reproducibility
    # ──────────────────────────────────────────────────────────────────────
    print("\n📌 Stage 5: Checking reproducible compile output...")

    result = _compile_with_python(vak_py, compiler_vak)

    if result.returncode != 0:
        print("❌ Recompilation failed:")
        print(f"   STDERR: {result.stderr[:500]}")
        sys.exit(1)

    second_hash = _file_hash(compiler_vakc)
    print(f"   Recompiled SHA256: {second_hash}")
    if second_hash != first_hash:
        print("❌ Reproducibility check failed: compiled hashes differ")
        sys.exit(1)
    second_meta_hash = _file_hash(compiler_meta)
    print(f"   Recompiled META SHA256: {second_meta_hash}")
    if second_meta_hash != first_meta_hash:
        print("❌ Reproducibility check failed: metadata hashes differ")
        sys.exit(1)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        repro_source_a = temp_root / "source_repro_a.vakc"
        repro_source_b = temp_root / "source_repro_b.vakc"
        repro_compiled_a = temp_root / "compiled_repro_a.vakc"
        repro_compiled_b = temp_root / "compiled_repro_b.vakc"

        source_repro = _run_bootstrap_repro(
            vak_py,
            compiler_vak,
            compiler_vak,
            str(repro_source_a),
            str(repro_source_b),
        )
        if source_repro.returncode != 0:
            print("❌ Source bootstrap reproducibility failed:")
            print(source_repro.stderr or source_repro.stdout)
            sys.exit(1)

        compiled_repro = _run_bootstrap_repro(
            vak_py,
            compiler_vakc,
            compiler_vak,
            str(repro_compiled_a),
            str(repro_compiled_b),
        )
        if compiled_repro.returncode != 0:
            print("❌ Compiled bootstrap reproducibility failed:")
            print(compiled_repro.stderr or compiled_repro.stdout)
            sys.exit(1)

        _assert_matching_artifacts(repro_source_a, repro_source_b)
        _assert_matching_artifacts(repro_compiled_a, repro_compiled_b)
    print("✓ Reproducibility check passed")
    
    # ──────────────────────────────────────────────────────────────────────
    # Summary
    # ──────────────────────────────────────────────────────────────────────
    print("\n" + "═" * 70)
    print("   Bootstrap Summary")
    print("═" * 70)
    print("""
✓ Stage 1: Compilation completed
✓ Stage 2: Bytecode disassembly succeeded
✓ Stage 3: Source execution succeeded
✓ Stage 4: Source/compiled bootstrap drivers matched Python compiler output
✓ Stage 4b: Native subset bootstrap drivers matched Python compiler output
✓ Stage 5: Reproducible compile output verified

The compiler bootstrap path is now behaviorally verified and the
Vak-written bootstrap driver can compile targets, including itself, and
the Vak-native subset now reproduces Python compiler artifacts for
control flow, recursion, collection literals, indexing, and iterable
loop samples under the current Python-hosted runtime.

Next Steps:
1. Replace the current staged bootstrap driver with a real Vak-native compiler core
2. Preserve standalone .vakc completeness without sidecar/source fallback
3. Achieve true self-hosting without Python bridge delegation

Note: This still does not prove full native self-hosting. It proves that
the Vak-written bootstrap driver compiles deterministically and that both
its source and compiled forms reproduce Python-hosted compiler artifacts.
""")
    print("═" * 70)
    
    return True


def main():
    """Main entry point."""
    try:
        success = bootstrap()
        if success:
            print("\n✅ Bootstrap complete!")
            sys.exit(0)
        else:
            print("\n❌ Bootstrap failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Bootstrap error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
