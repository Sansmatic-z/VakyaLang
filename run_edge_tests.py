#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run edge case tests for VakyaLang"""

import sys
import os
from pathlib import Path

# Get the directory of this script
BASE_DIR = Path(__file__).parent.resolve()

# Add paths
sys.path.insert(0, str(BASE_DIR / "runtime"))
sys.path.insert(0, str(BASE_DIR / "sanskrit_coder"))

print("=" * 60)
print("VakyaLang - Edge Case Tests")
print("=" * 60)
print()

from runtime.src.interpreter import VakInterpreter

interpreter = VakInterpreter()

# Test 1: Run remaining example files
print("\n" + "=" * 60)
print("TEST 1: Remaining Example Files")
print("=" * 60)

examples = [
    "examples/tasks.vak",
    "examples/webgen.vak",
    "examples/vyapak.vak",
]

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
        if result is not None:
            print(f"  Result: {result}")
    except Exception as e:
        print(f"✗ {example} failed: {e}")
        import traceback
        traceback.print_exc()

# Test 2: Run test files in tests/ directory
print("\n" + "=" * 60)
print("TEST 2: Test Files in tests/ Directory")
print("=" * 60)

test_files = [
    "tests/test_stdlib.vak",
    "tests/test_system.vak",
]

for test_file in test_files:
    test_path = BASE_DIR / test_file
    print(f"\n--- Running {test_file} ---")
    if not test_path.exists():
        print(f"✗ File not found: {test_path}")
        continue

    try:
        source = test_path.read_text(encoding='utf-8')
        result = interpreter.run(source, debug=False)
        print(f"✓ {test_file} executed successfully")
        if result is not None:
            print(f"  Result: {result}")
    except Exception as e:
        print(f"✗ {test_file} failed: {e}")
        import traceback
        traceback.print_exc()

# Test 3: Run Python test file
print("\n" + "=" * 60)
print("TEST 3: Python Test File")
print("=" * 60)

