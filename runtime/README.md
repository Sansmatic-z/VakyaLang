# वाक् — Sanskrit Computing Language

> **वाक् वै ब्रह्म** — *"Speech is indeed the universal principle."*  
> — Aitareya Āraṇyaka

**वाक् (Vāk)** is a general-purpose, dynamically-typed, interpreted programming
language written entirely in **Sanskrit Devanagari script**.

Every keyword, built-in function, and language construct is a genuine Sanskrit
word with a precise, intentional meaning — rooted in Pāṇini's grammar
(~500 BCE), the most formally rigorous linguistic system ever constructed.

---

## Vision

Sanskrit was not chosen for nostalgia. It was chosen because:

1. **Pāṇini's Ashtadhyayi** is a formal generative grammar — 3,959 rules that
   derive the entire Sanskrit language from first principles. This is structurally
   isomorphic to a programming language's formal grammar.

2. **Nyāya logic** (the Sanskrit school of reasoning) provides Sanskrit with a
   native logical calculus — predicates, inference rules, and negation — that
   maps directly to boolean and conditional logic in computing.

3. **Sanskrit's root-based morphology** (dhātu + pratyaya) mirrors
   object-oriented composition: a root verb + suffix = derived meaning,
   analogous to class + method = behavior.

वाक् plants this seed: **Sanskrit as a computing substrate, not a curiosity.**

---

## Features

- ✅ Full Devanagari syntax — every keyword is Sanskrit
- ✅ Devanagari numerals (०, १, २, … ९) alongside ASCII digits
- ✅ Variables (`चर`) and constants (`स्थिर`)
- ✅ Functions with closures (`कर्म`)
- ✅ Classes with inheritance (`वर्ग`)
- ✅ If/elif/else (`यदि` / `अन्यत्` / `अन्यथा`)
- ✅ While loops (`यावत्`)
- ✅ For-each loops (`प्रत्येक … अन्तर्गत`)
- ✅ Lists and dictionaries (`सूची`, `शब्दकोश`)
- ✅ Exception handling (`प्रयत्न` / `दोष` / `अन्ततः`)
- ✅ Module import system (`आयात`)
- ✅ 30+ built-in functions in Sanskrit
- ✅ Interactive REPL
- ✅ Python-style significant indentation

---

## Requirements

- Python 3.8+
- No external dependencies — pure standard library

Works on **Termux (Android)**, Linux, macOS, Windows.

---

## Installation

```bash
git clone https://github.com/your-repo/vak-lang
cd vak-lang
```

---

## Usage

### चलाएँ (Run a file)
```bash
python run.py examples/namaste.vak
```

### संवादात्मक REPL (Interactive REPL)
```bash
python run.py
```

### इनलाइन कोड (Inline code)
```bash
python run.py -c 'मुद्रय "नमस्ते जगत्!"'
```

### डीबग सहायक (Debug helpers)
```bash
python run.py --tokens examples/namaste.vak   # print token stream
python run.py --ast    examples/namaste.vak   # print AST
```

---

## Quick Reference

### चर और स्थिर (Variables & Constants)
```vak
चर नाम   = "राज"
चर संख्या = ४२
स्थिर पाई = ३.१४१५९
```

### कर्म (Functions)
```vak
कर्म योगफल(क, ख):
    प्रत्यागच्छ क + ख

मुद्रय योगफल(३, ४)   # → 7
```

### यदि / अन्यत् / अन्यथा (Conditionals)
```vak
यदि अंक >= ९०:
    मुद्रय "उत्कृष्ट"
अन्यत् अंक >= ७०:
    मुद्रय "अच्छा"
अन्यथा:
    मुद्रय "प्रयास करें"
```

### लूप (Loops)
```vak
# while
यावत् इ < १०:
    मुद्रय इ
    इ += १

# for-each
प्रत्येक चर व अन्तर्गत [१, २, ३, ४, ५]:
    मुद्रय व * व
```

### वर्ग (Classes)
```vak
वर्ग पशु:
    कर्म प्रारम्भ(स्वयं, नाम):
        स्वयं.नाम = नाम

    कर्म बोलो(स्वयं):
        मुद्रय स्वयं.नाम, "बोलता है"

वर्ग कुत्ता(पशु):
    कर्म बोलो(स्वयं):
        मुद्रय स्वयं.नाम + ": भौं भौं!"

चर क = नव कुत्ता("टॉमी")
क.बोलो()
```

### दोष संचालन (Error Handling)
```vak
प्रयत्न:
    उत्क्षिप "कुछ गलत!"
दोष ग:
    मुद्रय "पकड़ा:", ग
अन्ततः:
    मुद्रय "यह हमेशा चलता है"
```

---

## Built-in Functions (अन्तर्निर्मित कार्य)

| कार्य              | कार्य                |
|--------------------|----------------------|
| `दीर्घता(x)`       | `len(x)`             |
| `प्रकार(x)`        | `type(x)`            |
| `परास(n)`          | `range(n)`           |
| `योग(l)`           | `sum(l)`             |
| `अधिकतम(...)` | `max(...)`           |
| `न्यूनतम(...)` | `min(...)`           |
| `क्रमबद्ध(l)`     | `sorted(l)`          |
| `वर्गमूल(x)`      | `math.sqrt(x)`       |
| `पाठ_कर(x)`       | `str(x)`             |
| `पूर्णांक_कर(x)`  | `int(x)`             |
| `प्रवेश(prompt)`  | `input(prompt)`      |

---

## Examples

| फ़ाइल               | विवरण                    |
|---------------------|--------------------------|
| `examples/namaste.vak` | Hello World           |
| `examples/fibonacci.vak` | Fibonacci sequence  |
| `examples/varg.vak`    | Classes & OOP         |
| `examples/data.vak`    | Lists & Dictionaries  |
| `examples/dosh.vak`    | Error Handling        |
| `examples/tasks.vak`   | Persistent CLI Task Manager (File I/O) |
| `examples/webgen.vak`  | Static Website Generator (File I/O) |

---

## Project Structure

```
vak-lang/
├── run.py              ← Entry point & REPL
├── src/
│   ├── tokens.py       ← Token types & keyword map
│   ├── lexer.py        ← Devanagari-aware tokenizer
│   ├── ast_nodes.py    ← AST node definitions
│   ├── parser.py       ← Recursive descent parser
│   ├── environment.py  ← Lexical scope / closures
│   └── interpreter.py  ← Tree-walk interpreter
├── spec/
│   └── GRAMMAR.md      ← Formal grammar specification
└── examples/
    ├── namaste.vak
    ├── fibonacci.vak
    ├── varg.vak
    ├── data.vak
    └── dosh.vak
```

---

## Roadmap

- [ ] Standard library modules in `.vak`
- [ ] File I/O operations
- [ ] Pattern matching (`रूप_मिलान`)
- [ ] Generator functions (`उत्पादक`)
- [ ] Async/await (`अनुक्रमिक` / `प्रतीक्षा`)
- [ ] Bytecode compiler for performance
- [ ] VS Code / Neovim syntax highlighting
- [ ] Online playground

---

## License

- **Runtime & Interpreter**: GNU Affero General Public License v3 (AGPL-3.0)
- **Specification**: Apache License 2.0

---

## Author

**Visionary RM (Raj Mitra)**  
Original inventor and creator of the वाक् language.  
© 2026 Raj Mitra. All rights reserved.

---

*"The study of grammar is the door to liberation."*  
— Pāṇini tradition
