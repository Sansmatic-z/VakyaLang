# 🕉️ VakyaLang — Living Project Status & Version Document

**Project:** वाक् (Vāk) Language + संस्कृत-कोडकः (Sanskrit Coder)  
**Author & Inventor:** Raj Mitra  
**Copyright:** © 2026 Raj Mitra. All Rights Reserved.  
**License:** Runtime → AGPL v3 | Specifications → Apache 2.0  
**Repository:** https://github.com/Sansmatic-z/VakyaLang  

---

> **Purpose of this document:**  
> This file is the single source of truth for the entire VakyaLang ecosystem.  
> Every AI assistant and every collaborator should read this first.  
> Nothing is ever fully removed — only added or upgraded.  
> Every change is logged here.

---

## 📌 Current Version

| Component | Version | Status |
|---|---|---|
| वाक् Language (Vāk) | 1.1.0 | ✅ Stable |
| संस्कृत-कोडकः (Sanskrit Coder) | 1.0.0 | ✅ Stable |
| Bytecode VM | 0.2.0 | 🔶 Partial (built-ins only) |
| Standard Library | 0.3.0 | 🔶 Growing |
| System Bridge (File I/O) | 1.0.0 | ✅ Stable |
| HTTP Bridge (Web Server) | 0.0.0 | ❌ Not yet built |

---

## 🏗️ Architecture Overview

### वाक् Execution Pipeline

```
Source (.vak file)
    ↓
[Lexer]         src/lexer.py         — Devanagari tokenizer
    ↓
[Parser]        src/parser.py        — Recursive descent → AST
    ↓
[Interpreter]   src/interpreter.py   — Tree-walk execution (PRIMARY)
    ↓
[Output / File / Memory]

Alternative (--vm flag):
[Compiler]      src/core/compiler.py — AST → Bytecode
    ↓
[VakVM]         src/core/vm.py       — Stack-based VM execution
```

### Sanskrit Coder Pipeline

```
User Command (Sanskrit or English)
    ↓
[SanskritEngine]     core/engine.py       — Main dispatcher
    ↓
[SanskritTranslator] core/translator.py   — Detect & translate
    ↓
[MathEngine]         math_engine/         — Arithmetic, algebra, formulas
[LogicEngine]        logic_engine/        — Nyāya syllogism
[Grammar]            grammar/             — Vibhakti, Lakara
[Numbers]            numbers/             — Sanskrit ↔ Arabic ↔ Words
```

---

## ✅ WHAT IS BUILT (Verified Working)

### वाक् Language Core

