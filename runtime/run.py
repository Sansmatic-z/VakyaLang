#!/usr/bin/env python3
# वाक् भाषा — मुख्य प्रवेश बिन्दु (Main Entry Point)
# Vak Language - CLI Runner & Interactive REPL

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.lexer       import Lexer
from src.parser      import Parser
from src.interpreter import VakInterpreter
from src.compiler    import Compiler
from src.vm          import VakVM
from src.errors      import VakError

# ====================== AUTO VERSIONING (competitive grade) ======================
try:
    from importlib.metadata import version, PackageNotFoundError
    __version__ = version("vakyalang")
except (PackageNotFoundError, Exception):
    # Fallback: git describe (works even without installing)
    try:
        import subprocess
        __version__ = subprocess.check_output(
            ["git", "describe", "--tags", "--always", "--dirty"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        __version__ = "dev"

# Beautiful dynamic banner (never outdated again)
BANNER = f"""\
╔══════════════════════════════════════════════════════════════╗
║          वाक् भाषा  —  संस्कृत संगणन भाषा                  ║
║          Vāk Language  —  Sanskrit Computing Language        ║
║                                                              ║
║  संस्करण (version): {__version__:<33} ║
║  लेखक   (author) : Raj Mitra  © 2026                        ║
║  लाइसेंस (license): AGPL-3.0-or-later                        ║
║                                                              ║
║  'विराम' लिखें बाहर निकलने के लिए  (type 'विराम' to exit)  ║
╚══════════════════════════════════════════════════════════════╝
"""


def run_source(source: str, interp: VakInterpreter, filename: str = "<वाक्>") -> bool:
    """Execute source code using the high-level VakInterpreter."""
    try:
        interp.run(source)
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

    interp = VakInterpreter()
    ok = run_source(source, interp, filename=path)
    sys.exit(0 if ok else 1)


def run_repl():
    """Interactive REPL — Read-Eval-Print Loop."""
    interp = VakInterpreter()
    interp.repl(banner=BANNER)


def main():
    args = sys.argv[1:]

    if not args:
        run_repl()
        return

    if args[0] == '-c':
        if len(args) < 2:
            print("उपयोग: python run.py -c \"कोड\"", file=sys.stderr)
            sys.exit(1)
        interp = VakInterpreter()
        ok = run_source(args[1], interp)
        sys.exit(0 if ok else 1)

    if args[0] == '--tokens':
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

    if args[0] == '--bytecode' or args[0] == '--vm':
        if len(args) < 2:
            print(f"उपयोग: python run.py {args[0]} file.vak", file=sys.stderr)
            sys.exit(1)
        with open(args[1], encoding='utf-8') as f:
            source = f.read()
        
        interp = VakInterpreter()
        if args[0] == '--bytecode':
            bytecode = interp.compile_only(source)
            print(f"Bytecode for {args[1]}:")
            print(bytecode.disassemble())
        else:
            # --vm just runs it via the bytecode interpreter
            ok = run_source(source, interp, filename=args[1])
            sys.exit(0 if ok else 1)
        return

    # Run file
    run_file(args[0])


if __name__ == "__main__":
    main()

