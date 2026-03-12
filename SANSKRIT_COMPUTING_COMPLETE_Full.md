# 🕉️ Sanskrit Computing Ecosystem — Complete Technical Manual

**Version 1.0 | March 8, 2026**  
**Author & Inventor: Raj Mitra**  
**Copyright © 2026 Raj Mitra. All Rights Reserved.**  
**Licenses: Runtime → AGPL v3 | Specifications → Apache 2.0**

---

> *"वाक् वै ब्रह्म"* — Speech is indeed the universal principle.  
> *"संस्कृतं देवभाषा च सर्वविज्ञानवाहिनी"* — Sanskrit, the language of gods, carries all knowledge.

---

## Overview

The Sanskrit Computing Ecosystem is a first-of-its-kind software project that treats Sanskrit not as a historical curiosity but as a rigorous, formal substrate for computing. It consists of two interconnected but architecturally distinct systems:

| System | Role |
|--------|------|
| **वाक् (Vāk)** | General-purpose programming language written entirely in Sanskrit Devanagari |
| **संस्कृत-कोडकः (Sanskrit Coder)** | Mathematical and logical execution engine that processes Sanskrit expressions |

Together they form a complete computing ecosystem where Sanskrit is the primary medium — from writing programs to performing calculations to reasoning through logic.

---

---

# Part I — वाक् (Vāk): The Sanskrit Programming Language

---

## 1. What Is वाक्?

वाक् (Vāk, meaning *"The Word"* or *"primordial speech"*) is a general-purpose, dynamically-typed, interpreted programming language whose entire syntax is expressed in Sanskrit Devanagari script.

- Every **keyword** is a Sanskrit word with a precise, intentional meaning
- **Devanagari numerals** (०, १, २, … ९) are natively supported alongside ASCII digits
- The grammar draws from **Pāṇini's Ashtadhyayi** — the oldest and most formally precise grammar system in human history
- The logical operators map to **Nyāya school** reasoning primitives
- File extension: `.vak`
- Runs on: Python 3.8+ (no external dependencies), including **Termux on Android**

---

## 2. Architecture

वाक् has a layered execution pipeline:

```
Source (.vak file)
       ↓
   [Lexer]         → Tokenizes Devanagari script, handles indentation
       ↓
   [Parser]        → Recursive descent, produces Abstract Syntax Tree (AST)
       ↓
[Interpreter]      → Tree-walk execution (primary runtime)
       ↓
   [Output]        → Console / File / Memory

Alternative path (--vm flag):
   [Compiler]      → Translates AST to bytecode (CodeObject)
       ↓
    [VakVM]        → Stack-based virtual machine executes bytecode
```

### 2.1 Lexer (`src/lexer.py`)

The lexer is Devanagari-aware and handles:

- **Full Unicode Devanagari block** (U+0900–U+097F) for identifiers and keywords
- **Devanagari digit recognition**: `०१२३४५६७८९` converted to ASCII for numeric parsing
- **Significant whitespace**: Python-style indentation with an indent-stack generating `INDENT` and `DEDENT` tokens
- **Bracket depth tracking**: `INDENT`/`DEDENT` are suppressed inside `()`, `[]`, `{}` — enabling multi-line expressions inside collections
- **Comment syntax**: `#` (ASCII) and `टीका` (Sanskrit) both mark line comments
- **String literals**: Both `"` and `'` delimited, with standard escape sequences

### 2.2 Parser (`src/parser.py`)

Recursive descent parser implementing the full Pāṇinian-inspired grammar. Produces a fully typed AST with line numbers for error reporting. Handles:

- All statement types (declarations, control flow, classes, imports)
- Expression precedence via Pratt-style climbing (10 levels)
- Multi-line collections without indent/dedent interference
- `स्वयं` (self) as a valid function parameter

### 2.3 AST Nodes (`src/ast_nodes.py`)

The complete set of typed AST nodes:

**Statements**: `Program`, `VarDecl`, `ConstDecl`, `FuncDecl`, `ClassDecl`, `ReturnStmt`, `PrintStmt`, `IfStmt`, `WhileStmt`, `ForStmt`, `BreakStmt`, `ContinueStmt`, `TryStmt`, `ThrowStmt`, `ImportStmt`, `ExprStmt`, `Block`

