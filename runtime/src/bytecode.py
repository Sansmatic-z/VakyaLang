# वाक् भाषा - बाइटकोड प्रतिनिधित्व (Bytecode Representation)
# Vak Language - Bytecode format and utilities

from enum import Enum
from typing import List, Any, Dict, Optional
from .opcodes import OpCode, OPCODE_NAMES

ABI_FORMAT = "vak_bytecode_abi"
ABI_VERSION = 1


class DefaultSentinel(Enum):
    NO_DEFAULT = "no_default"


NO_DEFAULT = DefaultSentinel.NO_DEFAULT

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
        self.param_names: List[str] = []  # Parameter names (subset of var_names)
        self.functions: Dict[str, 'Bytecode'] = {}  # Nested functions
        self.defaults: List[Any] = []  # Default parameter values
        self.varargs_name: Optional[str] = None # Name of *args param
        self.num_params: int = 0  # Number of fixed parameters
        self.global_names: set = set() # Names marked 'वैश्विक'
        self.nonlocal_names: set = set() # Names marked 'अस्थानिक'
        self.local_names: set = set() # Names bound in the current scope
        self.closure_names: set = set() # Names captured from enclosing scopes
        self.type_hints: Dict[str, str] = {} # Variable/Parameter type annotations
        self.is_async: bool = False  # True if function is async (अतुल्यकालिक)
        self.vibhakti_signature: Any = None  # VibhaktiSignature object if applicable
        self.source_path: Optional[str] = None  # Source file for import resolution
        
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
        for idx, existing in enumerate(self.constants):
            if type(existing) is type(value) and existing == value:
                return idx

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
        # Instruction starts at offset (opcode), followed by 2 bytes of operand
        # Relative jump is calculated from the end of the instruction
        instruction_end = offset + 3
        jump_dist = target - instruction_end
        
        # Store 16-bit signed offset in the two bytes following the opcode
        self.code[offset + 1] = (jump_dist >> 8) & 0xFF
        self.code[offset + 2] = jump_dist & 0xFF
        
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
            if op in (OpCode.LOAD_CONST.value, OpCode.CALL_BUILTIN.value, OpCode.JUMP.value, 
                     OpCode.JUMP_IF_TRUE.value, OpCode.JUMP_IF_FALSE.value):
                if i + 2 < len(self.code):
                    operand = (self.code[i+1] << 8) | self.code[i+2]
                    lines.append(f"{i:04d}: {op_name:15} {operand:5}  ; {self._format_const(operand)}")
                    i += 3
                    continue
                    
            # Instructions with 1-byte operand
            if op in (
                OpCode.LOAD_VAR.value,
                OpCode.STORE_VAR.value,
                OpCode.CALL.value,
                OpCode.CALL_METHOD.value,
                OpCode.CALL_KW.value,
                OpCode.CALL_METHOD_KW.value,
                OpCode.BUILD_LIST.value,
                OpCode.BUILD_DICT.value,
                OpCode.BUILD_SET.value,
                OpCode.BUILD_TUPLE.value,
                OpCode.UNPACK_SEQUENCE.value,
            ):
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
        
    def symbols(self) -> List[str]:
        """Get variable names."""
        return self.var_names
        
    def to_bytes(self) -> bytes:
        """Serialize to bytes."""
        # Simple serialization format
        import pickle
        return pickle.dumps({
            'name': self.name,
            'code': bytes(self.code),
            'constants': self.constants,
            'var_names': self.var_names,
            'param_names': self.param_names,
            'defaults': self.defaults,
            'varargs_name': self.varargs_name,
            'num_params': self.num_params,
            'global_names': self.global_names,
            'nonlocal_names': self.nonlocal_names,
            'local_names': self.local_names,
            'closure_names': self.closure_names,
            'type_hints': self.type_hints,
            'source_path': self.source_path,
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
        bc.param_names = obj.get('param_names', [])
        bc.defaults = obj.get('defaults', [])
        bc.varargs_name = obj.get('varargs_name')
        bc.num_params = obj.get('num_params', 0)
        bc.global_names = obj.get('global_names', set())
        bc.nonlocal_names = obj.get('nonlocal_names', set())
        bc.local_names = obj.get('local_names', set())
        bc.closure_names = obj.get('closure_names', set())
        bc.type_hints = obj.get('type_hints', {})
        bc.source_path = obj.get('source_path')
        return bc

    @classmethod
    def _encode_value(cls, value: Any) -> dict[str, Any]:
        if value is NO_DEFAULT:
            return {'kind': 'no_default'}
        if value is None:
            return {'kind': 'null'}
        if type(value) is bool:
            return {'kind': 'bool', 'value': value}
        if type(value) is int:
            return {'kind': 'int', 'value': value}
        if type(value) is float:
            return {'kind': 'float', 'value': value}
        if isinstance(value, str):
            return {'kind': 'str', 'value': value}
        if isinstance(value, list):
            return {'kind': 'list', 'items': [cls._encode_value(item) for item in value]}
        if isinstance(value, tuple):
            if len(value) >= 2 and value[0] in ('function', 'coroutine'):
                payload = {
                    'kind': 'callable_ref',
                    'callable_kind': value[0],
                    'name': value[1],
                }
                if len(value) >= 4 and type(value[3]) is bool:
                    payload['is_async'] = value[3]
                return payload
            return {'kind': 'tuple', 'items': [cls._encode_value(item) for item in value]}
        if isinstance(value, dict):
            if not all(isinstance(key, str) for key in value):
                raise TypeError("ABI only supports dictionaries with string keys")
            return {
                'kind': 'dict',
                'items': {key: cls._encode_value(item) for key, item in value.items()},
            }
        raise TypeError(f"Unsupported ABI value type: {type(value).__name__}")

    @classmethod
    def _decode_value(cls, payload: dict[str, Any]) -> Any:
        kind = payload.get('kind')
        if kind == 'no_default':
            return NO_DEFAULT
        if kind == 'null':
            return None
        if kind == 'bool':
            return bool(payload['value'])
        if kind == 'int':
            return int(payload['value'])
        if kind == 'float':
            return float(payload['value'])
        if kind == 'str':
            return payload['value']
        if kind == 'list':
            return [cls._decode_value(item) for item in payload.get('items', [])]
        if kind == 'tuple':
            return tuple(cls._decode_value(item) for item in payload.get('items', []))
        if kind == 'dict':
            return {
                key: cls._decode_value(item)
                for key, item in payload.get('items', {}).items()
            }
        if kind == 'callable_ref':
            callable_kind = payload.get('callable_kind', 'function')
            name = payload['name']
            if 'is_async' in payload:
                return (callable_kind, name, {}, bool(payload['is_async']))
            return (callable_kind, name, {})
        raise ValueError(f"Unsupported ABI value kind: {kind}")

    @staticmethod
    def _encode_vibhakti_signature(signature: Any) -> Optional[dict[str, Any]]:
        if signature is None:
            return None
        return {
            'params': [
                {
                    'name': param.name,
                    'vibhakti': param.vibhakti.name,
                    'type_hint': param.type_hint,
                    'default': Bytecode._encode_value(param.default),
                    'line': param.line,
                }
                for param in getattr(signature, 'params', [])
            ],
            'return_vibhakti': (
                signature.return_vibhakti.name
                if getattr(signature, 'return_vibhakti', None) is not None
                else None
            ),
            'strict_mode': bool(getattr(signature, 'strict_mode', True)),
            'allow_omission': bool(getattr(signature, 'allow_omission', False)),
        }

    @staticmethod
    def _decode_vibhakti_signature(payload: Optional[dict[str, Any]]) -> Any:
        if payload is None:
            return None

        from .vibhakti import VibhaktiCase, VibhaktiParam, VibhaktiSignature

        signature = VibhaktiSignature()
        signature.return_vibhakti = (
            VibhaktiCase[payload['return_vibhakti']]
            if payload.get('return_vibhakti')
            else None
        )
        signature.strict_mode = bool(payload.get('strict_mode', True))
        signature.allow_omission = bool(payload.get('allow_omission', False))

        for item in payload.get('params', []):
            signature.add_param(
                VibhaktiParam(
                    name=item['name'],
                    vibhakti=VibhaktiCase[item['vibhakti']],
                    type_hint=item.get('type_hint'),
                    default=Bytecode._decode_value(item.get('default', {'kind': 'null'})),
                    line=int(item.get('line', 0)),
                )
            )

        return signature

    def _to_abi_payload(self) -> dict[str, Any]:
        return {
            'name': self.name,
            'source_path': self.source_path,
            'code': list(self.code),
            'constants': [self._encode_value(value) for value in self.constants],
            'var_names': list(self.var_names),
            'param_names': list(self.param_names),
            'functions': {
                name: bytecode._to_abi_payload()
                for name, bytecode in self.functions.items()
            },
            'defaults': [self._encode_value(value) for value in self.defaults],
            'varargs_name': self.varargs_name,
            'num_params': self.num_params,
            'global_names': sorted(self.global_names),
            'nonlocal_names': sorted(self.nonlocal_names),
            'local_names': sorted(self.local_names),
            'closure_names': sorted(self.closure_names),
            'type_hints': dict(self.type_hints),
            'is_async': self.is_async,
            'vibhakti_signature': self._encode_vibhakti_signature(self.vibhakti_signature),
        }

    def to_abi_dict(self, version: int = ABI_VERSION) -> dict[str, Any]:
        if version != ABI_VERSION:
            raise ValueError(f"Unsupported ABI version: {version}")
        return {
            'format': ABI_FORMAT,
            'version': version,
            'bytecode': self._to_abi_payload(),
        }

    @classmethod
    def _from_abi_payload(cls, payload: dict[str, Any]) -> 'Bytecode':
        bc = cls(payload.get('name', '<module>'))
        bc.source_path = payload.get('source_path')
        bc.code = list(payload.get('code', []))
        bc.constants = [
            cls._decode_value(value)
            for value in payload.get('constants', [])
        ]
        bc.var_names = list(payload.get('var_names', []))
        bc.param_names = list(payload.get('param_names', []))
        bc.functions = {
            name: cls._from_abi_payload(function_payload)
            for name, function_payload in payload.get('functions', {}).items()
        }
        bc.defaults = [
            cls._decode_value(value)
            for value in payload.get('defaults', [])
        ]
        bc.varargs_name = payload.get('varargs_name')
        bc.num_params = int(payload.get('num_params', 0))
        bc.global_names = set(payload.get('global_names', []))
        bc.nonlocal_names = set(payload.get('nonlocal_names', []))
        bc.local_names = set(payload.get('local_names', []))
        bc.closure_names = set(payload.get('closure_names', []))
        bc.type_hints = dict(payload.get('type_hints', {}))
        bc.is_async = bool(payload.get('is_async', False))
        bc.vibhakti_signature = cls._decode_vibhakti_signature(
            payload.get('vibhakti_signature')
        )
        return bc

    @classmethod
    def from_abi_dict(cls, payload: dict[str, Any]) -> 'Bytecode':
        if payload.get('format') == ABI_FORMAT:
            version = int(payload.get('version', ABI_VERSION))
            if version != ABI_VERSION:
                raise ValueError(f"Unsupported ABI version: {version}")
            payload = payload['bytecode']
        return cls._from_abi_payload(payload)

    def to_abi_json(self, *, indent: int = 2) -> str:
        import json

        return json.dumps(
            self.to_abi_dict(),
            ensure_ascii=False,
            indent=indent,
            sort_keys=True,
        )

    @classmethod
    def from_abi_json(cls, payload: str) -> 'Bytecode':
        import json

        return cls.from_abi_dict(json.loads(payload))
