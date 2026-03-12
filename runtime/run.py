# VakyaLang (????) � Copyright (c) 2026 Raj Mitra. All Rights Reserved.
# Original author: Raj Mitra (Visionary RM)
# Licensed under GNU AGPL v3.0 � see LICENSE and NOTICE.
# Any use, modification, or derivative work must preserve this header
# and include the NOTICE file. https://github.com/Sansmatic-z/VakyaLang

#!/usr/bin/env python3
# वाक् भाषा — मुख्य प्रवेश बिन्दु (Main Entry Point)
# Vak Language - CLI Runner & Interactive REPL
#
# उपयोग (Usage):
#   python run.py              → start REPL
#   python run.py file.vak     → run a .vak file
#   python run.py -c "code"    → run inline code

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.lexer       import Lexer
from src.parser      import Parser
from src.interpreter import Interpreter
from src.core.compiler import Compiler
from src.core.vm       import VakVM
from src.errors      import VakError


BANNER = """\
╔══════════════════════════════════════════════════════════════╗
║          वाक् भाषा  —  संस्कृत संगणन भाषा                  ║
║          Vāk Language  —  Sanskrit Computing Language        ║
║                                                              ║
║  संस्करण (version): 1.0.0                                   ║
║  लेखक   (author) : Raj Mitra  © 2026                        ║
║  लाइसेंस (license): AGPL v3                                  ║
║                                                              ║
║  'विराम' लिखें बाहर निकलने के लिए  (type 'विराम' to exit)  ║
╚══════════════════════════════════════════════════════════════╝
"""


def run_vm(source: str, vm: VakVM, filename: str = "<वाक्>") -> bool:
    """Lex → Parse → Compile → Execute (VM)."""
    try:
        tokens   = Lexer(source).tokenize()
        program  = Parser(tokens).parse()
        compiler = Compiler()
        code     = compiler.compile(program)
        vm.run(code)
        return True
    except VakError as e:
        print(str(e), file=sys.stderr)
        return False
    except Exception as e:
        print(f"\n  VM त्रुटि: {e}", file=sys.stderr)
        return False

def run_source(source: str, interp: Interpreter,
               filename: str = "<वाक्>") -> bool:
    """Lex → Parse → Execute. Returns True on success."""
    try:
        tokens  = Lexer(source).tokenize()
        program = Parser(tokens).parse()
        interp.execute(program)
        return True
    except VakError as e:
        print(str(e), file=sys.stderr)
        return False
    except SystemExit:
        raise
    except KeyboardInterrupt:
        print("\n(बाधित — interrupted)", file=sys.stderr)
        return False
    except Exception as e:
        print(f"\n  आंतरिक त्रुटि (internal error): {e}", file=sys.stderr)
        return False


def run_file(path: str):
    """Run a .vak source file."""
    if not os.path.exists(path):
        print(f"  फ़ाइल नहीं मिली: '{path}' (file not found)", file=sys.stderr)
        sys.exit(1)

    with open(path, encoding='utf-8') as f:
        source = f.read()

    interp = Interpreter()
    ok = run_source(source, interp, filename=path)
    sys.exit(0 if ok else 1)


def run_repl():
    """Interactive REPL — Read-Eval-Print Loop."""
    print(BANNER)
    interp = Interpreter()

    while True:
        try:
            line = input("वाक्> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nनमस्कार। (Goodbye.)")
            break

        if not line:
            continue
        if line in ("विराम", "exit", "quit", ":q"):
            print("नमस्कार। (Goodbye.)")
            break

        # Multi-line input: if line ends with ':', keep reading until blank line
        if line.endswith(':'):
            lines = [line]
            while True:
                try:
                    cont = input("...  ")
                except (EOFError, KeyboardInterrupt):
                    break
                if cont == "":
                    break
                lines.append(cont)
            source = '\n'.join(lines)
        else:
            source = line

        run_source(source, interp)


def main():
    args = sys.argv[1:]

    if not args:
        run_repl()
        return

    if args[0] == '-c':
        if len(args) < 2:
            print("उपयोग: python run.py -c \"कोड\"", file=sys.stderr)
            sys.exit(1)
        interp = Interpreter()
        ok = run_source(args[1], interp)
        sys.exit(0 if ok else 1)

    if args[0] == '--tokens':
        # Debug: print tokens for a file
        if len(args) < 2:
            print("उपयोग: python run.py --tokens file.vak", file=sys.stderr)
            sys.exit(1)
        with open(args[1], encoding='utf-8') as f:
            source = f.read()
        tokens = Lexer(source).tokenize()
        for tok in tokens:
            print(tok)
        return

    if args[0] == '--ast':
        # Debug: print AST for a file
        if len(args) < 2:
            print("उपयोग: python run.py --ast file.vak", file=sys.stderr)
            sys.exit(1)
        import pprint
        with open(args[1], encoding='utf-8') as f:
            source = f.read()
        tokens  = Lexer(source).tokenize()
        program = Parser(tokens).parse()
        pprint.pprint(program)
        return

    if args[0] == '--vm':
        if len(args) < 2:
            print("उपयोग: python run.py --vm file.vak", file=sys.stderr)
            sys.exit(1)
        with open(args[1], encoding='utf-8') as f:
            source = f.read()
        # Initialize VM with globals from a dummy interpreter to get system bridge
        interp = Interpreter()
        vm = VakVM(globals_env=interp.globals)
        ok = run_vm(source, vm, filename=args[1])
        sys.exit(0 if ok else 1)

    if args[0] == '--bytecode':
        if len(args) < 2:
            print("उपयोग: python run.py --bytecode file.vak", file=sys.stderr)
            sys.exit(1)
        with open(args[1], encoding='utf-8') as f:
            source = f.read()
        tokens   = Lexer(source).tokenize()
        program  = Parser(tokens).parse()
        compiler = Compiler()
        code     = compiler.compile(program)
        print(f"Bytecode for {args[1]}:")
        for i, (op, operand) in enumerate(code.instructions):
            print(f"  {i:4}: {op.name:<15} {operand if operand is not None else ''}")
        return

    # Run file
    run_file(args[0])


if __name__ == "__main__":
    main()