**Expressions**: `BinaryExpr`, `UnaryExpr`, `AssignExpr`, `CallExpr`, `MemberExpr`, `IndexExpr`, `IdentifierExpr`, `NumberLiteral`, `StringLiteral`, `BoolLiteral`, `NullLiteral`, `ListLiteral`, `DictLiteral`, `LambdaExpr`

### 2.4 Environment / Scope (`src/environment.py`)

Lexical scope with a parent-chain for closures:

- `define(name, value, constant=False)` — creates variable in current scope
- `get(name, line)` — walks the scope chain upward; raises `VakNameError` if not found
- `assign(name, value, line)` — walks chain and assigns; raises error on constant reassignment
- `child(name)` — creates a new child scope (used for each block, function, and class body)

### 2.5 Interpreter (`src/interpreter.py`)

Tree-walk interpreter. Dispatches on AST node type. Key runtime values:

| Runtime Type | Description |
|---|---|
| `int / float` | Native Python numbers |
| `str` | Native Python strings |
| `bool` | Native Python booleans |
| `list` | Native Python lists (mutable) |
| `dict` | Native Python dicts |
| `VakNull` | Singleton null value (शून्य) |
| `VakFunction` | User-defined function with closure |
| `VakClass` | User-defined class |
| `VakInstance` | Instance of a user-defined class |
| `BuiltinFunction` | Native built-in wrapped in वाक् interface |

### 2.6 Bytecode Compiler (`src/core/compiler.py`)

Compiles AST into a `CodeObject` — a flat list of `(OpCode, operand)` pairs plus a constants pool. Supports: variable declaration, constants, print, if/elif/else, while loops, for loops, function calls, return, basic expressions.

**Current limitation**: The compiler is a subset implementation. Function definitions, classes, closures, try/catch, and import are handled by the tree-walk interpreter. Use `--vm` only for programs that do not use these features yet.

### 2.7 Virtual Machine (`src/core/vm.py`)

Stack-based VM with 157 lines. Executes `CodeObject` instructions. Fully implements:

- All arithmetic: `ADD`, `SUB`, `MUL`, `DIV`, `IDIV`, `MOD`, `POW`, `NEG`
- All comparisons: `EQ`, `NEQ`, `LT`, `GT`, `LTE`, `GTE`, `IN`
- Boolean logic: `NOT`
- Control flow: `JUMP`, `JUMP_IF_FALSE`, `LOOP`
- Variables: `DEFINE_VAR`, `DEFINE_CONST`, `LOAD_VAR`, `STORE_VAR`
- Output: `PRINT`
- Built-in function calls: `CALL` (built-ins only at this stage)

**Benchmark result** (10,000 iteration loop):  
- Tree-walk interpreter: 0.432s  
- Bytecode VM: 0.390s (~10% faster, limited by Python startup overhead at this loop size)

---

## 3. Full Keyword Reference

| Sanskrit | IAST | Meaning | Role |
|---|---|---|---|
| `चर` | cara | moving/changing | variable declaration |
| `स्थिर` | sthira | stable/fixed | constant declaration |
| `कर्म` | karma | action | function definition |
| `वर्ग` | varga | category/class | class definition |
| `प्रत्यागच्छ` | pratyāgaccha | return/come back | return statement |
| `यदि` | yadi | if | conditional |
| `अन्यत्` | anyat | otherwise | else-if |
| `अन्यथा` | anyathā | in another way | else |
| `यावत्` | yāvat | as long as | while loop |
| `प्रत्येक` | pratyek | each/every | for-each loop |
| `अन्तर्गत` | antargata | within/contained in | loop `in` operator |
| `विराम` | virāma | stop/pause | break |
| `अग्रे` | agre | forward | continue |
| `मुद्रय` | mudraya | imprint/print | print statement |
| `और` | aur | and | logical AND |
| `अथवा` | athavā | or | logical OR |
| `न` | na | no/not | logical NOT |
| `सत्य` | satya | truth | `true` literal |
| `असत्य` | asatya | untruth | `false` literal |
| `शून्य` | śūnya | zero/void | `null` literal |
| `प्रयत्न` | prayatna | attempt | try block |
| `दोष` | doṣa | fault/error | catch block |
| `अन्ततः` | antataḥ | ultimately/finally | finally block |
| `उत्क्षिप` | utkṣipa | throw/hurl | throw statement |
| `आयात` | āyāta | import/bring in | import statement |
| `से` | se | from | `from` in import |
| `नव` | nava | new | object instantiation |
| `स्वयं` | svayam | oneself | self reference |
| `अभिभावक` | abhibhāvaka | parent/guardian | super reference |

