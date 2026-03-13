# 📄 VakyaLang Language Specification

The official grammar and syntax specification for VakyaLang (वाक्).

## Formal Grammar
The language uses a recursive descent parser to process a Pāṇinian-inspired grammar. The full EBNF (Extended Backus-Naur Form) specification is available here:

👉 **[Official Grammar Specification](../vak-coder/vak-lang/spec/GRAMMAR.md)**

---

## 🏗️ Language Core Concepts
VakyaLang is built as a dynamically-typed, interpreted language with a performance-oriented stack-based VM.

### 1. Character Set & Numerals
Vāk supports the full Devanagari Unicode block (U+0900–U+097F). Devanagari numerals (०, १, २, ३, ४, ५, ६, ७, ८, ९) are treated as first-class citizens and are interchangeable with ASCII digits.

### 2. Lexical Scoping
Scoping is lexically determined, supporting closures and nested function/class environments.

### 3. Native Sanskrit Keywords
Every keyword is a carefully chosen Sanskrit word that represents its computational role:
- `चर` (cara) for variable declaration (meaning "moving/changing").
- `कर्म` (karma) for functions (meaning "action").
- `वर्ग` (varga) for classes (meaning "category").

---

## 📜 Full Technical Manual
For a comprehensive guide covering both Vāk and the Sanskrit Coder engine, please refer to the primary technical manual:

👉 **[Complete Technical Manual](../SANSKRIT_COMPUTING_COMPLETE_Full.md)**

---

**Specification by Raj Mitra**