| Feature | File | Status | Notes |
|---|---|---|---|
| Devanagari Lexer | `src/lexer.py` | ✅ Working | Full Unicode block U+0900–U+097F |
| Devanagari numerals | `src/lexer.py` | ✅ Working | ०-९ identical to 0-9 |
| Bracket depth tracking | `src/lexer.py` | ✅ Working | Multi-line lists/dicts work |
| Recursive descent parser | `src/parser.py` | ✅ Working | All statement types |
| Typed AST nodes | `src/ast_nodes.py` | ✅ Working | 17 statement + 15 expression types |
| Lexical scope / closures | `src/environment.py` | ✅ Working | Full parent-chain |
| Tree-walk interpreter | `src/interpreter.py` | ✅ Working | Primary runtime |
| Variable declaration (`चर`) | interpreter | ✅ Working | |
| Constant declaration (`स्थिर`) | interpreter | ✅ Working | Immutable, reassign raises error |
| Functions with closures (`कर्म`) | interpreter | ✅ Working | Default params supported |
| Classes + inheritance (`वर्ग`) | interpreter | ✅ Working | Single inheritance |
| Polymorphism | interpreter | ✅ Working | Method override works |
| If/elif/else (`यदि/अन्यत्/अन्यथा`) | interpreter | ✅ Working | |
| While loop (`यावत्`) | interpreter | ✅ Working | |
| For-each loop (`प्रत्येक…अन्तर्गत`) | interpreter | ✅ Working | |
| Break (`विराम`) | interpreter | ✅ Working | |
| Continue (`अग्रे`) | interpreter | ✅ Working | |
| Try/catch/finally (`प्रयत्न/दोष/अन्ततः`) | interpreter | ✅ Working | |
| Throw (`उत्क्षिप`) | interpreter | ✅ Working | Custom exception objects too |
| Print (`मुद्रय`) | interpreter | ✅ Working | Multiple values, auto-stringify |
| Import system (`आयात`) | interpreter | ✅ Working | Module files as .vak |
| Lists (`सूची`) | interpreter | ✅ Working | Mutable, indexable |
| Dictionaries (`शब्दकोश`) | interpreter | ✅ Working | String/number keys |
| String concatenation | interpreter | ✅ Working | `+` operator |
| All arithmetic operators | interpreter | ✅ Working | `+` `-` `*` `/` `//` `%` `**` |
| All comparison operators | interpreter | ✅ Working | `==` `!=` `<` `>` `<=` `>=` |
| Logical operators (`और/अथवा/न`) | interpreter | ✅ Working | Short-circuit evaluation |
| `अन्तर्गत` (in operator) | interpreter | ✅ Working | Works on list/dict/string |
| Compound assignment (`+=` `-=` etc.) | interpreter | ✅ Working | |
| Member access (`obj.attr`) | interpreter | ✅ Working | |
| Index access (`obj[i]`) | interpreter | ✅ Working | |
| Interactive REPL | `run.py` | ✅ Working | Multi-line with `:` detection |
| `--tokens` debug flag | `run.py` | ✅ Working | Print token stream |
| `--ast` debug flag | `run.py` | ✅ Working | Print AST |
| `--bytecode` debug flag | `run.py` | ✅ Working | Print bytecode |
| `--vm` execution flag | `run.py` | 🔶 Partial | Built-ins only (see VM section) |

### Built-in Functions (30+ verified)

| Sanskrit | Meaning | Equivalent | Status |
|---|---|---|---|
| `दीर्घता(x)` | length | `len(x)` | ✅ |
| `प्रकार(x)` | type | `type(x)` | ✅ |
| `पाठ_कर(x)` | to-string | `str(x)` | ✅ |
| `पूर्णांक_कर(x)` | to-integer | `int(x)` | ✅ |
| `दशमलव_कर(x)` | to-float | `float(x)` | ✅ |
| `प्रवेश(prompt)` | input | `input()` | ✅ |
| `परास(n)` | range | `range(n)` | ✅ |
| `योग(list)` | sum | `sum()` | ✅ |
| `अधिकतम(...)` | maximum | `max()` | ✅ |
| `न्यूनतम(...)` | minimum | `min()` | ✅ |
| `क्रमबद्ध(list)` | sorted | `sorted()` | ✅ |
| `उलटो(list)` | reversed | `reversed()` | ✅ |
| `वर्गमूल(x)` | square root | `math.sqrt()` | ✅ |
| `परम(x)` | absolute | `abs()` | ✅ |
| `तल(x)` | floor | `math.floor()` | ✅ |
| `छत(x)` | ceiling | `math.ceil()` | ✅ |
| `जोड़ो(list, x)` | append | `list.append()` | ✅ |
| `हटाओ(list, x)` | remove | `list.remove()` | ✅ |
| `निकालो(list)` | pop | `list.pop()` | ✅ |
| `विभाजन(s, sep)` | split | `str.split()` | ✅ |
| `संयोग(list, sep)` | join | `str.join()` | ✅ |
| `उच्च(s)` | upper | `str.upper()` | ✅ |
| `निम्न(s)` | lower | `str.lower()` | ✅ |
| `छाँटो(s)` | strip | `str.strip()` | ✅ |
| `कुंजियाँ(dict)` | keys | `dict.keys()` | ✅ |
| `मान(dict)` | values | `dict.values()` | ✅ |
| `काल()` | timestamp | `time.time()` | ✅ |
| `दृढ़ता(cond)` | assert | `assert` | ✅ |
| `निर्गम(code)` | exit | `exit()` | ✅ |
| `पाई` | π constant | `math.pi` | ✅ |
| `प्रकृतिक_आधार` | e constant | `math.e` | ✅ |