---

## 4. Built-in Functions

### 4.1 Core Utilities

| Function | Sanskrit Meaning | Equivalent | Description |
|---|---|---|---|
| `दीर्घता(x)` | length | `len(x)` | Length of string, list, or dict |
| `प्रकार(x)` | type/kind | `type(x)` | Returns Sanskrit type name |
| `पाठ_कर(x)` | make-text | `str(x)` | Convert to string |
| `पूर्णांक_कर(x)` | make-integer | `int(x)` | Convert to integer |
| `दशमलव_कर(x)` | make-decimal | `float(x)` | Convert to float |
| `प्रवेश(prompt)` | entrance/input | `input()` | Read user input |
| `परास(n)` | range/extent | `range(n)` | Generate range 0..n-1 |
| `परास(a,b)` | range/extent | `range(a,b)` | Generate range a..b-1 |
| `परास(a,b,c)` | range/extent | `range(a,b,c)` | Generate range with step |
| `दृढ़ता(cond)` | firmness/assert | `assert` | Assert condition |
| `निर्गम(code)` | exit/departure | `exit()` | Exit program |
| `काल()` | time/epoch | `time.time()` | Unix timestamp |

### 4.2 Math Functions

| Function | Sanskrit Meaning | Equivalent |
|---|---|---|
| `वर्गमूल(x)` | square-root | `math.sqrt(x)` |
| `परम(x)` | absolute/supreme | `abs(x)` |
| `तल(x)` | floor | `math.floor(x)` |
| `छत(x)` | ceiling | `math.ceil(x)` |
| `अधिकतम(...)` | maximum | `max(...)` |
| `न्यूनतम(...)` | minimum | `min(...)` |
| `योग(list)` | sum/addition | `sum(list)` |

**Built-in constants**: `पाई` = π (3.14159…), `प्रकृतिक_आधार` = e (2.71828…)

### 4.3 List Functions

| Function | Sanskrit Meaning | Equivalent |
|---|---|---|
| `जोड़ो(list, x)` | add/attach | `list.append(x)` |
| `हटाओ(list, x)` | remove | `list.remove(x)` |
| `निकालो(list)` | take out | `list.pop()` |
| `क्रमबद्ध(list)` | ordered | `sorted(list)` |
| `उलटो(list)` | reversed | `list(reversed(list))` |

### 4.4 String Functions

| Function | Sanskrit Meaning | Equivalent |
|---|---|---|
| `विभाजन(s, sep)` | division/split | `s.split(sep)` |
| `संयोग(list, sep)` | union/join | `sep.join(list)` |
| `उच्च(s)` | high/upper | `s.upper()` |
| `निम्न(s)` | low/lower | `s.lower()` |
| `छाँटो(s)` | trim/cut | `s.strip()` |

### 4.5 Dictionary Functions

| Function | Sanskrit Meaning | Equivalent |
|---|---|---|
| `कुंजियाँ(dict)` | keys | `dict.keys()` |
| `मान(dict)` | values | `dict.values()` |

---

## 5. System Bridge — File I/O & OS Access (`src/bridge/system.py`)

The system bridge registers native OS-level functions into the वाक् global scope:

### File Operations

| Function | Sanskrit Meaning | Description |
|---|---|---|
| `पठन(path)` | reading | Read file at path, returns string (UTF-8) |
| `लेखन(path, data)` | writing | Write data to file (mode `'w'` default) |
| `लेखन(path, data, 'a')` | writing (append) | Append data to file |
| `अस्तित्व(path)` | existence | Returns `सत्य` if path exists |
| `मिटाओ(path)` | erase/delete | Delete file at path |

### Directory Operations

| Function | Sanskrit Meaning | Description |
|---|---|---|
| `सूची_निर्देशिका(path)` | list-directory | Returns list of filenames in directory |
| `बनाओ_निर्देशिका(path)` | make-directory | Creates directory (recursive, like `mkdir -p`) |
| `कार्य_निर्देशिका()` | working-directory | Returns current working directory |

### OS & Process

| Function | Sanskrit Meaning | Description |
|---|---|---|
| `मंच()` | platform | Returns OS name (Linux / Windows / Darwin) |
| `प्रणाली_कमांड(cmd)` | system-command | Runs shell command, returns exit code |
| `परिवेश_प्राप्त(key)` | environment-get | Get environment variable |
| `परिवेश_सेट(key, val)` | environment-set | Set environment variable |

