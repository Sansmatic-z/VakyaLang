# 📝 Changelog

All notable changes to **VakyaLang (वाक्)** will be documented in this file.

## [2.16.0] - 2026-03-17
### Major Upgrade: Async, Package Management & Macros
- **Pāṇinian Macro System (`सूत्र`):**
  - High-performance, compile-time AST transformation system.
  - Support for parameterized macros with zero runtime overhead.
  - Recursive expansion and integration with the compiler pipeline.
- **Async/Await (`अतुल्यकालिक` / `प्रतीक्षा`):**
  - Native coroutine support in the VM.
  - New `event_loop.py` for cooperative multitasking.
  - Keywords `अतुल्यकालिक` (async) and `प्रतीक्षा` (await) added to the lexer/parser.
- **VakPack Package Manager (`vpm.py`):**
  - Complete CLI for managing project dependencies.
  - `vakya.json` manifest support and `वाक्_ग्रंथालय` local library resolution.
- **VM & Compiler Enhancements:**
  - Added `AWAIT` and `MAKE_COROUTINE` opcodes.
  - Refactored compiler for multi-phase optimization.

## [0.1.0] - 2026-03-08
### Initial Research & Core Release
- **Vāk Language Runtime:**
  - Full Devanagari-aware Lexer and recursive descent Parser.
  - Tree-walk Interpreter with lexical scope and closures.
  - Initial implementation of stack-based Virtual Machine and Bytecode Compiler.
  - Support for Classes (`वर्ग`), OOP, and Error Handling (`दोष`).
  - System bridge for File I/O and OS access.
- **Sanskrit Coder Engine:**
  - Arithmetic and algebraic execution through natural Sanskrit commands.
  - Formula lookup database (Physics, Geometry, Astronomy).
  - Nyāya logic engine (*Pañcāvayava* syllogism).
  - Pāṇinian grammar lookup (*Vibhakti*, *Lakāra*).
- **Documentation & Examples:**
  - Formal EBNF Grammar specification (`GRAMMAR.md`).
  - 10+ example programs demonstrating functional and OOP features.
  - 100% test pass rate for Sanskrit Coder core modules.

---
**Author:** Raj Mitra (Visionary RM) - Visionary RM (Raj Mitra)
