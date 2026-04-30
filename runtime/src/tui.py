from __future__ import annotations

import argparse
import contextlib
import difflib
import io
import os
import shlex
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

from branches.chitrakala.runtime import build_chitrakala_builtins
from sansmatic.src.engine import SansmaticEngine
from vpm import PACKAGE_DIR, VakPackageManager

from .errors import format_vak_error_with_suggestions
from .interpreter import VakInterpreter
from .codex import CodexResult, build_default_codex
from .runtime_catalog import format_builtin_help
from .rupantar import RupantarResult, VakyaRupantar
from .stdlib_manifest import format_stdlib_manifest

try:
    from rich import box
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table

    RICH_AVAILABLE = True
except Exception:
    box = None
    Console = None
    Layout = None
    Panel = None
    Table = None
    RICH_AVAILABLE = False


MODE_LABELS = {
    "main": "मुख्य",
    "repl": "REPL",
    "sandbox": "आयाम",
    "proof": "सान्समैटिक",
    "chitra": "चित्रकला",
    "vpm": "VPM",
    "repair": "रूपान्तर",
    "codex": "कोडेक्स",
}

MODE_ALIASES = {
    "main": "main",
    "मुख्य": "main",
    "repl": "repl",
    "sandbox": "sandbox",
    "sandboxes": "sandbox",
    "आयाम": "sandbox",
    "proof": "proof",
    "sansmatic": "proof",
    "सान्समैटिक": "proof",
    "चित्रकला": "chitra",
    "chitra": "chitra",
    "chitrakala": "chitra",
    "graphics": "chitra",
    "vpm": "vpm",
    "package": "vpm",
    "packages": "vpm",
    "repair": "repair",
    "rupantar": "repair",
    "रूपान्तर": "repair",
    "codex": "codex",
    "कोडेक्स": "codex",
}