**Important**: The system bridge must be explicitly registered. In `run.py` this is done automatically. If using the API directly, call `register_system_bridge(interp.globals)` after creating the interpreter.

---

## 6. Standard Library (stdlib/)

### 6.1 `stdlib/mool.vak` — Foundation (Root)

Core algorithmic functions written in pure वाक्:

- `भाज्यफल(गण)` — factorial (recursive)
- `भाज्यफल_पुनरावर्तक(गण)` — factorial (iterative, faster)
- `सम_है(गण)` — is even
- `विषम_है(गण)` — is odd
- `अभाज्य_है(गण)` — is prime
- `अभाज्य_सूची(सीमा)` — list of primes up to limit
- `महत्तम_समापवर्तक(अ, ब)` — GCD (Euclidean)
- `लघुत्तम_समापवर्त्य(अ, ब)` — LCM
- `चित्रण(list, fn)` — map
- `छानना(list, fn)` — filter
- `संकुचन(list, fn, init)` — reduce/fold
- `समतल(list)` — flatten one level
- `दोहराओ(str, n)` — repeat string n times
- `उलटा_तार(str)` — reverse string
- `पैलिंड्रोम_है(str)` — check palindrome

### 6.2 `stdlib/path.vak` — Path Manipulation

Path utility functions for file system navigation.

### 6.3 `stdlib/file.vak` — File API

Object-oriented file wrapper (`संचिका` class) for structured file access.

### 6.4 `stdlib/json.vak` — Serialization

Basic JSON-like serialization for वाक् dictionaries and lists.

---

## 7. Language Syntax Reference

### Variables & Constants

```vak
चर नाम = "राज"           # variable
चर संख्या = ४२           # Devanagari numerals
स्थिर पाई = ३.१४१५९      # constant (cannot be reassigned)
```

### Functions

```vak
कर्म योगफल(क, ख):
    प्रत्यागच्छ क + ख

कर्म नमस्ते(नाम = "दुनिया"):    # default parameter
    मुद्रय "नमस्ते, " + नाम + "!"
```

### Conditionals

```vak
यदि अंक >= ९०:
    मुद्रय "उत्कृष्ट"
अन्यत् अंक >= ७०:
    मुद्रय "अच्छा"
अन्यथा:
    मुद्रय "प्रयास करें"
```

### Loops

```vak
# while
चर इ = ०
यावत् इ < १०:
    मुद्रय इ
    इ += १

# for-each
प्रत्येक चर व अन्तर्गत [१, २, ३, ४, ५]:
    मुद्रय व * व

# range
प्रत्येक चर इ अन्तर्गत परास(१, ११):
    मुद्रय इ
```

### Classes & Inheritance

```vak
वर्ग पशु:
    कर्म प्रारम्भ(स्वयं, नाम):
        स्वयं.नाम = नाम

    कर्म बोलो(स्वयं):
        मुद्रय स्वयं.नाम, "बोलता है"

वर्ग कुत्ता(पशु):          # inherits from पशु
    कर्म बोलो(स्वयं):       # overrides parent method
        मुद्रय स्वयं.नाम + ": भौं भौं!"

चर क = नव कुत्ता("टॉमी")
क.बोलो()
```

### Error Handling

```vak
प्रयत्न:
    उत्क्षिप "कुछ गलत!"
दोष ग:
    मुद्रय "पकड़ा:", ग
अन्ततः:
    मुद्रय "हमेशा चलता है"
```

### File I/O

```vak
# Write a file
लेखन("data.txt", "वाक् ने लिखा!")

# Read a file
चर सामग्री = पठन("data.txt")
मुद्रय सामग्री

# Check existence
यदि अस्तित्व("data.txt"):
    मुद्रय "फ़ाइल मिली"
```

### Import System

```vak
आयात mool              # imports the full module
आयात भाज्यफल से mool   # imports a specific name
```

### Data Structures

```vak
# List (सूची)
चर फल = ["आम", "केला", "सेब"]
फल.जोड़ो("संतरा")
मुद्रय फल[०]

# Dictionary (शब्दकोश)
चर व्यक्ति = {
    "नाम": "राज",
    "आयु": ३०
}
मुद्रय व्यक्ति["नाम"]
```

