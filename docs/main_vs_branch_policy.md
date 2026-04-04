# Main vs Branch Policy

## Purpose

This file defines how Vak features are classified as:

- `main` (trunk VakyaLang)
- `branch` (optional, experimental, or domain-specific capability)

The goal is to let Vak evolve aggressively without destabilizing the language
core.

## Core Rule

Use this rule first:

- `main = guarantee`
- `branch = experiment or specialization`

If a feature is something the project is willing to guarantee as part of Vak
itself, it belongs in `main`.

If a feature is still exploratory, heuristic, domain-specific, or optional, it
belongs in a `branch`.

## What Belongs in Main

Main Vak should contain features that are:

- language-wide
- deterministic
- stable
- low-risk
- needed by most users
- not tied to a single domain
- appropriate for long-term support

Typical examples:

- parser, compiler, VM, runtime correctness
- import/module correctness
- core stdlib
- error quality
- deterministic `वाक्य-अनुवादक`
- conservative `वाक्य-रूपान्तर`
- type-system correctness
- branch framework itself

## What Belongs in a Branch

A branch should contain features that are:

- experimental
- heuristic
- optional
- domain-specific
- likely to change shape
- risky if enabled silently
- useful to some users but not required by all Vak programs

Typical examples:

- graphics systems like `chitrakala`
- runtime probes and validation branches
- adaptive/self-healing repair logic
- aggressive code intelligence
- domain DSLs
- semantic experiments that may later be narrowed and promoted

## Decision Questions

Before adding a feature to `main`, ask:

1. Does this apply to Vak as a whole, not just one workflow?
2. Is it deterministic and explainable?
3. Can it run safely by default?
4. Would failure be visible and recoverable without silent semantic drift?
5. Is the project willing to support this as a long-term Vak contract?

If any of these answers is `no`, the feature should usually begin as a
`branch`.

## Promotion Rule

Branch features may graduate into `main`, but only after they satisfy all of
the following:

1. They are deterministic.
2. They pass broad verification repeatedly.
3. They are useful outside a niche domain.
4. They do not silently change program meaning.
5. Their stable subset is clear enough to support long-term.

Only the stable deterministic subset should move to `main`. The rest should
remain branch-only.

## Policy for Vakya-Rupantar

`वाक्य-रूपान्तर` follows a split design:

- `main रूपान्तर` = conservative compatibility and normalization engine
- `branch रूपान्तर` = adaptive or aggressive repair behavior

Main `रूपान्तर` may do:

- syntax drift normalization
- canonical keyword repair
- safe import correction
- deterministic member/builtin alias repair
- branch-aware API normalization
- compile-validated conservative rewrites

Branch `रूपान्तर` may do:

- fuzzy repair
- adaptive unresolved-name recovery
- lower-confidence builtin/member correction
- domain-specific repair packs
- multi-pass experimental healing strategies

Main must remain understandable and conservative. Branches may explore more,
but only as opt-in behavior with visible reports.

## Things Branches Must Not Redefine

The following remain protected regardless of branch policy:

- sūtra rule system
- apavāda exception logic
- pariṇāma term rewriting semantics
- Vibhakti semantic annotations
- bytecode format
- VM opcode meanings
- Rust VM ABI

## Operational Policy

Use this lifecycle:

1. build in branch
2. validate through tests and real usage
3. narrow to the stable deterministic subset
4. promote that subset into main only if it deserves long-term support

This keeps Vak flexible without letting experimental behavior redefine the
language by accident.
