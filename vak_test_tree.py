#!/usr/bin/env python3
"""
VakyaLang tree test runner.

Runs the repository test surface as a subsystem tree so leaf failures are
reported with a stable path such as:

    vak-tree/python/unittest-discover
    vak-tree/vak/source-tests/full_test_clean
    vak-tree/native/rust-tests
"""

from __future__ import annotations

from dataclasses import dataclass, field
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parent


def _safe_print(*args, **kwargs) -> None:
    file = kwargs.pop("file", sys.stdout)
    sep = kwargs.pop("sep", " ")
    end = kwargs.pop("end", "\n")
    flush = kwargs.pop("flush", False)
    if kwargs:
        raise TypeError(f"Unsupported print kwargs: {', '.join(kwargs)}")

    text = sep.join(str(arg) for arg in args) + end
    try:
        file.write(text)
    except UnicodeEncodeError:
        encoding = getattr(file, "encoding", None) or "utf-8"
        safe_text = text.encode(encoding, errors="backslashreplace").decode(
            encoding,
            errors="replace",
        )
        file.write(safe_text)
    if flush and hasattr(file, "flush"):
        file.flush()


print = _safe_print


@dataclass(frozen=True)
class CommandSpec:
    argv: tuple[str, ...]
    cwd: Path
    must_contain: tuple[str, ...] = ()


@dataclass
class TestNode:
    name: str
    description: str
    command: CommandSpec | None = None
    children: list["TestNode"] = field(default_factory=list)

    @property
    def is_leaf(self) -> bool:
        return self.command is not None


def _python_command(*args: str, cwd: Path | None = None, must_contain: Iterable[str] = ()) -> CommandSpec:
    return CommandSpec(
        argv=(sys.executable, *args),
        cwd=cwd or REPO_ROOT,
        must_contain=tuple(must_contain),
    )


def _cargo_command(*args: str, cwd: Path, must_contain: Iterable[str] = ()) -> CommandSpec:
    cargo_path = shutil.which("cargo")
    if not cargo_path and os.name == "nt":
        fallback = Path.home() / ".cargo" / "bin" / "cargo.exe"
        if fallback.exists():
            cargo_path = str(fallback)

    argv: tuple[str, ...]
    if os.name == "nt":
        argv = (cargo_path or "cargo", "+stable-x86_64-pc-windows-gnu", *args)
    else:
        argv = (cargo_path or "cargo", *args)
    return CommandSpec(
        argv=argv,
        cwd=cwd,
        must_contain=tuple(must_contain),
    )


def build_test_tree(repo_root: Path | None = None) -> TestNode:
    root = repo_root or REPO_ROOT
    native_root = root / "native" / "vakvm-rs"

    vak_source_tests = [
        "tests/full_test.vak",
        "tests/full_test_clean.vak",
        "tests/integration_test.vak",
        "tests/master_test.vak",
        "tests/test_container_sangrah.vak",
        "tests/test_core_builtins.vak",
        "tests/test_http.vak",
        "tests/test_matrix_ganit.vak",
        "tests/test_stdlib.vak",
        "tests/test_stdlib_file.vak",
        "tests/test_system.vak",
    ]

    return TestNode(
        name="vak-tree",
        description="Full VakyaLang validation tree",
        children=[
            TestNode(
                name="python",
                description="Python unit, script, and ecosystem tests",
                children=[
                    TestNode(
                        name="unittest-discover",
                        description="All unittest-discoverable Python suites",
                        command=_python_command(
                            "-m",
                            "unittest",
                            "discover",
                            "-s",
                            "tests",
                            "-p",
                            "test_*.py",
                            must_contain=("OK",),
                        ),
                    ),
                    TestNode(
                        name="month2-3-script",
                        description="Script-style advanced feature suite",
                        command=_python_command(
                            "tests/test_month2_3_features.py",
                            must_contain=("ALL TESTS PASSED!",),
                        ),
                    ),
                    TestNode(
                        name="sanskrit-coder-script",
                        description="Direct Sanskrit Coder script suite",
                        command=_python_command(
                            "tests/test_sanskrit_coder.py",
                            must_contain=("Passed",),
                        ),
                    ),
                    TestNode(
                        name="live-features-smoke",
                        description="Live Sanskrit Coder feature smoke path",
                        command=_python_command(
                            "tests/test_live_features.py",
                            must_contain=("Sanskrit Coder - Live Features Test",),
                        ),
                    ),
                ],
            ),
            TestNode(
                name="vak",
                description="Vak source, examples, and runtime paths",
                children=[
                    TestNode(
                        name="runtime-examples",
                        description="Example and stdlib runtime suite",
                        command=_python_command(
                            "runtime/run_tests.py",
                            must_contain=("All tests PASSED!",),
                        ),
                    ),
                    TestNode(
                        name="source-tests",
                        description="Direct .vak test programs",
                        children=[
                            TestNode(
                                name=Path(relative_path).stem,
                                description=f"Direct execution of {relative_path}",
                                command=_python_command("vak.py", relative_path),
                            )
                            for relative_path in vak_source_tests
                        ],
                    ),
                ],
            ),
            TestNode(
                name="ecosystem",
                description="Top-level integration audits",
                children=[
                    TestNode(
                        name="master-audit",
                        description="Repository-wide truth audit",
                        command=_python_command(
                            "master_test.py",
                            must_contain=("FINAL VERDICT: 100% PRODUCTION READY",),
                        ),
                    ),
                ],
            ),
            TestNode(
                name="native",
                description="Native Rust VM validation",
                children=[
                    TestNode(
                        name="rust-tests",
                        description="Rust VM unit and doc tests",
                        command=_cargo_command("test", cwd=native_root),
                    ),
                ],
            ),
        ],
    )