---

## 8. Operator Precedence (low to high)

| Level | Operators | Associativity |
|---|---|---|
| 1 | `=` `+=` `-=` `*=` `/=` | right |
| 2 | `अथवा` | left |
| 3 | `और` | left |
| 4 | `न` | right (unary) |
| 5 | `==` `!=` `<` `>` `<=` `>=` `अन्तर्गत` | left |
| 6 | `+` `-` | left |
| 7 | `*` `/` `//` `%` | left |
| 8 | `**` | right |
| 9 | `-` (unary) | right |
| 10 | `()` `.` `[]` | left |

---

## 9. Number System

Both Devanagari and ASCII digits are valid everywhere and are treated identically at execution time:

| Devanagari | ASCII |
|---|---|
| ० | 0 |
| १ | 1 |
| २ | 2 |
| ३ | 3 |
| ४ | 4 |
| ५ | 5 |
| ६ | 6 |
| ७ | 7 |
| ८ | 8 |
| ९ | 9 |

`४२` and `42` are the same token. `३.१४` and `3.14` are the same token.

---

## 10. Running वाक् Programs

```bash
# Run a .vak file
python run.py examples/namaste.vak

# Interactive REPL
python run.py

# Inline code
python run.py -c 'मुद्रय "नमस्ते जगत्!"'

# Run via bytecode VM
python run.py --vm benchmark.vak

# Debug: inspect token stream
python run.py --tokens examples/fibonacci.vak

# Debug: inspect AST
python run.py --ast examples/fibonacci.vak

# Debug: inspect compiled bytecode
python run.py --bytecode benchmark.vak
```

---

## 11. Known Limitations & Reserved Names

The following single-character Sanskrit words are **reserved keywords** and cannot be used as variable names. Use alternatives:

| Reserved | Alternative variable names |
|---|---|
| `न` (NOT keyword) | `गण`, `संख्या`, `मान` |
| `वर्ग` (CLASS keyword) | `श्रेणी`, `वर्गफल` |
| `से` (FROM keyword) | `स्रोत`, `स्थान` |

The VM (`--vm` mode) currently supports built-in function calls only. User-defined function calls, classes, closures, try/catch, and import work only under the tree-walk interpreter (default mode).

---

---

# Part II — संस्कृत-कोडकः (Sanskrit Coder): The Math & Logic Engine

---

## 12. What Is Sanskrit Coder?

संस्कृत-कोडकः is a separate execution engine designed for mathematical calculation, algebraic solving, logical reasoning, and Sanskrit grammar lookup — all accessible through natural Sanskrit command syntax.

Where वाक् is a *programming language* (you write full programs with it), Sanskrit Coder is an *execution engine* (you issue commands and receive direct answers). Think of it as a Sanskrit-native scientific calculator combined with a Nyāya logic processor.

---

## 13. Architecture

```
User Input (Sanskrit or English)
         ↓
  [SanskritEngine]         ← Main dispatcher
         ↓
  [SanskritTranslator]     ← Detects language, translates expressions
         ↓
  ┌──────────────────────────────────┐
  │  [SanskritMathEngine]            │  ← Arithmetic, algebra, formulas
  │  [SanskritLogicEngine]           │  ← Nyāya logic, search
  │  [SanskritGrammar]               │  ← Vibhakti, Lakara lookup
  │  [SanskritNumbers]               │  ← Number ↔ word conversion
  └──────────────────────────────────┘
         ↓
   Result (bilingual output)
```

---

## 14. Components In Detail

### 14.1 SanskritNumbers (`numbers/sanskrit_numbers.py`)

Handles three layers of the Sanskrit number system:

**Devanagari digits** (full bidirectional conversion):  
`०` ↔ `0`, `१` ↔ `1`, … `९` ↔ `9`

**Sanskrit number words** (0–100 and major values):

| Number | Sanskrit word |
|---|---|
| 0 | शून्यम् |
| 1 | एकम् |
| 2 | द्वे |
| 3 | त्रीणि |
| 4 | चत्वारि |
| 5 | पञ्च |
| 6 | षट् |
| 7 | सप्त |
| 8 | अष्टौ |
| 9 | नव |
| 10 | दश |
| 11 | एकादश |
| 12 | द्वादश |
| 15 | पञ्चदश |
| 20 | विंशति |
| 30 | त्रिंशत् |
| 50 | पञ्चाशत् |
| 100 | शतम् |
| 1000 | सहस्रम् |

