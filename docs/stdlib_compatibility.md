**Stdlib Compatibility**

Vak stdlib now follows a simple split:

- `main` modules are the canonical APIs new Vak code should prefer.
- `compatibility` modules are preserved so salvaged, imported, or older systems still run.

Current important example:

- `आयात रंग_पुस्तकालय`
  Canonical curated color API.
- `आयात colour_lib`
  Full repaired compatibility color library. It is preserved so the larger external color system is not lost, but new code should prefer `रंग_पुस्तकालय`.

Design rules:

- Prefer canonical module names in new code.
- Keep compatibility modules additive; do not silently replace curated modules.
- Let `वाक्य-रूपान्तर` use the stdlib manifest to repair imports safely.