def iter_leaves(node: TestNode, prefix: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], TestNode]]:
    path = (*prefix, node.name)
    if node.is_leaf:
        yield path, node
        return
    for child in node.children:
        yield from iter_leaves(child, path)


def find_leaf(node: TestNode, target_path: str) -> tuple[tuple[str, ...], TestNode] | None:
    normalized = tuple(part for part in target_path.split("/") if part)
    for path, leaf in iter_leaves(node):
        if path == normalized or path[-len(normalized):] == normalized:
            return path, leaf
    return None


def validate_tree(node: TestNode) -> None:
    child_names = [child.name for child in node.children]
    if len(child_names) != len(set(child_names)):
        raise ValueError(f"Duplicate child names under {node.name}")
    if node.is_leaf and node.children:
        raise ValueError(f"Leaf node {node.name} cannot also have children")
    if not node.is_leaf and not node.children:
        raise ValueError(f"Non-leaf node {node.name} must have children")
    for child in node.children:
        validate_tree(child)


def _run_leaf(path: tuple[str, ...], leaf: TestNode, *, show_output_on_pass: bool = False) -> dict:
    assert leaf.command is not None

    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    label = "/".join(path)
    started = time.time()
    try:
        result = subprocess.run(
            leaf.command.argv,
            cwd=leaf.command.cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            check=False,
        )
    except FileNotFoundError as exc:
        duration = time.time() - started
        missing_executable = leaf.command.argv[0]
        skip_reason = f"missing executable: {missing_executable}"
        print(f"[SKIP] {label} ({duration:.2f}s) - {skip_reason}")
        return {
            "path": label,
            "description": leaf.description,
            "passed": False,
            "skipped": True,
            "returncode": None,
            "duration_seconds": round(duration, 3),
            "missing_markers": [],
            "skip_reason": str(exc),
        }

    duration = time.time() - started
    stdout = result.stdout or ""
    stderr = result.stderr or ""

    missing_markers = [
        marker for marker in leaf.command.must_contain
        if marker not in stdout and marker not in stderr
    ]
    passed = result.returncode == 0 and not missing_markers

    print(f"[{'PASS' if passed else 'FAIL'}] {label} ({duration:.2f}s)")
    if show_output_on_pass and passed and stdout.strip():
        print(stdout.strip())
    if not passed:
        print("--- COMMAND ---")
        print(" ".join(leaf.command.argv))
        print("--- STDOUT ---")
        print(stdout)
        print("--- STDERR ---")
        print(stderr)
        if missing_markers:
            print("--- MISSING MARKERS ---")
            print(", ".join(missing_markers))

    return {
        "path": label,
        "description": leaf.description,
        "passed": passed,
        "skipped": False,
        "returncode": result.returncode,
        "duration_seconds": round(duration, 3),
        "missing_markers": missing_markers,
    }


def _print_tree(node: TestNode, prefix: str = "") -> None:
    print(f"{prefix}{node.name} - {node.description}")
    for child in node.children:
        _print_tree(child, prefix + "  ")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VakyaLang tree test runner")
    parser.add_argument("--list", action="store_true", help="List the test tree and exit")
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        help="Run only a leaf path, for example python/unittest-discover",
    )
    parser.add_argument("--fail-fast", action="store_true", help="Stop at first failing leaf")
    parser.add_argument("--json-out", help="Write a JSON summary to the given path")
    parser.add_argument(
        "--show-output-on-pass",
        action="store_true",
        help="Print successful command output in addition to the summary",
    )
    args = parser.parse_args(argv)

    tree = build_test_tree()
    validate_tree(tree)

    if args.list:
        _print_tree(tree)
        return 0

    selected: list[tuple[tuple[str, ...], TestNode]] = []
    if args.only:
        for requested in args.only:
            match = find_leaf(tree, requested)
            if match is None:
                print(f"Unknown leaf path: {requested}", file=sys.stderr)
                return 2
            selected.append(match)
    else:
        selected = list(iter_leaves(tree))

    seen_paths = set()
    unique_selected: list[tuple[tuple[str, ...], TestNode]] = []
    for path, leaf in selected:
        label = "/".join(path)
        if label not in seen_paths:
            unique_selected.append((path, leaf))
            seen_paths.add(label)

    print(f"Running {len(unique_selected)} tree leaves...")
    results = []
    for path, leaf in unique_selected:
        result = _run_leaf(path, leaf, show_output_on_pass=args.show_output_on_pass)
        results.append(result)
        if args.fail_fast and not result["passed"] and not result.get("skipped", False):
            break

    passed = sum(1 for item in results if item["passed"])
    skipped = sum(1 for item in results if item.get("skipped", False))
    failed = len(results) - passed - skipped
    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "repo_root": str(REPO_ROOT),
        "passed": passed,
        "skipped": skipped,
        "failed": failed,
        "results": results,
    }

    print(f"\nSummary: {passed} passed, {skipped} skipped, {failed} failed")
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(summary, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
