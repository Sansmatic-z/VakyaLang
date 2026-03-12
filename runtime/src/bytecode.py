# VakyaLang (????) � Copyright (c) 2026 Raj Mitra. All Rights Reserved.
# Original author: Raj Mitra (Visionary RM)
# Licensed under GNU AGPL v3.0 � see LICENSE and NOTICE.
# Any use, modification, or derivative work must preserve this header
# and include the NOTICE file. https://github.com/Sansmatic-z/VakyaLang

# वाक् भाषा - बाइटकोड प्रतिनिधित्व (Bytecode Representation)
# Vak Language - Bytecode format and utilities

from typing import List, Any, Dict
from .opcodes import OpCode, OPCODE_NAMES

class Bytecode:
    """
    Represents compiled bytecode for a VakyaLang function or module.
    
    Structure:
    - code: List of bytes (opcodes and operands)
    - constants: Constant pool (numbers, strings, etc.)
    - var_names: Mapping of variable names to slot indices
    - name: Function/module name
    """
    
    def __init__(self, name: str = "<module>"):
        self.name = name
        self.code: List[int] = []  # Bytecode instructions
        self.constants: List[Any] = []  # Constant pool
        self.var_names: List[str] = []  # Local variable names
        self.functions: Dict[str, 'Bytecode'] = {}  # Nested functions
        
    def emit(self, opcode: OpCode, *operands: int):
        """Emit an opcode with operands."""
        self.code.append(opcode.value)
        for op in operands:
            self.code.append(op & 0xFF)  # Ensure byte-sized
            
    def emit_16bit(self, opcode: OpCode, operand: int):
        """Emit opcode with 16-bit operand."""
        self.code.append(opcode.value)
        self.code.append((operand >> 8) & 0xFF)  # High byte
        self.code.append(operand & 0xFF)         # Low byte
        
    def add_constant(self, value: Any) -> int:
        """Add constant to pool, return index."""
        try:
            # Reuse existing constant if possible
            return self.constants.index(value)
        except ValueError:
            idx = len(self.constants)
            self.constants.append(value)
            return idx
            
    def get_var_slot(self, name: str) -> int:
        """Get or create variable slot."""
        if name not in self.var_names:
            self.var_names.append(name)
        return self.var_names.index(name)
        
    def get_current_offset(self) -> int:
        """Get current bytecode offset."""
        return len(self.code)
        
    def patch_jump(self, offset: int, target: int):
        """Patch a jump instruction at offset to target."""
        # offset points to the operand byte(s), so the instruction ends at offset + 2
        instruction_end = offset + 2
        jump_dist = target - instruction_end
        self.code[offset] = (jump_dist >> 8) & 0xFF
        self.code[offset + 1] = jump_dist & 0xFF
        
    def disassemble(self) -> str:
        """Create human-readable disassembly."""
        lines = []
        lines.append(f"=== Bytecode: {self.name} ===")
        lines.append(f"Constants: {self.constants}")
        lines.append(f"Variables: {self.var_names}")
        lines.append("")
        
        i = 0
        while i < len(self.code):
            op = self.code[i]
            op_name = OPCODE_NAMES.get(op, f"UNKNOWN({op:02X})")
            
            # Instructions with 16-bit operands
            if op in (OpCode.LOAD_CONST.value, OpCode.JUMP.value, 
                     OpCode.JUMP_IF_TRUE.value, OpCode.JUMP_IF_FALSE.value):
                if i + 2 < len(self.code):
                    operand = (self.code[i+1] << 8) | self.code[i+2]
                    lines.append(f"{i:04d}: {op_name:15} {operand:5}  ; {self._format_const(operand)}")
                    i += 3
                    continue
                    
            # Instructions with 1-byte operand
            if op in (OpCode.LOAD_VAR.value, OpCode.STORE_VAR.value,
                     OpCode.CALL.value, OpCode.CALL_BUILTIN.value,
                     OpCode.BUILD_LIST.value, OpCode.BUILD_DICT.value):
                if i + 1 < len(self.code):
                    operand = self.code[i+1]
                    lines.append(f"{i:04d}: {op_name:15} {operand:5}")
                    i += 2
                    continue
            
            # No operand
            lines.append(f"{i:04d}: {op_name}")
            i += 1
            
        return "\n".join(lines)
        
    def _format_const(self, idx: int) -> str:
        """Format constant for display."""
        if 0 <= idx < len(self.constants):
            val = self.constants[idx]
            if isinstance(val, str):
                return f'"{val}"'
            return repr(val)
        return "?"
        
    def to_bytes(self) -> bytes:
        """Serialize to bytes."""
        # Simple serialization format
        import pickle
        return pickle.dumps({
            'name': self.name,
            'code': bytes(self.code),
            'constants': self.constants,
            'var_names': self.var_names
        })
        
    @classmethod
    def from_bytes(cls, data: bytes) -> 'Bytecode':
        """Deserialize from bytes."""
        import pickle
        obj = pickle.loads(data)
        bc = cls(obj['name'])
        bc.code = list(obj['code'])
        bc.constants = obj['constants']
        bc.var_names = obj['var_names']
        return bc

