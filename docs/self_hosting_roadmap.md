**Self-Hosting Roadmap**

Vak is not yet a fully self-hosting language. The runtime, repair system,
Codex, proof engine, and TUI are already substantial, but the bootstrap
compiler path still needs more work before Vak should claim true self-hosting.

## Current Truth

Stable today:

- main runtime and VM
- stdlib and compatibility layers
- `वाक्य-रूपान्तर`
- Codex
- Sansmatic proof tooling
- Vak-native self-checking examples

Still evolving:

- `compiler/compiler.vak`
- bootstrap reproducibility beyond the current demo path
- standalone compiled-artifact completeness
- moving more tooling from Python into Vak itself

## Staged Plan

1. **Bootstrap correctness**
   - keep `compiler.vak` behaviorally correct on real inputs
   - expand compile/disassemble/run tests
   - keep reproducibility checks on emitted bootstrap artifacts

2. **Tool migration only where safe**
   - move narrow diagnostic and self-check logic into Vak first
   - keep orchestration-heavy host tooling in Python until Vak-side compiler
     confidence is higher

3. **Nontrivial self-compile**
   - compile real Vak tools, not only minimal demos
   - compare runtime behavior between source and compiled compiler paths

4. **Reproducible self-hosting**
   - compiler compiles itself
   - emitted artifact is reproducible enough to trust as a stage boundary

## What Not To Do

- do not force large tooling migrations into Vak before bootstrap is ready
- do not claim full self-hosting because a skeleton compiler exists
- do not change bytecode format or VM opcodes just to accelerate the roadmap

## Why This Matters

Vak already benefits from Vak-native self-check programs and `.vak` Codex pages.
That is the correct direction. The next steps should stay additive and verified
until the bootstrap compiler becomes genuinely trustworthy.
