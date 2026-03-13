# वाक् भाषा - परिवेश (Environment / Scope)
# Vak Language - Lexical Scope Implementation

from .errors import VakNameError


class Environment:
    """
    A lexical scope — maps names to values.
    Each scope has an optional parent (enclosing scope), enabling closures.
    """

    def __init__(self, parent=None, name: str = "global"):
        self._vars:    dict = {}
        self._consts:  set  = set()   # names that are immutable
        self.parent         = parent
        self.name           = name    # for debugging

    # ── Variable operations ───────────────────────────────────────────────────

    def define(self, name: str, value, constant: bool = False):
        """Define a new variable in *this* scope."""
        self._vars[name] = value
        if constant:
            self._consts.add(name)

    def get(self, name: str, line: int = None):
        """Walk the scope chain to find a variable."""
        if name in self._vars:
            return self._vars[name]
        if self.parent:
            return self.parent.get(name, line)
        raise VakNameError(
            f"अपरिभाषित नाम: '{name}' (undefined name)", line
        )

    def assign(self, name: str, value, line: int = None):
        """Assign to an *existing* variable (walk the chain)."""
        if name in self._vars:
            if name in self._consts:
                raise VakNameError(
                    f"स्थिर '{name}' को बदला नहीं जा सकता "
                    f"(cannot reassign constant)", line
                )
            self._vars[name] = value
            return
        if self.parent:
            self.parent.assign(name, value, line)
            return
        raise VakNameError(
            f"अपरिभाषित नाम: '{name}' (undefined name)", line
        )

    def has(self, name: str) -> bool:
        if name in self._vars:
            return True
        if self.parent:
            return self.parent.has(name)
        return False

    def child(self, name: str = "block") -> "Environment":
        """Create a child scope."""
        return Environment(parent=self, name=name)

    def __repr__(self):
        return f"Environment({self.name}, vars={list(self._vars.keys())})"
