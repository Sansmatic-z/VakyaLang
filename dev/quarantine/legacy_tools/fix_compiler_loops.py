import re

def fix():
    with open("runtime/src/compiler.py", "r") as f:
        content = f.read()
    
    # 1. Fix ContinueStmt offset calculation
    # Old: self.bytecode.emit_16bit(OpCode.JUMP, loop_start - self.bytecode.get_current_offset())
    # New: self.bytecode.emit_16bit(OpCode.JUMP, loop_start - (self.bytecode.get_current_offset() + 3))
    
    pattern = r'(def _compile_ContinueStmt\(self, node: ContinueStmt\):.*?self\.bytecode\.emit_16bit\(OpCode\.JUMP, loop_start - )self\.bytecode\.get_current_offset\(\)\)'
    replacement = r'\1(self.bytecode.get_current_offset() + 3))'
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # 2. Fix WhileStmt to support multiple breaks
    # We should add a break_list to the loop_stack
    
    # Actually, the user's project seems to use a simpler approach.
    # I'll just fix the Continue calculation for now as it's the immediate cause of the crash.
    
    with open("runtime/src/compiler.py", "w") as f:
        f.write(content)

if __name__ == "__main__":
    fix()
