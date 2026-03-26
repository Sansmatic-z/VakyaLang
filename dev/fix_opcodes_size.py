import re

def fix_file(path):
    with open(path, "r") as f:
        content = f.read()
    
    # 1. Fix CALL_BUILTIN in _eliminate_dead_code if it exists
    # Move CALL_BUILTIN from op8 to op16 (or just handle it as 3 bytes)
    # Actually, CALL_BUILTIN is 3 bytes but NOT 16-bit operand. It's two 8-bit operands.
    
    # I'll just use a more robust way to define sizes in both files
    
    if "compiler.py" in path:
        # Fix _eliminate_dead_code
        # I'll just rewrite it to use a helper or a clean map
        pass

    if "bytecode.py" in path:
        # Fix disassemble
        pass

    # Actually, I'll just use regex to move CALL_BUILTIN to the correct size group
    content = content.replace("OpCode.CALL_BUILTIN.value,", "") # remove from current
    # Add to the 3-byte group
    content = content.replace("OpCode.LOAD_CONST.value,", "OpCode.LOAD_CONST.value, OpCode.CALL_BUILTIN.value,")
    
    with open(path, "w") as f:
        f.write(content)

fix_file("runtime/src/compiler.py")
fix_file("runtime/src/bytecode.py")
