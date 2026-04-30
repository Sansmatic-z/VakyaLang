# vakvm-rs

This is the bootstrap Rust-side entrypoint for the future native VakyaLang runtime.

Current scope:
- load VakyaLang bytecode ABI v1 JSON
- validate envelope/version
- inspect constants, locals, nested functions, and source metadata
- execute a verified subset of the VM:
  arithmetic
  comparisons
  jumps
  locals
  list/tuple building
  print/halt
- keep Python-vs-Rust subset parity tests for the supported surface

This is intentionally the first native layer, not a fake full rewrite.

Why it exists:
- the Python compiler is currently the reference frontend
- the stable ABI is the contract between Python and Rust
- the native VM can now be built against that contract instead of Python `pickle`

Next milestones:
1. add opcode decoder utilities
2. add a real Rust `CallFrame`
3. add function calls, closures, and returns
4. add imports, classes, and methods
5. broaden parity against the Python regression subset, then expand feature support

## Current Parity Expectation

The Rust VM is not claimed to be a full replacement for the Python VM yet.

It is expected to match Python VM behavior on the currently supported subset,
and the regression suite checks that subset directly by comparing Rust output
against Python output for representative Vak programs.

## Current Build Command

```powershell
.\build.ps1
```

Or directly:

```powershell
C:\Users\Admin\.cargo\bin\cargo.exe +stable-x86_64-pc-windows-gnu test
C:\Users\Admin\.cargo\bin\cargo.exe +stable-x86_64-pc-windows-gnu build
```
