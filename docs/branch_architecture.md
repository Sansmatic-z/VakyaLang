# Vak Branch Architecture

## Purpose

Vak is the trunk. Optional capabilities must grow as branches without changing
the semantic core by accident.

The decision rule for what belongs in trunk vs branch is documented in:

- `docs/main_vs_branch_policy.md`

This first-stage branch framework is intentionally conservative:

- trunk remains authoritative
- branches are additive
- branches may observe and validate
- branches do not redefine core semantics in this stage

## Protected Trunk

These areas are not branch-editable through the framework:

- sūtra rule system
- apavāda exception logic
- pariṇāma term rewriting
- Vibhakti semantic annotations
- bytecode format
- VM opcode meanings
- Rust VM ABI

## Current Hook Surface

The framework exposes only these typed observation points:

- `on_program_parsed(program, context)`
- `before_compile(program, context)`
- `after_typecheck(program, context)`
- `after_compile(bytecode, context)`
- `extend_vm_builtins(builtins, context)`

Each hook receives a `BranchHookContext` that can:

- emit diagnostics
- attach metadata

The runtime builtin hook is also narrow:

- branches may add new builtin names
- branches may not override or remove protected trunk builtins

This does not grant unrestricted mutation of the compiler pipeline.

## Why This Order

This is the safe order for Vak tree growth:

1. doctrine
2. typed branch framework
3. harmless validation branch
4. real low-risk branch migration
5. only then higher-risk semantic branches

## First Validation Branch

`tree_sentinel` is the proof-of-safety branch. It:

- counts AST nodes
- records top-level structure
- records emitted bytecode size
- does not modify user-visible behavior

`runtime_probe` is the proof-of-safety runtime branch. It:

- adds one harmless builtin for validation
- proves runtime builtin extension works
- verifies additive-only registration before real runtime branches migrate

## Activation Model

At this stage, branches are activated through the Python API, not language
syntax. This keeps parser and compiler surface changes minimal while the branch
framework stabilizes.

## Branch Admission

Vak now uses manifest-first branch admission:

1. discover `branch.json`
2. verify manifest schema and policy
3. register verified branches
4. quarantine invalid branches
5. activate only through registry policy

Discovery reads manifest data only. Branch code is not imported during
discovery.

Current manifest fields:

- `name`
- `version`
- `api_version`
- `kind`
- `entrypoint`
- `capabilities`
- `depends_on`
- `conflicts_with`
- `default_activation`

Current registry states:

- `registered`
- `quarantined`

Quarantined branches are visible in registry reports but cannot activate.

## First Real Runtime Branch

`chitrakala` is the first migrated real branch. The drawing engine remains in
its existing runtime package, but VM builtin registration now flows through the
branch system instead of hardcoded VM integration.