### System Bridge — File I/O & OS (`src/bridge/system.py`)

| Function | Meaning | Status |
|---|---|---|
| `पठन(path)` | read file → string | ✅ Working |
| `लेखन(path, data)` | write file | ✅ Working |
| `लेखन(path, data, 'a')` | append to file | ✅ Working |
| `अस्तित्व(path)` | file/dir exists | ✅ Working |
| `मिटाओ(path)` | delete file | ✅ Working |
| `सूची_निर्देशिका(path)` | list directory | ✅ Working |
| `बनाओ_निर्देशिका(path)` | mkdir -p | ✅ Working |
| `कार्य_निर्देशिका()` | getcwd | ✅ Working |
| `मंच()` | OS platform | ✅ Working |
| `प्रणाली_कमांड(cmd)` | shell command | ✅ Working |
| `परिवेश_प्राप्त(key)` | getenv | ✅ Working |
| `परिवेश_सेट(key, val)` | setenv | ✅ Working |

### Bytecode VM (`src/core/`)

| Component | File | Status | Notes |
|---|---|---|---|
| Opcode ISA (60+ opcodes) | `src/core/opcodes.py` | ✅ Defined | Full instruction set |
| AST → Bytecode Compiler | `src/core/compiler.py` | 🔶 Partial | No functions/classes yet |
| Stack-based VM | `src/core/vm.py` | 🔶 Partial | Built-ins only for CALL |
| All arithmetic opcodes | vm.py | ✅ Working | ADD SUB MUL DIV IDIV MOD POW NEG |
| All comparison opcodes | vm.py | ✅ Working | EQ NEQ LT GT LTE GTE IN |
| Control flow | vm.py | ✅ Working | JUMP JUMP_IF_FALSE LOOP |
| Variable ops | vm.py | ✅ Working | DEFINE LOAD STORE |
| User-defined function calls | vm.py | ❌ Not yet | CALL only handles built-ins |
| Classes in VM | vm.py | ❌ Not yet | — |
| Closures in VM | vm.py | ❌ Not yet | — |
| Try/catch in VM | vm.py | ❌ Not yet | — |

### Standard Library (`stdlib/`)

| Module | File | Status | Contents |
|---|---|---|---|
| Foundation | `stdlib/mool.vak` | ✅ Working | factorial, primes, GCD, map, filter, reduce, flatten, palindrome |
| Path utils | `stdlib/path.vak` | 🔶 Basic | Path manipulation |
| File API | `stdlib/file.vak` | 🔶 Basic | OOP file wrapper (`संचिका` class) |
| JSON-like | `stdlib/json.vak` | 🔶 Basic | Basic serialization |

### Example Programs (`examples/`)

| File | Description | Status |
|---|---|---|
| `namaste.vak` | Hello World, variables, strings | ✅ Verified |
| `fibonacci.vak` | Recursion + iteration | ✅ Verified |
| `varg.vak` | Classes, inheritance, polymorphism | ✅ Verified |
| `data.vak` | Lists, dicts, higher-order functions | ✅ Verified |
| `dosh.vak` | Try/catch/finally, custom exceptions | ✅ Verified |
| `vyapak.vak` | Comprehensive — all major features | ✅ Verified |
| `tasks.vak` | Persistent CLI task manager (real software) | ✅ Verified |
| `webgen.vak` | Static website generator (writes real HTML) | ✅ Verified |

### संस्कृत-कोडकः (Sanskrit Coder)

| Component | File | Status | Notes |
|---|---|---|---|
| Main engine | `core/engine.py` | ✅ Working | Dispatcher for all commands |
| Translator | `core/translator.py` | ✅ Working | Sanskrit ↔ English math terms |
| Number system | `numbers/sanskrit_numbers.py` | ✅ Working | 0–1000+ in Sanskrit words |
| Math engine | `math_engine/math_engine.py` | ✅ Working | Arithmetic, algebra, 5 formulas |
| Logic engine | `logic_engine/logic_engine.py` | ✅ Working | Nyāya search and info |
| Grammar | `grammar/grammar.py` | ✅ Working | 8 Vibhakti, 10 Lakara |
| CLI | `main.py` | ✅ Working | Interactive command interface |
| Tests | `tests/test_sanskrit_coder.py` | ✅ Working | 19/19 passing |

