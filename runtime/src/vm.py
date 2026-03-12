# VakyaLang (????) � Copyright (c) 2026 Raj Mitra. All Rights Reserved.
# Original author: Raj Mitra (Visionary RM)
# Licensed under GNU AGPL v3.0 � see LICENSE and NOTICE.
# Any use, modification, or derivative work must preserve this header
# and include the NOTICE file. https://github.com/Sansmatic-z/VakyaLang

# वाक् भाषा - आभासी यन्त्र (Virtual Machine)
# Vak Language - Stack-based Bytecode VM

from typing import Any, List, Dict, Callable
from dataclasses import dataclass
from .bytecode import Bytecode
from .opcodes import OpCode, OPCODE_NAMES

@dataclass
class CallFrame:
    """Represents a function call frame."""
    bytecode: Bytecode
    pc: int = 0  # Program counter
    locals: List[Any] = None
    stack: List[Any] = None
    blocks: List[int] = None # For try/except exception handler offsets
    is_constructor: bool = False
    
    def __post_init__(self):
        if self.locals is None:
            self.locals = [None] * len(self.bytecode.var_names)
        if self.stack is None:
            self.stack = []
        if self.blocks is None:
            self.blocks = []

class VakClass:
    """Represents a custom VakyaLang class."""
    def __init__(self, name: str, methods: dict):
        self.name = name
        self.methods = methods
        
    def __call__(self, *args):
        return VakInstance(self)

class VakInstance:
    """Represents an instance of a VakyaLang class."""
    def __init__(self, klass: VakClass):
        self.klass = klass
        self.attrs = {}

