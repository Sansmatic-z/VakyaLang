#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# VakyaLang (वाक्) — Copyright (c) 2026 Raj Mitra. All Rights Reserved.
# Original author: Raj Mitra (Visionary RM)
# Licensed under GNU AGPL v3.0 — see LICENSE and NOTICE.
# Any use, modification, or derivative work must preserve this header
# and include the NOTICE file. https://github.com/Sansmatic-z/VakyaLang

"""
VakyaLang (वाक्) Unified CLI - Production Grade
The definitive entry point for the Sanskrit Computing Ecosystem.
"""

import sys
import os
import argparse
from pathlib import Path

# Add the project root to sys.path to ensure absolute imports work
root_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(root_dir))

def run_vak(args):
    """Orchestrates the Vāk language runtime."""
    from runtime.src.interpreter import VakInterpreter
    from runtime.src.errors import VakError
    
    interpreter = VakInterpreter()
    
    if not args.source:
        # Start REPL
        interpreter.repl()
        return

    try:
        source_path = Path(args.source)
        if not source_path.exists():
            print(f"Error: File not found: {args.source}")
            sys.exit(1)
            
        code = source_path.read_text(encoding='utf-8')
        
        if args.compile:
            bytecode = interpreter.compile_only(code)
            output_file = source_path.with_suffix('.vakc')
            output_file.write_bytes(bytecode.to_bytes())
            print(f"Successfully compiled to: {output_file}")
            return

        # Execute
        result = interpreter.run(code, debug=args.debug)
        if result is not None:
            print(result)
            
    except VakError as e:
        print(f"Vāk Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Internal System Error: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def run_coder(args):
    """Orchestrates the Sanskrit Coder engine."""
    from sanskrit_coder.main import main as coder_main
    # sanskrit_coder.main expects its own sys.argv logic
    sys.argv = [sys.argv[0]] 
    coder_main()

def run_tests(args):
    """Executes the unified test suite."""
    import unittest
    import pytest
    
    print("🕉️ Starting VakyaLang Unified Test Suite...")
    
    # 1. Run Sanskrit Coder Tests
    print("\n--- Phase 1: Sanskrit Coder Core Tests ---")
    from tests.test_sanskrit_coder import run_tests as run_coder_tests
    try:
        run_coder_tests()
    except Exception as e:
        print(f"Sanskrit Coder Tests failed: {e}")

    # 2. Run Vāk Language Integration Tests
    print("\n--- Phase 2: Vāk Language Integration Tests ---")
    test_files = list(Path(root_dir / "tests").glob("test_*.py"))
    if not test_files:
        print("No Python-based integration tests found in /tests.")
    else:
        suite = unittest.TestLoader().discover(str(root_dir / "tests"))
        unittest.TextTestRunner(verbosity=2).run(suite)

    # 3. Run Vāk Example Verification
    print("\n--- Phase 3: Vāk Example Verification ---")
    from runtime.src.interpreter import VakInterpreter
    examples = [
        "examples/namaste.vak",
        "examples/fibonacci.vak",
        "examples/varg.vak",
        "examples/data.vak",
        "examples/dosh.vak"
    ]
    interpreter = VakInterpreter()
    for ex in examples:
        ex_path = root_dir / ex
        if ex_path.exists():
            print(f"Verifying {ex}... ", end="")
            try:
                interpreter.run(ex_path.read_text(encoding='utf-8'))
                print("✅ PASS")
            except Exception as e:
                print(f"❌ FAIL: {e}")
        else:
            print(f"Skipping {ex} (not found)")

def main():
    parser = argparse.ArgumentParser(
        description='VakyaLang (वाक्) Unified CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # 'run' command
    run_parser = subparsers.add_parser('run', help='Run a Vāk program or start REPL')
    run_parser.add_argument('source', nargs='?', help='.vak source file')
    run_parser.add_argument('--debug', '-d', action='store_true', help='Show execution trace')
    run_parser.add_argument('--compile', '-c', action='store_true', help='Compile to bytecode only')

    # 'coder' command
    subparsers.add_parser('coder', help='Start Sanskrit Coder interactive engine')

    # 'test' command
    subparsers.add_parser('test', help='Run the full system test suite')

    args = parser.parse_args()

    if args.command == 'run' or (args.command is None and len(sys.argv) == 1):
        run_vak(args)
    elif args.command == 'coder':
        run_coder(args)
    elif args.command == 'test':
        run_tests(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
