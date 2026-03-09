import os
import subprocess
import sys

def run_command(cmd):
    """Run a shell command and return (returncode, stdout, stderr)."""
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr

def test_examples():
    # Run regular examples
    examples_dir = "examples"
    examples = [os.path.join(examples_dir, f) for f in os.listdir(examples_dir) if f.endswith(".vak")]
    
    # Also run our new stdlib test
    tests = examples + ["test_stdlib.vak"]
    tests.sort()
    
    results = []
    print(f"Running {len(tests)} tests...")
    for path in tests:
        if not os.path.exists(path): continue
        print(f"Testing {path}...", end=" ", flush=True)
        rc, out, err = run_command(f"{sys.executable} run.py {path}")
        if rc == 0:
            print("PASS")
            results.append((path, True))
        else:
            print("FAIL")
            print(f"--- STDOUT ---\n{out}")
            print(f"--- STDERR ---\n{err}")
            results.append((path, False))
    return results

def test_cli():
    print("Testing CLI flags...")
    cli_results = []
    
    # Test inline code
    print("Testing -c (inline code)...", end=" ", flush=True)
    rc, out, err = run_command(f"{sys.executable} run.py -c 'मुद्रय \"नमस्ते\"'")
    if rc == 0 and "नमस्ते" in out:
        print("PASS")
        cli_results.append(("CLI -c", True))
    else:
        print("FAIL")
        print(f"RC: {rc}, OUT: {out}, ERR: {err}")
        cli_results.append(("CLI -c", False))

    # Test --tokens
    print("Testing --tokens...", end=" ", flush=True)
    rc, out, err = run_command(f"{sys.executable} run.py --tokens examples/namaste.vak")
    if rc == 0 and "Token(PRINT" in out:
        print("PASS")
        cli_results.append(("CLI --tokens", True))
    else:
        print("FAIL")
        cli_results.append(("CLI --tokens", False))

    # Test --ast
    print("Testing --ast...", end=" ", flush=True)
    rc, out, err = run_command(f"{sys.executable} run.py --ast examples/namaste.vak")
    if rc == 0 and "Program" in out:
        print("PASS")
        cli_results.append(("CLI --ast", True))
    else:
        print("FAIL")
        cli_results.append(("CLI --ast", False))
    return cli_results

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    example_results = test_examples()
    cli_results = test_cli()
    
    all_results = example_results + cli_results
    failed = [name for name, success in all_results if not success]
    if failed:
        print(f"\n{len(failed)} tests FAILED: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("\nAll tests PASSED!")
        sys.exit(0)
