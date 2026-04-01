# Sansmatic Production Architecture

## Target

Evolve Sansmatic from a prototype rule engine into a production-grade proof subsystem
for VakyaLang without breaking the current built-in surface.

## Architecture

```text
                    +-----------------------------------+
                    | VakyaLang Source / Macro System   |
                    +----------------+------------------+
                                     |
                                     v
                    +-----------------------------------+
                    | NyayaProofVerifier                |
                    | - proof sandbox                   |
                    | - compile-time proof policy       |
                    +----------------+------------------+
                                     |
                                     v
      +------------------------------+------------------------------+
      |                     Sansmatic Core                          |
      |-------------------------------------------------------------|
      |  Statement / Fact Model   |  Rule Engine / Obligations      |
      |  Proof Registry           |  Contradiction Detection        |
      |  Certificate Authority    |  Observability / Audit Log      |
      |  Configuration            |  Security Policy                |
      +------------------------------+------------------------------+
                                     |
                      +--------------+---------------+
                      |                              |
                      v                              v
        +-----------------------------+  +---------------------------+
        | Runtime Bridge / VM         |  | Tooling / CI / Packaging  |
        | - builtins                  |  | - tests                   |
        | - runtime verification      |  | - env config              |
        | - backward compatibility    |  | - container / workflows   |
        +-----------------------------+  +---------------------------+
```

## First Production Hardening Step

1. Add explicit Sansmatic runtime settings loaded from the environment.
2. Add authenticated certificate support while preserving the legacy hash field.
3. Reject unsafe proof registration that could authorize arbitrary statements.
4. Add regression tests that lock down security-sensitive behavior.

## Design Decisions

- Use standard-library-only configuration and certificate code in the core path.
  This keeps the proof kernel lightweight, auditable, and compatible with the
  current packaging model.
- Preserve the current builtins (`परिभाषय`, `दावा`, `नियम`, `मूल्यांकन`,
  `सिद्ध_है`) and existing certificate payload keys. New security metadata is additive.
- Default to strict proof registration. Unsafe universal proof IDs are rejected
  unless explicitly re-enabled by configuration.
- Support authenticated certificates through environment configuration so local
  development remains easy, while deployment can enforce stronger trust.

## Async Guidance

The current VakyaLang runtime has a custom event loop. We will not mix deeper
proof-kernel changes with async refactors. For Python integration points, the
target reference is modern asyncio structured concurrency:

- `asyncio.TaskGroup`
- `asyncio.timeout()`
- `asyncio.Runner` / `asyncio.run()`

We will avoid old loop-parameter patterns and low-level event-loop coupling in
new Sansmatic code.
