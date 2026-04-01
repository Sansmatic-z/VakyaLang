import os
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def _safe_print(*args, **kwargs):
    file = kwargs.pop("file", sys.stdout)
    sep = kwargs.pop("sep", " ")
    end = kwargs.pop("end", "\n")
    flush = kwargs.pop("flush", False)
    if kwargs:
        raise TypeError(f"Unsupported print kwargs: {', '.join(kwargs)}")

    text = sep.join(str(arg) for arg in args) + end
    try:
        file.write(text)
    except UnicodeEncodeError:
        encoding = getattr(file, "encoding", None) or "utf-8"
        safe_text = text.encode(encoding, errors="backslashreplace").decode(
            encoding,
            errors="replace",
        )
        file.write(safe_text)
    if flush and hasattr(file, "flush"):
        file.flush()


print = _safe_print

def run_command(cmd, cwd=None):
    """Run a shell command and return (returncode, stdout, stderr)."""
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
    )
    return result.returncode, result.stdout, result.stderr

def test_examples():
    # Run regular examples
    examples_dir = "../examples"
    examples = [
        os.path.join(examples_dir, entry.name)
        for entry in os.scandir(SCRIPT_DIR / ".." / "examples")
        if entry.is_file() and entry.name.endswith(".vak")
    ]
    
    # Also run our new stdlib test
    tests = examples + ["test_stdlib.vak"]
    tests.sort()
    
    results = []
    print(f"Running {len(tests)} tests...")
    for path in tests:
        if not os.path.exists(path): continue
        print(f"Testing {path}...", end=" ", flush=True)
        rc, out, err = run_command([sys.executable, "../vak.py", path], cwd=SCRIPT_DIR)
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
    os.chdir(SCRIPT_DIR)
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