Methods: `number_to_sanskrit(n)`, `sanskrit_to_number(word)`, `to_devanagari(digits)`, `to_arabic(devanagari)`

### 14.2 SanskritTranslator (`core/translator.py`)

Detects whether input is Sanskrit/Devanagari or English/ASCII, then translates math operator vocabulary:

| Sanskrit term | Mathematical meaning |
|---|---|
| `प्लस` | + |
| `धन` | + |
| `ऋण` | - |
| `गुणनम्` | × |
| `भाजनम्` | ÷ |
| `समम्` | = |
| `शक्तिः` | power/exponent |
| `वर्गमूलम्` | square root |
| `दश` | 10 |
| `पञ्च` | 5 |
| `त्रीणि` | 3 |

Also provides `english_to_sanskrit(text)` for output translation, and `is_sanskrit(text)` detection.

### 14.3 SanskritMathEngine (`math_engine/math_engine.py`)

**Arithmetic**: Evaluates expressions using Python's `eval` after translation. Handles `+`, `-`, `*`, `/`, `**`, `%`, `//`, parentheses.

**Equation solving**: Parses `ax + b = c` form equations and solves for the variable.

**Formula database** (built-in):

| Formula | Sanskrit Name | Description |
|---|---|---|
| `F = ma` | बलम् = द्रव्यमानम् × त्वरणम् | Newton's Second Law |
| `E = mc^2` | शक्तिः = द्रव्यमानम् × प्रकाशवेगः² | Mass-Energy Equivalence |
| `A = πr^2` | वृत्तस्य क्षेत्रफलम् = π × त्रिज्या² | Area of Circle |
| `v = u + at` | वेगः = प्रारम्भिक-वेगः + त्वरणम् × कालः | Kinematic equation |
| `PV = nRT` | दाबः × आयतनम् = मात्रा × गैस-स्थिरांक × तापमानम् | Ideal Gas Law |

**Unit conversion**: Supports length (km, m, cm, mm, ft, in), mass (kg, g, lb), temperature (C, F, K).

### 14.4 SanskritLogicEngine (`logic_engine/logic_engine.py`)

Implements the **Nyāya school** of Indian logic (न्याय दर्शनम्). The Nyāya syllogism has five members (पञ्चावयव):

1. **Pratijñā** (प्रतिज्ञा) — Proposition: *"The hill has fire"*
2. **Hetu** (हेतु) — Reason: *"Because it has smoke"*
3. **Udāharaṇa** (उदाहरण) — Example: *"Where there is smoke, there is fire, as in a kitchen"*
4. **Upanaya** (उपनय) — Application: *"This hill has smoke"*
5. **Nigamana** (निगमन) — Conclusion: *"Therefore this hill has fire"*

The engine can construct, validate, and explain Nyāya syllogisms. It also provides a **knowledge base** for philosophical and scientific topics searchable in both Sanskrit and English.

### 14.5 SanskritGrammar (`grammar/grammar.py`)

Provides lookup for Pāṇinian grammatical categories:

**Vibhakti** (विभक्ति — Cases): All 8 cases with Sanskrit names, meanings, and usage:

| Case | Sanskrit | Meaning/Usage |
|---|---|---|
| 1st | प्रथमा | Subject |
| 2nd | द्वितीया | Object (direct) |
| 3rd | तृतीया | Instrument/agent |
| 4th | चतुर्थी | Indirect object/purpose |
| 5th | पञ्चमी | Source/ablative |
| 6th | षष्ठी | Possession/genitive |
| 7th | सप्तमी | Location/locative |
| 8th | सम्बोधन | Vocative |

**Lakāra** (लकार — Tense/Mood): 10 forms including Laṭ (present), Liṭ (perfect), Luṭ (periphrastic future), Lṛṭ (simple future), Leṭ (subjunctive/Vedic), Loṭ (imperative), Laṅ (imperfect), Liṅ (optative/conditional), Luṅ (aorist), Lṛṅ (conditional).

---

## 15. Commands Reference

### Core Commands

