**Vak TUI**

`vakyalang` launches the additive Vak terminal environment.

Available sections:
- `मुख्य`
- `REPL`
- `आयाम`
- `सान्समैटिक`
- `चित्रकला`
- `VPM`
- `रूपान्तर`

Local launch options:
- `vakyalang`
- `python vakyalang.py`
- `python vak.py --tui`
- `python runtime/run.py --tui`

Useful flags:
- `--plain`
  Force the built-in fallback renderer instead of Rich.
- `--mode <name>`
  Start directly in `repl`, `sandbox`, `proof`, `chitra`, `vpm`, or `repair`.
- `--cwd <path>`
  Use a specific working directory for VPM and Chitrakala saves.
- `--command <text>`
  Run one or more commands non-interactively and render the resulting state.
- `--no-clear`
  Do not clear the screen between renders.

Mode overview:
- `REPL`
  Runs Vak code in a persistent named sandbox. `:block` starts multiline entry.
- `आयाम`
  Create, switch, reset, drop, inspect globals, and inspect the current Vak stack.
- `सान्समैटिक`
  Manage definitions, facts, rules, evaluations, traces, proof trees, and explanations with a live proof-state panel.
- `चित्रकला`
  Create canvases, draw primitives, run effects, preview in terminal, and save PNGs.
- `VPM`
  Initialize a project, inspect installed packages, search, inspect, install, and remove packages.
- `रूपान्तर`
  Load a `.vak` file, run `वाक्य-रूपान्तर`, inspect the report and unified diff, then apply or reject the result.

Global help commands:
- `builtins [category]`
- `modules`

Examples:

```text
vakyalang --plain --mode repl --command "चर संख्या = ७" --command "मुद्रय संख्या"
vakyalang --plain --mode proof --command "define अग्नि ताप" --command "assert अग्नि HAS ताप"
vakyalang --plain --mode chitra --command "new 80 40 white" --command "mandala" --command "save demo.png"
vakyalang --plain --mode vpm --cwd . --command "init" --command "installed"
vakyalang --plain --mode repair --command "load demo.vak" --command "analyze" --command "diff"
```

Rich support:
- If `rich` is installed, the TUI uses panel/layout rendering.
- If `rich` is unavailable, Vak falls back to a plain terminal renderer so the environment remains usable without introducing new dependencies.
