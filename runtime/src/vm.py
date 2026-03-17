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
    closure_env: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.locals is None:
            self.locals = [None] * len(self.bytecode.var_names)
        if self.stack is None:
            self.stack = []
        if self.blocks is None:
            self.blocks = []

class Cell:
    """A container for shared mutable variables (upvalues)."""
    def __init__(self, value=None):
        self.value = value
    def __repr__(self):
        return f"Cell({self.value})"

class VakClass:
    """Represents a custom VakyaLang class."""
    def __init__(self, name: str, methods: dict):
        self.name = name
        self.methods = methods

class VakInstance:
    """Represents an instance of a VakyaLang class."""
    def __init__(self, klass: VakClass):
        self.klass = klass
        self.attrs = {}

class VakModule:
    """Represents an imported VakyaLang module."""
    def __init__(self, name: str, attrs: dict):
        self.name = name
        self.attrs = attrs

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
        import sys
        
        # Get the directory of vm.py, then go up 3 levels to find the unified root
        vm_dir = os.path.dirname(os.path.abspath(__file__))
        unified_root = os.path.abspath(os.path.join(vm_dir, '..', '..'))
        if unified_root not in sys.path:
            sys.path.insert(0, unified_root)
            
        from sansmatic.src.engine import SansmaticEngine, ProofError
        from atmalipi.src.engine import AtmaLipiEngine, AtmaValue
        from runtime.src.errors import VMError
        
        _sansmatic = SansmaticEngine(verbose=True)
        _atmalipi = AtmaLipiEngine()
        
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
            
        def _http_get(url):
            import urllib.request
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'VakyaLang/2.0'})
                with urllib.request.urlopen(req) as response:
                    return response.read().decode('utf-8')
            except Exception as e:
                return f"त्रुटि: {e}"
                
        def _http_post(url, data_dict):
            import urllib.request
            import urllib.parse
            import json
            try:
                if isinstance(data_dict, dict):
                    data = json.dumps(data_dict).encode('utf-8')
                    headers = {'User-Agent': 'VakyaLang/2.0', 'Content-Type': 'application/json'}
                else:
                    data = str(data_dict).encode('utf-8')
                    headers = {'User-Agent': 'VakyaLang/2.0'}
                req = urllib.request.Request(url, data=data, headers=headers)
                with urllib.request.urlopen(req) as response:
                    return response.read().decode('utf-8')
            except Exception as e:
                return f"त्रुटि: {e}"
                
        def _get_time():
            import time
            return time.time()
            
        def _sleep(seconds):
            import time
            time.sleep(float(seconds))
            return None
            
        def _start_thread(func, args_tuple):
            import threading
            def thread_target():
                if callable(func):
                    func(*args_tuple)
                elif isinstance(func, tuple) and func[0] == 'function':
                    # It's a VakyaLang function. Run it in a new VM instance to avoid state corruption.
                    thread_vm = VakVM()
                    # Shallow copy globals so it has access to the same shared state
                    thread_vm.globals = self.globals
                    
                    # Construct a mini bytecode to invoke the function
                    from runtime.src.bytecode import Bytecode
                    from runtime.src.opcodes import OpCode
                    bc = Bytecode("<thread>")
                    
                    # Push func
                    idx = bc.add_constant(func)
                    bc.emit_16bit(OpCode.LOAD_CONST, idx)
                    
                    # Push args
                    for arg in args_tuple:
                        idx = bc.add_constant(arg)
                        bc.emit_16bit(OpCode.LOAD_CONST, idx)
                    
                    # Call
                    bc.emit(OpCode.CALL, len(args_tuple))
                    bc.emit(OpCode.HALT)
                    
                    # Ensure thread VM has access to the same functions
                    if self.frames:
                        bc.functions.update(self.frames[0].bytecode.functions)
                    
                    try:
                        thread_vm.run(bc)
                    except Exception as e:
                        print(f"धागा त्रुटि (Thread Error): {e}")
                        
            t = threading.Thread(target=thread_target)
            t.start()
            return None
            
        def _re_match(pattern, string):
            import re
            try:
                match = re.search(pattern, string)
                if match:
                    return list(match.groups()) if match.groups() else [match.group()]
                return None
            except Exception as e:
                return f"त्रुटि: {e}"
                
        def _re_replace(pattern, repl, string):
            import re
            try:
                return re.sub(pattern, repl, string)
            except Exception as e:
                return f"त्रुटि: {e}"
                
        def _json_encode(obj):
            import json
            try:
                return json.dumps(obj, ensure_ascii=False)
            except Exception as e:
                return f"त्रुटि: {e}"
                
        def _json_decode(s):
            import json
            try:
                return json.loads(s)
            except Exception as e:
                return f"त्रुटि: {e}"
            
        def _atma_wrap(*args):
            if not args: raise VMError("आत्म_मूल्य: मूल्य चाहिए")
            val = args[0]
            bhav = str(args[1]) if len(args) > 1 else None
            avastha = str(args[2]) if len(args) > 2 else None
            note = str(args[3]) if len(args) > 3 else None
            return _atmalipi.wrap(val, bhav, avastha, note)
            
        def _vak_type(obj: Any) -> str:
            t = type(obj)
            if t is int: return "पूर्णांक"
            if t is float: return "दशमलव"
            if t is str: return "तार"
            if t is list: return "सूची"
            if t is dict: return "शब्दकोश"
            if t is bool: return "बूलियन"
            if type(obj).__name__ == 'NoneType': return "शून्य"
            if hasattr(obj, 'klass'): return obj.klass.name
            return str(t)

        return {
            'पाठ_कर': str,
            'str': str,
            'परास': range,
            'range': range,
            'दीर्घता': len,
            'len': len,
            'प्रकार': _vak_type,
            'type': _vak_type,
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
            'वर्गमूल': math.sqrt,
            'जाल_लाओ': _http_get,
            'जाल_भेजो': _http_post,
            'समय': _get_time,
            'निद्रा': _sleep,
            'धागा_शुरू': _start_thread,
            'रेगेक्स_खोज': _re_match,
            'रेगेक्स_बदलो': _re_replace,
            'जेसन_लिखो': _json_encode,
            'जेसन_पढ़ो': _json_decode,
            
            # Sansmatic Builtins
            'परिभाषय': lambda *args: _sansmatic.define(str(args[0]), args[1]),
            'दावा': lambda *args: _sansmatic.assert_fact(str(args[0]), str(args[1]), str(args[2]), str(args[3]) if len(args)>3 else None),
            'नियम': lambda *args: _sansmatic.rule((str(args[0]), str(args[1]), str(args[2])), (str(args[3]), str(args[4]), str(args[5]))),
            'मूल्यांकन': lambda *args: _sansmatic.evaluate(str(args[0]), str(args[1]), str(args[2])),
            'सिद्ध_है': lambda *args: _sansmatic.is_provable(str(args[0]), str(args[1]), str(args[2])),
            
            # AtmaLipi Builtins
            'आत्म_मूल्य': _atma_wrap,
            'भाव_पढ़ो': lambda *args: _atmalipi.read_bhav(str(args[0])),
            'अवस्था_पढ़ो': lambda *args: _atmalipi.read_avastha(str(args[0])),
            'सभी_भाव': lambda *args: [f"{k} → {v}" for k, v in _atmalipi.all_bhav().items()],
            'सभी_अवस्था': lambda *args: [f"{k} → {v}" for k, v in _atmalipi.all_avastha().items()],
            'आत्म_इतिहास': lambda *args: _atmalipi.get_history(),
            'आत्म_है': lambda *args: isinstance(args[0], AtmaValue) if args else False,
            'आत्म_भाव': lambda *args: args[0].bhav or "शून्य" if args and isinstance(args[0], AtmaValue) else "शून्य",
            'आत्म_अवस्था': lambda *args: args[0].avastha or "शून्य" if args and isinstance(args[0], AtmaValue) else "शून्य",
            'आत्म_मूल': lambda *args: args[0].value if args and isinstance(args[0], AtmaValue) else (args[0] if args else None)
        }
        
    def _pop(self) -> Any:
        """Pop a value from the current frame's stack with safety check."""
        if not self.current_frame or not self.current_frame.stack:
            raise VMError("Stack Underflow: Attempted to pop from an empty stack")
        return self.current_frame.stack.pop()

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
        except Exception as e:
            # Catch non-VM errors (Python crashes) and wrap them
            trace = self._format_stack_trace()
            raise VMError(f"Internal VM Crash: {e}\n{trace}")
            
    def _execute(self) -> Any:
        """Main execution loop."""
        frame = self.current_frame
        code = frame.bytecode.code
        constants = frame.bytecode.constants
        
        while frame.pc < len(code):
            op = code[frame.pc]
            
            # --- DEBUG TRACE ---
            # op_name = OPCODE_NAMES.get(op, f"UNKNOWN({op})")
            # print(f"TRACE: pc={frame.pc:04d} op={op_name:15} stack={frame.stack}")
            # -------------------
            
            if op == OpCode.HALT.value:
                break
                
            elif op == OpCode.LOAD_CONST.value:
                # 16-bit operand
                idx = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
                val = constants[idx]
                if isinstance(val, tuple) and len(val) >= 2 and val[0] == 'function':
                    # Create a closure!
                    closure_env = {}
                    for i, n in enumerate(frame.bytecode.var_names):
                        # Ensure outer variable is in a Cell for sharing
                        if not isinstance(frame.locals[i], Cell):
                            frame.locals[i] = Cell(frame.locals[i])
                        closure_env[n] = frame.locals[i]
                    val = ('function', val[1], closure_env)
                frame.stack.append(val)
                frame.pc += 3
                
            elif op == OpCode.LOAD_VAR.value:
                slot = code[frame.pc + 1]
                if slot >= len(frame.locals):
                    raise VMError(f"VM Error: Invalid local variable slot {slot}")
                
                name = frame.bytecode.var_names[slot]
                val = None
                
                # Check globals first if in main frame or marked global
                if len(self.frames) == 1 or name in frame.bytecode.global_names:
                    if name in self.globals:
                        val = self.globals[name]
                
                if val is None:
                    val = frame.locals[slot]
                
                # Unwrap Cell
                if isinstance(val, Cell):
                    val = val.value
                    
                if val is None:
                    # Fallback to globals/builtins
                    if name in self.globals:
                        val = self.globals[name]
                    elif name in self.builtins:
                        val = self.builtins[name]
                
                frame.stack.append(val)
                frame.pc += 2
                
            elif op == OpCode.STORE_VAR.value:
                slot = code[frame.pc + 1]
                if slot >= len(frame.locals):
                    raise VMError(f"VM Error: Invalid local variable slot {slot}")
                
                val = self._pop()
                name = frame.bytecode.var_names[slot]
                
                # If slot already has a Cell, update the Cell's value
                if isinstance(frame.locals[slot], Cell):
                    frame.locals[slot].value = val
                else:
                    # Otherwise update locals normally
                    frame.locals[slot] = val
                
                # If we are in the top-level module frame OR if marked global, store in globals
                if len(self.frames) == 1 or name in frame.bytecode.global_names:
                    self.globals[name] = val
                
                # If this variable is part of a closure environment, update the environment
                # This is a simplified upvalue implementation
                if hasattr(frame, 'closure_env') and frame.closure_env is not None:
                    if name in frame.closure_env:
                        frame.closure_env[name] = val
                
                frame.pc += 2
                
            elif op == OpCode.POP.value:
                self._pop()
                frame.pc += 1
                
            elif op == OpCode.DUP.value:
                frame.stack.append(frame.stack[-1])
                frame.pc += 1
                
            elif op == OpCode.SWAP.value:
                frame.stack[-1], frame.stack[-2] = frame.stack[-2], frame.stack[-1]
                frame.pc += 1
                
            # ── Arithmetic ──────────────────────────────────────────────────────
            elif op == OpCode.ADD.value:
                b = self._pop()
                a = self._pop()
                # Handle string concatenation automatically
                if isinstance(a, str) or isinstance(b, str):
                    frame.stack.append(str(a) + str(b))
                else:
                    frame.stack.append(a + b)
                frame.pc += 1
                
            elif op == OpCode.SUB.value:
                b = self._pop()
                a = self._pop()
                frame.stack.append(a - b)
                frame.pc += 1
                
            elif op == OpCode.MUL.value:
                b = self._pop()
                a = self._pop()
                frame.stack.append(a * b)
                frame.pc += 1
                
            elif op == OpCode.DIV.value:
                b = self._pop()
                a = self._pop()
                frame.stack.append(a / b)
                frame.pc += 1
            elif op == OpCode.IDIV.value:
                b = self._pop()
                a = self._pop()
                frame.stack.append(a // b)
                frame.pc += 1
            elif op == OpCode.MOD.value:
                b = self._pop()
                a = self._pop()
                frame.stack.append(a % b)
                frame.pc += 1
                
            elif op == OpCode.POW.value:
                b = self._pop()
                a = self._pop()
                frame.stack.append(a ** b)
                frame.pc += 1
                
            elif op == OpCode.NEG.value:
                a = self._pop()
                frame.stack.append(-a)
                frame.pc += 1

            # ── Bitwise ─────────────────────────────────────────────────────────
            elif op == OpCode.BAND.value:
                b = self._pop()
                a = self._pop()
                frame.stack.append(a & b)
                frame.pc += 1

            elif op == OpCode.BOR.value:
                b = self._pop()
                a = self._pop()
                frame.stack.append(a | b)
                frame.pc += 1

            elif op == OpCode.BXOR.value:
                b = self._pop()
                a = self._pop()
                frame.stack.append(a ^ b)
                frame.pc += 1

            elif op == OpCode.BNOT.value:
                a = self._pop()
                frame.stack.append(~a)
                frame.pc += 1

            elif op == OpCode.LSHIFT.value:
                b = self._pop()
                a = self._pop()
                frame.stack.append(a << b)
                frame.pc += 1

            elif op == OpCode.RSHIFT.value:
                b = self._pop()
                a = self._pop()
                frame.stack.append(a >> b)
                frame.pc += 1

            # ── Comparison ──────────────────────────────────────────────────────
            elif op == OpCode.EQ.value:
                b = self._pop()
                a = self._pop()
                frame.stack.append(a == b)
                frame.pc += 1
                
            elif op == OpCode.NEQ.value:
                b = self._pop()
                a = self._pop()
                frame.stack.append(a != b)
                frame.pc += 1
                
            elif op == OpCode.LT.value:
                b = self._pop()
                a = self._pop()
                frame.stack.append(a < b)
                frame.pc += 1
                
            elif op == OpCode.GT.value:
                b = self._pop()
                a = self._pop()
                frame.stack.append(a > b)
                frame.pc += 1
                
            elif op == OpCode.LTE.value:
                b = self._pop()
                a = self._pop()
                frame.stack.append(a <= b)
                frame.pc += 1
                
            elif op == OpCode.GTE.value:
                b = self._pop()
                a = self._pop()
                frame.stack.append(a >= b)
                frame.pc += 1
                
            # ── Logical ─────────────────────────────────────────────────────────
            elif op == OpCode.AND.value:
                b = self._pop()
                a = self._pop()
                frame.stack.append(a and b)
                frame.pc += 1
                
            elif op == OpCode.OR.value:
                b = self._pop()
                a = self._pop()
                frame.stack.append(a or b)
                frame.pc += 1
                
            elif op == OpCode.NOT.value:
                a = self._pop()
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
                cond = self._pop()
                if cond:
                    frame.pc += 3 + offset
                else:
                    frame.pc += 3
                    
            elif op == OpCode.JUMP_IF_FALSE.value:
                offset = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
                if offset > 32767: offset -= 65536
                cond = self._pop()
                if not cond:
                    frame.pc += 3 + offset
                else:
                    frame.pc += 3
                    
            # ── Functions ───────────────────────────────────────────────────────
            elif op == OpCode.CALL.value:
                argc = code[frame.pc + 1]
                # Pop arguments
                args = [self._pop() for _ in range(argc)]
                args.reverse()
                # Get function
                func = self._pop()
                
                if isinstance(func, tuple) and func[0] == 'function':
                    func_name = func[1]
                    func_bc = frame.bytecode.functions.get(func_name)
                    if not func_bc:
                        func_bc = self.frames[0].bytecode.functions.get(func_name)
                    if func_bc:
                        # Create new frame
                        new_frame = CallFrame(func_bc)
                        # Set up arguments as locals
                        num_fixed = func_bc.num_params
                        for i in range(min(len(args), num_fixed)):
                            arg_val = args[i]
                            # Sansmatic Runtime Type Checking
                            if i < len(func_bc.var_names):
                                p_name = func_bc.var_names[i]
                                if hasattr(func_bc, 'type_hints') and p_name in func_bc.type_hints:
                                    expected_type = func_bc.type_hints[p_name]
                                    actual_type = self.builtins['प्रकार'](arg_val)
                                    
                                    match = False
                                    if expected_type == actual_type or expected_type == 'कोई_भी':
                                        match = True
                                    elif expected_type == 'संख्या' and actual_type in ('पूर्णांक', 'दशमलव'):
                                        match = True
                                        
                                    if not match:
                                        raise VMError(f"प्रकार त्रुटि (Type Error): '{p_name}' के लिए '{expected_type}' अपेक्षित था, लेकिन '{actual_type}' मिला।")
                                        
                            if i < len(new_frame.locals):
                                new_frame.locals[i] = arg_val
                        
                        # Handle variadic arguments
                        if func_bc.varargs_name:
                            varargs_list = list(args[num_fixed:])
                            # Varargs slot is immediately after the fixed params
                            if num_fixed < len(new_frame.locals):
                                new_frame.locals[num_fixed] = varargs_list
                        
                        # Apply default arguments for missing fixed parameters
                        if hasattr(func_bc, 'defaults'):
                            for i in range(len(args), num_fixed):
                                if i < len(new_frame.locals) and func_bc.defaults[i] is not None:
                                    new_frame.locals[i] = func_bc.defaults[i]
                                
                        # Inject closure variables (these remain necessary)
                        if len(func) == 3:
                            closure_env = func[2]
                            new_frame.closure_env = closure_env
                            for i, name in enumerate(new_frame.bytecode.var_names):
                                if i >= num_fixed and name in closure_env:
                                    # Store the Cell directly
                                    new_frame.locals[i] = closure_env[name]
                                    
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
                elif hasattr(func, 'methods') and hasattr(func, 'name'):
                    # VakyaLang Class instantiation
                    instance = VakInstance(func)
                    frame.pc += 2
                    
                    if 'प्रारम्भ' in func.methods:
                        func_bc = func.methods['प्रारम्भ']
                        new_frame = CallFrame(func_bc, is_constructor=True)
                        if len(new_frame.locals) > 0:
                            new_frame.locals[0] = instance
                            
                        num_fixed = func_bc.num_params
                        for i in range(min(len(args), num_fixed)):
                            if i + 1 < len(new_frame.locals):
                                new_frame.locals[i + 1] = args[i]
                                
                        if func_bc.varargs_name:
                            varargs_list = list(args[num_fixed:])
                            if num_fixed + 1 < len(new_frame.locals):
                                new_frame.locals[num_fixed + 1] = varargs_list
                                    
                        self.frames.append(new_frame)
                        self.current_frame = new_frame
                        frame = new_frame
                        code = frame.bytecode.code
                        constants = frame.bytecode.constants
                        frame.pc = 0
                        continue
                    else:
                        frame.stack.append(instance)
                        continue
                        
                elif callable(func):
                    # Python callable
                    result = func(*args)
                    frame.stack.append(result)
                    frame.pc += 2
                else:
                    raise VMError(f"Not a function: {func}")
                    
            elif op == OpCode.RETURN.value:
                result = self._pop()
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
                class_info = self._pop()
                class_name = class_info[1] if isinstance(class_info, tuple) else class_info
                parent_class = self._pop()
                
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
                args = [self._pop() for _ in range(argc)]
                args.reverse()
                method_name = self._pop()
                obj = self._pop()
                
                if isinstance(obj, VakInstance):
                    if method_name in obj.klass.methods:
                        func_bc = obj.klass.methods[method_name]
                        new_frame = CallFrame(func_bc)
                        # The first argument is 'स्व' (self)
                        if len(new_frame.locals) > 0:
                            new_frame.locals[0] = obj
                            
                        num_fixed = func_bc.num_params
                        for i in range(min(len(args), num_fixed)):
                            if i + 1 < len(new_frame.locals):
                                new_frame.locals[i + 1] = args[i]
                                
                        if func_bc.varargs_name:
                            varargs_list = list(args[num_fixed:])
                            if num_fixed + 1 < len(new_frame.locals):
                                new_frame.locals[num_fixed + 1] = varargs_list
                                    
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
                elif isinstance(obj, VakModule):
                    if method_name in obj.attrs:
                        func = obj.attrs[method_name]
                        # Put the function back on the stack, followed by args, then let CALL handle it
                        # Since we are replacing CALL_METHOD, we can just execute the CALL logic here.
                        # Wait, easier: put func and args on stack, then decrement PC to execute a standard CALL.
                        # Actually, our CALL opcode pops args then func.
                        frame.stack.append(func)
                        for arg in args:
                            frame.stack.append(arg)
                        
                        # We must jump to a CALL opcode. We can just execute the CALL logic inline.
                        if isinstance(func, tuple) and func[0] == 'function':
                            func_name = func[1]
                            # Modules use the main VM's function dictionary which we updated during import
                            func_bc = self.frames[0].bytecode.functions.get(func_name)
                            if func_bc:
                                new_frame = CallFrame(func_bc)
                                num_fixed = func_bc.num_params
                                
                                for i in range(min(len(args), num_fixed)):
                                    if i < len(new_frame.locals):
                                        new_frame.locals[i] = args[i]
                                        
                                if func_bc.varargs_name:
                                    varargs_list = list(args[num_fixed:])
                                    if num_fixed < len(new_frame.locals):
                                        new_frame.locals[num_fixed] = varargs_list
                                        
                                if len(func) == 3:
                                    closure_env = func[2]
                                    new_frame.closure_env = closure_env
                                    for i, name in enumerate(new_frame.bytecode.var_names):
                                        if i >= argc and name in closure_env:
                                            new_frame.locals[i] = closure_env[name]
                                            
                                frame.pc += 2
                                self.frames.append(new_frame)
                                self.current_frame = new_frame
                                frame = new_frame
                                code = frame.bytecode.code
                                constants = frame.bytecode.constants
                                frame.pc = 0
                                continue
                            else:
                                raise VMError(f"Function not found in module: {func_name}")
                        elif hasattr(func, 'methods') and hasattr(func, 'name'):
                            # It's a VakClass in a module. Instantiate it.
                            instance = VakInstance(func)
                            frame.pc += 2
                            
                            if 'प्रारम्भ' in func.methods:
                                func_bc = func.methods['प्रारम्भ']
                                new_frame = CallFrame(func_bc, is_constructor=True)
                                if len(new_frame.locals) > 0:
                                    new_frame.locals[0] = instance
                                    
                                num_fixed = func_bc.num_params
                                for i in range(min(len(args), num_fixed)):
                                    if i + 1 < len(new_frame.locals):
                                        new_frame.locals[i + 1] = args[i]
                                        
                                if func_bc.varargs_name:
                                    varargs_list = list(args[num_fixed:])
                                    if num_fixed + 1 < len(new_frame.locals):
                                        new_frame.locals[num_fixed + 1] = varargs_list
                                            
                                self.frames.append(new_frame)
                                self.current_frame = new_frame
                                frame = new_frame
                                code = frame.bytecode.code
                                constants = frame.bytecode.constants
                                frame.pc = 0
                                continue
                            else:
                                # No constructor, push instance
                                # Wait, the stack has func and args on top because we did:
                                # frame.stack.append(func); for arg in args: frame.stack.append(arg)
                                # But we popped them earlier in CALL_METHOD!
                                # So the stack is clean. We just push the instance.
                                # Actually, I pushed them back earlier!
                                # "frame.stack.append(func); for arg in args: frame.stack.append(arg)"
                                # I need to POP them back out.
                                for _ in range(len(args) + 1):
                                    self._pop()
                                frame.stack.append(instance)
                                continue
                        else:
                            raise VMError(f"Attribute '{method_name}' in module '{obj.name}' is not callable")
                    else:
                        raise VMError(f"Method '{method_name}' not found in module {obj.name}")
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
                elements = [self._pop() for _ in range(count)]
                elements.reverse()
                frame.stack.append(elements)
                frame.pc += 2
                
            elif op == OpCode.BUILD_DICT.value:
                count = code[frame.pc + 1]
                pairs = {}
                for _ in range(count):
                    key = self._pop()
                    val = self._pop()
                    pairs[key] = val
                frame.stack.append(pairs)
                frame.pc += 2

            elif op == OpCode.BUILD_SET.value:
                count = code[frame.pc + 1]
                elements = set()
                for _ in range(count):
                    elements.add(self._pop())
                frame.stack.append(elements)
                frame.pc += 2

            elif op == OpCode.BUILD_STRING.value:
                count = code[frame.pc + 1]
                elements = [str(self._pop()) for _ in range(count)]
                elements.reverse()
                frame.stack.append(''.join(elements))
                frame.pc += 2

            elif op == OpCode.LIST_APPEND.value:
                val = self._pop()
                lst = frame.stack[-2] # stack is [... list, iter]
                lst.append(val)
                frame.pc += 1

            elif op == OpCode.UNPACK_SEQUENCE.value:
                count = code[frame.pc + 1]
                seq = self._pop()
                # Ensure seq is iterable and has correct length
                items = list(seq)
                if len(items) != count:
                    raise VMError(f"UNPACK_SEQUENCE: अपेक्षित {count} मान, मिले {len(items)}")
                # Push in reverse order so first item is popped first by STORE_VAR
                for item in reversed(items):
                    frame.stack.append(item)
                frame.pc += 2

            elif op == OpCode.INDEX_GET.value:
                idx = self._pop()
                obj = self._pop()
                frame.stack.append(obj[idx])
                frame.pc += 1
                
            elif op == OpCode.MAKE_SLICE.value:
                step = self._pop()
                stop = self._pop()
                start = self._pop()
                frame.stack.append(slice(start, stop, step))
                frame.pc += 1
                
            elif op == OpCode.INDEX_SET.value:
                val = self._pop()
                idx = self._pop()
                obj = self._pop()
                obj[idx] = val
                frame.pc += 1
                
            elif op == OpCode.ATTR_GET.value:
                attr_name = constants[(code[frame.pc + 1] << 8) | code[frame.pc + 2]]
                obj = self._pop()
                if isinstance(obj, VakInstance):
                    if attr_name in obj.attrs:
                        frame.stack.append(obj.attrs[attr_name])
                    elif attr_name in obj.klass.methods:
                        # Return bound method equivalent
                        frame.stack.append(('bound_method', obj, attr_name))
                    else:
                        raise VMError(f"Attribute '{attr_name}' not found on {obj.klass.name}")
                elif isinstance(obj, VakModule):
                    if attr_name in obj.attrs:
                        frame.stack.append(obj.attrs[attr_name])
                    else:
                        raise VMError(f"Attribute '{attr_name}' not found in module {obj.name}")
                else:
                    try:
                        frame.stack.append(getattr(obj, attr_name))
                    except AttributeError:
                        raise VMError(f"Object has no attribute '{attr_name}'")
                frame.pc += 3
                
            elif op == OpCode.ATTR_SET.value:
                attr_name = constants[(code[frame.pc + 1] << 8) | code[frame.pc + 2]]
                val = self._pop()
                obj = self._pop()
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
                exception_val = self._pop()
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

            elif op == OpCode.WITH_CLEANUP.value:
                # Pop the context manager object and call its cleanup method
                obj = self._pop()
                if isinstance(obj, VakInstance) and 'बंद_कर' in obj.klass.methods:
                    close_method = obj.klass.methods['बंद_कर']
                    new_frame = CallFrame(close_method)
                    if len(new_frame.locals) > 0:
                        new_frame.locals[0] = obj
                    self.frames.append(new_frame)
                    self.current_frame = new_frame
                    frame = new_frame
                    code = frame.bytecode.code
                    constants = frame.bytecode.constants
                    frame.pc = 0
                    continue
                elif hasattr(obj, '__exit__'):
                    obj.__exit__(None, None, None)
                frame.pc += 1

            elif op == OpCode.IMPORT_NAME.value:
                idx = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
                module_name = constants[idx]
                
                # Check for standard library path
                import os
                import sys
                from runtime.src.lexer import Lexer
                from runtime.src.parser import Parser
                from runtime.src.compiler import Compiler
                
                # Find the module file
                base_dir = os.path.dirname(os.path.abspath(__file__))
                # Correct path: runtime/src/vm.py -> runtime/stdlib/
                stdlib_path = os.path.abspath(os.path.join(base_dir, '..', 'stdlib', f"{module_name}.vak"))
                local_path = os.path.abspath(os.path.join(os.getcwd(), f"{module_name}.vak"))
                
                target_path = None
                if os.path.exists(local_path):
                    target_path = local_path
                elif os.path.exists(stdlib_path):
                    target_path = stdlib_path
                
                if not target_path:
                    raise VMError(f"Module not found: {module_name}")
                
                # Compile and execute the module in isolation
                with open(target_path, 'r', encoding='utf-8') as f:
                    source = f.read()
                    
                lexer = Lexer(source)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                ast = parser.parse()
                compiler = Compiler()
                module_bytecode = compiler.compile(ast)
                
                # Run the module to populate its frame
                module_vm = VakVM()
                # Run without halting the main VM
                try:
                    module_vm.run(module_bytecode)
                except Exception as e:
                    raise VMError(f"Error executing module '{module_name}': {e}")

                # Extract the top-level globals that were defined
                exported_attrs = {}
                module_env = {}
                
                # Check shared globals (V2.2.0+)
                exported_attrs.update(module_vm.globals)
                module_env.update(module_vm.globals)
                
                # Check local slots (for backward compatibility or module-level locals)
                module_frame = module_vm.frames[0] if module_vm.frames else module_vm.current_frame
                if module_frame and hasattr(module_frame, 'locals'):
                    for i, name in enumerate(module_bytecode.var_names):
                        if i < len(module_frame.locals) and module_frame.locals[i] is not None:
                            exported_attrs[name] = module_frame.locals[i]
                            module_env[name] = module_frame.locals[i]

                # Add module functions to the module environment so they can call each other
                for fn_name in module_bytecode.functions.keys():
                    module_env[fn_name] = ('function', fn_name, module_env)

                # Merge module's internal bytecodes into the main VM's function registry
                # This is CRITICAL for classes and methods defined inside modules
                self.frames[0].bytecode.functions.update(module_bytecode.functions)

                # Add module functions to exported attributes
                for fn_name, fn_bc in module_bytecode.functions.items():
                    # Do not overwrite classes that were exported from globals
                    if fn_name not in exported_attrs or not hasattr(exported_attrs[fn_name], 'methods'):
                        func_tuple = ('function', fn_name, module_env)
                        exported_attrs[fn_name] = func_tuple

                mod_obj = VakModule(module_name, exported_attrs)
                frame.stack.append(mod_obj)
                frame.pc += 3
            elif op == OpCode.GET_ITER.value:
                obj = self._pop()
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
                    self._pop() # Remove iterator
                    frame.pc += 3 + offset
                
            # ── I/O ──────────────────────────────────────────────────────────────
            elif op == OpCode.PRINT.value:
                val = self._pop()
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
                    args = [self._pop() for _ in range(argc)]
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
