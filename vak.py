#!/usr/bin/env python3
# वाक् भाषा - CLI Entry Point

import sys
import argparse
import os
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from runtime.src.interpreter import VakInterpreter
from runtime.src.bytecode import Bytecode
from runtime.src.codex import build_default_codex
from runtime.src.errors import VakError, format_vak_error_with_suggestions
from runtime.src.rupantar import VakyaRupantar


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        delete=False,
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".tmp",
    ) as handle:
        handle.write(payload)
        temp_path = Path(handle.name)
    try:
        os.replace(temp_path, path)
    except PermissionError:
        path.write_bytes(payload)
        try:
            temp_path.unlink()
        except OSError:
            pass


def _atomic_write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        delete=False,
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".tmp",
        mode="w",
        encoding="utf-8",
        newline="",
    ) as handle:
        handle.write(payload)
        temp_path = Path(handle.name)
    try:
        os.replace(temp_path, path)
    except PermissionError:
        path.write_text(payload, encoding="utf-8", newline="")
        try:
            temp_path.unlink()
        except OSError:
            pass


def _handle_compiled_file(
    source_path: Path,
    interpreter: VakInterpreter,
    *,
    disassemble: bool = False,
) -> None:
    bytecode = Bytecode.from_bytes(source_path.read_bytes())
    bytecode = interpreter.hydrate_bytecode_functions(
        bytecode,
        compiled_path=source_path,
    )
    if disassemble:
        print(bytecode.disassemble())
        return

    has_callable_refs = any(
        isinstance(value, tuple) and value and value[0] in {"function", "coroutine"}
        for value in bytecode.constants
    )
    if has_callable_refs and not bytecode.functions:
        raise VakError(
            "यह .vakc फ़ाइल कार्य/कोरूटीन संदर्भ रखती है, "
            "पर वर्तमान स्वतंत्र .vakc पथ उनके अंतः-बाइटकोड निकाय पुनर्स्थापित नहीं करता। "
            "स्रोत .vak चलाएँ या --disassemble उपयोग करें।"
        )

    result = interpreter.run_bytecode(bytecode)
    if result is not None:
        print(result)

