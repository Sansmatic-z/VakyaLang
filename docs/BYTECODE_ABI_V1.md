# VakyaLang Bytecode ABI v1

This document defines the first stable, language-independent bytecode ABI for VakyaLang.

Purpose:
- make the Python compiler a real frontend
- replace Python `pickle` as the portability layer
- enable a native runtime in Rust without reverse-engineering Python internals

Current status:
- implemented in [runtime/src/bytecode.py](/C:/RIZAMD/vakyalang-upgraded%20xyz/vakyalang-upgraded/runtime/src/bytecode.py)
- export CLI in [runtime/export_abi.py](/C:/RIZAMD/vakyalang-upgraded%20xyz/vakyalang-upgraded/runtime/export_abi.py)

## Envelope

```json
{
  "format": "vak_bytecode_abi",
  "version": 1,
  "bytecode": { "...": "..." }
}
```

## Bytecode Object

Each bytecode object contains:

- `name`: function or module name
- `source_path`: original source path when available
- `code`: raw opcode bytes as integer array
- `constants`: typed constant pool entries
- `var_names`: slot-ordered local names
- `param_names`: slot-ordered parameter names
- `functions`: nested function bytecodes keyed by function name
- `defaults`: typed default values
- `varargs_name`: variadic parameter name or `null`
- `num_params`: fixed parameter count
- `global_names`: names marked global
- `type_hints`: string type hints
- `is_async`: async marker
- `vibhakti_signature`: optional serialized Vibhakti metadata

## Constant Encoding

Constants are tagged objects, not raw JSON values, so `true` and `1` remain distinct.

Supported kinds:

- `null`
- `bool`
- `int`
- `float`
- `str`
- `list`
- `tuple`
- `dict`
- `callable_ref`

Example:

```json
{ "kind": "int", "value": 42 }
```

Callable references are encoded by symbolic name:

```json
{
  "kind": "callable_ref",
  "callable_kind": "function",
  "name": "योग"
}
```

The runtime reconstructs closure state dynamically at execution time.

## Why This Exists

The previous `Bytecode.to_bytes()` format used Python `pickle` and did not serialize nested functions. That is fine for local Python-only experiments and unusable for a native runtime.

ABI v1 fixes that by being:

- explicit
- typed
- nested-function aware
- JSON-serializable
- Rust-friendly

## Rust Runtime Target

The intended native runtime pipeline is:

1. Vak source
2. Python lexer/parser/compiler
3. ABI v1 JSON or a future binary form
4. Rust VM / JIT / AOT backend

## CLI

Export a program:

```bash
python runtime/export_abi.py tests/full_test.vak -o full_test.abi.json
```

## Forward Compatibility

Any breaking change to:

- opcode encoding
- operand width
- constant tagging
- function metadata
- control-flow semantics

must increment the ABI version.
