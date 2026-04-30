**Performance Profiling**

Vak now includes built-in measurement tooling for the parser, compiler, VM, and
module import path. This is measurement tooling, not a claim that Vak has been
fully performance-tuned yet.

## What It Measures

Current profiling surfaces collect per-stage timing for:

- `prepare`
- `lex`
- `parse`
- `compile`
- `execute`

Import profiling routes through the same pipeline with an `आयात <module>` source
snippet, so the numbers reflect the real import path rather than a synthetic
counter.

## Python API

Available through `runtime/src/interpreter.py`:

- `VakInterpreter.profile_source(source, filename=None, repeat=3, execute=True)`
- `VakInterpreter.profile_import(module_name, filename=None, repeat=3)`

These return `VakPerformanceProfile` instances from
`runtime/src/performance.py`.

## Vak Builtins

Available through `runtime/src/vm.py`:

- `प्रदर्शन_विवरण(source, filename = शून्य, repeat = 3, execute = सत्य)`
- `प्रदर्शन_पाठ(source, filename = शून्य, repeat = 3, execute = सत्य)`
- `आयात_प्रदर्शन_विवरण(module_name, filename = शून्य, repeat = 3)`
- `आयात_प्रदर्शन_पाठ(module_name, filename = शून्य, repeat = 3)`

Use these from Vak when you want the language to inspect its own frontend and
runtime behavior.

## CLI Tool

Use the dedicated profiler script:

```bash
python runtime/tooling/profile_runtime.py examples/vak_self_check.vak
python runtime/tooling/profile_runtime.py --import रंग_पुस्तकालय --repeat 5
python runtime/tooling/profile_runtime.py examples/vak_self_check.vak --json
```

## Design Boundary

- The profiler is intended for guided measurement before optimization.
- It does not claim cycle-accurate benchmarking.
- It should be used to compare Vak surfaces against themselves, not as a
  substitute for a dedicated benchmark harness.
