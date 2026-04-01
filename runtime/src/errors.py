# वाक् भाषा - त्रुटि वर्ग (Error Classes)
# Vak Language - Error Handling

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
    def __init__(self, message: str, line: int = 0):
        self.line = line
        super().__init__(f"[Line {line}] {message}")

class CompileError(VakError):
    """Compilation error."""
    def __init__(self, message: str, line: int = 0):
        self.line = line
        super().__init__(f"[Line {line}] {message}")

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


def format_vak_error(error: Exception) -> str:
    """Render exceptions with Vak-facing bilingual labels."""
    if isinstance(error, LexerError):
        prefix = "शब्द-विश्लेषण त्रुटि (Lexer Error)"
    elif isinstance(error, ParseError):
        prefix = "वाक्यरचना त्रुटि (Parse Error)"
    elif isinstance(error, CompileError):
        prefix = "संकलन त्रुटि (Compile Error)"
    elif isinstance(error, (VMError, VakRuntimeError)):
        prefix = "चालना त्रुटि (Runtime Error)"
    elif isinstance(error, MacroError):
        prefix = "सूत्र त्रुटि (Macro Error)"
    elif isinstance(error, VakError):
        prefix = "वाक् त्रुटि (Vak Error)"
    else:
        prefix = "आन्तरिक त्रुटि (Internal Error)"
    return f"{prefix}: {error}"
