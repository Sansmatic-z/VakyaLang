"""
Code Generator Engine — Template-based code generation.

Provides:
- GenerationContext for managing generation state
- CodeGenerator for producing code from templates and ASTs
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from ..vak_surface import looks_like_vak_surface, normalize_vak_surface


@dataclass
class GenerationContext:
    """
    Mutable context carried through code generation.

    Tracks:
    - Variables in scope
    - Imports collected
    - Warnings and errors
    - Custom metadata
    """
    variables: dict[str, Any] = field(default_factory=dict)
    imports: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    _indent_level: int = 0

    def push_indent(self) -> None:
        self._indent_level += 1

    def pop_indent(self) -> None:
        self._indent_level = max(0, self._indent_level - 1)

    @property
    def indent(self) -> str:
        return "    " * self._indent_level

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)

    def add_import(self, module: str) -> None:
        if module not in self.imports:
            self.imports.append(module)

    def add_variable(self, name: str, value: Any) -> None:
        self.variables[name] = value

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    def snapshot(self) -> dict[str, Any]:
        return {
            "variables": dict(self.variables),
            "imports": list(self.imports),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "metadata": dict(self.metadata),
            "indent_level": self._indent_level,
        }

    def restore(self, snapshot: dict[str, Any]) -> None:
        self.variables = dict(snapshot.get("variables", {}))
        self.imports = list(snapshot.get("imports", []))
        self.warnings = list(snapshot.get("warnings", []))
        self.errors = list(snapshot.get("errors", []))
        self.metadata = dict(snapshot.get("metadata", {}))
        self._indent_level = snapshot.get("indent_level", 0)


class CodeGenerator:
    """
    Template-based code generator.

    Supports:
    - Template rendering with $variable and ${variable} substitution
    - Conditional blocks: $if var ... $endif
    - Loop blocks: $for items ... $endfor
    - Indentation management
    - Multi-part code assembly
    - Vak code generation helpers
    """

    # Template pattern: $var or ${var}
    _VAR_RE = re.compile(r"\$\{?(\w+)\}?")
    _IF_RE = re.compile(r"\$if\s+(\w+)\s*\n(.*?)\$endif", re.DOTALL)
    _FOR_RE = re.compile(r"\$for\s+(\w+)\s+in\s+(\w+)\s*\n(.*?)\$endfor", re.DOTALL)

    def __init__(self, *, indent_size: int = 4):
        self._indent_size = indent_size
        self._templates: dict[str, str] = {}
        self._custom_directives: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Template management
    # ------------------------------------------------------------------
    def register_template(self, name: str, template: str) -> None:
        """Register a named template."""
        self._templates[name] = template

    def get_template(self, name: str) -> str | None:
        return self._templates.get(name)

    def load_templates(self, templates: dict[str, str]) -> None:
        """Register multiple templates at once."""
        self._templates.update(templates)

    def register_directive(self, name: str, handler: Any) -> None:
        """Register a custom directive handler (callable or string)."""
        self._custom_directives[name] = handler

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------
    def generate(
        self,
        template_name: str | None = None,
        template_text: str | None = None,
        context: GenerationContext | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate code from a template.

        Parameters
        ----------
        template_name : str | None
            Name of a registered template.
        template_text : str | None
            Raw template text (overrides template_name).
        context : GenerationContext | None
            Generation context for state tracking.
        **kwargs
            Variables to substitute into the template.

        Returns
        -------
        str
            Generated code.
        """
        if template_text is None:
            if template_name is None:
                raise ValueError("Either template_name or template_text is required")
            template_text = self._templates.get(template_name, "")
            if not template_text:
                raise ValueError(f"Template not found: {template_name}")

        ctx = context or GenerationContext()

        # Populate context variables
        for k, v in kwargs.items():
            ctx.add_variable(k, v)

        # Process template
        result = template_text
        result = self._process_conditionals(result, ctx)
        result = self._process_loops(result, ctx)
        result = self._process_variables(result, ctx)
        result = self._process_directives(result, ctx)
        if looks_like_vak_surface(result):
            result = normalize_vak_surface(result)

        return result

    def generate_vak(
        self,
        source_kind: str,
        constructs: list[dict[str, Any]],
        context: GenerationContext | None = None,
    ) -> str:
        """
        Generate Vak code from a list of construct descriptions.

        Each construct dict should have:
        - kind: "function", "class", "variable", "import", etc.
        - name: identifier
        - body: optional content
        - params: optional parameters
        """
        ctx = context or GenerationContext()
        lines: list[str] = []

        for construct in constructs:
            kind = construct.get("kind", "unknown")
            name = construct.get("name", "")

            if kind == "import":
                module = construct.get("module", name)
                alias = construct.get("alias")
                if alias:
                    lines.append(f'आयात "{module}" से "{alias}"')
                else:
                    lines.append(f'आयात "{module}"')
                ctx.add_import(module)

            elif kind == "function":
                params = ", ".join(construct.get("params", []))
                lines.append(f"कर्म {name}({params}):")
                ctx.push_indent()
                body = construct.get("body", "")
                if body:
                    for bline in body.strip().splitlines():
                        lines.append(f"{ctx.indent}{bline}")
                else:
                    lines.append(f"{ctx.indent}कोई_कार्य_नहीं")
                ctx.pop_indent()

            elif kind == "class":
                lines.append(f"वर्ग {name}:")
                ctx.push_indent()
                body = construct.get("body", "")
                if body:
                    for bline in body.strip().splitlines():
                        lines.append(f"{ctx.indent}{bline}")
                else:
                    lines.append(f"{ctx.indent}कोई_कार्य_नहीं")
                ctx.pop_indent()

            elif kind == "variable":
                value = construct.get("value", "अपरिभाषित")
                lines.append(f"चर {name} = {value}")

            elif kind == "if":
                condition = construct.get("condition", "सत्य")
                lines.append(f"यदि ({condition}):")
                ctx.push_indent()
                body = construct.get("body", "")
                if body:
                    for bline in body.strip().splitlines():
                        lines.append(f"{ctx.indent}{bline}")
                else:
                    lines.append(f"{ctx.indent}कोई_कार्य_नहीं")
                ctx.pop_indent()

            elif kind == "while":
                condition = construct.get("condition", "सत्य")
                lines.append(f"यावत् ({condition}):")
                ctx.push_indent()
                body = construct.get("body", "")
                if body:
                    for bline in body.strip().splitlines():
                        lines.append(f"{ctx.indent}{bline}")
                else:
                    lines.append(f"{ctx.indent}कोई_कार्य_नहीं")
                ctx.pop_indent()

            elif kind == "for":
                var = construct.get("variable", "x")
                iterable = construct.get("iterable", "संग्रह")
                lines.append(f"प्रत्येक {var} अन्तर्गत {iterable}:")
                ctx.push_indent()
                body = construct.get("body", "")
                if body:
                    for bline in body.strip().splitlines():
                        lines.append(f"{ctx.indent}{bline}")
                else:
                    lines.append(f"{ctx.indent}कोई_कार्य_नहीं")
                ctx.pop_indent()

            elif kind == "return":
                value = construct.get("value", "")
                lines.append(f"प्रत्यागच्छ {value}")

            elif kind == "comment":
                text = construct.get("text", "")
                lines.append(f"# {text}")

            else:
                ctx.add_warning(f"Unknown construct kind: {kind}")
                lines.append(f"# TODO: {kind} {name}")

        return normalize_vak_surface("\n".join(lines))

    def generate_python(
        self,
        constructs: list[dict[str, Any]],
        context: GenerationContext | None = None,
    ) -> str:
        """
        Generate Python code from a list of construct descriptions.

        Same construct dict format as generate_vak but outputs Python syntax.
        """
        ctx = context or GenerationContext()
        lines: list[str] = []

        for construct in constructs:
            kind = construct.get("kind", "unknown")
            name = construct.get("name", "")

            if kind == "import":
                module = construct.get("module", name)
                alias = construct.get("alias")
                if alias:
                    lines.append(f"import {module} as {alias}")
                else:
                    lines.append(f"import {module}")
                ctx.add_import(module)

            elif kind == "function":
                params = ", ".join(construct.get("params", []))
                lines.append(f"def {name}({params}):")
                ctx.push_indent()
                body = construct.get("body", "pass")
                for bline in body.strip().splitlines():
                    lines.append(f"{ctx.indent}{bline}")
                ctx.pop_indent()

            elif kind == "class":
                bases = construct.get("bases", "")
                header = f"class {name}"
                if bases:
                    header += f"({bases})"
                header += ":"
                lines.append(header)
                ctx.push_indent()
                body = construct.get("body", "pass")
                for bline in body.strip().splitlines():
                    lines.append(f"{ctx.indent}{bline}")
                ctx.pop_indent()

            elif kind == "variable":
                value = construct.get("value", "None")
                lines.append(f"{name} = {value}")

            elif kind == "if":
                condition = construct.get("condition", "True")
                lines.append(f"if {condition}:")
                ctx.push_indent()
                body = construct.get("body", "pass")
                for bline in body.strip().splitlines():
                    lines.append(f"{ctx.indent}{bline}")
                ctx.pop_indent()

            elif kind == "for":
                var = construct.get("variable", "x")
                iterable = construct.get("iterable", "collection")
                lines.append(f"for {var} in {iterable}:")
                ctx.push_indent()
                body = construct.get("body", "pass")
                for bline in body.strip().splitlines():
                    lines.append(f"{ctx.indent}{bline}")
                ctx.pop_indent()

            elif kind == "while":
                condition = construct.get("condition", "True")
                lines.append(f"while {condition}:")
                ctx.push_indent()
                body = construct.get("body", "pass")
                for bline in body.strip().splitlines():
                    lines.append(f"{ctx.indent}{bline}")
                ctx.pop_indent()

            elif kind == "return":
                value = construct.get("value", "")
                lines.append(f"return {value}")

            elif kind == "comment":
                text = construct.get("text", "")
                lines.append(f"# {text}")

            else:
                ctx.add_warning(f"Unknown construct kind: {kind}")
                lines.append(f"# TODO: {kind} {name}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Template processing internals
    # ------------------------------------------------------------------
    def _process_conditionals(self, text: str, ctx: GenerationContext) -> str:
        def replacer(m: re.Match) -> str:
            var_name = m.group(1)
            body = m.group(2)
            if ctx.variables.get(var_name):
                return body
            return ""
        return self._IF_RE.sub(replacer, text)

    def _process_loops(self, text: str, ctx: GenerationContext) -> str:
        def replacer(m: re.Match) -> str:
            var_name = m.group(1)
            iterable_name = m.group(2)
            body_template = m.group(3)
            iterable = ctx.variables.get(iterable_name, [])
            results: list[str] = []
            for item in iterable:
                local_ctx = GenerationContext()
                local_ctx.variables = dict(ctx.variables)
                local_ctx.variables[var_name] = item
                result = self._process_variables(body_template, local_ctx)
                results.append(result)
            return "\n".join(results)
        return self._FOR_RE.sub(replacer, text)

    def _process_variables(self, text: str, ctx: GenerationContext) -> str:
        def replacer(m: re.Match) -> str:
            var_name = m.group(1)
            val = ctx.variables.get(var_name, "")
            return str(val)
        result = self._VAR_RE.sub(replacer, text)
        # Also support {var} / {variable} notation used by registered templates
        result = re.sub(
            r"\{(\w+)\}",
            lambda m: str(ctx.variables.get(m.group(1), m.group(0))),
            result,
        )
        return result

    def _process_directives(self, text: str, ctx: GenerationContext) -> str:
        for name, handler in self._custom_directives.items():
            if callable(handler):
                text = handler(text, ctx)
            else:
                text = text.replace(f"${name}", str(handler))
        return text
