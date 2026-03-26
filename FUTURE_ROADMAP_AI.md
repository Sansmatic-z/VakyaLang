# VakyaLang Future Roadmap: AI Implementation Instructions

This document provides exact technical specifications for implementing the final three advanced features of the VakyaLang ecosystem (Version 2.16.0+). 

**Target AI:** You are acting as a Senior Systems Architect and Virtual Machine Engineer. Your task is to implement the following features in a stack-based, Python-hosted Virtual Machine without breaking existing functionality.

---

## 1. Real Async/Await (अतुल्यकालिक / प्रतीक्षा)

### Current Architecture
The current `VakVM` executes a linear `while frame.pc < len(code)` loop. Threading is currently implemented via `धागा.vak` which spawns new Python threads and deep-copies the VM. This is not true async concurrency.

### Implementation Strategy (Event Loop & Generators)
To implement native async/await, the VM must support **suspendable frames (Generators/Coroutines)**.

1.  **Lexer/Parser Updates (`tokens.py`, `parser.py`):**
    *   Add tokens: `ASYNC` (`अतुल्यकालिक`), `AWAIT` (`प्रतीक्षा`).
    *   Update `_func_decl` to recognize `अतुल्यकालिक कर्म ...` and flag the `FuncDecl` AST node with `is_async=True`.
    *   Add `AwaitExpr` to `ast_nodes.py` and parse it as a unary operator.
2.  **Compiler Updates (`compiler.py`):**
    *   If a function is async, emit a new opcode `MAKE_COROUTINE` at the start, or flag the `Bytecode` object.
    *   For `AwaitExpr`, emit `GET_AWAITABLE` followed by a `YIELD_FROM` or `AWAIT` opcode.
3.  **VM Updates (`vm.py`):**
    *   Introduce a `VakCoroutine` wrapper class.
    *   When an async function is `CALL`ed, it should *not* immediately execute. Instead, it pushes a `VakCoroutine` object to the stack.
    *   **The `AWAIT` Opcode:** When executed, it must suspend the current `CallFrame`, save its PC and stack, and yield control back to an Event Loop.
    *   **Event Loop (`runtime/src/event_loop.py`):** Build a basic Python `asyncio`-style scheduler that polls a queue of active `VakCoroutine` frames, advancing their VMs until completion.

---

## 2. Package Manager (`वाक्-पैकेज` / VakPack)

### Current Architecture
Imports currently use `_import_stmt` which reads `.vak` files directly from the current directory or `runtime/stdlib/`. There is no central registry, dependency resolution, or versioning.

### Implementation Strategy
Build a CLI-driven package manager that creates a local `node_modules` equivalent (e.g., `वाक्_ग्रंथालय/`).

1.  **Registry Structure:**
    *   Create a simple JSON-based metadata file format (`vakya.json` or `वाक्.json`) containing `नाम` (name), `संस्करण` (version), and `निर्भरताएँ` (dependencies).
2.  **CLI Tool (`vpm.py`):**
    *   Commands: `vpm install <pkg>`, `vpm init`.
    *   It should fetch packages from a remote GitHub repository or a central JSON registry list, download the `.vak` files, and place them in the local `वाक्_ग्रंथालय/` directory.
3.  **VM Import Path Resolution (`vm.py`):**
    *   Update the `IMPORT_NAME` opcode logic. Currently, it searches local files and `stdlib`. 
    *   Add a check for `os.path.join(os.getcwd(), 'वाक्_ग्रंथालय', module_name + '.vak')`.
    *   Ensure namespace collision detection is robust.

---

## 3. Pāṇinian Macro System (पाणिनीय सूत्र)

### Current Architecture
The current parser is a hardcoded recursive-descent parser. The `Sanskrit Coder` uses the Ashtadhyayi database for logic, but it does not allow the user to define custom syntax at compile-time.

### Implementation Strategy
Implement a compile-time AST transformation step (Lisp-style macros) using Pāṇini's concept of *Sūtras* (rules) and *Anuvritti* (context continuation).

1.  **Syntax Definition:**
    *   Allow users to define macros using the `सूत्र` keyword.
    *   Example: `सूत्र स्व_लूप(चर x): अनुवाद -> यावत् x > ०:`
2.  **Compiler Pre-Processor (`compiler.py`):**
    *   Before generating bytecode, run a `MacroExpander` pass over the AST.
    *   If it encounters a node matching a defined `सूत्र` pattern, it replaces that AST node with the expanded `अनुवाद` (translation) AST.
3.  **Integration with Sansmatic:**
    *   Tie the macro expansion into the `SansmaticEngine` so that macros are only expanded if they pass a logical proof (e.g., "Only expand this loop if x is a Number").

---

### ⚠️ Critical Constraints for the AI
*   **Do not break `master_test.py`.** The VM currently has a 100% pass rate.
*   **Maintain the `CallFrame` and `Cell` upvalue architecture.** Do not revert the true closure implementation when building async frames.
*   **No external Python dependencies** outside of the standard library (no `requests`, no `pip install`). Everything must be native to the VakyaLang runtime.

*Author: Visionary RM (Raj Mitra)*
