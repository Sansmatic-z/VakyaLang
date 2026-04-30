from __future__ import annotations

import difflib


def is_internal_binding_name(name: str) -> bool:
    return name.startswith("__imported_module_") or (
        name.startswith("<") and name.endswith(">")
    )


def describe_available_names(
    names: list[str] | tuple[str, ...] | set[str],
) -> str:
    visible = sorted(
        str(name) for name in names if name and not is_internal_binding_name(str(name))
    )
    if not visible:
        return ""
    preview = visible[:5]
    suffix = " ..." if len(visible) > 5 else ""
    return ", ".join(preview) + suffix


def build_missing_attribute_message(
    *,
    owner_kind: str,
    owner_name: str,
    attr_name: str,
    available_names: list[str] | tuple[str, ...] | set[str],
) -> str:
    message = f"Attribute '{attr_name}' not found in {owner_kind} {owner_name}"
    visible = sorted(
        str(name)
        for name in available_names
        if name and not is_internal_binding_name(str(name))
    )
    if not visible:
        return message

    similar = difflib.get_close_matches(attr_name, visible, n=1, cutoff=0.6)
    if similar:
        message += f". Did you mean '{similar[0]}'?"

    available_text = describe_available_names(visible)
    if available_text:
        message += f". Available: {available_text}"
    return message