**Sanskrit Coder Commands:**

| Sanskrit | English | What it does | Status |
|---|---|---|---|
| `गणय` | `calculate` | Arithmetic expression | ✅ |
| `समाधत्स्व` | `solve` | Solve equation (ax+b=c) | ✅ |
| `पश्य` | `show` | Formula lookup | ✅ |
| `अन्वेषय` | `search` | Knowledge/logic search | ✅ |
| `परिवर्तय` | `convert` | Unit conversion | ✅ |
| `भाषा` | `language` | Switch Sanskrit/English output | ✅ |

**Built-in Formula Database:**

| Formula | Sanskrit | Status |
|---|---|---|
| F = ma | बलम् = द्रव्यमानम् × त्वरणम् | ✅ |
| E = mc² | शक्तिः = द्रव्यमानम् × प्रकाशवेगः² | ✅ |
| A = πr² | वृत्तस्य क्षेत्रफलम् = π × त्रिज्या² | ✅ |
| v = u + at | वेगः = प्रारम्भिक-वेगः + त्वरणम् × कालः | ✅ |
| PV = nRT | दाबः × आयतनम् = मात्रा × R × तापमानम् | ✅ |

### Repository & Legal

| Item | Status | Notes |
|---|---|---|
| GitHub repo live | ✅ | github.com/Sansmatic-z/VakyaLang |
| Folder structure | ✅ | runtime/, sanskrit_coder/, examples/, docs/, tests/ |
| AGPL v3 LICENSE file | ✅ Fixed | 3rd commit scrubbed MIT/Apache mentions |
| LICENSE_AGPL | ✅ | Full AGPL text |
| LICENSE_APACHE | ✅ | For spec documents |
| CITATION.cff | ✅ | Academic attribution — Raj Mitra as inventor |
| NOTICE file | ✅ | Legal notices |
| CONTRIBUTING.md | ✅ | |
| SECURITY.md | ✅ | |
| CODE_OF_CONDUCT.md | ✅ | |
| CHANGELOG.md | ✅ | |
| pyproject.toml | ✅ Fixed | AGPL classifier set |
| Repo description | ❌ Not yet | Needs adding via GitHub gear icon |
| Repo topics | ❌ Not yet | Needs adding via GitHub gear icon |
| Commits | 3 | Clean history from restructure |

---

## 🔶 WHAT NEEDS UPGRADING (Priority Order)

### Priority 1 — Immediate (small effort, big impact)

| Task | Where | Why |
|---|---|---|
| Add repo description on GitHub | GitHub web UI → gear icon | First thing visitors see |
| Add repo topics on GitHub | GitHub web UI → gear icon | `sanskrit`, `programming-language`, `compiler`, `virtual-machine`, `devanagari`, `nyaya-logic` |
| Verify AGPL badge shows on GitHub | GitHub repo page | Confirm license fix worked |
| Multi-line string support in Lexer | `src/lexer.py` | Needed for cleaner programs (workaround: single-line concat) |

### Priority 2 — Next Features (medium effort)

| Task | Where | What it unlocks |
|---|---|---|
| HTTP Bridge | `src/bridge/http.py` | वाक् can serve web pages — real web apps |
| VM: user-defined function calls | `src/core/vm.py` | `--vm` mode becomes fully usable |
| VM: classes and closures | `src/core/vm.py` | Complete VM execution |
| JSON module (proper) | `stdlib/json.vak` + bridge | Real data exchange with other systems |
| String formatting (`प्रारूप`) | interpreter | `"नमस्ते {नाम}"` style strings |
| Math stdlib module | `stdlib/ganit.vak` | Trigonometry, logarithms in Sanskrit |

### Priority 3 — Expansion (larger effort)

