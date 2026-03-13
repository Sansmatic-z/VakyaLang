# वाक् भाषा - बाइटकोड अपरेशन कोड (Bytecode Opcodes)
# Vak Language - Instruction Set Architecture

from enum import Enum, auto

class OpCode(Enum):
    """
    Stack-based bytecode instruction set for VakyaLang VM.
    
    Architecture: Stack machine with local variable slots
    - All operations work on an evaluation stack
    - Local variables stored in fixed slots per frame
    - Constants stored in a constant pool
    """
    
    # ── Stack Manipulation ───────────────────────────────────────────────────
    LOAD_CONST = 0x01       # LOAD_CONST idx: Push constant[idx] onto stack
    LOAD_VAR = 0x02         # LOAD_VAR slot: Push local[slot] onto stack  
    STORE_VAR = 0x03        # STORE_VAR slot: Pop stack into local[slot]
    POP = 0x04              # Pop top of stack
    DUP = 0x05              # Duplicate top of stack
    SWAP = 0x06             # Swap top two stack items
    
    # ── Arithmetic ──────────────────────────────────────────────────────────
    ADD = 0x10              # Pop b, pop a, push a + b
    SUB = 0x11              # Pop b, pop a, push a - b
    MUL = 0x12              # Pop b, pop a, push a * b
    DIV = 0x13              # Pop b, pop a, push a / b
    MOD = 0x14              # Pop b, pop a, push a % b
    POW = 0x15              # Pop b, pop a, push a ** b
    NEG = 0x16              # Pop a, push -a
    IDIV = 0x17             # Pop b, pop a, push a // b
    
    # ── Comparison ───────────────────────────────────────────────────────────
    EQ = 0x20               # Pop b, pop a, push a == b
    NEQ = 0x21              # Pop b, pop a, push a != b
    LT = 0x22               # Pop b, pop a, push a < b
    GT = 0x23               # Pop b, pop a, push a > b
    LTE = 0x24              # Pop b, pop a, push a <= b
    GTE = 0x25              # Pop b, pop a, push a >= b
    
    # ── Logical ─────────────────────────────────────────────────────────────
    AND = 0x30              # Pop b, pop a, push a and b
    OR = 0x31               # Pop b, pop a, push a or b
    NOT = 0x32              # Pop a, push not a
    
    # ── Control Flow ─────────────────────────────────────────────────────────
    JUMP = 0x40             # JUMP offset: PC += offset
    JUMP_IF_TRUE = 0x41     # Pop cond, if true: PC += offset
    JUMP_IF_FALSE = 0x42    # Pop cond, if false: PC += offset
    
    # ── Functions & OOP ─────────────────────────────────────────────────────
    CALL = 0x50             # CALL func_idx argc: Call function with argc args
    RETURN = 0x51           # Pop value, return from function
    RETURN_VOID = 0x52      # Return None from function
    BUILD_CLASS = 0x53      # Pop methods/attrs, push Class object
    CALL_METHOD = 0x54      # Pop args, pop method_name, pop obj, call obj.method
    
    # ── Data Structures ─────────────────────────────────────────────────────
    BUILD_LIST = 0x60       # BUILD_LIST count: Pop count items, push list
    BUILD_DICT = 0x61       # BUILD_DICT count: Pop count*2 items, push dict
    INDEX_GET = 0x62        # Pop idx, pop obj, push obj[idx]
    INDEX_SET = 0x63        # Pop val, pop idx, pop obj, obj[idx] = val
    ATTR_GET = 0x64         # Pop obj, push obj.attr (attr in next byte)
    ATTR_SET = 0x65         # Pop val, pop obj, obj.attr = val
    GET_ITER = 0x66         # Pop obj, push iter(obj)
    FOR_ITER = 0x67         # FOR_ITER offset: Peek iter, push next(iter). If exhausted, jump offset.
    
    # ── Exceptions & Imports ────────────────────────────────────────────────
    SETUP_EXCEPT = 0x68     # Push exception handler address
    POP_EXCEPT = 0x69       # Pop exception handler
    THROW = 0x6A            # Pop value, raise it as an exception
    IMPORT_NAME = 0x6B      # Import module
    
    # ── I/O and Builtins ────────────────────────────────────────────────────
    PRINT = 0x70            # Pop value, print it
    CALL_BUILTIN = 0x71     # CALL_BUILTIN idx argc: Call builtin[idx]
    
    # ── Special ─────────────────────────────────────────────────────────────
    HALT = 0xFF             # Stop execution

# Opcode names for disassembly
OPCODE_NAMES = {op.value: op.name for op in OpCode}

# Stack effect of each opcode (net change in stack depth)
STACK_EFFECT = {
    OpCode.LOAD_CONST: 1,
    OpCode.LOAD_VAR: 1,
    OpCode.STORE_VAR: -1,
    OpCode.POP: -1,
    OpCode.DUP: 1,
    OpCode.SWAP: 0,
    
    OpCode.ADD: -1,
    OpCode.SUB: -1,
    OpCode.MUL: -1,
    OpCode.DIV: -1,
    OpCode.MOD: -1,
    OpCode.POW: -1,
    OpCode.NEG: 0,
    OpCode.IDIV: -1,
    
    OpCode.EQ: -1,
    OpCode.NEQ: -1,
    OpCode.LT: -1,
    OpCode.GT: -1,
    OpCode.LTE: -1,
    OpCode.GTE: -1,
    
    OpCode.AND: -1,
    OpCode.OR: -1,
    OpCode.NOT: 0,
    
    OpCode.JUMP: 0,
    OpCode.JUMP_IF_TRUE: -1,
    OpCode.JUMP_IF_FALSE: -1,
    
    OpCode.CALL: -999,  # Variable, depends on argc
    OpCode.RETURN: -1,
    OpCode.RETURN_VOID: 0,
    
    OpCode.BUILD_LIST: -999,  # Variable
    OpCode.BUILD_DICT: -999,  # Variable
    OpCode.INDEX_GET: -1,
    OpCode.INDEX_SET: -3,
    OpCode.ATTR_GET: 0,
    OpCode.ATTR_SET: -2,
    
    OpCode.PRINT: -1,
    OpCode.CALL_BUILTIN: -999,
    
    OpCode.HALT: 0,
}