class _PlainConsole:
    def clear(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")

    def print(self, value: Any = "") -> None:
        try:
            print(value)
        except UnicodeEncodeError:
            encoding = sys.stdout.encoding or "utf-8"
            text = str(value).encode(encoding, errors="backslashreplace").decode(
                encoding,
                errors="replace",
            )
            sys.stdout.write(f"{text}\n")

    def input(self, prompt: str = "") -> str:
        return input(prompt)


@dataclass
class SandboxState:
    name: str
    interpreter: VakInterpreter
    history: list[str] = field(default_factory=list)
    last_output: str = ""

    def globals_count(self) -> int:
        return len(self.interpreter.vm.globals)


class VakTuiError(Exception):
    """Raised for user-facing TUI command errors."""


class VakTuiApp:
    """
    वाक् TUI — Terminal UI environment for VakyaLang.

    This is intentionally command-driven instead of raw-key dependent so it
    remains reliable across Windows, Linux, and Termux without changing core
    runtime behavior.
    """

    def __init__(
        self,
        *,
        cwd: str | Path | None = None,
        use_rich: bool | None = None,
        clear_screen: bool = True,
    ):
        self.cwd = Path(cwd or os.getcwd()).resolve()
        self.use_rich = bool(
            RICH_AVAILABLE if use_rich is None else (use_rich and RICH_AVAILABLE)
        )
        self.clear_screen = clear_screen
        self.console = Console() if self.use_rich else _PlainConsole()

        self.mode = "main"
        self.running = True
        self.status_message = "वाक् TUI तैयार"
        self.activity_log: list[str] = []

        self.sandboxes: dict[str, SandboxState] = {}
        self.active_sandbox = "default"
        self._create_sandbox("default")

        self.repl_log: list[str] = []

        self.sansmatic = SansmaticEngine(verbose=False)
        self.proof_log: list[str] = []
        self.proof_snapshots: dict[str, dict[str, Any]] = {}

        self.chitra_support = build_chitrakala_builtins()
        self.chitra_canvas = None
        self.chitra_last_saved: str | None = None
        self.chitra_preview_cols = 48
        self.chitra_preview_rows = 18
        if self.chitra_support.available:
            self._new_canvas(96, 48, "white")

        self.vpm = VakPackageManager(str(self.cwd))
        self.vpm_last_output = ""
        self.vpm_last_search: list[dict[str, Any]] = []
        self.vpm_last_info: dict[str, Any] | None = None
        self.vpm_last_cache: dict[str, Any] | None = None
        self.repair_file: Path | None = None
        self.repair_original_source = ""
        self.repair_result: RupantarResult | None = None
        self.repair_branches: tuple[str, ...] = ()
        self.codex_file: Path | None = None
        self.codex_original_source = ""
        self.codex_result: CodexResult | None = None
        self.codex_branches: tuple[str, ...] = ()
        self.codex_page = "auto"

    # ---- Generic helpers -------------------------------------------------

    def _record(self, message: str) -> str:
        self.status_message = message
        self.activity_log.append(message)
        self.activity_log = self.activity_log[-40:]
        return message

    def _resolve_mode(self, value: str) -> str:
        key = MODE_ALIASES.get(value.strip().lower()) or MODE_ALIASES.get(value.strip())
        if key is None:
            raise VakTuiError(f"अज्ञात मोड (unknown mode): {value}")
        return key

    def set_mode(self, value: str) -> str:
        self.mode = self._resolve_mode(value)
        return self._record(f"मोड बदला गया: {MODE_LABELS[self.mode]}")

    def prompt(self) -> str:
        prompts = {
            "main": "वाक्-tui> ",
            "repl": f"वाक्[{self.active_sandbox}]> ",
            "sandbox": "आयाम> ",
            "proof": "प्रमाण> ",
            "chitra": "चित्र> ",
            "vpm": "vpm> ",
            "repair": "रूपान्तर> ",
            "codex": "कोडेक्स> ",
        }
        return prompts[self.mode]

    def mode_help(self) -> str:
        common = (
            "सामान्य आदेश:\n"
            "  help                   सहायता दिखाओ\n"
            "  mode <name>            मोड बदलो (main/repl/sandbox/proof/chitra/vpm/repair)\n"
            "                        या codex\n"
            "  modes                  सभी मोड दिखाओ\n"
            "  builtins [category]    उपलब्ध builtins दिखाओ\n"
            "  modules                stdlib मानचित्र दिखाओ\n"
            "  render                 वर्तमान पटल दोबारा दिखाओ\n"
            "  quit                   बाहर निकलो\n"
        )
        per_mode = {
            "main": (
                "मुख्य आदेश:\n"
                "  open repl|sandbox|proof|chitra|vpm|repair|codex\n"
            ),
            "repl": (
                "REPL आदेश:\n"
                "  <वाक् कोड>            सक्रिय आयाम में चलाओ\n"
                "  :block                 बहु-पंक्ति वाक् ब्लॉक प्रविष्टि\n"
                "  :stack                 वर्तमान Vak स्टैक निरीक्षण\n"
                "  :globals               वर्तमान वैश्विक नाम\n"
            ),
            "sandbox": (
                "आयाम आदेश:\n"
                "  list\n"
                "  new <name>\n"
                "  switch <name>\n"
                "  reset [name]\n"
                "  drop <name>\n"
                "  globals [name]\n"
                "  stack [name]\n"
            ),
            "proof": (
                "सान्समैटिक आदेश:\n"
                "  define <name> <prop...>\n"
                "  assert <entity> <relation> <property> [proof_id]\n"
                "  rule <a b c> => <x y z>\n"
                "  theorem list [tag]\n"
                "  theorem show <name>\n"
                "  theorem fact <name> <entity> <relation> <property>\n"
                "  theorem rule <name> <a b c> => <x y z>\n"
                "  eval <entity> <relation> <property>\n"
                "  backward <entity> <relation> <property>\n"
                "  summary\n"
                "  trace [limit]\n"
                "  tree <entity> <relation> <property>\n"
                "  explain <entity> <relation> <property>\n"
                "  snapshot [name]\n"
                "  restore [name]\n"
                "  reset\n"
            ),
            "chitra": (
                "चित्रकला आदेश:\n"
                "  new <w> <h> [color]\n"
                "  fill <color>\n"
                "  line <x0> <y0> <x1> <y1> [color]\n"
                "  rect <x> <y> <w> <h> [color] [fill]\n"
                "  circle <x> <y> <r> [color] [fill]\n"
                "  text <x> <y> <text> [color] [scale]\n"
                "  center <y> <text> [color] [scale]\n"
                "  gradient <c1> <c2>\n"
                "  mandala [cx cy radius petals]\n"
                "  rotate <angle>\n"
                "  kaleidoscope <segments>\n"
                "  save <path>\n"
                "  load <path>\n"
                "  preview [cols rows]\n"
            ),
            "vpm": (
                "VPM आदेश:\n"
                "  init\n"
                "  installed\n"
                "  python\n"
                "  search <query>\n"
                "  info <package>\n"
                "  install <package>\n"
                "  remove <package>\n"
                "  remove-py <package>\n"
                "  update [package]\n"
                "  lock\n"
                "  cache [info|clear]\n"
                "  cwd <path>\n"
            ),
            "repair": (
                "रूपान्तर आदेश:\n"
                "  load|open <path>\n"
                "  reload\n"
                "  workspace\n"
                "  branches [name...]\n"
                "  branch <name> [on|off|toggle]\n"
                "  analyze\n"
                "  report\n"
                "  diff\n"
                "  show original|current\n"
                "  apply [path]\n"
                "  save [path]\n"
                "  reject\n"
            ),
            "codex": (
                "कोडेक्स आदेश:\n"
                "  load|open <path>\n"
                "  reload\n"
                "  workspace\n"
                "  chapters\n"
                "  pages\n"
                "  page <name|auto>\n"
                "  branches [name...]\n"
                "  branch <name> [on|off|toggle]\n"
                "  promotion [page]\n"
                "  analyze\n"
                "  report\n"
                "  diff\n"
                "  show original|current\n"
                "  apply [path]\n"
                "  save [path]\n"
                "  reject\n"
            ),
        }
        return common + "\n" + per_mode[self.mode]

    def run_commands(self, commands: Iterable[str]) -> list[str]:
        outputs = []
        for command in commands:
            outputs.append(self.execute_command(command))
        return outputs

    # ---- Sandbox / REPL --------------------------------------------------

    def _create_sandbox(self, name: str) -> SandboxState:
        sandbox = SandboxState(name=name, interpreter=VakInterpreter())
        self.sandboxes[name] = sandbox
        return sandbox

    def _get_sandbox(self, name: str | None = None) -> SandboxState:
        sandbox_name = name or self.active_sandbox
        try:
            return self.sandboxes[sandbox_name]
        except KeyError as error:
            raise VakTuiError(f"आयाम नहीं मिला: {sandbox_name}") from error

    def _execute_vak_source(self, source: str, *, sandbox_name: str | None = None) -> str:
        sandbox = self._get_sandbox(sandbox_name)
        buffer = io.StringIO()
        try:
            with contextlib.redirect_stdout(buffer):
                result = sandbox.interpreter.run(
                    source,
                    filename=f"<tui:{sandbox.name}>",
                )
        except Exception as error:
            rendered = format_vak_error_with_suggestions(
                error,
                sandbox.interpreter.error_context(),
            )
            sandbox.last_output = rendered
            self.repl_log.append(rendered)
            return self._record(rendered)

        output = buffer.getvalue().strip()
        messages: list[str] = []
        if output:
            messages.extend(output.splitlines())
        translation_message = sandbox.interpreter.translation_status_message()
        if translation_message:
            messages.append(translation_message)
        if result is not None:
            messages.append(f"=> {result}")
        if not messages:
            messages.append("✓ निष्पादन पूर्ण")
        combined = "\n".join(messages)
        sandbox.history.append(source)
        sandbox.last_output = combined
        self.repl_log.extend(messages)
        self.repl_log = self.repl_log[-30:]
        return self._record(combined)

    # ---- Sansmatic -------------------------------------------------------

    def _parse_fact_parts(self, parts: list[str]) -> tuple[str, str, str]:
        if len(parts) < 3:
            raise VakTuiError("त्रिक अपेक्षित: entity relation property")
        return parts[0], parts[1], parts[2]

    def _handle_proof_command(self, command: str) -> str:
        parts = shlex.split(command)
        if not parts:
            return self.status_message
        op = parts[0].lower()
        if op == "define":
            if len(parts) < 3:
                raise VakTuiError("define <name> <prop...> अपेक्षित")
            result = self.sansmatic.define(parts[1], parts[2:])
        elif op == "assert":
            if len(parts) < 4:
                raise VakTuiError("assert <entity> <relation> <property> [proof_id] अपेक्षित")
            proof_id = parts[4] if len(parts) > 4 else None
            result = self.sansmatic.assert_fact(parts[1], parts[2], parts[3], proof_id)
        elif op == "rule":
            if "=>" not in parts:
                raise VakTuiError("rule <a b c> => <x y z> अपेक्षित")
            arrow_index = parts.index("=>")
            left = parts[1:arrow_index]
            right = parts[arrow_index + 1 :]
            premise = self._parse_fact_parts(left)
            conclusion = self._parse_fact_parts(right)
            result = self.sansmatic.rule(premise, conclusion)
        elif op in {"eval", "evaluate"}:
            if len(parts) < 4:
                raise VakTuiError("eval <entity> <relation> <property> अपेक्षित")
            result = self.sansmatic.evaluate(parts[1], parts[2], parts[3])
        elif op in {"prove", "backward"}:
            if len(parts) < 4:
                raise VakTuiError("backward <entity> <relation> <property> अपेक्षित")
            proved = self.sansmatic.backward_chain((parts[1], parts[2], parts[3]))
            result = "✓ लक्ष्य सिद्ध है" if proved else "✗ लक्ष्य सिद्ध नहीं है"
        elif op == "summary":
            result = self.sansmatic.summary_text()
        elif op == "trace":
            limit = int(parts[1]) if len(parts) > 1 else 10
            result = self.sansmatic.trace_text(limit=limit)
        elif op == "tree":
            if len(parts) < 4:
                raise VakTuiError("tree <entity> <relation> <property> अपेक्षित")
            result = self.sansmatic.proof_tree_text((parts[1], parts[2], parts[3]))
        elif op == "explain":
            if len(parts) < 4:
                raise VakTuiError("explain <entity> <relation> <property> अपेक्षित")
            result = self.sansmatic.explain_text((parts[1], parts[2], parts[3]))
        elif op == "theorems":
            rows = self.sansmatic.list_theorems(parts[1] if len(parts) > 1 else None)
            if not rows:
                result = "कोई प्रमेय पंजीकृत नहीं"
            else:
                lines = ["प्रमेय सूची"]
                for item in rows:
                    suffix = ""
                    if "proved" in item:
                        suffix = f" | सिद्ध={'हाँ' if item['proved'] else 'नहीं'}"
                    if "active" in item:
                        suffix = f"{suffix} | सक्रिय={'हाँ' if item['active'] else 'नहीं'}"
                    lines.append(
                        f"- {item['name']} [{item['kind']}] {item['statement']}{suffix}"
                    )
                result = "\n".join(lines)
        elif op == "theorem":
            if len(parts) < 2:
                raise VakTuiError("theorem list|show|fact|rule अपेक्षित")
            subop = parts[1].lower()
            if subop == "list":
                rows = self.sansmatic.list_theorems(parts[2] if len(parts) > 2 else None)
                if not rows:
                    result = "कोई प्रमेय पंजीकृत नहीं"
                else:
                    lines = ["प्रमेय सूची"]
                    for item in rows:
                        lines.append(f"- {item['name']} [{item['kind']}] {item['statement']}")
                    result = "\n".join(lines)
            elif subop == "show":
                if len(parts) < 3:
                    raise VakTuiError("theorem show <name> अपेक्षित")
                detail = self.sansmatic.theorem_details(parts[2])
                if detail is None:
                    raise VakTuiError(f"अज्ञात प्रमेय: {parts[2]}")
                lines = [
                    f"प्रमेय: {detail['name']}",
                    f"प्रकार: {detail['kind']}",
                ]
                if "statement" in detail:
                    lines.append(f"वचन: {detail['statement']}")
                if "premise" in detail and "conclusion" in detail:
                    lines.append(f"नियम: {detail['premise']} ⇒ {detail['conclusion']}")
                if "proved" in detail:
                    lines.append(f"सिद्ध: {'हाँ' if detail['proved'] else 'नहीं'}")
                if detail.get("blocked_by"):
                    lines.append(f"अवरोध: {', '.join(detail['blocked_by'])}")
                if detail.get("tags"):
                    lines.append(f"टैग: {', '.join(detail['tags'])}")
                if detail.get("note"):
                    lines.append(f"टिप्पणी: {detail['note']}")
                result = "\n".join(lines)
            elif subop == "fact":
                if len(parts) < 6:
                    raise VakTuiError("theorem fact <name> <entity> <relation> <property> अपेक्षित")
                payload = self.sansmatic.register_theorem(
                    parts[2],
                    (parts[3], parts[4], parts[5]),
                    note=" ".join(parts[6:]) if len(parts) > 6 else None,
                )
                result = f"प्रमेय पंजीकृत: {payload['name']}"
            elif subop == "rule":
                if "=>" not in parts:
                    raise VakTuiError("theorem rule <name> <a b c> => <x y z> अपेक्षित")
                if len(parts) < 4:
                    raise VakTuiError("theorem rule <name> <a b c> => <x y z> अपेक्षित")
                arrow_index = parts.index("=>")
                theorem_name = parts[2]
                left = parts[3:arrow_index]
                right = parts[arrow_index + 1 :]
                premise = self._parse_fact_parts(left)
                conclusion = self._parse_fact_parts(right)
                payload = self.sansmatic.register_rule_theorem(theorem_name, premise, conclusion)
                result = f"प्रमेय नियम पंजीकृत: {payload['name']}"
            else:
                raise VakTuiError("theorem list|show|fact|rule अपेक्षित")
        elif op == "snapshot":
            name = parts[1] if len(parts) > 1 else f"snapshot_{len(self.proof_snapshots) + 1}"
            self.proof_snapshots[name] = self.sansmatic.snapshot()
            result = f"प्रमाण स्नैपशॉट सुरक्षित: {name}"
        elif op == "restore":
            if len(parts) > 1:
                name = parts[1]
                state = self.proof_snapshots.get(name)
                if state is None:
                    raise VakTuiError(f"अज्ञात स्नैपशॉट: {name}")
                restored = self.sansmatic.restore(state)
                result = f"प्रमाण स्नैपशॉट पुनर्स्थापित: {name}" if restored else f"स्नैपशॉट पुनर्स्थापन विफल: {name}"
            else:
                restored = self.sansmatic.restore()
                result = "अंतिम प्रमाण स्नैपशॉट पुनर्स्थापित" if restored else "कोई उपलब्ध स्नैपशॉट नहीं"
        elif op == "reset":
            self.sansmatic = SansmaticEngine(verbose=False)
            result = "सान्समैटिक अवस्था रीसेट की गई"
        else:
            raise VakTuiError(f"अज्ञात सान्समैटिक आदेश: {parts[0]}")
        self.proof_log.append(result)
        self.proof_log = self.proof_log[-20:]
        return self._record(result)

    # ---- Repair workspace -----------------------------------------------

    def _resolve_workspace_path(self, raw_path: str) -> Path:
        path = Path(raw_path)
        if not path.is_absolute():
            path = self.cwd / path
        return path.resolve()

    def _default_workspace_save_path(self, target: Path | None, suffix: str) -> Path:
        if target is None:
            return (self.cwd / suffix).resolve()
        return target.with_name(f"{target.stem}.{suffix}{target.suffix}")

    @staticmethod
    def _toggle_workspace_branch(
        branches: tuple[str, ...],
        name: str,
        action: str,
    ) -> tuple[str, ...]:
        updated = list(branches)
        exists = name in updated
        mode = action.lower()
        if mode == "toggle":
            mode = "off" if exists else "on"
        if mode == "on" and not exists:
            updated.append(name)
        elif mode == "off" and exists:
            updated.remove(name)
        return tuple(updated)

    def _workspace_summary(
        self,
        *,
        kind: str,
        file: Path | None,
        branches: tuple[str, ...],
        page: str | None = None,
        analyzed: bool = False,
    ) -> str:
        lines = [
            f"कार्यस्थल: {kind}",
            f"फ़ाइल: {file if file is not None else 'कोई नहीं'}",
            f"शाखाएँ: {', '.join(branches) if branches else 'कोई नहीं'}",
            f"विश्लेषण: {'हाँ' if analyzed else 'नहीं'}",
        ]
        if page is not None:
            lines.append(f"पृष्ठ: {page}")
        return "\n".join(lines)

    def _repair_diff_text(self) -> str:
        if self.repair_result is None or self.repair_file is None:
            return "कोई रूपान्तर परिणाम नहीं"
        diff = list(
            difflib.unified_diff(
                self.repair_original_source.splitlines(),
                self.repair_result.source.splitlines(),
                fromfile=str(self.repair_file),
                tofile=f"{self.repair_file} (रूपान्तरित)",
                lineterm="",
            )
        )
        if not diff:
            return "कोई अंतर नहीं"
        return "\n".join(diff[:120])

    def _codex_diff_text(self) -> str:
        if self.codex_result is None or self.codex_file is None:
            return "कोई कोडेक्स परिणाम नहीं"
        diff = list(
            difflib.unified_diff(
                self.codex_original_source.splitlines(),
                self.codex_result.source.splitlines(),
                fromfile=str(self.codex_file),
                tofile=f"{self.codex_file} (कोडेक्स)",
                lineterm="",
            )
        )
        if not diff:
            return "कोई अंतर नहीं"
        return "\n".join(diff[:120])

    def _handle_repair_command(self, command: str) -> str:
        parts = shlex.split(command)
        if not parts:
            return self.status_message
        op = parts[0].lower()
        if op in {"load", "open"}:
            if len(parts) < 2:
                raise VakTuiError("load <path> अपेक्षित")
            target = self._resolve_workspace_path(parts[1])
            self.repair_file = target
            self.repair_original_source = target.read_text(encoding="utf-8")
            self.repair_result = None
            return self._record(f"रूपान्तर फ़ाइल लोड हुई: {target}")
        if op == "reload":
            if self.repair_file is None:
                raise VakTuiError("पहले load <path> चलाएँ")
            self.repair_original_source = self.repair_file.read_text(encoding="utf-8")
            self.repair_result = None
            return self._record(f"रूपान्तर फ़ाइल पुनः लोड हुई: {self.repair_file}")
        if op == "workspace":
            return self._record(
                self._workspace_summary(
                    kind="रूपान्तर",
                    file=self.repair_file,
                    branches=self.repair_branches,
                    analyzed=self.repair_result is not None,
                )
            )
        if op == "branches":
            if len(parts) == 1:
                if self.repair_branches:
                    return self._record(f"रूपान्तर शाखाएँ: {', '.join(self.repair_branches)}")
                return self._record("रूपान्तर शाखाएँ: कोई नहीं")
            self.repair_branches = tuple(parts[1:])
            if self.repair_branches:
                return self._record(f"रूपान्तर शाखाएँ: {', '.join(self.repair_branches)}")
            return self._record("रूपान्तर शाखाएँ साफ की गईं")
        if op == "branch":
            if len(parts) < 2:
                raise VakTuiError("branch <name> [on|off|toggle] अपेक्षित")
            action = parts[2] if len(parts) > 2 else "toggle"
            self.repair_branches = self._toggle_workspace_branch(
                self.repair_branches,
                parts[1],
                action,
            )
            if self.repair_branches:
                return self._record(f"रूपान्तर शाखाएँ: {', '.join(self.repair_branches)}")
            return self._record("रूपान्तर शाखाएँ: कोई नहीं")
        if op == "analyze":
            if self.repair_file is None:
                raise VakTuiError("पहले load <path> चलाएँ")
            engine = VakyaRupantar(active_branches=list(self.repair_branches))
            self.repair_result = engine.transform_source(
                self.repair_original_source,
                source_path=str(self.repair_file),
            )
            return self._record(self.repair_result.report_text())
        if op == "report":
            if self.repair_result is None:
                raise VakTuiError("पहले analyze चलाएँ")
            return self._record(self.repair_result.report_text())
        if op == "diff":
            return self._record(self._repair_diff_text())
        if op == "show":
            if len(parts) < 2:
                raise VakTuiError("show original|current अपेक्षित")
            target = parts[1].lower()
            if target == "original":
                if not self.repair_original_source:
                    raise VakTuiError("कोई मूल स्रोत नहीं")
                return self._record(self.repair_original_source)
            if target == "current":
                if self.repair_result is None:
                    raise VakTuiError("पहले analyze चलाएँ")
                return self._record(self.repair_result.source)
            raise VakTuiError("show original|current अपेक्षित")
        if op == "apply":
            if self.repair_result is None:
                raise VakTuiError("पहले analyze चलाएँ")
            target = self.repair_file if len(parts) < 2 else self._resolve_workspace_path(parts[1])
            if target is None:
                raise VakTuiError("कोई लक्ष्य फ़ाइल नहीं")
            target.write_text(self.repair_result.source, encoding="utf-8")
            if self.repair_file is not None and target == self.repair_file:
                self.repair_original_source = self.repair_result.source
                self.repair_result = None
            return self._record(f"रूपान्तर परिणाम लिखा गया: {target}")
        if op == "save":
            if self.repair_result is None:
                raise VakTuiError("पहले analyze चलाएँ")
            target = (
                self._default_workspace_save_path(self.repair_file, "rupantar")
                if len(parts) < 2
                else self._resolve_workspace_path(parts[1])
            )
            target.write_text(self.repair_result.source, encoding="utf-8")
            return self._record(f"रूपान्तर सहेजा गया: {target}")
        if op == "reject":
            self.repair_result = None
            return self._record("रूपान्तर परिणाम हटाया गया")
        raise VakTuiError(f"अज्ञात रूपान्तर आदेश: {parts[0]}")

    def _handle_codex_command(self, command: str) -> str:
        parts = shlex.split(command)
        if not parts:
            return self.status_message
        op = parts[0].lower()
        if op in {"load", "open"}:
            if len(parts) < 2:
                raise VakTuiError("load <path> अपेक्षित")
            target = self._resolve_workspace_path(parts[1])
            self.codex_file = target
            self.codex_original_source = target.read_text(encoding="utf-8")
            self.codex_result = None
            return self._record(f"कोडेक्स फ़ाइल लोड हुई: {target}")
        if op == "reload":
            if self.codex_file is None:
                raise VakTuiError("पहले load <path> चलाएँ")
            self.codex_original_source = self.codex_file.read_text(encoding="utf-8")
            self.codex_result = None
            return self._record(f"कोडेक्स फ़ाइल पुनः लोड हुई: {self.codex_file}")
        if op == "workspace":
            return self._record(
                self._workspace_summary(
                    kind="कोडेक्स",
                    file=self.codex_file,
                    branches=self.codex_branches,
                    page=self.codex_page,
                    analyzed=self.codex_result is not None,
                )
            )
        if op == "pages":
            codex = build_default_codex(active_branches=list(self.codex_branches))
            names = ", ".join(item["name"] for item in codex.list_pages())
            return self._record(f"उपलब्ध कोडेक्स पृष्ठ: {names}")
        if op == "chapters":
            codex = build_default_codex(active_branches=list(self.codex_branches))
            lines = []
            for chapter in codex.list_chapters():
                lines.append(f"{chapter['name']}: {chapter['title']}")
                lines.append(f"  पृष्ठ: {', '.join(chapter['pages'])}")
            return self._record("\n".join(lines) if lines else "कोई कोडेक्स अध्याय नहीं")
        if op == "page":
            if len(parts) < 2:
                return self._record(f"कोडेक्स पृष्ठ: {self.codex_page}")
            self.codex_page = parts[1]
            return self._record(f"कोडेक्स पृष्ठ: {self.codex_page}")
        if op == "branches":
            if len(parts) == 1:
                if self.codex_branches:
                    return self._record(f"कोडेक्स शाखाएँ: {', '.join(self.codex_branches)}")
                return self._record("कोडेक्स शाखाएँ: कोई नहीं")
            self.codex_branches = tuple(parts[1:])
            if self.codex_branches:
                return self._record(f"कोडेक्स शाखाएँ: {', '.join(self.codex_branches)}")
            return self._record("कोडेक्स शाखाएँ साफ की गईं")
        if op == "branch":
            if len(parts) < 2:
                raise VakTuiError("branch <name> [on|off|toggle] अपेक्षित")
            action = parts[2] if len(parts) > 2 else "toggle"
            self.codex_branches = self._toggle_workspace_branch(
                self.codex_branches,
                parts[1],
                action,
            )
            if self.codex_branches:
                return self._record(f"कोडेक्स शाखाएँ: {', '.join(self.codex_branches)}")
            return self._record("कोडेक्स शाखाएँ: कोई नहीं")
        if op == "promotion":
            target_page = parts[1] if len(parts) > 1 else self.codex_page
            codex = build_default_codex(active_branches=list(self.codex_branches))
            return self._record(codex.promotion_report(target_page).text())
        if op == "analyze":
            if self.codex_file is None:
                raise VakTuiError("पहले load <path> चलाएँ")
            codex = build_default_codex(active_branches=list(self.codex_branches))
            self.codex_result = codex.transform_source(
                self.codex_original_source,
                filename=str(self.codex_file),
                page=self.codex_page,
            )
            return self._record(self.codex_result.report_text())
        if op == "report":
            if self.codex_result is None:
                raise VakTuiError("पहले analyze चलाएँ")
            return self._record(self.codex_result.report_text())
        if op == "diff":
            return self._record(self._codex_diff_text())
        if op == "show":
            if len(parts) < 2:
                raise VakTuiError("show original|current अपेक्षित")
            target = parts[1].lower()
            if target == "original":
                if not self.codex_original_source:
                    raise VakTuiError("कोई मूल स्रोत नहीं")
                return self._record(self.codex_original_source)
            if target == "current":
                if self.codex_result is None:
                    raise VakTuiError("पहले analyze चलाएँ")
                return self._record(self.codex_result.source)
            raise VakTuiError("show original|current अपेक्षित")
        if op == "apply":
            if self.codex_result is None:
                raise VakTuiError("पहले analyze चलाएँ")
            target = self.codex_file if len(parts) < 2 else self._resolve_workspace_path(parts[1])
            if target is None:
                raise VakTuiError("कोई लक्ष्य फ़ाइल नहीं")
            target.write_text(self.codex_result.source, encoding="utf-8")
            if self.codex_file is not None and target == self.codex_file:
                self.codex_original_source = self.codex_result.source
                self.codex_result = None
            return self._record(f"कोडेक्स परिणाम लिखा गया: {target}")
        if op == "save":
            if self.codex_result is None:
                raise VakTuiError("पहले analyze चलाएँ")
            target = (
                self._default_workspace_save_path(self.codex_file, "codex")
                if len(parts) < 2
                else self._resolve_workspace_path(parts[1])
            )
            target.write_text(self.codex_result.source, encoding="utf-8")
            return self._record(f"कोडेक्स सहेजा गया: {target}")
        if op == "reject":
            self.codex_result = None
            return self._record("कोडेक्स परिणाम हटाया गया")
        raise VakTuiError(f"अज्ञात कोडेक्स आदेश: {parts[0]}")

    # ---- Chitrakala ------------------------------------------------------

    def _require_chitra(self) -> None:
        if not self.chitra_support.available:
            raise VakTuiError("चित्रकला समर्थन उपलब्ध नहीं है")

    def _new_canvas(self, width: int, height: int, color: str = "white") -> str:
        self._require_chitra()
        self.chitra_canvas = self.chitra_support.builtins["_chitra_canvas"](width, height, color)
        return self._record(f"चित्रफलक बनाया गया: {width}x{height}")

    def _parse_bool(self, value: str, default: bool = False) -> bool:
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "fill", "filled", "सत्य"}:
            return True
        if normalized in {"0", "false", "no", "outline", "असत्य"}:
            return False
        return default

    def _canvas_preview(self) -> str:
        if self.chitra_canvas is None:
            return "कोई चित्रफलक नहीं"
        chars = " .:-=+*#%@"
        width = min(self.chitra_preview_cols, self.chitra_canvas.width)
        height = min(self.chitra_preview_rows, self.chitra_canvas.height)
        x_step = self.chitra_canvas.width / max(1, width)
        y_step = self.chitra_canvas.height / max(1, height)
        lines = []
        for row in range(height):
            parts = []
            for col in range(width):
                x = min(self.chitra_canvas.width - 1, int((col + 0.5) * x_step))
                y = min(self.chitra_canvas.height - 1, int((row + 0.5) * y_step))
                pixel = self.chitra_canvas.get_pixel(x, y)
                alpha = getattr(pixel, "a", 255) / 255.0
                luminance = (
                    0.2126 * getattr(pixel, "r", 0)
                    + 0.7152 * getattr(pixel, "g", 0)
                    + 0.0722 * getattr(pixel, "b", 0)
                ) * alpha
                darkness = 255 - luminance
                index = int((darkness / 255) * (len(chars) - 1))
                parts.append(chars[index])
            lines.append("".join(parts))
        return "\n".join(lines)

    def _handle_chitra_command(self, command: str) -> str:
        parts = shlex.split(command)
        if not parts:
            return self.status_message
        op = parts[0].lower()
        builtins = self.chitra_support.builtins
        if op == "new":
            if len(parts) < 3:
                raise VakTuiError("new <width> <height> [color] अपेक्षित")
            return self._new_canvas(
                int(parts[1]),
                int(parts[2]),
                parts[3] if len(parts) > 3 else "white",
            )
        self._require_chitra()
        if self.chitra_canvas is None:
            self._new_canvas(96, 48, "white")
        if op == "fill":
            builtins["_chitra_fill"](self.chitra_canvas, parts[1] if len(parts) > 1 else "white")
            return self._record("चित्रफलक भरा गया")
        if op == "clear":
            builtins["_chitra_clear"](self.chitra_canvas, parts[1] if len(parts) > 1 else "white")
            return self._record("चित्रफलक साफ किया गया")
        if op == "line":
            if len(parts) < 5:
                raise VakTuiError("line <x0> <y0> <x1> <y1> [color] अपेक्षित")
            builtins["_chitra_line"](
                self.chitra_canvas,
                int(parts[1]),
                int(parts[2]),
                int(parts[3]),
                int(parts[4]),
                parts[5] if len(parts) > 5 else "black",
            )
            return self._record("रेखा अंकित की गई")
        if op == "rect":
            if len(parts) < 5:
                raise VakTuiError("rect <x> <y> <w> <h> [color] [fill] अपेक्षित")
            fill = self._parse_bool(parts[6], False) if len(parts) > 6 else False
            builtins["_chitra_rect"](
                self.chitra_canvas,
                int(parts[1]),
                int(parts[2]),
                int(parts[3]),
                int(parts[4]),
                parts[5] if len(parts) > 5 else "black",
                fill,
            )
            return self._record("आयत अंकित किया गया")
        if op == "circle":
            if len(parts) < 4:
                raise VakTuiError("circle <x> <y> <radius> [color] [fill] अपेक्षित")
            fill = self._parse_bool(parts[5], False) if len(parts) > 5 else False
            builtins["_chitra_circle"](
                self.chitra_canvas,
                int(parts[1]),
                int(parts[2]),
                int(parts[3]),
                parts[4] if len(parts) > 4 else "black",
                fill,
            )
            return self._record("वृत्त अंकित किया गया")
        if op == "text":
            if len(parts) < 4:
                raise VakTuiError("text <x> <y> <text> [color] [scale] अपेक्षित")
            color = parts[4] if len(parts) > 4 else "black"
            scale = int(parts[5]) if len(parts) > 5 else 1
            builtins["_chitra_text"](
                self.chitra_canvas,
                int(parts[1]),
                int(parts[2]),
                parts[3],
                None,
                scale,
                color,
            )
            return self._record("पाठ अंकित किया गया")
        if op == "center":
            if len(parts) < 3:
                raise VakTuiError("center <y> <text> [color] [scale] अपेक्षित")
            color = parts[3] if len(parts) > 3 else "black"
            scale = int(parts[4]) if len(parts) > 4 else 1
            builtins["_chitra_text_centered"](
                self.chitra_canvas,
                int(parts[1]),
                parts[2],
                color,
                scale,
            )
            return self._record("मध्य-पाठ अंकित किया गया")
        if op == "gradient":
            if len(parts) < 3:
                raise VakTuiError("gradient <color1> <color2> अपेक्षित")
            builtins["_chitra_gradient"](self.chitra_canvas, parts[1], parts[2])
            return self._record("ग्रेडिएंट लगाया गया")
        if op == "mandala":
            cx = int(parts[1]) if len(parts) > 1 else self.chitra_canvas.width // 2
            cy = int(parts[2]) if len(parts) > 2 else self.chitra_canvas.height // 2
            radius = (
                int(parts[3])
                if len(parts) > 3
                else min(self.chitra_canvas.width, self.chitra_canvas.height) // 3
            )
            petals = int(parts[4]) if len(parts) > 4 else 12
            builtins["_chitra_mandala"](self.chitra_canvas, cx, cy, radius, petals)
            return self._record("मण्डल रचा गया")
        if op == "rotate":
            if len(parts) < 2:
                raise VakTuiError("rotate <angle> अपेक्षित")
            self.chitra_canvas = builtins["_chitra_rotate"](
                self.chitra_canvas,
                float(parts[1]),
            )
            return self._record("चित्र घुमाया गया")
        if op == "kaleidoscope":
            segments = int(parts[1]) if len(parts) > 1 else 8
            self.chitra_canvas = builtins["_chitra_kaleidoscope"](
                self.chitra_canvas,
                segments,
            )
            return self._record("कैलाइडोस्कोप प्रभाव लगाया गया")
        if op == "save":
            if len(parts) < 2:
                raise VakTuiError("save <path> अपेक्षित")
            target = (self.cwd / parts[1]).resolve() if not os.path.isabs(parts[1]) else Path(parts[1])
            builtins["_chitra_save"](self.chitra_canvas, str(target))
            self.chitra_last_saved = str(target)
            return self._record(f"चित्र सहेजा गया: {target}")
        if op == "load":
            if len(parts) < 2:
                raise VakTuiError("load <path> अपेक्षित")
            target = (self.cwd / parts[1]).resolve() if not os.path.isabs(parts[1]) else Path(parts[1])
            self.chitra_canvas = builtins["_chitra_load"](str(target))
            return self._record(f"चित्र लोड किया गया: {target}")
        if op == "preview":
            if len(parts) > 1:
                self.chitra_preview_cols = max(8, int(parts[1]))
            if len(parts) > 2:
                self.chitra_preview_rows = max(4, int(parts[2]))
            return self._record("पूर्वावलोकन आकार अद्यतन किया गया")
        if op == "colors":
            colors = builtins["_chitra_colors"]()
            preview = ", ".join(colors[:20])
            return self._record(f"रंग: {preview}")
        raise VakTuiError(f"अज्ञात चित्रकला आदेश: {parts[0]}")

    # ---- VPM -------------------------------------------------------------

    def _capture_vpm(self, func: Any, *args: Any, **kwargs: Any) -> tuple[Any, str]:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            result = func(*args, **kwargs)
        output = buffer.getvalue().strip()
        self.vpm_last_output = output
        return result, output

    def _handle_vpm_command(self, command: str) -> str:
        parts = shlex.split(command)
        if not parts:
            return self.status_message
        op = parts[0].lower()
        if op == "init":
            result, output = self._capture_vpm(self.vpm.init)
            self.vpm_last_info = None
            self.vpm_last_cache = None
            return self._record(output or ("vakya.json तैयार" if result else "vakya.json पहले से मौजूद"))
        if op == "installed":
            self.vpm_last_search = self.vpm.list_installed()
            self.vpm_last_info = None
            self.vpm_last_cache = None
            return self._record(f"स्थापित पैकेज: {len(self.vpm_last_search)}")
        if op == "python":
            deps = self.vpm.list_python_deps()
            self.vpm_last_search = [{"name": item, "version": "python"} for item in deps]
            self.vpm_last_info = None
            self.vpm_last_cache = None
            return self._record(f"Python निर्भरताएँ: {len(deps)}")
        if op == "search":
            if len(parts) < 2:
                raise VakTuiError("search <query> अपेक्षित")
            self.vpm_last_search = self.vpm.search(" ".join(parts[1:]))
            self.vpm_last_info = None
            self.vpm_last_cache = None
            return self._record(f"खोज परिणाम: {len(self.vpm_last_search)}")
        if op == "info":
            if len(parts) < 2:
                raise VakTuiError("info <package> अपेक्षित")
            self.vpm_last_info = self.vpm.info(parts[1])
            self.vpm_last_cache = None
            if self.vpm_last_info is None:
                return self._record(f"पैकेज नहीं मिला: {parts[1]}")
            return self._record(f"पैकेज सूचना लोड हुई: {parts[1]}")
        if op == "install":
            if len(parts) < 2:
                raise VakTuiError("install <package> अपेक्षित")
            result, output = self._capture_vpm(self.vpm.install, parts[1])
            self.vpm_last_info = None
            self.vpm_last_cache = None
            return self._record(output or ("पैकेज स्थापित" if result else "स्थापना विफल"))
        if op == "remove":
            if len(parts) < 2:
                raise VakTuiError("remove <package> अपेक्षित")
            result, output = self._capture_vpm(self.vpm.remove, parts[1])
            self.vpm_last_info = None
            self.vpm_last_cache = None
            return self._record(output or ("पैकेज हटाया गया" if result else "हटाना विफल"))
        if op == "remove-py":
            if len(parts) < 2:
                raise VakTuiError("remove-py <package> अपेक्षित")
            result, output = self._capture_vpm(self.vpm.remove_python_dep, parts[1])
            self.vpm_last_info = None
            self.vpm_last_cache = None
            return self._record(output or ("Python निर्भरता हटाई गई" if result else "हटाना विफल"))
        if op == "update":
            target = parts[1] if len(parts) > 1 else None
            result, output = self._capture_vpm(self.vpm.update, target)
            self.vpm_last_info = None
            self.vpm_last_cache = None
            return self._record(output or ("पैकेज अद्यतन" if result else "अद्यतन विफल"))
        if op == "lock":
            payload, output = self._capture_vpm(self.vpm.write_lockfile)
            if isinstance(payload, dict):
                self.vpm_last_info = {
                    "नाम": "vakya.lock.json",
                    "संस्करण": payload.get("version"),
                    "स्थिति": "generated",
                    "पैकेज": len(payload.get("packages", [])),
                    "Python": len(payload.get("python_dependencies", [])),
                }
                self.vpm_last_search = []
                self.vpm_last_cache = None
            return self._record(output or f"लॉकफ़ाइल लिखी गई: {self.vpm.lockfile_path}")
        if op == "cache":
            action = parts[1].lower() if len(parts) > 1 else "info"
            if action == "clear":
                result, output = self._capture_vpm(self.vpm.clear_cache)
                self.vpm_last_cache = self.vpm.cache_info()
                self.vpm_last_info = None
                self.vpm_last_search = []
                return self._record(output or ("कैश साफ किया गया" if result else "कैश साफ नहीं हुआ"))
            self.vpm_last_cache = self.vpm.cache_info()
            self.vpm_last_info = None
            self.vpm_last_search = []
            return self._record(
                "कैश जानकारी: "
                f"metadata={self.vpm_last_cache['metadata_files']}, "
                f"archives={self.vpm_last_cache['archive_files']}, "
                f"size={self.vpm_last_cache['size_bytes']}"
            )
        if op == "cwd":
            if len(parts) < 2:
                raise VakTuiError("cwd <path> अपेक्षित")
            self.cwd = Path(parts[1]).resolve()
            self.vpm = VakPackageManager(str(self.cwd))
            self.vpm_last_info = None
            self.vpm_last_search = []
            self.vpm_last_cache = None
            return self._record(f"VPM कार्य-पथ बदला गया: {self.cwd}")
        raise VakTuiError(f"अज्ञात VPM आदेश: {parts[0]}")

    # ---- Rendering -------------------------------------------------------

    def _sidebar_lines(self) -> list[str]:
        lines = []
        for key in ("main", "repl", "sandbox", "proof", "chitra", "vpm", "repair", "codex"):
            prefix = "▶" if key == self.mode else " "
            lines.append(f"{prefix} {MODE_LABELS[key]} ({key})")
        return lines

    def _main_body_text(self) -> str:
        if self.mode == "main":
            lines = [
                "वाक् TUI — समेकित पर्यावरण",
                "",
                f"सक्रिय आयाम: {self.active_sandbox}",
                f"Rich renderer: {'हाँ' if self.use_rich else 'नहीं (fallback)'}",
                f"कार्य-पथ: {self.cwd}",
                "",
                "प्रमुख प्रणालियाँ:",
                "  • REPL with persistent sandboxes",
                "  • आयाम manager",
                "  • Sansmatic proof explorer",
                "  • Chitrakala graphics studio",
                "  • VPM package interface",
                "  • रूपान्तर repair workspace",
                "  • कोडेक्स translation workspace",
                "",
                "हाल की गतिविधि:",
            ]
            recent = self.activity_log[-8:] or ["  • अभी कोई गतिविधि नहीं"]
            lines.extend(f"  • {entry}" for entry in recent)
            return "\n".join(lines)
        if self.mode == "repl":
            sandbox = self._get_sandbox()
            lines = [
                f"सक्रिय आयाम: {sandbox.name}",
                f"वैश्विक नाम: {sandbox.globals_count()}",
                "",
                "हाल का आउटपुट:",
            ]
            recent = self.repl_log[-12:] or ["(कोई आउटपुट नहीं)"]
            lines.extend(recent)
            return "\n".join(lines)
        if self.mode == "sandbox":
            lines = ["आयाम सूची:"]
            for name, sandbox in self.sandboxes.items():
                marker = "▶" if name == self.active_sandbox else " "
                lines.append(
                    f"{marker} {name} | globals={sandbox.globals_count()} | history={len(sandbox.history)}"
                )
            lines.append("")
            lines.append("आदेश: new/switch/reset/drop/globals/stack")
            return "\n".join(lines)
        if self.mode == "proof":
            summary = self.sansmatic.summary()
            lines = [
                f"तथ्य: {summary['facts']}",
                f"व्युत्पन्न: {summary['derived']}",
                f"नियम: {summary['rules']}",
                f"दायित्व: {summary['obligations']['pending']}",
                f"विरोध: {summary['contradictions']}",
                f"प्रमेय: {summary['theorems']}",
                f"अनुक्रम: {summary['trace_events']}",
                "",
                "हाल के तथ्य:",
            ]
            facts = sorted(self.sansmatic.facts)[-8:]
            if facts:
                lines.extend(f"  • {a} {b} {c}" for a, b, c in facts)
            else:
                lines.append("  • (अभी कोई तथ्य नहीं)")
            lines.append("")
            lines.append("हाल के व्युत्पन्न तथ्य:")
            derived = sorted(self.sansmatic._derived)[-8:]
            if derived:
                lines.extend(f"  • {a} {b} {c}" for a, b, c in derived)
            else:
                lines.append("  • (अभी कोई व्युत्पन्न तथ्य नहीं)")
            lines.append("")
            lines.append("पंजीकृत प्रमेय:")
            theorems = self.sansmatic.list_theorems()[-6:]
            if theorems:
                for item in theorems:
                    lines.append(f"  • {item['name']} [{item['kind']}]")
            else:
                lines.append("  • (अभी कोई प्रमेय नहीं)")
            explanation = getattr(self.sansmatic, "_last_explanation", None)
            if explanation:
                lines.append("")
                lines.append("अंतिम व्याख्या:")
                lines.append(f"  • लक्ष्य: {explanation.get('goal', '—')}")
                lines.append(
                    f"  • सिद्ध: {'हाँ' if explanation.get('proved') else 'नहीं'}"
                )
                if explanation.get("blocked_by"):
                    lines.append(
                        f"  • अवरोध: {', '.join(explanation.get('blocked_by', ())) }".rstrip()
                    )
            lines.append("")
            lines.append("हाल के लॉग:")
            recent = self.proof_log[-8:] or ["  • (अभी कोई सान्समैटिक आउटपुट नहीं)"]
            lines.extend(recent)
            return "\n".join(lines)
        if self.mode == "chitra":
            lines = []
            if self.chitra_canvas is None:
                lines.append("चित्रफलक उपलब्ध नहीं")
            else:
                lines.extend(
                    [
                        f"चित्रफलक: {self.chitra_canvas.width}x{self.chitra_canvas.height}",
                        f"अंतिम सहेजना: {self.chitra_last_saved or '—'}",
                        "",
                        self._canvas_preview(),
                    ]
                )
            return "\n".join(lines)
        if self.mode == "repair":
            lines = [
                f"फ़ाइल: {self.repair_file or '—'}",
                f"शाखाएँ: {', '.join(self.repair_branches) if self.repair_branches else 'कोई नहीं'}",
            ]
            if self.repair_result is None:
                lines.extend(
                    [
                        "",
                        "आदेश: load / reload / workspace / branches / branch / analyze / report / diff / apply / save / reject",
                    ]
                )
            else:
                lines.extend(
                    [
                        f"परिवर्तन: {'हाँ' if self.repair_result.transformed else 'नहीं'}",
                        f"वाक्यरचना मान्य: {'हाँ' if self.repair_result.syntax_valid else 'नहीं'}",
                        f"संकलन मान्य: {'हाँ' if self.repair_result.compiled else 'नहीं'}",
                        f"संशोधन: {len(self.repair_result.edits)}",
                        f"सुझाव: {len(self.repair_result.suggestions)}",
                        f"अस्वीकृत: {len(self.repair_result.rejected_fixes)}",
                        "",
                        self._repair_diff_text(),
                    ]
                )
            return "\n".join(lines)
        if self.mode == "codex":
            lines = [
                f"फ़ाइल: {self.codex_file or '—'}",
                f"पृष्ठ: {self.codex_page}",
                f"शाखाएँ: {', '.join(self.codex_branches) if self.codex_branches else 'कोई नहीं'}",
            ]
            if self.codex_result is None:
                lines.extend(
                    [
                        "",
                        "आदेश: load / reload / workspace / pages / chapters / page / branches / branch / promotion / analyze / report / diff / apply / save / reject",
                    ]
                )
            else:
                lines.extend(
                    [
                        f"चयनित पृष्ठ: {self.codex_result.page}",
                        f"विश्वास: {self.codex_result.confidence}",
                        f"वाक्यरचना मान्य: {'हाँ' if (self.codex_result.validation and self.codex_result.validation.syntax_valid) else 'नहीं'}",
                        f"संकलन मान्य: {'हाँ' if (self.codex_result.validation and self.codex_result.validation.compiled) else 'नहीं'}",
                        f"लागू नियम: {len(self.codex_result.applied_rules)}",
                        f"अस्वीकृत नियम: {len(self.codex_result.rejected_rules)}",
                        "",
                        self._codex_diff_text(),
                    ]
                )
            return "\n".join(lines)
        installed = self.vpm.list_installed()
        lines = [
            f"कार्य-पथ: {self.cwd}",
            f"vakya.json: {'हाँ' if (self.cwd / 'vakya.json').exists() else 'नहीं'}",
            f"लॉकफ़ाइल: {'हाँ' if (self.cwd / 'vakya.lock.json').exists() else 'नहीं'}",
            f"पैकेज निर्देशिका: {self.cwd / PACKAGE_DIR}",
            f"स्थापित पैकेज: {len(installed)}",
            "",
        ]
        if self.vpm_last_info:
            lines.append("चयनित पैकेज:")
            for key in ("नाम", "संस्करण", "विवरण", "स्थिति"):
                if key in self.vpm_last_info:
                    lines.append(f"  • {key}: {self.vpm_last_info[key]}")
        elif self.vpm_last_cache:
            lines.append("कैश:")
            lines.append(f"  • metadata: {self.vpm_last_cache['metadata_files']}")
            lines.append(f"  • archives: {self.vpm_last_cache['archive_files']}")
            lines.append(f"  • size_bytes: {self.vpm_last_cache['size_bytes']}")
        elif self.vpm_last_search:
            lines.append("परिणाम:")
            for item in self.vpm_last_search[:10]:
                name = item.get("नाम") or item.get("name") or "?"
                version = item.get("संस्करण") or item.get("version") or "?"
                lines.append(f"  • {name} ({version})")
        else:
            lines.append("आदेश: init / installed / python / search / info / install / remove / remove-py / update / lock / cache")
        if self.vpm_last_output:
            lines.extend(["", "अंतिम आउटपुट:", self.vpm_last_output])
        return "\n".join(lines)

    def render_text(self) -> str:
        header = (
            "╔══════════════════════════════════════════════════════════════════════╗\n"
            f"║  ॐ वाक् TUI  |  मोड: {MODE_LABELS[self.mode]:<12} | आयाम: {self.active_sandbox:<12} ║\n"
            "╚══════════════════════════════════════════════════════════════════════╝"
        )
        sidebar = "\n".join(self._sidebar_lines())
        body = self._main_body_text()
        footer = f"स्थिति: {self.status_message}\nआदेश: {self.prompt()}help"
        return "\n\n".join([header, sidebar, body, footer])

    def _build_rich_layout(self) -> Any:
        sidebar = Table(box=box.SIMPLE, expand=True, show_header=False)
        sidebar.add_column(style="cyan")
        for line in self._sidebar_lines():
            style = "bold yellow" if line.startswith("▶") else "white"
            sidebar.add_row(f"[{style}]{line}[/{style}]")

        layout = Layout()
        layout.split_column(
            Layout(
                Panel(
                    f"ॐ वाक् TUI | मोड: {MODE_LABELS[self.mode]} | आयाम: {self.active_sandbox}",
                    style="bold white on blue",
                ),
                name="header",
                size=3,
            ),
            Layout(name="body", ratio=1),
            Layout(
                Panel(
                    f"स्थिति: {self.status_message}\nआदेश: {self.prompt()}help",
                    border_style="green",
                ),
                name="footer",
                size=5,
            ),
        )
        layout["body"].split_row(
            Layout(Panel(sidebar, title="विभाग", border_style="cyan"), name="sidebar", size=28),
            Layout(
                Panel(
                    self._main_body_text(),
                    title=f"{MODE_LABELS[self.mode]} परिवेश",
                    border_style="magenta",
                ),
                name="main",
            ),
        )
        return layout

    def render(self) -> None:
        if self.clear_screen:
            self.console.clear()
        if self.use_rich:
            self.console.print(self._build_rich_layout())
        else:
            self.console.print(self.render_text())

    # ---- Command dispatcher ----------------------------------------------

    def _read_multiline_block(self) -> str:
        self.console.print("ब्लॉक प्रारम्भ करें; '.end' लिखकर समाप्त करें.")
        lines = []
        while True:
            line = self.console.input("... ")
            if line.strip() == ".end":
                break
            lines.append(line)
        return "\n".join(lines)

    def _handle_sandbox_command(self, command: str) -> str:
        parts = shlex.split(command)
        if not parts:
            return self.status_message
        op = parts[0].lower()
        if op == "list":
            names = ", ".join(self.sandboxes.keys())
            return self._record(f"आयाम: {names}")
        if op == "new":
            if len(parts) < 2:
                raise VakTuiError("new <name> अपेक्षित")
            name = parts[1]
            if name in self.sandboxes:
                raise VakTuiError(f"आयाम पहले से मौजूद: {name}")
            self._create_sandbox(name)
            self.active_sandbox = name
            return self._record(f"नया आयाम बना: {name}")
        if op == "switch":
            if len(parts) < 2:
                raise VakTuiError("switch <name> अपेक्षित")
            self._get_sandbox(parts[1])
            self.active_sandbox = parts[1]
            return self._record(f"सक्रिय आयाम बदला गया: {parts[1]}")
        if op == "reset":
            name = parts[1] if len(parts) > 1 else self.active_sandbox
            self._get_sandbox(name)
            self.sandboxes[name] = SandboxState(name=name, interpreter=VakInterpreter())
            if self.active_sandbox == name:
                self.active_sandbox = name
            return self._record(f"आयाम रीसेट हुआ: {name}")
        if op == "drop":
            if len(parts) < 2:
                raise VakTuiError("drop <name> अपेक्षित")
            name = parts[1]
            if name == "default":
                raise VakTuiError("default आयाम हटाया नहीं जा सकता")
            if name == self.active_sandbox:
                self.active_sandbox = "default"
            del self.sandboxes[name]
            return self._record(f"आयाम हटाया गया: {name}")
        if op == "globals":
            name = parts[1] if len(parts) > 1 else self.active_sandbox
            sandbox = self._get_sandbox(name)
            names = sorted(sandbox.interpreter.vm.globals.keys())
            preview = ", ".join(names[:20]) if names else "(none)"
            return self._record(f"{name} globals: {preview}")
        if op == "stack":
            name = parts[1] if len(parts) > 1 else self.active_sandbox
            sandbox = self._get_sandbox(name)
            stack = sandbox.interpreter.inspect_vm_stack()
            if not stack:
                return self._record(f"{name} stack: (empty)")
            preview = " | ".join(frame.get("name", "<frame>") for frame in stack[:8])
            return self._record(f"{name} stack: {preview}")
        raise VakTuiError(f"अज्ञात आयाम आदेश: {parts[0]}")

    def execute_command(self, command: str) -> str:
        text = command.strip()
        if not text:
            return self.status_message
        lower = text.lower()
        try:
            if lower in {"quit", "exit", "विराम"}:
                self.running = False
                return self._record("वाक् TUI बंद किया जा रहा है")
            if lower in {"help", "?"}:
                return self._record(self.mode_help())
            if lower == "modes":
                return self._record(", ".join(f"{k}={v}" for k, v in MODE_LABELS.items()))
            if lower.startswith("builtins"):
                parts = shlex.split(text)
                category = parts[1] if len(parts) > 1 else None
                return self._record(
                    format_builtin_help(
                        self._get_sandbox().interpreter.vm.builtins,
                        category=category,
                    )
                )
            if lower == "modules":
                return self._record(format_stdlib_manifest())
            if lower == "render":
                return self._record("पटल ताज़ा किया गया")
            if lower.startswith("mode "):
                return self.set_mode(text.split(None, 1)[1])
            if self.mode == "main" and lower.startswith("open "):
                return self.set_mode(text.split(None, 1)[1])

            if self.mode == "main":
                raise VakTuiError("मुख्य मोड में 'open <mode>' या 'mode <mode>' उपयोग करें, जैसे open codex")
            if self.mode == "repl":
                if text == ":block":
                    source = self._read_multiline_block()
                    return self._execute_vak_source(source)
                if text == ":stack":
                    stack = self._get_sandbox().interpreter.inspect_vm_stack()
                    if not stack:
                        return self._record("stack: (empty)")
                    return self._record(
                        "stack: " + " | ".join(item.get("name", "<frame>") for item in stack)
                    )
                if text == ":globals":
                    names = sorted(self._get_sandbox().interpreter.vm.globals.keys())
                    return self._record("globals: " + (", ".join(names[:30]) if names else "(none)"))
                return self._execute_vak_source(text)
            if self.mode == "sandbox":
                return self._handle_sandbox_command(text)
            if self.mode == "proof":
                return self._handle_proof_command(text)
            if self.mode == "chitra":
                return self._handle_chitra_command(text)
            if self.mode == "vpm":
                return self._handle_vpm_command(text)
            if self.mode == "repair":
                return self._handle_repair_command(text)
            if self.mode == "codex":
                return self._handle_codex_command(text)
        except VakTuiError as error:
            return self._record(f"वाक् TUI त्रुटि: {error}")
        except Exception as error:
            return self._record(format_vak_error_with_suggestions(error))
        return self.status_message

    # ---- Interactive loop -----------------------------------------------

    def run(self) -> int:
        while self.running:
            self.render()
            try:
                command = self.console.input(self.prompt())
            except EOFError:
                break
            except KeyboardInterrupt:
                self.running = False
                break
            self.execute_command(command)
        if self.clear_screen:
            self.console.clear()
        self.console.print("वाक् TUI समाप्त")
        return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="वाक् TUI (Terminal UI Environment)",
    )
    parser.add_argument("--plain", action="store_true", help="Disable Rich renderer")
    parser.add_argument("--mode", default="main", help="Initial mode")
    parser.add_argument("--cwd", default=os.getcwd(), help="Working directory for VPM and saves")
    parser.add_argument(
        "--command",
        action="append",
        default=[],
        help="Run one or more commands non-interactively before exiting",
    )
    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="Do not clear the terminal between renders",
    )
    args = parser.parse_args(argv)

    app = VakTuiApp(
        cwd=args.cwd,
        use_rich=not args.plain,
        clear_screen=not args.no_clear,
    )
    app.set_mode(args.mode)
    if args.command:
        app.run_commands(args.command)
        app.render()
        return 0
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