| Sanskrit | English | Usage | Example |
|---|---|---|---|
| `गणय` | `calculate` | Arithmetic expression | `गणय दश प्लस ५` |
| `समाधत्स्व` | `solve` | Solve equation | `समाधत्स्व 3x + 5 = 20` |
| `पश्य` | `show` | Formula lookup | `पश्य F = ma` |
| `अन्वेषय` | `search` | Knowledge search | `अन्वेषय न्याय` |
| `परिवर्तय` | `convert` | Unit conversion | `परिवर्तय 5 km to m` |
| `भाषा` | `language` | Switch language | `भाषा english` |

### Example Interactions

```
>>> गणय दश प्लस ५
15 (पञ्चदश)

>>> गणय १० गुणनम् ५
50 (पञ्चाशत्)

>>> समाधत्स्व 3x + 5 = 20
x = 5

>>> पश्य E = mc^2
सूत्रम् (Formula): E = mc^2
संस्कृतम् (Sanskrit): शक्तिः = द्रव्यमानम् × प्रकाशवेगः²
नाम (Name): Mass-Energy Equivalence

>>> परिवर्तय 5 km to m
5000.0 m

>>> अन्वेषय न्याय
विषयः: न्याय
[Nyāya philosophy definition and explanation]
```

---

## 16. Running Sanskrit Coder

```bash
cd sanskrit-coder

# Interactive CLI
python main.py

# Run test suite (19 tests)
python tests/test_sanskrit_coder.py
```

**Requirements**: `requirements.txt` — Python standard library only (no pip installs needed for core functionality).

---

---

# Part III — Integration & The Full Ecosystem

---

## 17. How the Two Systems Relate

| Dimension | वाक् (Vāk) | संस्कृत-कोडकः |
|---|---|---|
| **Type** | Programming language | Execution engine |
| **Input** | `.vak` source files | Command strings |
| **Output** | Application behavior | Computed answers |
| **Use case** | Build software, automation, algorithms | Math, logic, grammar queries |
| **Complexity** | High — requires understanding syntax | Low — natural language commands |
| **Learning curve** | Like learning Python | Like using a calculator |
| **Foundation** | Pāṇini's grammar as syntax | Nyāya logic as reasoning |

### How They Integrate

वाक् can function as the **host language** for Sanskrit Coder. A वाक् program can:
1. Call `प्रणाली_कमांड` to invoke Sanskrit Coder as a subprocess
2. Use `लेखन`/`पठन` to pass data between them via files
3. Once the Python-level API bridge is written, call Sanskrit Coder functions directly from वाक् code

Planned integration path:
```vak
आयात गणक से sanskrit_coder    # import the calculator module
चर परिणाम = गणक.गणय("दश प्लस पञ्च")
मुद्रय परिणाम    # → 15 (पञ्चदश)
```

---

## 18. Project Structure

```
vak-coder/
├── runtime/                    ← The वाक् programming language
│   ├── run.py                   ← Entry point, REPL, CLI
│   ├── run_tests.py             ← Test runner
│   ├── benchmark.vak            ← Performance benchmark
│   ├── src/
│   │   ├── tokens.py            ← Token types + Sanskrit keyword map
│   │   ├── lexer.py             ← Devanagari-aware tokenizer
│   │   ├── ast_nodes.py         ← Typed AST node definitions
│   │   ├── parser.py            ← Recursive descent parser
│   │   ├── environment.py       ← Lexical scope + closures
│   │   ├── interpreter.py       ← Tree-walk interpreter + 30 built-ins
│   │   ├── errors.py            ← VakError hierarchy
│   │   ├── core/
│   │   │   ├── opcodes.py       ← Bytecode ISA (60+ opcodes)
│   │   │   ├── compiler.py      ← AST → bytecode compiler
│   │   │   └── vm.py            ← Stack-based virtual machine
│   │   └── bridge/
│   │       └── system.py        ← File I/O + OS access bridge
│   ├── stdlib/
│   │   ├── mool.vak             ← Core algorithms in pure वाक्
│   │   ├── path.vak             ← Path utilities
│   │   ├── file.vak             ← OOP file wrapper
│   │   └── json.vak             ← JSON-like serialization
│   ├── spec/
│   │   └── GRAMMAR.md           ← Formal EBNF grammar specification
│   └── examples/
│       ├── namaste.vak          ← Hello World
│       ├── fibonacci.vak        ← Fibonacci (recursive + iterative)
│       ├── varg.vak             ← Classes & OOP
│       ├── data.vak             ← Lists & Dictionaries
│       ├── dosh.vak             ← Error handling
│       └── vyapak.vak           ← Comprehensive feature demo
│
└── sanskrit_coder/              ← The Sanskrit math/logic engine
    ├── main.py                  ← CLI entry point
    ├── core/
    │   ├── engine.py            ← Main dispatcher
    │   └── translator.py        ← Sanskrit ↔ English translation
    ├── numbers/
    │   └── sanskrit_numbers.py  ← Full Sanskrit number system
    ├── grammar/
    │   └── grammar.py           ← Vibhakti + Lakara lookup
    ├── math_engine/
    │   └── math_engine.py       ← Arithmetic, algebra, formulas
    ├── logic_engine/
    │   └── logic_engine.py      ← Nyāya logic engine
    └── tests/
        └── test_sanskrit_coder.py  ← 19 tests, 100% pass rate
```

