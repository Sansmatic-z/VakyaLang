#!/usr/bin/env python3
"""
VakyaLang (वाक्) Unified CLI
Unified entry point for Vāk programming language and Sanskrit Coder.

© 2026 Raj Mitra. All Rights Reserved.
"""
import sys
import os

# Add root to sys.path to allow imports
root_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_path)

def usage():
    print("VakyaLang (वाक्) Unified CLI")
    print("Usage:")
    print("  python vak.py run <file.vak>    Run a Vāk program")
    print("  python vak.py repl              Start the Vāk interactive REPL")
    print("  python vak.py coder             Start Sanskrit Coder CLI")
    print("  python vak.py test              Run all tests")
    print("  python vak.py --version         Show version info")

def main():
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "run":
        if len(sys.argv) < 3:
            print("Error: Specify a .vak file to run.")
            sys.exit(1)
        import runtime.run as vak_run
        sys.argv = [sys.argv[0]] + sys.argv[2:] # Strip 'run'
        vak_run.main()

    elif cmd == "repl":
        import runtime.run as vak_run
        sys.argv = [sys.argv[0]] # Empty args for REPL
        vak_run.main()

    elif cmd == "coder":
        import sanskrit_coder.main as coder_main
        coder_main.main()

    elif cmd == "test":
        print("Running VakyaLang Test Suite...")
        # Run Sanskrit Coder tests
        import tests.test_sanskrit_coder as coder_test
        coder_test.main()
        
        # Run Vāk examples as integration tests
        import runtime.run as vak_run
        examples = [
            "examples/namaste.vak",
            "examples/fibonacci.vak",
            "examples/varg.vak"
        ]
        for ex in examples:
            print(f"\n--- Testing Example: {ex} ---")
            ex_path = os.path.join(root_path, ex)
            if os.path.exists(ex_path):
                sys.argv = [sys.argv[0], ex_path]
                vak_run.main()

    elif cmd in ["--version", "-v"]:
        print("VakyaLang v0.1.0")

    else:
        usage()

if __name__ == "__main__":
    main()
