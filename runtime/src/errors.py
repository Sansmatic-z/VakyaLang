# वाक् भाषा - त्रुटि परिभाषाएँ (Error Definitions)
# Vak Language - Error Classes

class VakError(Exception):
    """Base error class for all Vak language errors."""
    def __init__(self, message, line=None):
        self.message = message
        self.line = line
        super().__init__(self._format())

    def _format(self):
        if self.line:
            return f"\n  वाक्-दोष (पंक्ति {self.line}): {self.message}"
        return f"\n  वाक्-दोष: {self.message}"


class LexerError(VakError):
    """Raised during tokenization."""
    def _format(self):
        if self.line:
            return f"\n  शब्द-विच्छेद-दोष (पंक्ति {self.line}): {self.message}"
        return f"\n  शब्द-विच्छेद-दोष: {self.message}"


class ParseError(VakError):
    """Raised during parsing."""
    def _format(self):
        if self.line:
            return f"\n  व्याकरण-दोष (पंक्ति {self.line}): {self.message}"
        return f"\n  व्याकरण-दोष: {self.message}"


class VakRuntimeError(VakError):
    """Raised during execution."""
    def _format(self):
        if self.line:
            return f"\n  क्रियान्वयन-दोष (पंक्ति {self.line}): {self.message}"
        return f"\n  क्रियान्वयन-दोष: {self.message}"


class VakTypeError(VakRuntimeError):
    """Type mismatch error."""
    pass


class VakNameError(VakRuntimeError):
    """Undefined variable or name."""
    pass


class VakIndexError(VakRuntimeError):
    """Index out of bounds."""
    pass


# Control flow exceptions (not errors, used for flow control)
class ReturnException(Exception):
    def __init__(self, value):
        self.value = value


class BreakException(Exception):
    pass


class ContinueException(Exception):
    pass


class ThrowException(Exception):
    def __init__(self, value):
        self.value = value
