# Development Utilities

`dev/package_lib.py` is the only live tool kept at the root of `dev/` because
`vpm.py bundle` loads it directly.

All other historical fix/debug scripts and disassembly dumps have been moved to:

- `dev/quarantine/legacy_tools`

They are preserved for archaeology and recovery, but they are not part of the
supported runtime or editor/tooling surface.
