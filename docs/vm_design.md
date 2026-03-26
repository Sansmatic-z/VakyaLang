# ⚙️ VakVM Virtual Machine Design

VakVM is a performance-oriented stack-based virtual machine designed for executing Vāk bytecode.

## 🧱 Bytecode Architecture
Vāk source is compiled into a `CodeObject`, which consists of:
1. **Opcode Stream:** A linear sequence of instructions and operands.
2. **Constants Pool:** A table of all literal values (strings, numbers, booleans) used in the code.

## 📦 Stack-Based Execution
VakVM uses a **Value Stack** for all operations. For example, the expression `५ + ३` is executed as:
1. `PUSH_CONST 5`
2. `PUSH_CONST 3`
3. `ADD` (pops 5 and 3, pushes 8)

## 📋 Instruction Set (Opcodes)
The ISA (Instruction Set Architecture) includes:
- **Variable Ops:** `DEFINE_VAR`, `STORE_VAR`, `LOAD_VAR`
- **Arithmetic Ops:** `ADD`, `SUB`, `MUL`, `DIV`, `IDIV`, `MOD`, `POW`
- **Comparison Ops:** `EQ`, `NEQ`, `LT`, `GT`, `LTE`, `GTE`, `IN`
- **Control Flow:** `JUMP`, `JUMP_IF_FALSE`, `LOOP` (backward jump)
- **Output:** `PRINT`
- **Call System:** `CALL` (for built-in function invocation)

## 🏗️ Registering Variables
Unlike the tree-walk interpreter, which uses string-based environments, the VM is designed to use **offset-based variable access** for maximum performance. This is currently being optimized in the `compiler.py` and `vm.py` implementation.

## 🚧 Current Status
The VM is currently used for **core logic and arithmetic**. Complex features like user-defined functions and classes are in development. For full feature compatibility, the tree-walk interpreter is the default mode.

---
**Architect:** Raj Mitra