class VakVM:
    """
    Stack-based Virtual Machine for VakyaLang.
    
    Features:
    - Harvard architecture (separate code/data)
    - Stack-based evaluation
    - Call frames for function calls
    - Constant pool
    - Builtin functions
    """
    
    def __init__(self):
        self.frames: List[CallFrame] = []
        self.globals: Dict[str, Any] = {}
        self.builtins: Dict[str, Callable] = self._init_builtins()
        self.current_frame: CallFrame = None
        
    def _init_builtins(self) -> Dict[str, Callable]:
        """Initialize builtin functions."""
        import os
        import platform
        import math
        
        def _read_file(path):
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
                
        def _write_file(path, content, mode='w'):
            with open(path, mode, encoding='utf-8') as f:
                f.write(str(content))
            return None

        def _make_dir(path):
            os.makedirs(path, exist_ok=True)
            return None
            
        return {
            'पाठ_कर': str,
            'str': str,
            'परास': range,
            'range': range,
            'दीर्घता': len,
            'len': len,
            'प्रकार': type,
            'type': type,
            'संख्या': int,
            'int': int,
            'दशमलव': float,
            'float': float,
            'मुद्रय': print,
            'print': print,
            'पठन': _read_file,
            'लेखन': _write_file,
            'अस्तित्व': os.path.exists,
            'मिटाओ': lambda p: os.remove(p) if os.path.exists(p) else None,
            'सूची_निर्देशिका': os.listdir,
            'बनाओ_निर्देशिका': _make_dir,
            'परिवेश_प्राप्त': os.environ.get,
            'परिवेश_सेट': lambda k, v: os.environ.update({k: str(v)}),
            'प्रणाली_कमांड': os.system,
            'मंच': platform.system,
            'कार्य_निर्देशिका': os.getcwd,
            'संयोग': lambda lst, sep="": sep.join(str(x) for x in lst),
            'विभाजन': lambda s, sep=" ": s.split(sep),
            'छाँटो': lambda s: s.strip(),
            'पूर्णांक_कर': int,
            'क्रमबद्ध': sorted,
            'योग': sum,
            'अधिकतम': max,
            'न्यूनतम': min,
            'कुंजियाँ': lambda d: list(d.keys()) if isinstance(d, dict) else [],
            'मान': lambda d: list(d.values()) if isinstance(d, dict) else [],
            'वर्गमूल': math.sqrt
        }
        
    def run(self, bytecode: Bytecode) -> Any:
        """Execute bytecode and return result."""
        frame = CallFrame(bytecode)
        self.frames = [frame]
        self.current_frame = frame
        
        try:
            return self._execute()
        except VMError as e:
            # Add stack trace
            trace = self._format_stack_trace()
            raise VMError(f"{e}\n{trace}")
            
    def _execute(self) -> Any:
        """Main execution loop."""
        frame = self.current_frame
        code = frame.bytecode.code
        constants = frame.bytecode.constants
        
        while frame.pc < len(code):
            op = code[frame.pc]
            
            # --- DEBUG TRACE ---
            op_name = OPCODE_NAMES.get(op, f"UNKNOWN({op})")
            print(f"TRACE: pc={frame.pc:04d} op={op_name:15} stack={frame.stack}")
            # -------------------
            
            if op == OpCode.HALT.value:
                break
                
            elif op == OpCode.LOAD_CONST.value:
                # 16-bit operand
                idx = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
                val = constants[idx]
                if isinstance(val, tuple) and len(val) >= 2 and val[0] == 'function':
                    # Create a closure!
                    closure_env = {n: frame.locals[i] for i, n in enumerate(frame.bytecode.var_names)}
                    val = ('function', val[1], closure_env)
                frame.stack.append(val)
                frame.pc += 3
                
            elif op == OpCode.LOAD_VAR.value:
                slot = code[frame.pc + 1]
                frame.stack.append(frame.locals[slot])
                frame.pc += 2
                
            elif op == OpCode.STORE_VAR.value:
                slot = code[frame.pc + 1]
                frame.locals[slot] = frame.stack.pop()
                frame.pc += 2
                
            elif op == OpCode.POP.value:
                frame.stack.pop()
                frame.pc += 1
                
            elif op == OpCode.DUP.value:
                frame.stack.append(frame.stack[-1])
                frame.pc += 1
                
            elif op == OpCode.SWAP.value:
                frame.stack[-1], frame.stack[-2] = frame.stack[-2], frame.stack[-1]
                frame.pc += 1
                
            # ── Arithmetic ──────────────────────────────────────────────────────
            elif op == OpCode.ADD.value:
                b = frame.stack.pop()
                a = frame.stack.pop()
                frame.stack.append(a + b)
                frame.pc += 1
                
            elif op == OpCode.SUB.value:
                b = frame.stack.pop()
                a = frame.stack.pop()
                frame.stack.append(a - b)
                frame.pc += 1
                
            elif op == OpCode.MUL.value:
                b = frame.stack.pop()
                a = frame.stack.pop()
                frame.stack.append(a * b)
                frame.pc += 1
                
            elif op == OpCode.DIV.value:
                b = frame.stack.pop()
                a = frame.stack.pop()
                frame.stack.append(a / b)
                frame.pc += 1
                
            elif op == OpCode.MOD.value:
                b = frame.stack.pop()
                a = frame.stack.pop()
                frame.stack.append(a % b)
                frame.pc += 1
                
            elif op == OpCode.POW.value:
                b = frame.stack.pop()
                a = frame.stack.pop()
                frame.stack.append(a ** b)
                frame.pc += 1
                
            elif op == OpCode.NEG.value:
                a = frame.stack.pop()
                frame.stack.append(-a)
                frame.pc += 1
                
            # ── Comparison ──────────────────────────────────────────────────────
            elif op == OpCode.EQ.value:
                b = frame.stack.pop()
                a = frame.stack.pop()
                frame.stack.append(a == b)
                frame.pc += 1
                
            elif op == OpCode.NEQ.value:
                b = frame.stack.pop()
                a = frame.stack.pop()
                frame.stack.append(a != b)
                frame.pc += 1
                
            elif op == OpCode.LT.value:
                b = frame.stack.pop()
                a = frame.stack.pop()
                frame.stack.append(a < b)
                frame.pc += 1
                
            elif op == OpCode.GT.value:
                b = frame.stack.pop()
                a = frame.stack.pop()
                frame.stack.append(a > b)
                frame.pc += 1
                
            elif op == OpCode.LTE.value:
                b = frame.stack.pop()
                a = frame.stack.pop()
                frame.stack.append(a <= b)
                frame.pc += 1
                
            elif op == OpCode.GTE.value:
                b = frame.stack.pop()
                a = frame.stack.pop()
                frame.stack.append(a >= b)
                frame.pc += 1
                
            # ── Logical ─────────────────────────────────────────────────────────
            elif op == OpCode.AND.value:
                b = frame.stack.pop()
                a = frame.stack.pop()
                frame.stack.append(a and b)
                frame.pc += 1
                
            elif op == OpCode.OR.value:
                b = frame.stack.pop()
                a = frame.stack.pop()
                frame.stack.append(a or b)
                frame.pc += 1
                
            elif op == OpCode.NOT.value:
                a = frame.stack.pop()
                frame.stack.append(not a)
                frame.pc += 1
                
            # ── Control Flow ────────────────────────────────────────────────────
            elif op == OpCode.JUMP.value:
                offset = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
                if offset > 32767: offset -= 65536
                frame.pc += 3 + offset
                
            elif op == OpCode.JUMP_IF_TRUE.value:
                offset = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
                if offset > 32767: offset -= 65536
                cond = frame.stack.pop()
                if cond:
                    frame.pc += 3 + offset
                else:
                    frame.pc += 3
                    
            elif op == OpCode.JUMP_IF_FALSE.value:
                offset = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
                if offset > 32767: offset -= 65536
                cond = frame.stack.pop()
                if not cond:
                    frame.pc += 3 + offset
                else:
                    frame.pc += 3
                    
            # ── Functions ───────────────────────────────────────────────────────
            elif op == OpCode.CALL.value:
                argc = code[frame.pc + 1]
                # Pop arguments
                args = [frame.stack.pop() for _ in range(argc)]
                args.reverse()
                # Get function
                func = frame.stack.pop()
                
                if isinstance(func, tuple) and func[0] == 'function':
                    func_name = func[1]
                    func_bc = frame.bytecode.functions.get(func_name)
                    if not func_bc:
                        func_bc = self.frames[0].bytecode.functions.get(func_name)
                    if func_bc:
                        # Create new frame
                        new_frame = CallFrame(func_bc)
                        # Set up arguments as locals
                        for i, arg in enumerate(args):
                            if i < len(new_frame.locals):
                                new_frame.locals[i] = arg
                                
                        # Inject closure variables
                        if len(func) == 3:
                            closure_env = func[2]
                            for i, name in enumerate(new_frame.bytecode.var_names):
                                if i >= argc and name in closure_env:
                                    new_frame.locals[i] = closure_env[name]
                                
                        # Inject globals (simulate global scope)
                        global_frame = self.frames[0]
                        for i, name in enumerate(new_frame.bytecode.var_names):
                            if i >= argc:  # Not an argument
                                if name in global_frame.bytecode.var_names:
                                    g_slot = global_frame.bytecode.var_names.index(name)
                                    new_frame.locals[i] = global_frame.locals[g_slot]
                                    
                        # Advance parent PC before switching context
                        frame.pc += 2
                        self.frames.append(new_frame)
                        self.current_frame = new_frame
                        frame = new_frame
                        code = frame.bytecode.code
                        constants = frame.bytecode.constants
                        frame.pc = 0
                        continue
                    else:
                        raise VMError(f"Function not found: {func_name}")
                elif isinstance(func, tuple) and func[0] == 'bound_method':
                    obj = func[1]
                    method_name = func[2]
                    func_bc = obj.klass.methods.get(method_name)
                    if func_bc:
                        new_frame = CallFrame(func_bc)
                        # The first argument is 'स्व' (self)
                        if len(new_frame.locals) > 0:
                            new_frame.locals[0] = obj
                        for i, arg in enumerate(args):
                            if i + 1 < len(new_frame.locals):
                                new_frame.locals[i + 1] = arg
                        
                        # Inject globals
                        global_frame = self.frames[0]
                        for i, name in enumerate(new_frame.bytecode.var_names):
                            if i >= (argc + 1):  # Skip args and self
                                if name in global_frame.bytecode.var_names:
                                    g_slot = global_frame.bytecode.var_names.index(name)
                                    new_frame.locals[i] = global_frame.locals[g_slot]

                        frame.pc += 2
                        self.frames.append(new_frame)
                        self.current_frame = new_frame
                        frame = new_frame
                        code = frame.bytecode.code
                        constants = frame.bytecode.constants
                        frame.pc = 0
                        continue
                    else:
                        raise VMError(f"Method not found: {method_name}")
                elif isinstance(func, VakClass):
                    # Class instantiation
                    instance = func(*args)
                    frame.pc += 2
                    
                    if 'प्रारम्भ' in func.methods:
                        func_bc = func.methods['प्रारम्भ']
                        new_frame = CallFrame(func_bc, is_constructor=True)
                        if len(new_frame.locals) > 0:
                            new_frame.locals[0] = instance
                        for i, arg in enumerate(args):
                            if i + 1 < len(new_frame.locals):
                                new_frame.locals[i + 1] = arg
                                
                        global_frame = self.frames[0]
                        for i, name in enumerate(new_frame.bytecode.var_names):
                            if i >= (argc + 1):
                                if name in global_frame.bytecode.var_names:
                                    g_slot = global_frame.bytecode.var_names.index(name)
                                    new_frame.locals[i] = global_frame.locals[g_slot]
                                    
                        self.frames.append(new_frame)
                        self.current_frame = new_frame
                        frame = new_frame
                        code = frame.bytecode.code
                        constants = frame.bytecode.constants
                        frame.pc = 0
                        continue
                    else:
                        frame.stack.append(instance)
                        
                elif callable(func):
                    # Python callable
                    result = func(*args)
                    frame.stack.append(result)
                    frame.pc += 2
                else:
                    raise VMError(f"Not a function: {func}")
                    
            elif op == OpCode.RETURN.value:
                result = frame.stack.pop()
                is_ctor = frame.is_constructor
                if is_ctor:
                    result = frame.locals[0] # Return the instance instead
                self.frames.pop()
                if not self.frames:
                    return result
                self.current_frame = self.frames[-1]
                frame = self.current_frame
                frame.stack.append(result)
                code = frame.bytecode.code
                constants = frame.bytecode.constants
                
            elif op == OpCode.RETURN_VOID.value:
                is_ctor = frame.is_constructor
                result = frame.locals[0] if is_ctor else None
                self.frames.pop()
                if not self.frames:
                    return result
                self.current_frame = self.frames[-1]
                frame = self.current_frame
                frame.stack.append(result)
                code = frame.bytecode.code
                constants = frame.bytecode.constants
                
            elif op == OpCode.BUILD_CLASS.value:
                # Top of stack: class_name, then parent_class
                class_info = frame.stack.pop()
                class_name = class_info[1] if isinstance(class_info, tuple) else class_info
                parent_class = frame.stack.pop()
                
                class_bc = frame.bytecode.functions.get(class_name)
                
                # We won't fully execute the class block here, just bind its functions as methods
                methods = {}
                
                # Copy methods from parent if inheritance is used
                if parent_class and isinstance(parent_class, VakClass):
                    methods.update(parent_class.methods)
                    
                if class_bc:
                    for m_name, m_bc in class_bc.functions.items():
                        methods[m_name] = m_bc
                
                vak_class = VakClass(class_name, methods)
                frame.stack.append(vak_class)
                frame.pc += 1

            elif op == OpCode.CALL_METHOD.value:
                # Format: CALL_METHOD argc
                argc = code[frame.pc + 1]
                args = [frame.stack.pop() for _ in range(argc)]
                args.reverse()
                method_name = frame.stack.pop()
                obj = frame.stack.pop()
                
                if isinstance(obj, VakInstance):
                    if method_name in obj.klass.methods:
                        func_bc = obj.klass.methods[method_name]
                        new_frame = CallFrame(func_bc)
                        # The first argument is 'स्व' (self)
                        if len(new_frame.locals) > 0:
                            new_frame.locals[0] = obj
                        for i, arg in enumerate(args):
                            if i + 1 < len(new_frame.locals):
                                new_frame.locals[i + 1] = arg
                                
                        global_frame = self.frames[0]
                        for i, name in enumerate(new_frame.bytecode.var_names):
                            if i >= (argc + 1):  # Skip args and self
                                if name in global_frame.bytecode.var_names:
                                    g_slot = global_frame.bytecode.var_names.index(name)
                                    new_frame.locals[i] = global_frame.locals[g_slot]
                                    
                        frame.pc += 2
                        self.frames.append(new_frame)
                        self.current_frame = new_frame
                        frame = new_frame
                        code = frame.bytecode.code
                        constants = frame.bytecode.constants
                        frame.pc = 0
                        continue
                    else:
                        raise VMError(f"Method '{method_name}' not found on {obj.klass.name}")
                else:
                    # Map Sanskrit method names to Python builtins
                    method_map = {
                        'जोड़ो': 'append',
                        'निकालो': 'pop',
                        'विस्तार': 'extend',
                        'अनुक्रमणिका': 'index',
                        'गणना': 'count',
                        'स्वच्छ': 'clear',
                        'क्रमबद्ध': 'sort',
                        'विपरीत': 'reverse',
                    }
                    actual_method_name = method_map.get(method_name, method_name)
                    
                    if hasattr(obj, actual_method_name):
                        func = getattr(obj, actual_method_name)
                        result = func(*args)
                        frame.stack.append(result)
                        frame.pc += 2
                    else:
                        raise VMError(f"Object {type(obj).__name__} has no method {method_name}")

            # ── Data Structures ─────────────────────────────────────────────────
            elif op == OpCode.BUILD_LIST.value:
                count = code[frame.pc + 1]
                elements = [frame.stack.pop() for _ in range(count)]
                elements.reverse()
                frame.stack.append(elements)
                frame.pc += 2
                
            elif op == OpCode.BUILD_DICT.value:
                count = code[frame.pc + 1]
                pairs = {}
                for _ in range(count):
                    key = frame.stack.pop()
                    val = frame.stack.pop()
                    pairs[key] = val
                frame.stack.append(pairs)
                frame.pc += 2
                
            elif op == OpCode.INDEX_GET.value:
                idx = frame.stack.pop()
                obj = frame.stack.pop()
                frame.stack.append(obj[idx])
                frame.pc += 1
                
            elif op == OpCode.INDEX_SET.value:
                val = frame.stack.pop()
                idx = frame.stack.pop()
                obj = frame.stack.pop()
                obj[idx] = val
                frame.pc += 1
                
            elif op == OpCode.ATTR_GET.value:
                attr_name = constants[(code[frame.pc + 1] << 8) | code[frame.pc + 2]]
                obj = frame.stack.pop()
                if isinstance(obj, VakInstance):
                    if attr_name in obj.attrs:
                        frame.stack.append(obj.attrs[attr_name])
                    elif attr_name in obj.klass.methods:
                        # Return bound method equivalent
                        frame.stack.append(('bound_method', obj, attr_name))
                    else:
                        raise VMError(f"Attribute '{attr_name}' not found on {obj.klass.name}")
                else:
                    try:
                        frame.stack.append(getattr(obj, attr_name))
                    except AttributeError:
                        raise VMError(f"Object has no attribute '{attr_name}'")
                frame.pc += 3
                
            elif op == OpCode.ATTR_SET.value:
                attr_name = constants[(code[frame.pc + 1] << 8) | code[frame.pc + 2]]
                val = frame.stack.pop()
                obj = frame.stack.pop()
                if isinstance(obj, VakInstance):
                    obj.attrs[attr_name] = val
                else:
                    try:
                        setattr(obj, attr_name, val)
                    except AttributeError:
                        raise VMError(f"Cannot set attribute '{attr_name}' on object")
                frame.pc += 3

            # ── Exceptions & Imports ────────────────────────────────────────────────
            elif op == OpCode.SETUP_EXCEPT.value:
                offset = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
                frame.blocks.append(frame.pc + 3 + offset)
                frame.pc += 3
                
            elif op == OpCode.POP_EXCEPT.value:
                if frame.blocks:
                    frame.blocks.pop()
                frame.pc += 1
                
            elif op == OpCode.THROW.value:
                exception_val = frame.stack.pop()
                # Unwind stack to find nearest exception block
                handled = False
                while self.frames:
                    current = self.frames[-1]
                    if current.blocks:
                        catch_pc = current.blocks.pop()
                        current.pc = catch_pc
                        current.stack.append(exception_val)
                        self.current_frame = current
                        frame = current
                        code = frame.bytecode.code
                        constants = frame.bytecode.constants
                        handled = True
                        break
                    else:
                        self.frames.pop()
                if not handled:
                    raise VMError(f"Unhandled exception: {exception_val}")
                    
            elif op == OpCode.IMPORT_NAME.value:
                idx = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
                module_name = constants[idx]
                # Dummy import for now, returning string name.
                # A real import would load file, compile to bytecode, and execute it
                frame.stack.append(f"<module {module_name}>")
                frame.pc += 3

            elif op == OpCode.GET_ITER.value:
                obj = frame.stack.pop()
                frame.stack.append(iter(obj))
                frame.pc += 1
                
            elif op == OpCode.FOR_ITER.value:
                offset = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
                it = frame.stack[-1] # Peek the iterator
                try:
                    val = next(it)
                    frame.stack.append(val)
                    frame.pc += 3
                except StopIteration:
                    frame.stack.pop() # Remove iterator
                    frame.pc += 3 + offset
                
            # ── I/O ──────────────────────────────────────────────────────────────
            elif op == OpCode.PRINT.value:
                val = frame.stack.pop()
                print(val, end='')
                frame.pc += 1
                
            elif op == OpCode.CALL_BUILTIN.value:
                idx = code[frame.pc + 1]
                argc = code[frame.pc + 2]
                
                # Get builtin name by index
                builtins_list = list(self.builtins.keys())
                if idx < len(builtins_list):
                    name = builtins_list[idx]
                    func = self.builtins[name]
                    args = [frame.stack.pop() for _ in range(argc)]
                    args.reverse()
                    result = func(*args)
                    frame.stack.append(result)
                else:
                    raise VMError(f"Unknown builtin: {idx}")
                frame.pc += 3
                
            else:
                raise VMError(f"Unknown opcode: {op:02X} at PC {frame.pc}")
                
        # End of execution
        if frame.stack:
            return frame.stack[-1]
        return None
        
    def _format_stack_trace(self) -> str:
        """Format call stack for error reporting."""
        lines = ["Stack trace:"]
        for i, frame in enumerate(reversed(self.frames)):
            name = frame.bytecode.name
            pc = frame.pc
            lines.append(f"  {i}: {name} (PC={pc})")
        return "\n".join(lines)

class VMError(Exception):
    pass

