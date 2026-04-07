from __future__ import annotations

import re

from runtime.src.codex.models import CodexDiagnostic, CodexPageProbe, CodexResult
from runtime.src.codex.page import CodexPage


def _brace_reindent(lines: list[str]) -> str:
    emitted: list[str] = []
    indent = 0
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        while line.startswith("}"):
            indent = max(0, indent - 1)
            line = line[1:].strip()
        if not line:
            continue
        opens_block = line.endswith("{")
        if opens_block:
            line = line[:-1].rstrip()
        emitted.append("    " * indent + line)
        if opens_block:
            emitted[-1] = emitted[-1] + ":"
            indent += 1
    return "\n".join(emitted)


class CSubsetCodexPage(CodexPage):
    name = "c_subset"
    description = "Experimental C-like subset to Vak page"
    priority = 85
    kind = "branch_python"
    chapter = "experimental_systems"
    chapter_title = "Experimental Systems"
    chapter_order = 80
    capabilities = ("experimental", "c_subset", "bridge")
    emits_vak = True
    extensions = ("c", "h")
    experimental = True

    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        if filename and filename.lower().endswith((".c", ".h")):
            return CodexPageProbe(self.name, 100, "C-like source path")
        if "#include" in source or "printf(" in source or "int main(" in source:
            return CodexPageProbe(self.name, 88, "C-like constructs detected")
        return CodexPageProbe(self.name, 0, "not a C subset candidate")

    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        diagnostics: list[CodexDiagnostic] = []
        if any(marker in source for marker in ("malloc(", "free(", "->", "struct ", "typedef ")):
            diagnostics.append(
                CodexDiagnostic(
                    page=self.name,
                    level="warning",
                    message="unsupported C memory/struct features detected; subset translation is suggest-only",
                    confidence="suggest_only",
                )
            )
        lines: list[str] = []
        for raw in source.splitlines():
            line = raw.strip()
            if not line:
                continue
            if line.startswith("#include"):
                continue
            if line.startswith("//"):
                lines.append("# " + line[2:].strip())
                continue
            line = line.rstrip(";")
            line = line.replace("&&", " और ").replace("||", " अथवा ")
            line = re.sub(r"\btrue\b", "सत्य", line)
            line = re.sub(r"\bfalse\b", "असत्य", line)
            line = re.sub(r"\bNULL\b", "शून्य", line)

            function_match = re.match(
                r"^(?:int|void|float|double|bool|char(?:\s*\*)?)\s+([A-Za-z_]\w*)\s*\(([^)]*)\)\s*\{?$",
                line,
            )
            if function_match:
                name = function_match.group(1)
                raw_params = function_match.group(2).strip()
                params: list[str] = []
                if raw_params and raw_params != "void":
                    for chunk in raw_params.split(","):
                        token = chunk.strip().split()
                        if token:
                            params.append(token[-1].replace("*", ""))
                suffix = " {" if raw.strip().endswith("{") else ""
                lines.append(f"कर्म {name}({', '.join(params)}){suffix}")
                continue

            decl_match = re.match(
                r"^(?:int|float|double|bool|char(?:\s*\*)?)\s+([A-Za-z_]\w*)\s*=\s*(.+)$",
                line,
            )
            if decl_match:
                lines.append(f"चर {decl_match.group(1)} = {decl_match.group(2)}")
                continue

            decl_only_match = re.match(
                r"^(?:int|float|double|bool|char(?:\s*\*)?)\s+([A-Za-z_]\w*)$",
                line,
            )
            if decl_only_match:
                lines.append(f"चर {decl_only_match.group(1)}")
                continue

            while_match = re.match(r"^while\s*\((.+)\)\s*\{?$", line)
            if while_match:
                suffix = " {" if raw.strip().endswith("{") else ""
                lines.append(f"यावत् {while_match.group(1)}{suffix}")
                continue
            if_match = re.match(r"^if\s*\((.+)\)\s*\{?$", line)
            if if_match:
                suffix = " {" if raw.strip().endswith("{") else ""
                lines.append(f"यदि {if_match.group(1)}{suffix}")
                continue
            elif_match = re.match(r"^else\s+if\s*\((.+)\)\s*\{?$", line)
            if elif_match:
                suffix = " {" if raw.strip().endswith("{") else ""
                lines.append(f"अन्यत् {elif_match.group(1)}{suffix}")
                continue
            if re.match(r"^else\s*\{?$", line):
                suffix = " {" if raw.strip().endswith("{") else ""
                lines.append(f"अन्यथा{suffix}")
                continue
            return_match = re.match(r"^return(?:\s+(.+))?$", line)
            if return_match:
                value = return_match.group(1)
                lines.append("प्रत्यागच्छ" if value is None else f"प्रत्यागच्छ {value}")
                continue
            printf_match = re.match(r"^printf\s*\((.+)\)$", line)
            if printf_match:
                args = [item.strip() for item in printf_match.group(1).split(",") if item.strip()]
                if len(args) == 1:
                    lines.append(f"मुद्रय({args[0]})")
                elif len(args) == 2 and "{}" not in args[0] and "%" in args[0]:
                    lines.append(f"मुद्रय({args[1]})")
                else:
                    lines.append(f"मुद्रय({', '.join(args[1:] or args)})")
                continue
            if line == "break":
                lines.append("विराम")
                continue
            if line == "continue":
                lines.append("अग्रे")
                continue
            lines.append(line)

        output = _brace_reindent(lines)
        return CodexResult(
            page=self.name,
            original_source=source,
            source=output,
            transformed=output != source,
            confidence="suggest_only",
            diagnostics=tuple(diagnostics),
            metadata={
                "source_kind": "c_subset",
                "detected_constructs": ["c_subset"],
            },
        )


