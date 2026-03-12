# VakyaLang (????) � Copyright (c) 2026 Raj Mitra. All Rights Reserved.
# Original author: Raj Mitra (Visionary RM)
# Licensed under GNU AGPL v3.0 � see LICENSE and NOTICE.
# Any use, modification, or derivative work must preserve this header
# and include the NOTICE file. https://github.com/Sansmatic-z/VakyaLang

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

