**Runtime Status**

This document is the truth table for what Vak currently treats as stable,
experimental, or branch-only.

## Production-Ready Core

- lexer, parser, compiler, and Python VM runtime
- main CLI surfaces: `vak.py`, `runtime/run.py`
- core stdlib and curated module set
- Sansmatic core proof engine
- conservative mainline `वाक्य-रूपान्तर`
- main Codex pages:
  - `vak`
  - `vak_legacy`
  - `english_vak`
  - `math_logic`
  - `sanskrit_notation`
- `.vak` Codex page support
- TUI core workspaces
- Windows/Unicode-safe path and archive handling covered by tests

## Supported but Still Evolving

- standalone `.vakc` workflow with companion metadata
- LSP/editor tooling in `runtime/tooling/lsp_server.py`
- TUI repair/Codex workspaces
- measurement/profiling tooling
- stdlib compatibility aliases and manifests
- package manager lock/cache/update/remove flows
- bootstrap/compiler tooling

These are usable and tested, but still undergoing hardening.

## Experimental

- runtime JIT for a validated opcode subset with runtime fallback
- Rust VM subset parity
- aggressive/adaptive repair behavior
- Codex branch pages in `universal_codex_lab`
- natural-language suggest-only Codex page
- C subset / Rust subset Codex pages
- full self-hosting/bootstrap compiler claim

These should not be described as production-ready. The JIT now rejects
unsupported functions explicitly and falls back to the bytecode VM if an
experimental compiled path fails at runtime.

## Branch-Only Features

- `adaptive_rupantar`
- `universal_codex_lab`
- other branch-scoped APIs exposed through `branches/registry.py`

Branch-only systems are opt-in and may change shape more quickly than mainline
Vak surfaces.
