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
