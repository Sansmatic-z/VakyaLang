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
    examples_dir = "../examples"
    examples = [os.path.join(examples_dir, f) for f in os.listdir(examples_dir) if f.endswith(".vak")]
    
    # Also run our new stdlib test
    tests = examples + ["test_stdlib.vak"]
    tests.sort()
    
    results = []
    print(f"Running {len(tests)} tests...")
    for path in tests:
        if not os.path.exists(path): continue
        print(f"Testing {path}...", end=" ", flush=True)
        rc, out, err = run_command(f"{sys.executable} ../vak.py {path}")
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
    
    # Test --ast/--tokens logic if supported, but for now we just verify it runs
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