class RustSubsetCodexPage(CodexPage):
    name = "rust_subset"
    description = "Experimental Rust-like subset to Vak page"
    priority = 86
    kind = "branch_python"
    chapter = "experimental_systems"
    chapter_title = "Experimental Systems"
    chapter_order = 80
    capabilities = ("experimental", "rust_subset", "bridge")
    emits_vak = True
    extensions = ("rs",)
    experimental = True

    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        if filename and filename.lower().endswith(".rs"):
            return CodexPageProbe(self.name, 100, "Rust-like source path")
        if "fn main()" in source or "println!" in source or "let mut " in source:
            return CodexPageProbe(self.name, 88, "Rust-like constructs detected")
        return CodexPageProbe(self.name, 0, "not a Rust subset candidate")

    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        diagnostics: list[CodexDiagnostic] = []
        if any(marker in source for marker in ("impl ", "trait ", "unsafe", "&mut", "-> Result")):
            diagnostics.append(
                CodexDiagnostic(
                    page=self.name,
                    level="warning",
                    message="unsupported Rust ownership/trait features detected; subset translation is suggest-only",
                    confidence="suggest_only",
                )
            )
        lines: list[str] = []
        for raw in source.splitlines():
            line = raw.strip()
            if not line:
                continue
            if line.startswith("//"):
                lines.append("# " + line[2:].strip())
                continue
            line = line.rstrip(";")
            line = re.sub(r"\btrue\b", "सत्य", line)
            line = re.sub(r"\bfalse\b", "असत्य", line)

            fn_match = re.match(r"^fn\s+([A-Za-z_]\w*)\s*\(([^)]*)\)\s*(?:->\s*[^ ]+)?\s*\{?$", line)
            if fn_match:
                name = fn_match.group(1)
                raw_params = fn_match.group(2).strip()
                params: list[str] = []
                if raw_params:
                    for chunk in raw_params.split(","):
                        token = chunk.strip().split(":")[0].strip()
                        token = token.replace("mut ", "").replace("&", "")
                        if token:
                            params.append(token)
                suffix = " {" if raw.strip().endswith("{") else ""
                lines.append(f"कर्म {name}({', '.join(params)}){suffix}")
                continue

            let_match = re.match(r"^let\s+(?:mut\s+)?([A-Za-z_]\w*)\s*=\s*(.+)$", line)
            if let_match:
                expr = let_match.group(2).replace("vec![", "[").replace("String::from(", "(")
                lines.append(f"चर {let_match.group(1)} = {expr}")
                continue

            if_match = re.match(r"^if\s+(.+)\s*\{?$", line)
            if if_match:
                suffix = " {" if raw.strip().endswith("{") else ""
                lines.append(f"यदि {if_match.group(1)}{suffix}")
                continue
            elif_match = re.match(r"^else\s+if\s+(.+)\s*\{?$", line)
            if elif_match:
                suffix = " {" if raw.strip().endswith("{") else ""
                lines.append(f"अन्यत् {elif_match.group(1)}{suffix}")
                continue
            if re.match(r"^else\s*\{?$", line):
                suffix = " {" if raw.strip().endswith("{") else ""
                lines.append(f"अन्यथा{suffix}")
                continue
            while_match = re.match(r"^while\s+(.+)\s*\{?$", line)
            if while_match:
                suffix = " {" if raw.strip().endswith("{") else ""
                lines.append(f"यावत् {while_match.group(1)}{suffix}")
                continue
            if re.match(r"^loop\s*\{?$", line):
                suffix = " {" if raw.strip().endswith("{") else ""
                lines.append(f"यावत् सत्य{suffix}")
                continue
            return_match = re.match(r"^return(?:\s+(.+))?$", line)
            if return_match:
                value = return_match.group(1)
                lines.append("प्रत्यागच्छ" if value is None else f"प्रत्यागच्छ {value}")
                continue
            println_match = re.match(r'^println!\((.+)\)$', line)
            if println_match:
                args = [item.strip() for item in println_match.group(1).split(",") if item.strip()]
                if len(args) == 1:
                    lines.append(f"मुद्रय({args[0]})")
                elif len(args) == 2 and args[0].startswith('"') and "{}" in args[0]:
                    lines.append(f"मुद्रय({args[1]})")
                else:
                    lines.append(f"मुद्रय({', '.join(args[1:] or args)})")
                continue
            lines.append(line)

        output = _brace_reindent(lines)
        return CodexResult(
            page=self.name,
            original_source=source,
            source=output,
            transformed=output != source,
            confidence="suggest_only",
            diagnostics=tuple(diagnostics),
            metadata={
                "source_kind": "rust_subset",
                "detected_constructs": ["rust_subset"],
            },
        )


