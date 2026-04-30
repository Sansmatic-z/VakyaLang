"""Frozen Python-hosted legacy backend for Vak bootstrap migration.

This module intentionally exposes a small stable API that Vak-written
bootstrap stages can call through the Python bridge while the native
compiler core is still being built.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from runtime.src.bytecode import Bytecode
from runtime.src.bytecode import NO_DEFAULT
from runtime.src.interpreter import VakInterpreter
from runtime.src.opcodes import OpCode


_OPCODE_16BIT_NAMES = {
    "LOAD_CONST",
    "CALL_BUILTIN",
    "JUMP",
    "JUMP_IF_TRUE",
    "JUMP_IF_FALSE",
    "IMPORT_NAME",
    "SETUP_EXCEPT",
    "FOR_ITER",
    "ATTR_GET",
    "ATTR_SET",
}


def _sha256(path: str | Path) -> str:
    path = Path(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact_report(source_path: str | Path, output_path: str | Path, bytecode: Bytecode) -> dict[str, Any]:
    output_path = Path(output_path)
    meta_path = Bytecode.companion_path(output_path)
    return {
        "source_path": str(Path(source_path).resolve()),
        "compiled_path": str(output_path.resolve()),
        "meta_path": str(meta_path.resolve()),
        "byte_hash": _sha256(output_path),
        "meta_hash": _sha256(meta_path),
        "code_bytes": len(bytecode.code),
        "constants": len(bytecode.constants),
    }


def _decode_spec_value(value: Any) -> Any:
    if isinstance(value, dict):
        if value.get("__vak_default__") == "no_default":
            return NO_DEFAULT
        return {
            key: _decode_spec_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_decode_spec_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_decode_spec_value(item) for item in value)
    return value


def compile_file_to_artifact(source_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    source_path = Path(source_path).resolve()
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    interpreter = VakInterpreter()
    source = source_path.read_text(encoding="utf-8")
    bytecode = interpreter.compile_only(source, filename=str(source_path))

    output_path.write_bytes(bytecode.to_bytes())
    Bytecode.companion_path(output_path).write_text(
        bytecode.to_abi_json(),
        encoding="utf-8",
        newline="",
    )
    return _artifact_report(source_path, output_path, bytecode)


def reproduce_file_to_artifacts(
    source_path: str | Path,
    output_a: str | Path,
    output_b: str | Path,
) -> dict[str, Any]:
    first = compile_file_to_artifact(source_path, output_a)
    second = compile_file_to_artifact(source_path, output_b)
    return {
        "पहला": first,
        "दूसरा": second,
        "same_byte_hash": first["byte_hash"] == second["byte_hash"],
        "same_meta_hash": first["meta_hash"] == second["meta_hash"],
    }


def _apply_spec(bytecode: Bytecode, spec: dict[str, Any]) -> Bytecode:
    bytecode.constants = list(_decode_spec_value(spec.get("constants", [])))
    bytecode.var_names = list(spec.get("var_names", []))
    bytecode.param_names = list(spec.get("param_names", []))
    bytecode.defaults = list(_decode_spec_value(spec.get("defaults", [])))
    bytecode.varargs_name = spec.get("varargs_name")
    bytecode.num_params = int(spec.get("num_params", 0))
    bytecode.source_path = spec.get("source_path")
    bytecode.global_names = set(spec.get("global_names", []))
    bytecode.nonlocal_names = set(spec.get("nonlocal_names", []))
    bytecode.local_names = set(spec.get("local_names", []))
    bytecode.closure_names = set(spec.get("closure_names", []))
    bytecode.type_hints = dict(spec.get("type_hints", {}))
    bytecode.is_async = bool(spec.get("is_async", False))

    for function_name, function_spec in (spec.get("functions") or {}).items():
        nested = Bytecode(function_spec.get("name", function_name))
        bytecode.functions[function_name] = _apply_spec(nested, function_spec)

    for instruction in spec.get("instructions", []):
        op_name = instruction["op"]
        opcode = OpCode[op_name]
        width = int(instruction.get("width", 16 if op_name in _OPCODE_16BIT_NAMES else 0))
        operand = instruction.get("operand")
        operands = list(instruction.get("operands", []))

        if width == 16:
            if operand is None:
                raise ValueError(f"{op_name} requires 'operand' for width=16")
            bytecode.emit_16bit(opcode, int(operand))
            continue

        if operand is not None and not operands:
            operands = [operand]

        bytecode.emit(opcode, *[int(value) for value in operands])

    return bytecode


def assemble_spec_to_artifact(spec: dict[str, Any], output_path: str | Path) -> dict[str, Any]:
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bytecode = _apply_spec(Bytecode(spec.get("name", "<module>")), spec)

    output_path.write_bytes(bytecode.to_bytes())
    Bytecode.companion_path(output_path).write_text(
        bytecode.to_abi_json(),
        encoding="utf-8",
        newline="",
    )
    source_path = spec.get("source_path") or "<assembly>"
    return _artifact_report(source_path, output_path, bytecode)
