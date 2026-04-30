from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from runtime.src.interpreter import VakInterpreter


def main() -> int:
    parser = argparse.ArgumentParser(description="Profile Vak parser/compiler/VM/import stages.")
    parser.add_argument("source", nargs="?", help="Vak source file to profile")
    parser.add_argument("--import", dest="import_name", help="Profile import of a module name")
    parser.add_argument("--repeat", type=int, default=3, help="Number of profiling iterations")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()

    interpreter = VakInterpreter()

    if args.import_name:
        profile = interpreter.profile_import(args.import_name, repeat=max(args.repeat, 1))
    elif args.source:
        source_path = Path(args.source)
        source = source_path.read_text(encoding="utf-8")
        profile = interpreter.profile_source(
            source,
            filename=str(source_path),
            repeat=max(args.repeat, 1),
        )
    else:
        parser.error("either a source file or --import must be supplied")

    if args.json:
        print(json.dumps(profile.payload(), ensure_ascii=False, indent=2))
    else:
        print(profile.text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
