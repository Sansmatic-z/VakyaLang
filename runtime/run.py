#!/usr/bin/env python3
# वाक् भाषा — मुख्य प्रवेश बिन्दु (Main Entry Point)
# Vak Language - CLI Runner & Interactive REPL

import sys
import os

if __package__ in (None, ""):
    # Ensure runtime and project root are on the path when executed as a script.
    RUNTIME_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(RUNTIME_DIR)
    sys.path.insert(0, RUNTIME_DIR)
    sys.path.insert(0, PROJECT_ROOT)

    from src.lexer       import Lexer
    from src.parser      import Parser
    from src.interpreter import VakInterpreter
    from src.compiler    import Compiler
    from src.vm          import VakVM
    from src.errors      import VakError, format_vak_error_with_suggestions
    from src.rupantar    import VakyaRupantar
else:
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    from .src.lexer       import Lexer
    from .src.parser      import Parser
    from .src.interpreter import VakInterpreter
    from .src.compiler    import Compiler
    from .src.vm          import VakVM
    from .src.errors      import VakError, format_vak_error_with_suggestions
    from .src.rupantar    import VakyaRupantar

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
        prepared_source = interp.prepare_source(source)
        interp.run(prepared_source, filename=filename, source_prepared=True)
        if interp.translation_status_message():
            print(interp.translation_status_message())
        return True
    except VakError as e:
        print(
            format_vak_error_with_suggestions(e, interp.error_context()),
            file=sys.stderr,
        )
        return False
    except SystemExit:
        raise
    except KeyboardInterrupt:
        print("\n(बाधित — interrupted)", file=sys.stderr)
        return False
    except Exception as e:
        print(
            format_vak_error_with_suggestions(e, interp.error_context()),
            file=sys.stderr,
        )
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
    deep_meaning_mode = False
    active_branches: list[str] = []
    if '--गूढार्थ' in args:
        args = [arg for arg in args if arg != '--गूढार्थ']
        deep_meaning_mode = True
    if '--gudhartha' in args:
        args = [arg for arg in args if arg != '--gudhartha']
        deep_meaning_mode = True
    while True:
        if '--branch' in args:
            index = args.index('--branch')
        elif '--शाखा' in args:
            index = args.index('--शाखा')
        else:
            break
        if index + 1 >= len(args):
            print("उपयोग: python run.py --branch <name>", file=sys.stderr)
            sys.exit(1)
        active_branches.append(args[index + 1])
        del args[index:index + 2]

    if not args:
        interp = VakInterpreter(
            active_branches=active_branches,
            deep_meaning_mode=deep_meaning_mode,
        )
        interp.repl(banner=BANNER)
        return

    if args[0] == '-c':
        if len(args) < 2:
            print("उपयोग: python run.py -c \"कोड\"", file=sys.stderr)
            sys.exit(1)
        interp = VakInterpreter(
            active_branches=active_branches,
            deep_meaning_mode=deep_meaning_mode,
        )
        ok = run_source(args[1], interp)
        sys.exit(0 if ok else 1)

    if args[0] == '--tui':
        from src.tui import main as tui_main

        sys.exit(tui_main(args[1:]))

    if args[0] in ('--रूपान्तर', '--rupantar'):
        if len(args) < 3:
            print("उपयोग: python run.py --रूपान्तर input.vak output.vak", file=sys.stderr)
            sys.exit(1)
        try:
            engine = VakyaRupantar(active_branches=active_branches)
            result = engine.transform_file(args[1], args[2])
            print(f"रूपान्तरित स्रोत लिखा गया: {args[2]}")
            print(result.report_text())
            sys.exit(0 if result.syntax_valid and result.compiled else 1)
        except FileNotFoundError:
            print(f"  फ़ाइल नहीं मिली: '{args[1]}' (file not found)", file=sys.stderr)
            sys.exit(1)

    if args[0] == '--codex-pages':
        if __package__ in (None, ""):
            from src.codex import build_default_codex
        else:
            from .src.codex import build_default_codex
        codex = build_default_codex(
            active_branches=active_branches,
            deep_meaning_mode=deep_meaning_mode,
        )
        for page in codex.list_pages():
            print(f"{page['name']}: {page['description']}")
        return

    if args[0] in ('--कोडेक्स', '--codex'):
        if len(args) < 3:
            print("उपयोग: python run.py --कोडेक्स input output", file=sys.stderr)
            sys.exit(1)
        page_name = "auto"
        if len(args) >= 5 and args[3] == '--codex-page':
            page_name = args[4]
        if __package__ in (None, ""):
            from src.codex import build_default_codex
        else:
            from .src.codex import build_default_codex
        try:
            codex = build_default_codex(
                active_branches=active_branches,
                deep_meaning_mode=deep_meaning_mode,
            )
            result = codex.transform_file(args[1], args[2], page=page_name)
            print(f"कोडेक्स रूपान्तरित स्रोत लिखा गया: {args[2]}")
            print(result.report_text())
            sys.exit(0 if not (result.confidence == "do_not_touch" and not result.transformed) else 1)
        except FileNotFoundError:
            print(f"  फ़ाइल नहीं मिली: '{args[1]}' (file not found)", file=sys.stderr)
            sys.exit(1)

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
        
        interp = VakInterpreter(
            active_branches=active_branches,
            deep_meaning_mode=deep_meaning_mode,
        )
        if args[0] == '--bytecode':
            prepared_source = interp.prepare_source(source)
            bytecode = interp.compile_only(
                prepared_source,
                filename=args[1],
                source_prepared=True,
            )
            if interp.translation_status_message():
                print(interp.translation_status_message())
            print(f"Bytecode for {args[1]}:")
            print(bytecode.disassemble())
        else:
            # --vm just runs it via the bytecode interpreter
            ok = run_source(source, interp, filename=args[1])
            sys.exit(0 if ok else 1)
        return

    # Run file
    if not os.path.exists(args[0]):
        print(f"  फ़ाइल नहीं मिली: '{args[0]}' (file not found)", file=sys.stderr)
        sys.exit(1)

    with open(args[0], encoding='utf-8') as f:
        source = f.read()

    interp = VakInterpreter(
        active_branches=active_branches,
        deep_meaning_mode=deep_meaning_mode,
    )
    ok = run_source(source, interp, filename=args[0])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
