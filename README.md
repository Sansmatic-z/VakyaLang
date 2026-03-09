# 🕉️ VakyaLang (वाक्)

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-orange.svg)](https://opensource.org/licenses/Apache-2.0)
[![Stars](https://img.shields.io/github/stars/Sansmatic-z/VakyaLang)](https://github.com/Sansmatic-z/VakyaLang)

**वाक् वै ब्रह्म** — *"Speech is indeed the universal principle."*

**VakyaLang** is a Sanskrit-inspired symbolic programming language and computing framework that treats Sanskrit not as a historical artifact, but as a rigorous, formal substrate for modern computing.

The system combines:
- **वाक् (Vāk):** A general-purpose, virtual-machine-based programming language with syntax rooted in Pāṇinian grammar.
- **संस्कृत-कोडकः (Sanskrit Coder):** A symbolic reasoning engine and mathematical executor that operates through Nyāya logic and natural Sanskrit expressions.

---

## 🏗️ Architecture

VakyaLang implements a full classical compiler and runtime pipeline:

`Source (.vak) → Lexer → Parser → AST → Compiler → Bytecode → Virtual Machine`

### Key Features
- **Full Devanagari Syntax:** Keywords, operators, and digits in Sanskrit Devanagari.
- **Pāṇinian Logic:** Grammar-driven parsing and structural regularity.
- **Nyāya Syllogism:** Native logical reasoning (*Pañcāvayava*) for symbolic computing.
- **Multi-Level Runtime:** Tree-walk interpreter and a stack-based Virtual Machine.
- **Standard Library:** Core modules for math, file I/O, and string processing.

---

## 📂 Repository Structure

- `vak-lang/`: Core programming language runtime and interpreter.
- `sanskrit-coder/`: Sanskrit-native math, logic, and grammar engine.
- `docs/`: Language specifications, architectural philosophy, and research documentation.
- `examples/`: Example programs (Fibonacci, OOP, Task Managers, etc.).
- `stdlib/`: The standard library written in pure Vāk.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+ (No external dependencies required)

### Run a Program
```bash
# Navigate to the language directory
cd vak-lang

# Run a sample program
python run.py examples/namaste.vak

# Start the interactive REPL
python run.py
```

### Sanskrit Coder CLI
```bash
cd sanskrit-coder
python main.py
```

---

## 🤝 Contributing

We welcome contributions that respect the project's vision of Sanskrit as a computing substrate. Please see `CONTRIBUTING.md` for guidelines on how to participate.

---

## ⚖️ License & Attribution

This project is the original research and architecture of **Raj Mitra**.

- **Runtime & Runtime Source:** GNU Affero General Public License v3.0 (AGPL v3).
- **Language Specification & Docs:** Apache License 2.0.

See the `LICENSE`, `NOTICE`, and `CITATION.cff` files for full details on attribution requirements.

---

*"संस्कृतम् अमरम् भवतु"* — **May Sanskrit Become Immortal.**  
**© 2026 Raj Mitra. All Rights Reserved.**
