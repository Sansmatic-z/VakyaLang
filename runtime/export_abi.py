#!/usr/bin/env python3
"""Export VakyaLang source to the stable bytecode ABI JSON format."""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from runtime.src.interpreter import VakInterpreter
except ImportError:
    from src.interpreter import VakInterpreter


def compile_file(path: str | Path) -> str:
    path = Path(path)
    source = path.read_text(encoding="utf-8")
    interpreter = VakInterpreter()
    bytecode = interpreter.compile_only(source, filename=str(path))
    return bytecode.to_abi_json()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export a .vak program to VakyaLang bytecode ABI JSON."
    )
    parser.add_argument("input", help="Input .vak source file")
    parser.add_argument(
        "-o",
        "--output",
        help="Optional output path. Defaults to stdout.",
    )
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    abi_json = compile_file(input_path)

    if args.output:
        output_path = Path(args.output).resolve()
        output_path.write_text(abi_json, encoding="utf-8")
    else:
        print(abi_json)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
