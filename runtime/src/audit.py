# वाक् भाषा - लेखा निरीक्षण (Audit Hooks)
# Vak Language - Runtime audit helpers

from __future__ import annotations

from typing import Any


def _sanitize(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, (list, tuple)):
        return tuple(_sanitize(item) for item in value[:10])
    if isinstance(value, dict):
        sanitized = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= 10:
                break
            sanitized[str(key)] = _sanitize(item)
        return sanitized

    text = repr(value)
    if len(text) > 200:
        text = text[:197] + "..."
    return text


def emit_audit_event(event: str, *args: Any) -> None:
    """
    Emit a best-effort audit event.

    Failures must never disrupt language execution.
    """
    try:
        import sys

        if hasattr(sys, "audit"):
            sys.audit(event, *(_sanitize(arg) for arg in args))
    except Exception:
        return