| Task | Description |
|---|---|
| Sanskrit Coder: expanded formulas | Add geometry, thermodynamics, quantum physics formulas |
| Sanskrit Coder: word problems | Parse arithmetic described in Sanskrit prose |
| Vedic math module | Implement Vedic sutras as algorithms |
| वाक् ↔ Sanskrit Coder bridge | Call Coder engine directly from .vak code |
| Pattern matching (`रूप_मिलान`) | Modern language feature |
| Generator functions (`उत्पादक`) | `yield`-style lazy iteration |
| VS Code / Neovim syntax highlighting | `.vak` file syntax coloring |
| Online REPL | Run वाक् in browser via Pyodide |
| Package manager | Install/share `.vak` modules |

---

## 📋 KNOWN LIMITATIONS & WORKAROUNDS

| Limitation | Workaround |
|---|---|
| No multi-line strings | Use string concatenation with `+` |
| `न` is reserved (NOT keyword) | Use `गण`, `संख्या`, `मान` for number variables |
| `वर्ग` is reserved (CLASS keyword) | Use `श्रेणी`, `वर्गफल` for "square" functions |
| `से` is reserved (FROM keyword) | Use `स्रोत`, `स्थान` as variable names |
| VM mode: no user functions/classes | Use default mode (no `--vm` flag) for complex programs |
| System bridge must be registered | Call `register_system_bridge(interp.globals)` when using API directly |
| No HTTP server yet | Use `प्रणाली_कमांड` to call Python's http.server as workaround |

---

## 🚀 HOW TO RUN

```bash
# Termux / Android / Linux — no pip installs needed

cd VakyaLang/runtime

# Interactive REPL
python run.py

# Run a .vak file
python run.py examples/namaste.vak

# Inline code
python run.py -c 'मुद्रय "नमस्ते जगत्!"'

# Debug tools
python run.py --tokens examples/fibonacci.vak   # token stream
python run.py --ast    examples/fibonacci.vak   # AST
python run.py --bytecode benchmark.vak          # bytecode

# Bytecode VM mode (simple programs only)
python run.py --vm benchmark.vak

# Sanskrit Coder
cd ../sanskrit_coder
python main.py

# Sanskrit Coder tests
python tests/test_sanskrit_coder.py
```

---

## 📝 CHANGELOG

### v1.1.0 — 2026-03-09
- Added: System Bridge (`src/bridge/system.py`) — File I/O, OS access, 12 functions
- Added: Bytecode VM (`src/core/vm.py`) — all arithmetic + comparison opcodes
- Added: Bytecode Compiler (`src/core/compiler.py`) — partial AST compilation
- Added: `tasks.vak` — persistent CLI task manager (real software example)
- Added: `webgen.vak` — static website generator (writes real HTML)
- Fixed: Bracket depth tracking in Lexer (multi-line collections work)
- Fixed: `स्वयं` (self) accepted as function parameter
- Fixed: Method binding — self param correctly skipped when bound

### v1.0.0 — 2026-03-08
- Initial release: complete वाक् language
- Lexer: full Devanagari + significant whitespace
- Parser: recursive descent, all statement types
- Interpreter: tree-walk, 30+ built-ins
- Classes with single inheritance
- Closures and higher-order functions
- Error handling (try/catch/finally)
- Import system
- संस्कृत-कोडकः v1.0.0: 19/19 tests passing
- Repository published: github.com/Sansmatic-z/VakyaLang
- AGPL v3 + Apache 2.0 dual license
- CITATION.cff — Raj Mitra as inventor

---

## 👤 Authorship

**Raj Mitra** is the sole original inventor, visionary, and architect of:
- The concept of Sanskrit as a computing substrate
- The वाक् language design and keyword choices
- The connection between Pāṇinian grammar and programming language structure
- The Sanskrit Coder concept rooted in Nyāya logic
- The VakyaLang ecosystem as a whole

AI assistants (Claude, Gemini) were used as implementation tools under Raj Mitra's direction.

---

*"वाक् वै ब्रह्म"* — Speech is indeed the universal principle.  
*Last updated: 2026-03-09 by Raj Mitra*
