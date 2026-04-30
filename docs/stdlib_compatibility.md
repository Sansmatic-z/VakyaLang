**Stdlib Compatibility**

Vak stdlib now follows a simple split:

- `main` modules are the canonical APIs new Vak code should prefer.
- `compatibility` modules are preserved so salvaged, imported, or older systems still run.
- `alias` entries map legacy or Romanized import names back to canonical modules.

Current important example:

- `आयात रंग_पुस्तकालय`
  Canonical curated color API.
- `आयात colour_lib`
  Full repaired compatibility color library. It is preserved so the larger external color system is not lost, but new code should prefer `रंग_पुस्तकालय`.

Design rules:

- Prefer canonical module names in new code.
- Keep compatibility modules additive; do not silently replace curated modules.
- Let `वाक्य-रूपान्तर` use the stdlib manifest to repair imports safely.
- Let Codex and TUI module views use the same manifest instead of hard-coded lists.

Helpful manifest helpers in [stdlib_manifest.py](/C:/RIZAMD/vakyalang-upgraded%20xyz/vakyalang-upgraded/runtime/src/stdlib_manifest.py):

- `build_stdlib_manifest()`
- `module_alias_map()`
- `canonical_module_names()`
- `compatibility_module_names()`
- `canonical_module_specs()`
- `resolve_module_name(name)`

Current import policy:

- use the canonical module name in new Vak code
- keep compatibility imports working for repaired/salvaged systems
- let `रूपान्तर` normalize drifted imports toward canonical targets where the manifest makes that safe
