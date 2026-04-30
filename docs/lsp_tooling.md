**Vak LSP Tooling**

`runtime/tooling/lsp_server.py` currently provides:

- diagnostics
- hover
- completion
- definition lookup
- signature help
- whole-document code actions driven by `रूपान्तर` and Codex

## Current Behavior

- diagnostics use the real lexer/parser/compiler pipeline
- code actions are conservative whole-document rewrites
- completions include:
  - document symbols
  - builtins
  - keywords
  - stdlib modules
  - Codex pages
- hover and signature help provide function/builtin/type context where the
  current parser state makes that safe

## Truthful Boundary

The current LSP server is useful and tested, but it is not yet a full IDE-grade
refactoring engine. Code actions are:

- safe whole-document transforms
- not arbitrary AST refactors
- not speculative semantic rewrites

Windows `file:///...` URIs and percent-decoded Devanagari paths are explicitly
covered by tests.
