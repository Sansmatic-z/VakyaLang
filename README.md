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

- `runtime/`: Core programming language runtime and interpreter (`src/`) and standard library (`stdlib/`).
- `sanskrit_coder/`: Sanskrit-native math, logic, and grammar engine.
- `docs/`: Language specifications, architectural philosophy, and research documentation.
- `examples/`: Example programs (Fibonacci, OOP, Task Managers, etc.).
- `tests/`: Unified test suite.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+ (No external dependencies required)

### Installation
```bash
git clone https://github.com/Sansmatic-z/VakyaLang.git
cd VakyaLang
pip install -e .
```

### Run a Program
Once installed, you can use the `vak` command from anywhere:
```bash
# Run a sample program
vak examples/namaste.vak

# Start the interactive REPL
vak repl
```

### Sanskrit Coder CLI
```bash
# Start the symbolic engine
sanskrit-coder
```

For more detailed technical documentation, see the [Complete Technical Manual](SANSKRIT_COMPUTING_COMPLETE_Full.md) and the `docs/` folder.

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
