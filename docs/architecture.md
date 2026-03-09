# 🏗️ VakyaLang Architecture

VakyaLang (वाक्) is built as a complete computing ecosystem consisting of two primary pillars:

## 1. वाक् (Vāk): The Programming Language

Vāk implements a classical multi-stage execution pipeline designed for the unique structural requirements of the Sanskrit language.

### Compilation Pipeline
1. **Devanagari Lexer (`lexer.py`):** Tokenizes Devanagari script, handles Devanagari numerals (०-९), and generates Python-style INDENT/DEDENT tokens.
2. **Recursive Descent Parser (`parser.py`):** Converts the token stream into a typed Abstract Syntax Tree (AST), ensuring adherence to the Pāṇinian-inspired grammar.
3. **Interpreter (`interpreter.py`):** A tree-walk executor that provides immediate execution, closures, and object-oriented features.
4. **Bytecode Compiler (`compiler.py`):** Translates AST nodes into a flat instruction set (Opcodes) for the VM.
5. **VakVM (`vm.py`):** A stack-based virtual machine that executes compiled bytecode for higher performance.

### Environment & Scoping
The runtime uses a chain of `Environment` objects to implement lexical scoping. Each block, function, and class body generates a new environment that points to its parent, enabling closures and protected access.

---

## 2. संस्कृत-कोडकः (Sanskrit Coder): The Logic Engine

Sanskrit Coder is a specialized symbolic computation system that processes natural Sanskrit expressions through Indian logical frameworks.

### Core Modules
- **Translator Engine:** Detects and maps Sanskrit mathematical terms to executable Python expressions.
- **Nyāya Logic Engine:** Implements the *Pañcāvayava* (five-member) syllogism, allowing for structured logical proofs and reasoning.
- **Grammar Engine:** Provides programmatic lookup of Sanskrit cases (*Vibhakti*) and tenses (*Lakāra*) based on Pāṇinian rules.
- **Number Engine:** Handles the full bidirectional conversion between Arabic digits, Devanagari digits, and Sanskrit number words.

---

## 3. Integration Bridge

VakyaLang is designed to be extensible. The `System Bridge` provides:
- **File System API:** Native file reading, writing, and directory management.
- **OS Interface:** Platform detection and environment variable management.
- **Cross-Engine Calls:** A path for Vāk programs to invoke the Sanskrit Coder for advanced symbolic calculations.

---

*"संस्कृतं देवभाषा च सर्वविज्ञानवाहिनी"*  
**Architecture designed by Raj Mitra**