test_py = BASE_DIR / "tests" / "test_live_features.py"
print(f"\n--- Running {test_py} ---")
if test_py.exists():
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, str(test_py)],
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR)
        )
        print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")
        if result.returncode == 0:
            print(f"✓ test_live_features.py executed successfully")
        else:
            print(f"✗ test_live_features.py failed with code {result.returncode}")
    except Exception as e:
        print(f"✗ test_live_features.py failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"✗ File not found: {test_py}")

# Test 4: VM Edge Cases
print("\n" + "=" * 60)
print("TEST 4: VM Edge Cases")
print("=" * 60)

# 4a: Deep recursion test
print("\n--- 4a. Deep Recursion Test ---")
recursion_code = """
कर्म फैक्टोरियल(गण):
    यदि गण <= १:
        प्रत्यागच्छ १
    प्रत्यागच्छ गण * फैक्टोरियल(गण - १)

मुद्रय "फैक्टोरियल(१०) =", फैक्टोरियल(१०)
मुद्रय "फैक्टोरियल(१५) =", फैक्टोरियल(१५)
"""

try:
    result = interpreter.run(recursion_code, debug=False)
    print(f"✓ Deep recursion test passed")
    if result is not None:
        print(f"  Result: {result}")
except Exception as e:
    print(f"✗ Deep recursion test failed: {e}")
    import traceback
    traceback.print_exc()

# 4b: Large numbers test
print("\n--- 4b. Large Numbers Test ---")
large_numbers_code = """
चर बड़ा_१ = १२३४५६७८९०१२३४५६७८९०
चर बड़ा_२ = ९८७६५४३२१०९८७६५४३२१०
मुद्रय "बड़ा_१ =", बड़ा_१
मुद्रय "बड़ा_२ =", बड़ा_२
मुद्रय "योग =", बड़ा_१ + बड़ा_२
मुद्रय "गुणन =", बड़ा_१ * बड़ा_२
मुद्रय "भाग =", बड़ा_२ // बड़ा_१
"""

try:
    result = interpreter.run(large_numbers_code, debug=False)
    print(f"✓ Large numbers test passed")
    if result is not None:
        print(f"  Result: {result}")
except Exception as e:
    print(f"✗ Large numbers test failed: {e}")
    import traceback
    traceback.print_exc()

# 4c: Complex nested structures test
print("\n--- 4c. Complex Nested Structures Test ---")
nested_code = """
चर नेस्टेड = {
    "स्तर१": {
        "स्तर२": {
            "स्तर३": {
                "स्तर४": ["गहरा", "डेटा", [१, २, ३]]
            }
        }
    },
    "सूची": [
        {"नाम": "पहला", "मान": १००},
        {"नाम": "दूसरा", "मान": २००},
        {"नाम": "तीसरा", "मान": ३००}
    ]
}

मुद्रय "नेस्टेड संरचना:", नेस्टेड
मुद्रय "गहरा मान:", नेस्टेड["स्तर१"]["स्तर२"]["स्तर३"]["स्तर४"]
मुद्रय "सूची लम्बाई:", दीर्घता(नेस्टेड["सूची"])
प्रत्येक चर आइटम अन्तर्गत नेस्टेड["सूची"]:
    मुद्रय "  -", आइटम["नाम"], ":", आइटम["मान"]
"""

try:
    result = interpreter.run(nested_code, debug=False)
    print(f"✓ Complex nested structures test passed")
    if result is not None:
        print(f"  Result: {result}")
except Exception as e:
    print(f"✗ Complex nested structures test failed: {e}")
    import traceback
    traceback.print_exc()

# 4d: Very deep recursion stress test
print("\n--- 4d. Very Deep Recursion Stress Test ---")
stress_recursion_code = """
कर्म फिब(गण):
    यदि गण <= १:
        प्रत्यागच्छ गण
    प्रत्यागच्छ फिब(गण - १) + फिब(गण - २)

मुद्रय "फिबोनाची(२०) =", फिब(२०)
मुद्रय "फिबोनाची(२५) =", फिब(२५)
"""

try:
    result = interpreter.run(stress_recursion_code, debug=False)
    print(f"✓ Very deep recursion stress test passed")
    if result is not None:
        print(f"  Result: {result}")
except Exception as e:
    print(f"✗ Very deep recursion stress test failed: {e}")
    import traceback
    traceback.print_exc()

# 4e: Edge case - empty structures
print("\n--- 4e. Empty Structures Test ---")
empty_code = """
चर खाली_सूची = []
चर खाली_शब्दकोश = {}
मुद्रय "खाली सूची:", खाली_सूची
मुद्रय "खाली शब्दकोश:", खाली_शब्दकोश
मुद्रय "खाली सूची लम्बाई:", दीर्घता(खाली_सूची)
"""

try:
    result = interpreter.run(empty_code, debug=False)
    print(f"✓ Empty structures test passed")
    if result is not None:
        print(f"  Result: {result}")
except Exception as e:
    print(f"✗ Empty structures test failed: {e}")
    import traceback
    traceback.print_exc()

# 4f: String edge cases
print("\n--- 4f. String Edge Cases Test ---")
string_code = """
चर खाली_तार = ""
चर लम्बा_तार = "अ" * १०००
मुद्रय "खाली तार लम्बाई:", दीर्घता(खाली_तार)
मुद्रय "लम्बा तार लम्बाई:", दीर्घता(लम्बा_तार)
मुद्रय "प्रथम १० अक्षर:", लम्बा_तार[०:१०]
"""

try:
    result = interpreter.run(string_code, debug=False)
    print(f"✓ String edge cases test passed")
    if result is not None:
        print(f"  Result: {result}")
except Exception as e:
    print(f"✗ String edge cases test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("ALL EDGE CASE TESTS COMPLETED")
print("=" * 60)