---

## 19. Verified Test Results

### वाक् Language Tests (manual, all passing)

| Example | Features Tested | Status |
|---|---|---|
| `namaste.vak` | Variables, constants, strings, print | ✅ |
| `fibonacci.vak` | Recursion, iteration, lists | ✅ |
| `varg.vak` | Classes, inheritance, polymorphism | ✅ |
| `data.vak` | Lists, dicts, higher-order functions | ✅ |
| `dosh.vak` | try/catch/finally, custom exceptions | ✅ |
| `vyapak.vak` | All major features combined | ✅ |
| File I/O | `पठन`, `लेखन`, `अस्तित्व`, `मंच` | ✅ |

### Sanskrit Coder Tests (automated, all passing)

| Category | Tests | Status |
|---|---|---|
| Number system | 5/5 | ✅ |
| Translator | 3/3 | ✅ |
| Math engine | 5/5 | ✅ |
| Grammar | 3/3 | ✅ |
| Engine integration | 3/3 | ✅ |
| **Total** | **19/19** | **✅ 100%** |

---

## 20. Roadmap

### वाक् Language

- [ ] Complete VM: user-defined functions, classes, closures in bytecode
- [ ] Standard library growth: HTTP module, JSON parsing, datetime
- [ ] Pattern matching (`रूप_मिलान`)
- [ ] Generator functions (`उत्पादक`)
- [ ] VS Code / Neovim syntax highlighting extension
- [ ] Online REPL / playground
- [ ] Package manager for `.vak` modules

### Sanskrit Coder

- [ ] Expanded formula database (geometry, thermodynamics, quantum)
- [ ] Full Nyāya syllogism construction and validation
- [ ] Sanskrit word problem parsing (arithmetic described in Sanskrit prose)
- [ ] Vedic mathematics algorithms (Sūtras)
- [ ] Integration API for calling from वाक् programs directly

### Ecosystem

- [ ] GitHub / GitLab public repository with proper CITATION.cff
- [ ] Academic paper / preprint documenting the design
- [ ] Web interface (वाक् in the browser via WebAssembly or Pyodide)
- [ ] Devanagari keyboard shortcut layer for Termux

---

## 21. License & Attribution

| Component | License |
|---|---|
| वाक् Runtime & Interpreter | GNU AGPL v3 |
| वाक् Language Specification | Apache License 2.0 |
| Sanskrit Coder Engine | GNU AGPL v3 |
| All documentation | Apache License 2.0 |

**Copyright © 2026 Raj Mitra. All Rights Reserved.**

Raj Mitra is the original inventor, architect, and visionary behind the Sanskrit Computing Ecosystem. This includes the concept of Sanskrit as a computing substrate, the design of the वाक् language, the keyword choices, the integration with Pāṇinian grammar, and the vision of Sanskrit Coder as a Nyāya-logic execution engine.

---

## 22. Installation & Usage (Termux / Android)

```bash
# Clone or unzip the project
unzip vak-coder.zip
cd vak-coder

# Run वाक् REPL
cd vak-lang
python run.py

# Run a .vak file
python run.py examples/namaste.vak

# Run Sanskrit Coder CLI
cd ../sanskrit-coder
python main.py

# Run all Sanskrit Coder tests
python tests/test_sanskrit_coder.py
```

**Python version**: 3.8+ required. Python 3.13 confirmed working (both `.pyc` versions present in repository). No external packages required for either system.

---

*"संस्कृतम् अमरम् भवतु"* — May Sanskrit become immortal.

---

**Document Version**: 1.0  
**Last Updated**: March 8, 2026  
**Author**: Raj Mitra
