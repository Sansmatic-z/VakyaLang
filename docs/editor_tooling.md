# Vak Tooling

## Language Server

Vak now ships with a lightweight stdio language server backed by the real lexer, parser, and compiler.

Run it with:

```powershell
py -3 vak_lsp.py
```

Current capabilities:

- diagnostics from the real Vak frontend
- keyword and builtin completion
- hover help for core keywords and common builtins
- top-level document symbols
- top-level definition lookup inside the current file

## Runtime Stack Inspection

The Python interpreter/VM now exposes structured Vak-native stack inspection:

- `VakInterpreter.inspect_vm_stack()`
- `VakVM.inspect_stack()`

Runtime errors now include richer Vak stack traces with:

- frame name
- source file
- current program counter
- visible local bindings
- stack-top preview

This is additive only; it does not change Vak bytecode, VM opcodes, or `.vak` program output on successful runs.
