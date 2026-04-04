#!/usr/bin/env python3
# वाक् भाषा - CLI Entry Point

import sys
import argparse
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from runtime.src.interpreter import VakInterpreter
from runtime.src.errors import VakError, format_vak_error_with_suggestions
from runtime.src.rupantar import VakyaRupantar

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

    interpreter = VakInterpreter(
        active_branches=args.branches,
        deep_meaning_mode=args.gudhartha,
    )
    
    if args.file:
        try:
            source_path = Path(args.file).resolve()
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
                output_file.write_bytes(bytecode.to_bytes())
                print(f"Compiled to: {output_file}")
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
