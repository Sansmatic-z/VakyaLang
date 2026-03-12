#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run all tests for VakyaLang"""

import sys
import os
from pathlib import Path

# Get the directory of this script
BASE_DIR = Path(__file__).parent.resolve()

# Add paths
sys.path.insert(0, str(BASE_DIR / "runtime"))
sys.path.insert(0, str(BASE_DIR / "sanskrit_coder"))

print("=" * 60)
print("VakyaLang - Complete Test Suite")
print("=" * 60)
print(f"Base Directory: {BASE_DIR}")
print(f"Python Version: {sys.version}")
print()

# Test 1: Runtime tests
print("\n" + "=" * 60)
print("TEST 1: Runtime Core Tests")
print("=" * 60)
try:
    # Run runtime tests via subprocess since run_tests.py is a script
    import subprocess
    result = subprocess.run(
        [sys.executable, str(BASE_DIR / "runtime" / "run_tests.py")],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    print(result.stdout)
    if result.returncode == 0:
        print("✓ Runtime tests passed")
    else:
        print(f"✗ Runtime tests failed with exit code {result.returncode}")
        print(result.stderr)
except Exception as e:
    print(f"✗ Runtime tests failed: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Sanskrit Coder tests
print("\n" + "=" * 60)
print("TEST 2: Sanskrit Coder Tests")
print("=" * 60)
try:
    from tests.test_sanskrit_coder import run_tests as run_sanskrit_tests
    run_sanskrit_tests()
    print("✓ Sanskrit Coder tests passed")
except Exception as e:
    print(f"✗ Sanskrit Coder tests failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Run example files
print("\n" + "=" * 60)
print("TEST 3: Example Files Execution")
print("=" * 60)

from runtime.src.interpreter import VakInterpreter

examples = [
    "examples/namaste.vak",
    "examples/data.vak",
    "examples/fibonacci.vak",
    "examples/varg.vak",
    "examples/dosh.vak",
]

interpreter = VakInterpreter()

for example in examples:
    example_path = BASE_DIR / example
    print(f"\n--- Running {example} ---")
    if not example_path.exists():
        print(f"✗ File not found: {example_path}")
        continue
    
    try:
        source = example_path.read_text(encoding='utf-8')
        result = interpreter.run(source, debug=False)
        print(f"✓ {example} executed successfully")
    except Exception as e:
        print(f"✗ {example} failed: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
print("ALL TESTS COMPLETED")
print("=" * 60)