def main():
    raw_args = sys.argv[1:]
    if '--tui' in raw_args:
        from runtime.src.tui import main as tui_main

        tui_args = list(raw_args)
        tui_args.remove('--tui')
        return tui_main(tui_args)

    parser = argparse.ArgumentParser(
        description='वाक् भाषा (VakyaLang) - Sanskrit-inspired Programming Language',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          Start REPL
  %(prog)s file.vak                 Run a VakyaLang file
  %(prog)s file.vak --debug         Run with debug output
  %(prog)s --compile file.vak       Compile to bytecode only
        """
    )
    parser.add_argument('file', nargs='?', help='VakyaLang source file')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug mode')
    parser.add_argument('--compile', '-c', action='store_true', help='Compile only, do not run')
    parser.add_argument('--disassemble', action='store_true', help='Show bytecode disassembly')
    parser.add_argument('--tui', action='store_true', help='Launch the Vak terminal UI')
    parser.add_argument(
        '--branch', '--शाखा',
        dest='branches',
        action='append',
        default=[],
        help='Activate one or more Vak branches for this run',
    )
    parser.add_argument('--गूढार्थ', '--gudhartha', dest='gudhartha', action='store_true',
                        help='Enable Deep Meaning Mode for English source transformation')
    parser.add_argument(
        '--रूपान्तर', '--rupantar',
        dest='rupantar',
        nargs=2,
        metavar=('INPUT', 'OUTPUT'),
        help='Normalize Vak source into current live syntax and write the corrected .vak output',
    )
    parser.add_argument(
        '--कोडेक्स', '--codex',
        dest='codex',
        nargs=2,
        metavar=('INPUT', 'OUTPUT'),
        help='Run Sanskrit_Vakya_Universal_Codex and write Vak output',
    )
    parser.add_argument(
        '--codex-page',
        dest='codex_page',
        default='auto',
        help='Select a specific Codex page (default: auto)',
    )
    parser.add_argument(
        '--codex-pages',
        dest='codex_pages',
        action='store_true',
        help='List available Codex pages and exit',
    )
    parser.add_argument(
        '--codex-chapters',
        dest='codex_chapters',
        action='store_true',
        help='List available Codex chapters and exit',
    )
    parser.add_argument('--version', '-v', action='version', version='%(prog)s 2.17.0')
    
    args = parser.parse_args(raw_args)

    if args.rupantar:
        input_path = Path(args.rupantar[0]).resolve()
        output_path = Path(args.rupantar[1]).resolve()
        try:
            engine = VakyaRupantar(active_branches=args.branches)
            result = engine.transform_file(input_path, output_path)
            print(f"रूपान्तरित स्रोत लिखा गया: {output_path}")
            print(result.report_text())
            if not (result.syntax_valid and result.compiled):
                sys.exit(1)
            return
        except FileNotFoundError:
            print(f"Error: File not found: {input_path}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(format_vak_error_with_suggestions(e), file=sys.stderr)
            sys.exit(1)

    if args.codex_pages:
        codex = build_default_codex(
            active_branches=args.branches,
            deep_meaning_mode=args.gudhartha,
        )
        for page in codex.list_pages():
            print(f"{page['name']}: {page['description']}")
        return

    if args.codex_chapters:
        codex = build_default_codex(
            active_branches=args.branches,
            deep_meaning_mode=args.gudhartha,
        )
        for chapter in codex.list_chapters():
            print(f"{chapter['name']}: {chapter['title']}")
            print(f"  pages: {', '.join(chapter['pages'])}")
        return

    if args.codex:
        input_path = Path(args.codex[0]).resolve()
        output_path = Path(args.codex[1]).resolve()
        try:
            codex = build_default_codex(
                active_branches=args.branches,
                deep_meaning_mode=args.gudhartha,
            )
            result = codex.transform_file(
                input_path,
                output_path,
                page=args.codex_page,
            )
            print(f"कोडेक्स रूपान्तरित स्रोत लिखा गया: {output_path}")
            print(result.report_text())
            if result.confidence == "do_not_touch" and not result.transformed:
                sys.exit(1)
            return
        except FileNotFoundError:
            print(f"Error: File not found: {input_path}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(format_vak_error_with_suggestions(e), file=sys.stderr)
            sys.exit(1)

    interpreter = VakInterpreter(
        active_branches=args.branches,
        deep_meaning_mode=args.gudhartha,
    )
    
    if args.file:
        try:
            source_path = Path(args.file).resolve()
            if source_path.suffix == '.vakc':
                if args.compile:
                    print(
                        "Error: --compile expects a .vak source file, not compiled bytecode",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                _handle_compiled_file(
                    source_path,
                    interpreter,
                    disassemble=args.disassemble,
                )
                return
            source = source_path.read_text(encoding='utf-8')
            prepared_source = interpreter.prepare_source(source)
            
            if args.compile:
                bytecode = interpreter.compile_only(
                    prepared_source,
                    filename=str(source_path),
                    source_prepared=True,
                )
                if interpreter.translation_status_message():
                    print(interpreter.translation_status_message())
                output_file = source_path.with_suffix('.vakc')
                _atomic_write_bytes(output_file, bytecode.to_bytes())
                companion_path = Bytecode.companion_path(output_file)
                _atomic_write_text(companion_path, bytecode.to_abi_json())
                print(f"Compiled to: {output_file}")
                print(f"Metadata to: {companion_path}")
                if args.disassemble:
                    print("\n" + bytecode.disassemble())
            else:
                result = interpreter.run(
                    prepared_source,
                    debug=args.debug,
                    filename=str(source_path),
                    source_prepared=True,
                )
                if interpreter.translation_status_message():
                    print(interpreter.translation_status_message())
                if result is not None:
                    print(result)
                    
        except FileNotFoundError:
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        except VakError as e:
            print(
                format_vak_error_with_suggestions(
                    e,
                    {
                        "frame": interpreter.vm.current_frame,
                        "globals": interpreter.vm.globals,
                        "builtins": interpreter.vm.builtins,
                    },
                ),
                file=sys.stderr,
            )
            sys.exit(1)
        except Exception as e:
            print(
                format_vak_error_with_suggestions(
                    e,
                    {
                        "frame": interpreter.vm.current_frame,
                        "globals": interpreter.vm.globals,
                        "builtins": interpreter.vm.builtins,
                    },
                ),
                file=sys.stderr,
            )
            if args.debug:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    else:
        # Start REPL
        interpreter.repl()

if __name__ == '__main__':
    main()
