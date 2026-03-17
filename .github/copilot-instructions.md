# 🕉️ AI Coding Instructions for VakyaLang (वाक्)

This repository contains **VakyaLang (वाक्)**, a Sanskrit-inspired programming language and symbolic logic engine. When assisting with this codebase, follow these foundational principles:

## 🏛️ Architectural Context
- **Runtime (`runtime/`):** A compiler-pipeline-based interpreter and VM.
  - **Lexer:** Must remain Devanagari-aware. Supports ०-९ as first-class digits.
  - **Parser:** Follows a recursive-descent pattern inspired by Pāṇini’s formal rules.
  - **Interpreter:** Tree-walking by default, uses a stack-based VM for optimized bytecode.
- **Sanskrit Coder (`sanskrit_coder/`):** A symbolic engine for math and logic.
  - Uses **Nyāya school logic** (Pañcāvayava syllogism) as its reasoning primitive.
  - Translates natural Sanskrit expressions to Python logic.

## ✍️ Coding Standards & Sanskrit Integrity
- **Authenticity:** All new keywords or built-in functions must be authentic Sanskrit words. Do not use random Devanagari transliterations.
- **Transliteration:** Use IAST (International Alphabet of Sanskrit Transliteration) when documenting keywords in comments.
- **Purity:** Keep the Sanskrit logic distinct from Python implementation details. The Python code is the "substrate," but the user-facing language must be pure Sanskrit.

## 🛠️ Implementation Rules
1. **Never commit `__pycache__` or `.bak` files.** 
2. **Scoping:** The language uses lexical scoping via a chain of `Environment` objects.
3. **Numerals:** Always support both ASCII and Devanagari digits (०-९) in numeric operations.
4. **Attribution:** Always credit **Raj Mitra** as the architect.

## 🧪 Testing
- Always run the unified CLI for testing: `python vak.py test`
- New features must have a corresponding `.vak` example in `examples/`.

*"संस्कृतम् अमरम् भवतु"* — **May Sanskrit Become Immortal.**  
**Architect: Raj Mitra**
