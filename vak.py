#!/usr/bin/env python3
# वाक् भाषा - CLI Entry Point

import sys
import argparse
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from runtime.src.interpreter import VakInterpreter
from runtime.src.errors import VakError

def main():
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
    parser.add_argument('--version', '-v', action='version', version='%(prog)s 2.0.0')
    
    args = parser.parse_args()
    interpreter = VakInterpreter()
    
    if args.file:
        try:
            source = Path(args.file).read_text(encoding='utf-8')
            
            if args.compile:
                bytecode = interpreter.compile_only(source)
                output_file = Path(args.file).with_suffix('.vakc')
                output_file.write_bytes(bytecode.to_bytes())
                print(f"Compiled to: {output_file}")
                if args.disassemble:
                    print("\n" + bytecode.disassemble())
            else:
                result = interpreter.run(source, debug=args.debug)
                if result is not None:
                    print(result)
                    
        except FileNotFoundError:
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        except VakError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Internal error: {e}", file=sys.stderr)
            if args.debug:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    else:
        # Start REPL
        interpreter.repl()

if __name__ == '__main__':
    main()
