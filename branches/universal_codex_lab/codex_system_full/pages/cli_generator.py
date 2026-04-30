"""
Phase 3: CLI Tool Generator Codex Page.

Generates complete CLI applications from specifications:
- Parses CLI spec (commands, options, arguments)
- Generates command parsers, handlers, help text
- Outputs valid Vak code with proper CLI structure
"""
from __future__ import annotations

import json
import re
from typing import Any

from ..models import CodexDiagnostic, CodexPageManifest, CodexPageProbe, CodexResult
from ..page import CodexPage
from ..engines.code_generator import CodeGenerator, GenerationContext
from .utils import _overall_confidence


class CLIGeneratorCodexPage(CodexPage):
    """Generates CLI applications from specification descriptions."""
    name = "cli_generator"
    description = "CLI tool generator page"
    priority = 51
    kind = "python"
    chapter = "generators"
    chapter_title = "System Generators"
    chapter_order = 31
    capabilities = ("generate", "cli", "command_line", "argparse")
    emits_vak = True
    extensions = ("json", "yaml", "yml", "cli", "spec")
    max_fixpoint_passes = 2

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self._generator = CodeGenerator()
        self._diagnostics: list[CodexDiagnostic] = []
        self._detected_constructs: list[str] = []
        self._register_templates()

    def _register_templates(self) -> None:
        self._generator.register_template("cli_main", """# CLI Application: {app_name}
# Version: {version}
# Description: {description}

कर्म मुख्य() {{
    # Parse arguments
    args = parse_args()
    # Route to command handler
    command = args.get("command", "help")
    handler = handlers.get(command, help_handler)
    लौटाओ handler(args)
}}""")

        self._generator.register_template("cli_command", """# Command: {command_name}
कर्म {handler_name}(args) {{
    # {description}
    # Arguments: {args_list}
    # Implementation
    लौटाओ result
}}""")

        self._generator.register_template("cli_help", """# Help command
कर्म help_handler(args) {{
    छापो("{app_name} v{version}")
    छापो("{description}")
    छापो("")
    छापो("Available commands:")
{commands_help}
}}""")

    # ------------------------------------------------------------------
    # Probe
    # ------------------------------------------------------------------
    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        indicators = [
            "cli", "command", "commands", "argument", "option", "flag",
            "subcommand", "parser", "argparse", "click",
            "--help", "--version", "usage:", "synopsis:",
        ]
        score = 0
        for indicator in indicators:
            if indicator in source.lower():
                score += 10

        # JSON spec with commands field gets bonus
        if '"commands"' in source or "'commands'" in source:
            score += 10

        if filename and filename.endswith((".json", ".yaml", ".yml", ".cli", ".spec")):
            score += 30

        if score >= 20:
            return CodexPageProbe(self.name, min(score, 90), f"CLI specification detected ({score} indicators)")
        return CodexPageProbe(self.name, 0, "not a CLI spec candidate")

    # ------------------------------------------------------------------
    # Transform
    # ------------------------------------------------------------------
    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        self._diagnostics = []
        self._detected_constructs = []

        try:
            spec = self._parse_spec(source)
            if spec is None:
                return self._no_transform(source, "Could not parse CLI specification")

            vak_code = self._generate_cli(spec)

            return CodexResult(
                page=self.name,
                original_source=source,
                source=vak_code,
                transformed=True,
                confidence=_overall_confidence(self._diagnostics, True),
                diagnostics=tuple(self._diagnostics),
                manifest=self.manifest(),
                metadata={
                    "source_kind": "cli_spec",
                    "app_name": spec.get("name", "unknown"),
                    "commands_count": len(spec.get("commands", [])),
                },
            )
        except Exception as exc:
            return self._no_transform(source, str(exc))

    def _no_transform(self, source: str, reason: str) -> CodexResult:
        self._diagnostics.append(CodexDiagnostic(
            page=self.name, level="error", message=reason, confidence="do_not_touch",
        ))
        return CodexResult(
            page=self.name, original_source=source, source=source,
            transformed=False, confidence="do_not_touch",
            diagnostics=tuple(self._diagnostics), manifest=self.manifest(),
            metadata={"source_kind": "cli_spec", "error": reason},
        )

    # ------------------------------------------------------------------
    # Spec parsing
    # ------------------------------------------------------------------
    def _parse_spec(self, source: str) -> dict[str, Any] | None:
        try:
            data = json.loads(source)
            return self._normalize_spec(data)
        except (json.JSONDecodeError, ValueError):
            pass

        return self._parse_descriptive_spec(source)

    def _normalize_spec(self, data: dict) -> dict[str, Any]:
        return {
            "name": data.get("name", data.get("app_name", "cli_tool")),
            "version": data.get("version", "1.0.0"),
            "description": data.get("description", data.get("desc", "CLI tool")),
            "commands": data.get("commands", data.get("subcommands", [])),
        }

    def _parse_descriptive_spec(self, source: str) -> dict[str, Any] | None:
        spec: dict[str, Any] = {
            "name": "cli_tool", "version": "1.0.0",
            "description": "CLI application", "commands": [],
        }

        for line in source.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            m = re.match(r"(?:command|cmd)\s+(\w+)\s*(?:-|:)\s*(.+)", stripped, re.IGNORECASE)
            if m:
                spec["commands"].append({
                    "name": m.group(1),
                    "description": m.group(2),
                    "handler": f"handle_{m.group(1)}",
                    "options": [],
                })
                continue

            m = re.match(r"(?:app|name|tool)\s*:\s*(\w+)", stripped, re.IGNORECASE)
            if m:
                spec["name"] = m.group(1)

            m = re.match(r"(?:version)\s*:\s*(\S+)", stripped, re.IGNORECASE)
            if m:
                spec["version"] = m.group(1)

        if spec["commands"]:
            return spec
        return None

    # ------------------------------------------------------------------
    # Code generation
    # ------------------------------------------------------------------
    def _generate_cli(self, spec: dict[str, Any]) -> str:
        lines: list[str] = []
        app_name = spec.get("name", "cli_tool")
        version = spec.get("version", "1.0.0")
        description = spec.get("description", "CLI application")

        # Main entry point
        lines.append(self._generator.generate(
            template_name="cli_main",
            app_name=app_name, version=version, description=description,
        ))
        lines.append("")

        # Handler registry
        lines.append("handlers = मानचित्र()")
        lines.append("")

        # Commands
        commands_help: list[str] = []
        for cmd in spec.get("commands", []):
            name = cmd["name"]
            handler = cmd.get("handler", f"handle_{name}")
            desc = cmd.get("description", f"Handle {name}")
            args_list = ", ".join(cmd.get("options", ["args"]))

            self._detected_constructs.append(f"command:{name}")
            self._diagnostics.append(CodexDiagnostic(
                page=self.name, level="info",
                message=f"Generated CLI command: {name}",
                confidence="safe_auto_fix",
            ))

            vak = self._generator.generate(
                template_name="cli_command",
                command_name=name, handler_name=handler,
                description=desc, args_list=args_list,
            )
            lines.append(vak)
            lines.append(f"handlers[\"{name}\"] = {handler}")
            lines.append(f'छापो("  {name}: {desc}")')
            commands_help.append(f'    छापो("  {name} - {desc}")')
            lines.append("")

        # Help command
        lines.append(self._generator.generate(
            template_name="cli_help",
            app_name=app_name, version=version, description=description,
            commands_help="\n".join(commands_help) if commands_help else '    छापो("  No commands registered")',
        ))

        return "\n".join(lines)
