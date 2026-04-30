# वाक् भाषा - त्रुटि वर्ग (Error Classes)
# Vak Language - Error Handling

from typing import Optional
import re
from pathlib import Path

class VakError(Exception):
    """Base class for all VakyaLang errors."""
    pass

class LexerError(VakError):
    """Lexical analysis error."""
    def __init__(self, message: str, line: int = 0):
        self.line = line
        super().__init__(f"[Line {line}] {message}")

class ParseError(VakError):
    """Syntax error."""
    def __init__(self, message: str, line: int = 0, *, errors: Optional[list["ParseError"]] = None):
        self.line = line
        self.errors = list(errors or [])
        super().__init__(f"[Line {line}] {message}")

    @classmethod
    def aggregate(cls, errors: list["ParseError"]) -> "ParseError":
        if not errors:
            return cls("अज्ञात वाक्यरचना त्रुटि", 0)
        if len(errors) == 1:
            return cls(cls._strip_line_prefix(str(errors[0])), errors[0].line, errors=[errors[0]])
        first = errors[0]
        headline = f"{len(errors)} वाक्यरचना त्रुटियाँ मिलीं; पहली: {cls._strip_line_prefix(str(first))}"
        return cls(headline, first.line, errors=errors)

    @staticmethod
    def _strip_line_prefix(message: str) -> str:
        match = re.match(r"\[Line \d+\]\s*(.*)", message)
        if match:
            return match.group(1)
        return message

class CompileError(VakError):
    """Compilation error."""
    def __init__(self, message: str, line: int = 0):
        self.line = line
        super().__init__(f"[Line {line}] {message}")

class TranslationError(VakError):
    """English-to-Vak translation error."""
    def __init__(self, message: str, line: int = 0):
        self.line = line
        super().__init__(f"[Line {line}] {message}" if line else message)

class VMError(VakError):
    """Runtime error in VM."""
    pass

class VakRuntimeError(VakError):
    """Execution error."""
    def __init__(self, message: str, line: int = 0):
        self.line = line
        super().__init__(f"Runtime Error: {message} at line {line}" if line else f"Runtime Error: {message}")

class VakNameError(VakRuntimeError):
    """Variable not found."""
    pass

class VakTypeError(VakRuntimeError):
    """Invalid operation between types."""
    pass

class MacroError(VakError):
    """
    Macro expansion error.
    
    Raised when macro expansion fails due to:
    - Invalid macro syntax
    - Argument count mismatch
    - Invalid substitution
    """
    def __init__(self, message: str, line: int = 0):
        self.line = line
        super().__init__(f"Macro Error: {message} at line {line}" if line else f"Macro Error: {message}")


def format_exception_group(exc_group: BaseExceptionGroup) -> str:
    """Render nested Python exception groups in a Vak-readable form."""
    messages = [f"ExceptionGroup ({exc_group.message}):"]
    for index, exc in enumerate(exc_group.exceptions):
        messages.append(f"  [{index}] {type(exc).__name__}: {exc}")
    return "\n".join(messages)


def format_vak_error(error: Exception) -> str:
    """Render exceptions with Vak-facing bilingual labels."""
    if isinstance(error, BaseExceptionGroup):
        return (
            "समूह त्रुटि (Exception Group): "
            + format_exception_group(error)
        )
    if isinstance(error, LexerError):
        prefix = "शब्द-विश्लेषण त्रुटि (Lexer Error)"
    elif isinstance(error, ParseError):
        prefix = "वाक्यरचना त्रुटि (Parse Error)"
    elif isinstance(error, CompileError):
        prefix = "संकलन त्रुटि (Compile Error)"
    elif isinstance(error, TranslationError):
        prefix = "अनुवाद त्रुटि (Translation Error)"
    elif isinstance(error, (VMError, VakRuntimeError)):
        prefix = "चालना त्रुटि (Runtime Error)"
    elif isinstance(error, MacroError):
        prefix = "सूत्र त्रुटि (Macro Error)"
    elif isinstance(error, VakError):
        prefix = "वाक् त्रुटि (Vak Error)"
    else:
        prefix = "आन्तरिक त्रुटि (Internal Error)"
    rendered = f"{prefix}: {error}"
    sub_errors = getattr(error, "errors", None) or []
    if len(sub_errors) > 1:
        details = []
        for item in sub_errors[:10]:
            details.append(f"  - {item}")
        if len(sub_errors) > 10:
            details.append(f"  - ... और {len(sub_errors) - 10} त्रुटियाँ")
        rendered += "\n" + "\n".join(details)
    return rendered


_LINE_RE = re.compile(r"\[Line (\d+)\]")


def _extract_line_number(error: Exception) -> int:
    line = getattr(error, "line", 0)
    if isinstance(line, int) and line > 0:
        return line
    match = _LINE_RE.search(str(error))
    if match:
        return int(match.group(1))
    return 0


def _render_source_context(error: Exception, context: Optional[dict]) -> str:
    if not context:
        return ""

    line_no = _extract_line_number(error)
    if line_no <= 0:
        return ""

    source_text = context.get("prepared_source") or context.get("input_source") or ""
    filename = context.get("filename")

    if not source_text and filename:
        try:
            source_text = Path(filename).read_text(encoding="utf-8")
        except OSError:
            source_text = ""

    if not source_text:
        translation = context.get("translation") or {}
        source_text = translation.get("transformed_source") or translation.get("original_source") or ""

    if not source_text:
        return ""

    lines = source_text.splitlines()
    if not (1 <= line_no <= len(lines)):
        return ""

    start = max(1, line_no - 1)
    end = min(len(lines), line_no + 1)
    rendered = []
    if filename:
        rendered.append(f"  स्रोत: {filename}:{line_no}")
    else:
        rendered.append(f"  स्रोत: पंक्ति {line_no}")
    for current in range(start, end + 1):
        marker = ">" if current == line_no else " "
        rendered.append(f" {marker} {current:>4} | {lines[current - 1]}")
    return "\n".join(rendered)


def format_vak_error_with_suggestions(
    error: Exception,
    context: Optional[dict] = None,
) -> str:
    """
    Like format_vak_error, but appends cognitive fix suggestions when available.
    """
    base = format_vak_error(error)
    try:
        from .suggestions import CognitiveFixer, format_suggestions

        fixer = CognitiveFixer()
        suggestions = fixer.analyze(error, context=context)
        suggestion_text = format_suggestions(suggestions)
        source_context = _render_source_context(error, context)
        extras = []
        if source_context:
            extras.append(source_context)
        if suggestion_text:
            extras.append(suggestion_text)
        if extras:
            return f"{base}\n" + "\n".join(extras)
    except Exception:
        # Suggestion rendering must never break the primary error path.
        pass
    return base
