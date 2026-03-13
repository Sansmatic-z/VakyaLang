# वाक् भाषा - ओपकोड्स (Bytecode Opcodes)
# Vak Language - Instruction Set Architecture (ISA)

from enum import IntEnum, auto

class OpCode(IntEnum):
    # ── Data Operations ───────────────────────────────────────────────────────
    LOAD_CONST    = auto()  # Push constant from pool onto stack
    LOAD_VAR      = auto()  # Load variable from environment onto stack
    STORE_VAR     = auto()  # Store top of stack into environment
    DEFINE_VAR    = auto()  # Define new variable in environment
    DEFINE_CONST  = auto()  # Define new constant in environment
    POP           = auto()  # Discard top of stack

    # ── Arithmetic & Logic ────────────────────────────────────────────────────
    ADD           = auto()  # a + b
    SUB           = auto()  # a - b
    MUL           = auto()  # a * b
    DIV           = auto()  # a / b
    IDIV          = auto()  # a // b
    MOD           = auto()  # a % b
    POW           = auto()  # a ** b
    NEG           = auto()  # -a
    NOT           = auto()  # !a (न)

    # ── Comparisons ───────────────────────────────────────────────────────────
    EQ            = auto()  # ==
    NEQ           = auto()  # !=
    LT            = auto()  # <
    GT            = auto()  # >
    LTE           = auto()  # <=
    GTE           = auto()  # >=
    IN            = auto()  # अन्तर्गत

    # ── Control Flow ──────────────────────────────────────────────────────────
    JUMP          = auto()  # Unconditional jump
    JUMP_IF_FALSE = auto()  # Jump if top of stack is falsy
    LOOP          = auto()  # Backward jump for loops
    
    # ── Functions & Classes ───────────────────────────────────────────────────
    CALL          = auto()  # Call a function or class (args_count)
    RETURN        = auto()  # Return from function
    MAKE_FUNC     = auto()  # Create a function object from code object
    MAKE_CLASS    = auto()  # Create a class object
    GET_MEMBER    = auto()  # obj.attr
    SET_MEMBER    = auto()  # obj.attr = value
    GET_INDEX     = auto()  # obj[idx]
    SET_INDEX     = auto()  # obj[idx] = value

    # ── Data Structures ───────────────────────────────────────────────────────
    MAKE_LIST     = auto()  # Create list from N stack elements
    MAKE_DICT     = auto()  # Create dictionary from N stack pairs

    # ── Error Handling ────────────────────────────────────────────────────────
    TRY_BEGIN     = auto()  # Start try block (jump to catch)
    TRY_END       = auto()  # End try block
    THROW         = auto()  # Throw exception

    # ── Misc ──────────────────────────────────────────────────────────────────
    PRINT         = auto()  # Built-in print (मुद्रय)
    IMPORT        = auto()  # Import module
    HALT          = auto()  # Stop execution