class NaturalLanguageSuggestCodexPage(CodexPage):
    name = "natural_language"
    description = "Experimental natural-language to Vak suggestion page"
    priority = 87
    kind = "branch_python"
    chapter = "experimental_language"
    chapter_title = "Experimental Language"
    chapter_order = 90
    capabilities = ("experimental", "natural_language", "suggest_only")
    emits_vak = True
    extensions = ("txt", "nl")
    experimental = True

    _SUPPORTED_PATTERNS = (
        re.compile(r"^print numbers from \d+ to \d+$"),
        re.compile(r"^print even numbers from \d+ to \d+$"),
        re.compile(r"^set [a-z_]\w* to .+$"),
        re.compile(r"^if [a-z_]\w* is greater than \d+ then print [a-z_]\w*$"),
    )

    def probe(self, source: str, *, filename: str | None = None) -> CodexPageProbe:
        stripped = source.strip().lower()
        if any(pattern.fullmatch(stripped) for pattern in self._SUPPORTED_PATTERNS):
            return CodexPageProbe(self.name, 115, "deterministic natural-language command matched")
        if filename and filename.lower().endswith((".txt", ".nl")):
            return CodexPageProbe(self.name, 82, "natural-language source path")
        lowered = source.lower()
        if lowered.startswith("print ") or lowered.startswith("set ") or " then print " in lowered:
            return CodexPageProbe(self.name, 70, "simple imperative natural-language shape detected")
        return CodexPageProbe(self.name, 0, "not a supported natural-language candidate")

    def transform(self, source: str, *, filename: str | None = None) -> CodexResult:
        diagnostics: list[CodexDiagnostic] = []
        lowered = source.strip().lower()
        output = source
        transformed = False

        match = re.fullmatch(r"print numbers from (\d+) to (\d+)", lowered)
        if match:
            start, stop = match.groups()
            output = (
                f"प्रत्येक चर i अन्तर्गत परास({start}, {int(stop) + 1}):\n"
                "    मुद्रय(i)"
            )
            transformed = True
        else:
            match = re.fullmatch(r"print even numbers from (\d+) to (\d+)", lowered)
            if match:
                start, stop = match.groups()
                output = (
                    f"प्रत्येक चर i अन्तर्गत परास({start}, {int(stop) + 1}):\n"
                    "    यदि i % 2 == 0:\n"
                    "        मुद्रय(i)"
                )
                transformed = True
            else:
                match = re.fullmatch(r"set ([a-z_]\w*) to (.+)", lowered)
                if match:
                    name, value = match.groups()
                    output = f"चर {name} = {value}"
                    transformed = True
                else:
                    match = re.fullmatch(r"if ([a-z_]\w*) is greater than (\d+) then print ([a-z_]\w*)", lowered)
                    if match:
                        name, number, target = match.groups()
                        output = f"यदि {name} > {number}:\n    मुद्रय({target})"
                        transformed = True

        if not transformed:
            diagnostics.append(
                CodexDiagnostic(
                    page=self.name,
                    level="warning",
                    message="natural-language page only supports a small deterministic command subset",
                    confidence="do_not_touch",
                )
            )
            return CodexResult(
                page=self.name,
                original_source=source,
                source=source,
                transformed=False,
                confidence="do_not_touch",
                diagnostics=tuple(diagnostics),
                metadata={
                    "source_kind": "natural_language",
                    "detected_constructs": ["natural_language"],
                },
            )

        diagnostics.append(
            CodexDiagnostic(
                page=self.name,
                level="info",
                message="natural-language command matched deterministic Codex template",
                confidence="suggest_only",
            )
        )
        return CodexResult(
            page=self.name,
            original_source=source,
            source=output,
            transformed=True,
            confidence="suggest_only",
            diagnostics=tuple(diagnostics),
            metadata={
                "source_kind": "natural_language",
                "detected_constructs": ["natural_language"],
            },
        )
