from __future__ import annotations


class KernelError(Exception):
    """Base class for trusted Sansmatic kernel failures."""


class KernelScopeError(KernelError):
    """Raised when a kernel term references an unbound variable."""


class KernelTypeError(KernelError):
    """Raised when a kernel term is not well typed."""

