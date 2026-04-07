**Universal Codex Promotion Policy**

This file defines how Codex pages move from experimental branch space into
main Vak support.

## Main Rule

- `main Codex pages = deterministic and supportable`
- `branch Codex pages = experimental, heuristic, or language-subset research`

## Promotion Requirements

A branch Codex page may graduate into main only if all of the following are
true:

1. It is deterministic for its supported input subset.
2. It emits Vak that repeatedly passes Codex validation.
3. Its supported subset is clearly documented.
4. It does not silently guess dangerous semantics.
5. Its result quality is strong enough to justify long-term support.
6. A stable deterministic subset can be separated from any heuristic parts.

## Evidence Required

Before promotion, a page should have:

- focused unit tests
- corpus coverage under `stress/codex_corpus`
- validation history showing stable compile success
- clear confidence behavior:
  - `safe_auto_fix`
  - `suggest_only`
  - `do_not_touch`

## What Stays in Branches

These should remain branch-only unless a narrow stable subset emerges:

- C-like pages
- Rust-like pages
- natural-language pages
- pages that depend on semantic guesswork
- pages that can change meaning silently

## What Belongs in Main

These are good main-page candidates:

- Vak compatibility pages
- old Vak compatibility pages
- transliterated Sanskrit notation pages
- math/symbolic notation pages
- other deterministic Vak-adjacent normalization pages

## Graduation Process

Use this lifecycle:

1. build the page in a branch
2. add corpus cases and validation tests
3. identify the deterministic subset
4. graduate only that subset into main
5. leave risky/heuristic behavior behind in the branch

This keeps the Codex ambitious without letting experiments redefine Vak by
accident.
