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

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))
vaklan_root = os.path.dirname(script_dir)


def bootstrap():
    """
    Bootstrap the VakyaLang compiler.
    
    This script:
    1. Uses the Python-based VakyaLang compiler to compile compiler.vak
    2. Verifies the compiled bytecode
    3. Prepares for self-hosting
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
    print(f"   Command: python {vak_py} --compile {compiler_vak}")
    
    result = subprocess.run(
        ["python", vak_py, "--compile", compiler_vak],
        capture_output=True,
        text=True,
        cwd=vaklan_root
    )
    
    if result.returncode != 0:
        print(f"❌ Compilation failed:")
        print(f"   STDOUT: {result.stdout}")
        print(f"   STDERR: {result.stderr}")
        sys.exit(1)
    
    print("✓ compiler.vakc generated")
    
    # ──────────────────────────────────────────────────────────────────────
    # Stage 2: Verify the compiled bytecode
    # ──────────────────────────────────────────────────────────────────────
    print("\n📌 Stage 2: Verifying compiled bytecode...")
    
    compiler_vakc = os.path.join(script_dir, "compiler.vakc")
    if os.path.exists(compiler_vakc):
        print(f"   Found compiled bytecode: {compiler_vakc}")
        
        # Try to disassemble
        result = subprocess.run(
            ["python", vak_py, compiler_vakc, "--disassemble"],
            capture_output=True,
            text=True,
            cwd=vaklan_root
        )
        
        if result.returncode != 0:
            print(f"⚠️  Disassembly failed (expected for skeleton): {result.stderr}")
        else:
            print("✓ Bytecode disassembly successful")
            print("\n--- Disassembly Output ---")
            print(result.stdout[:500])  # Show first 500 chars
    else:
        print("⚠️  No .vakc file generated (expected for skeleton)")
    
    # ──────────────────────────────────────────────────────────────────────
    # Stage 3: Run the compiler.vak directly
    # ──────────────────────────────────────────────────────────────────────
    print("\n📌 Stage 3: Running compiler.vak directly...")
    
    result = subprocess.run(
        ["python", vak_py, compiler_vak],
        capture_output=True,
        text=True,
        cwd=vaklan_root
    )
    
    if result.returncode != 0:
        print(f"⚠️  Execution failed (may have syntax errors in skeleton):")
        print(f"   STDERR: {result.stderr[:500]}")
    else:
        print("✓ Compiler skeleton executed successfully")
        print("\n--- Compiler Output ---")
        print(result.stdout)
    
    # ──────────────────────────────────────────────────────────────────────
    # Summary
    # ──────────────────────────────────────────────────────────────────────
    print("\n" + "═" * 70)
    print("   Bootstrap Summary")
    print("═" * 70)
    print("""
✓ Stage 1: Compilation attempted
✓ Stage 2: Bytecode verification attempted
✓ Stage 3: Direct execution attempted

The self-hosting compiler skeleton is now in place.

Next Steps:
1. Complete the compiler.vak implementation
2. Fix any syntax/semantic errors
3. Achieve full self-hosting (compiler compiles itself)

Note: This is a SKELETON implementation. Full self-hosting requires
completing all compiler phases (lexing, parsing, code generation).
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
