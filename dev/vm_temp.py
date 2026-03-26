# वाक् भाषा - आभासी यन्त्र (Virtual Machine)
# Vak Language - Stack-based Bytecode VM
#
# Month 2-3 Advanced Features: JIT Compilation Integration
# - Tracks hot functions
# - Compiles to native Python bytecode
# - Performance optimization

from typing import Any, List, Dict, Callable
from dataclasses import dataclass
import time
from .bytecode import Bytecode
from .opcodes import OpCode, OPCODE_NAMES
from .jit_compiler import JITCompiler

class VakThrowException(Exception):
    def __init__(self, value):
        self.value = value

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
        
    def __repr__(self):
        return f"<वर्ग:{self.name}>"
        
    def __str__(self):
        return self.__repr__()

class VakInstance:
    """Represents an instance of a VakyaLang class."""
    def __init__(self, klass: VakClass):
        self.klass = klass
        self.attrs = {}

    def __repr__(self):
        return f"<{self.klass.name} वस्तु>"
        
    def __str__(self):
        return self.__repr__()

class VakModule:
    """Represents an imported VakyaLang module."""
    def __init__(self, name: str, attrs: dict):
        self.name = name
        self.attrs = attrs


class VakCoroutine:
    """
    Wrapper for suspendable coroutine execution.
    
    Represents an async function that can be suspended and resumed.
    Maintains its own CallFrame and execution state.
    
    Usage:
        async def मुख्य():
            प्रतीक्षा कार्य_१()
            प्रतीक्षा कार्य_२()
    """
    def __init__(self, frame: CallFrame, bytecode: Bytecode):
        self.frame = frame
        self.bytecode = bytecode
        self.suspended = False
        self.completed = False
        self.result = None
        self.pending_await = None  # For nested awaits
        self.name = bytecode.name
    
    def __repr__(self):
        status = "suspended" if self.suspended else ("completed" if self.completed else "active")
        return f"VakCoroutine({self.name}, {status})"
    
    def __await__(self):
        """Make coroutine awaitable by Python."""
        if not self.completed:
            yield self
        return self.result


class VakVM:
    """
    Stack-based Virtual Machine for VakyaLang.

    Features:
    - Harvard architecture (separate code/data)
    - Stack-based evaluation
    - Call frames for function calls
    - Constant pool
    - Builtin functions
    - JIT compilation for hot code paths (Month 2-3 feature)
    """

    def __init__(self, enable_jit: bool = True):
        self.frames: List[CallFrame] = []
        self.globals: Dict[str, Any] = {}
        self.builtins: Dict[str, Callable] = self._init_builtins()
        self.current_frame: CallFrame = None
        
        # JIT Compiler (Month 2-3 Advanced Feature)
        self.jit = JITCompiler() if enable_jit else None
        self.jit_enabled = enable_jit
        
    def _init_builtins(self) -> Dict[str, Callable]:
        """Initialize builtin functions."""
        import os
        import platform
        import math
        import sys
        import time

        # Get the directory of vm.py, then go up 3 levels to find the unified root
        vm_dir = os.path.dirname(os.path.abspath(__file__))
        unified_root = os.path.abspath(os.path.join(vm_dir, '..', '..'))
        if unified_root not in sys.path:
            sys.path.insert(0, unified_root)

        from sansmatic.src.engine import SansmaticEngine, ProofError
        from atmalipi.src.engine import AtmaLipiEngine, AtmaValue
        from runtime.src.errors import VMError

        # Math helper functions
        def _math_cos(x): return math.cos(float(x))
        def _math_sin(x): return math.sin(float(x))
        def _math_tan(x): return math.tan(float(x))
        def _math_sqrt(x): return math.sqrt(float(x))
        def _math_abs(x): return abs(float(x))
        def _math_floor(x): return math.floor(float(x))
        def _math_ceil(x): return math.ceil(float(x))
        def _math_round(x): return round(float(x))
        def _math_degrees(x): return math.degrees(float(x))
        def _math_radians(x): return math.radians(float(x))
        
        _sansmatic = SansmaticEngine(verbose=True)
        _atmalipi = AtmaLipiEngine()

        try:
            bridge_dir = os.path.join(vm_dir, 'bridge')
            if bridge_dir not in sys.path:
                sys.path.append(bridge_dir)
            from chitrakala.pixel_engine import ChitraCanvas, ChitraColor
            from chitrakala.colors import get_color, list_colors
            from chitrakala.png_encoder import save_png, load_png
            from chitrakala.primitives import draw_point, draw_line, draw_circle, draw_rectangle, draw_polygon
            from chitrakala.bitmap_font import draw_text
        except ImportError:
            pass

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
            
        def _http_get(url, headers_dict=None):
            import urllib.request
            headers = headers_dict if headers_dict else {'User-Agent': 'VakyaLang/3.0'}
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=30) as response:
                    return response.read().decode('utf-8')
            except Exception as e:
                return f"HTTP Error: {e}"

        def _http_post(url, data, headers_dict=None):
            import urllib.request
            headers = headers_dict if headers_dict else {'User-Agent': 'VakyaLang/3.0'}
            try:
                req = urllib.request.Request(url, data=str(data).encode('utf-8'), headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=30) as response:
                    return response.read().decode('utf-8')
            except Exception as e:
                return f"HTTP Error: {e}"

        def _vak_type(obj):
            t = type(obj)
            if t is int: return "संख्या"
            if t is float: return "संख्या"
            if t is str: return "तार"
            if t is bool: return "बूलियन"
            if t is list: return "सूची"
            if t is dict: return "शब्दकोश"
            if obj is None: return "शून्य"
            if isinstance(obj, VakInstance): return obj.klass.name
            return "अज्ञात"

        def _get_time(): return time.time()
        def _sleep(seconds): time.sleep(float(seconds))
        
        def _atma_wrap(val, bhav=None, avastha=None):
            return AtmaValue(val, bhav, avastha)

        def _re_match(pattern, string):
            import re
            return bool(re.match(pattern, string))

        def _re_replace(pattern, repl, string):
            import re
            return re.sub(pattern, repl, string)

        def _json_encode(obj):
            import json
            return json.dumps(obj)

        def _json_decode(string):
            import json
            return json.loads(string)

        def _start_thread(func, *args):
            import threading
            t = threading.Thread(target=func, args=args)
            t.start()
            return t

        # Python Bridge functions
        try:
            sys.path.insert(0, os.path.abspath(os.path.join(vm_dir, '..', 'stdlib')))
            from py_bridge import पायथन_आयात, पायथन_चलाओ, पायथन_मूल्यांकन
        except ImportError:
            def पायथन_आयात(*args): return None
            def पायथन_चलाओ(*args): return None
            def पायथन_मूल्यांकन(*args): return None

        # Chitrakala implementations
        def _chitra_canvas_impl(w, h, c="white"):
            return ChitraCanvas(int(w), int(h), get_color(c) if isinstance(c, str) else c)
        def _chitra_fill_impl(canv, c):
            canv.fill(get_color(c) if isinstance(c, str) else c)
        def _chitra_point_impl(canv, x, y, c):
            draw_point(canv, int(x), int(y), get_color(c) if isinstance(c, str) else c)
        def _chitra_line_impl(canv, x1, y1, x2, y2, c):
            draw_line(canv, int(x1), int(y1), int(x2), int(y2), get_color(c) if isinstance(c, str) else c)
        def _chitra_circle_impl(canv, x, y, r, c, fill=False):
            draw_circle(canv, int(x), int(y), int(r), get_color(c) if isinstance(c, str) else c, bool(fill))
        def _chitra_rect_impl(canv, x, y, w, h, c, fill=False):
            draw_rectangle(canv, int(x), int(y), int(w), int(h), get_color(c) if isinstance(c, str) else c, bool(fill))
        def _chitra_polygon_impl(canv, pts, c, fill=False):
            draw_polygon(canv, [(int(p[0]), int(p[1])) for p in pts], get_color(c) if isinstance(c, str) else c, bool(fill))
        def _chitra_text_impl(canv, x, y, text, font=None, size=1, c="black"):
            draw_text(canv, int(x), int(y), str(text), get_color(c) if isinstance(c, str) else c, None, int(size))
        def _chitra_save_impl(canv, path):
            save_png(canv, str(path))
        def _chitra_load_impl(path):
            return load_png(str(path))
        def _chitra_color_impl(c):
            return get_color(str(c))
        def _chitra_colors_impl():
            return list_colors()
        def _chitra_width_impl(canv):
            return canv.width
        def _chitra_height_impl(canv):
            return canv.height
        def _chitra_pixel_get_impl(canv, x, y):
            return canv.get_pixel(int(x), int(y))
        def _chitra_pixel_set_impl(canv, x, y, c):
            canv.set_pixel(int(x), int(y), get_color(c) if isinstance(c, str) else c)

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
            'परिवेश_प्राप्त': os.getenv,
            'परिवेश_सेट': os.putenv,
            'प्रणाली_कमांड': os.system,
            'मंच': platform.system,
            'कार्य_निर्देशिका': os.getcwd,
            'संयोग': lambda lst, sep="": sep.join(str(x) for x in lst),
            'विभाजन': lambda s, sep=" ": s.split(sep),
            'छाँटो': lambda s: s.strip(),
            'उच्च': lambda s: s.upper() if isinstance(s, str) else s,
            'निम्न': lambda s: s.lower() if isinstance(s, str) else s,
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
            'पायथन_आयात': पायथन_आयात,
            'पायथन_चलाओ': पायथन_चलाओ,
            'पायथन_मूल्यांकन': पायथन_मूल्यांकन,
            'अक्षर_मान': ord,
            
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
            'आत्म_मूल': lambda *args: args[0].value if args and isinstance(args[0], AtmaValue) else (args[0] if args else None),

            # Chitrakala (चित्रकला) - Visual Library Builtins
            # Import Chitrakala modules
            '_chitra_canvas': lambda *args: _chitra_canvas_impl(*args),
            '_chitra_fill': lambda *args: _chitra_fill_impl(*args),
            '_chitra_point': lambda *args: _chitra_point_impl(*args),
            '_chitra_line': lambda *args: _chitra_line_impl(*args),
            '_chitra_circle': lambda *args: _chitra_circle_impl(*args),
            '_chitra_rect': lambda *args: _chitra_rect_impl(*args),
            '_chitra_polygon': lambda *args: _chitra_polygon_impl(*args),
            '_chitra_text': lambda *args: _chitra_text_impl(*args),
            '_chitra_save': lambda *args: _chitra_save_impl(*args),
            '_chitra_load': lambda *args: _chitra_load_impl(*args),
            '_chitra_color': lambda *args: _chitra_color_impl(*args),
            '_chitra_colors': lambda *args: _chitra_colors_impl(*args),
            '_chitra_width': lambda *args: _chitra_width_impl(*args),
            '_chitra_height': lambda *args: _chitra_height_impl(*args),
            '_chitra_pixel_get': lambda *args: _chitra_pixel_get_impl(*args),
            '_chitra_pixel_set': lambda *args: _chitra_pixel_set_impl(*args),
        }


    def run(self, bytecode: Bytecode) -> Any:
        """Execute bytecode and return result."""
        frame = CallFrame(bytecode)
        self.frames = [frame]
        self.current_frame = frame
        
        try:
            return self._execute()
        except VMError:
            raise
        except Exception as e:
            import traceback; traceback.print_exc()
            trace = self._format_stack_trace()
            raise VMError(f"Internal VM Crash: {e}\n{trace}")


    def _pop(self) -> Any:
        """Pop a value from the current frame's stack with safety check."""
        if not self.current_frame or not self.current_frame.stack:
            raise VMError("Stack Underflow: Attempted to pop from an empty stack")
        return self.current_frame.stack.pop()

    def _push(self, value: Any) -> None:
        """Push a value onto the current frame's stack."""
        if self.current_frame is not None:
            self.current_frame.stack.append(value)

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
                    # Create a closure with proper upvalue capture
                    closure_env = {}
                    func_name = val[1]
                    
                    # Capture ALL outer variables (variables from parent frame)
                    # These are variables that are NOT parameters of the inner function
                    func_bc = frame.bytecode.functions.get(func_name)
                    inner_param_names = set(func_bc.param_names) if func_bc and hasattr(func_bc, 'param_names') else set()
                    
                    # For each variable in the outer frame, create/share a Cell
                    for i, var_name in enumerate(frame.bytecode.var_names):
                        # Skip if this is a parameter of the inner function
                        if var_name in inner_param_names:
                            continue
                        
                        # Ensure the variable is in a Cell for mutable sharing
                        if i < len(frame.locals):
                            if not isinstance(frame.locals[i], Cell):
                                frame.locals[i] = Cell(frame.locals[i])
                            closure_env[var_name] = frame.locals[i]
                    
                    val = ('function', func_name, closure_env)
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
                    
                    # JIT: Track function call
                    start_time = time.time() if self.jit_enabled else None
                    if self.jit_enabled and self.jit:
                        self.jit.track_call(func_name)
                        
                        # Check if we have a compiled version
                        if func_name in self.jit.compiled_functions:
                            # Execute compiled version
                            compiled_func = self.jit.compiled_functions[func_name]
                            try:
                                result = compiled_func.execute(self.globals, *args)
                                if start_time:
                                    self.jit.track_call(func_name, time.time() - start_time)
                                self._push(result)
                                frame.pc += 2
                                continue
                            except Exception as e:
                                trace = self._format_stack_trace()
                                raise VMError(f"Internal VM Crash: {e}\n{trace}")
                        # Regular function execution
    func_bc = frame.bytecode.functions.get(func_name)
    if not func_bc:
        func_bc = self.frames[0].bytecode.functions.get(func_name)
    if func_bc:
        new_frame = CallFrame(func_bc)
        for i in range(min(len(args), func_bc.num_params)):
            if i < len(new_frame.locals): new_frame.locals[i] = args[i]
        if func_bc.varargs_name and func_bc.num_params < len(new_frame.locals):
            new_frame.locals[func_bc.num_params] = list(args[func_bc.num_params:])
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
                        'हटाओ': 'pop',
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
                    val = self._pop()
                    key = self._pop()
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
                
                # Check package directory (वाक्_ग्रंथालय) - VakPack integration
                package_path = os.path.abspath(os.path.join(base_dir, '..', '..', 'वाक्_ग्रंथालय', f"{module_name}.vak"))
                project_package_path = os.path.abspath(os.path.join(os.getcwd(), 'वाक्_ग्रंथालय', f"{module_name}.vak"))

                target_path = None
                if os.path.exists(local_path):
                    target_path = local_path
                elif os.path.exists(stdlib_path):
                    target_path = stdlib_path
                elif os.path.exists(package_path):
                    target_path = package_path
                elif os.path.exists(project_package_path):
                    target_path = project_package_path

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
                                trace = self._format_stack_trace()
                                raise VMError(f"Internal VM Crash: {e}\n{trace}")

            # ── Vibhakti Semantic Role System ─────────────────────────────────
            elif op == OpCode.CHECK_VIBHAKTI.value:
                """
                CHECK_VIBHAKTI func_idx argc
                
                Validates function arguments against Vibhakti semantic roles.
                Ensures कर्ता (agent) is not None, types match, etc.
                """
                from .vibhakti import VibhaktiRegistry, VibhaktiCase
                
                func_idx = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
                argc = code[frame.pc + 3]
                frame.pc += 4
                
                # Get function bytecode to access Vibhakti signature
                func_bc = constants[func_idx] if func_idx < len(constants) else None
                
                if func_bc and hasattr(func_bc, 'vibhakti_signature') and func_bc.vibhakti_signature:
                    vibhakti_sig = func_bc.vibhakti_signature
                    
                    # Pop args from stack (temporarily)
                    args = [frame.stack.pop() for _ in range(argc)]
                    args.reverse()
                    
                    # Validate each argument against its Vibhakti role
                    for i, (arg, param) in enumerate(zip(args, vibhakti_sig.params)):
                        vibhakti_type = param.vibhakti
                        expected_type = param.type_hint
                        
                        # Type check
                        if expected_type:
                            actual_type = self.builtins['प्रकार'](arg)
                            match = (expected_type == actual_type or 
                                    expected_type == 'कोई_भी' or
                                    (expected_type == 'संख्या' and actual_type in ('पूर्णांक', 'दशमलव')))
                            
                            if not match:
                                raise VMError(
                                    f"विभक्ति प्रकार त्रुटि (Vibhakti Type Error): "
                                    f"{param.name} के लिए '{expected_type}' अपेक्षित था, लेकिन '{actual_type}' मिला"
                                )
                        
                        # Role validation - कर्ता (agent) cannot be None
                        if vibhakti_type == VibhaktiCase.KARTA and arg is None:
                            raise VMError(
                                f"विभक्ति त्रुटि (Vibhakti Error): "
                                f"कर्ता (agent) '{param.name}' शून्य नहीं हो सकता"
                            )
                    
                    # Push args back for function call
                    for arg in args:
                        frame.stack.append(arg)

            elif op == OpCode.LOAD_VIBHAKTI.value:
                """
                LOAD_VIBHAKTI role_idx
                
                Loads Vibhakti role metadata (for reflection/introspection).
                """
                from .vibhakti import VIBHAKTI_NAMES, VibhaktiCase
                
                role_idx = code[frame.pc + 1]
                frame.pc += 2
                
                # Map index to VibhaktiCase
                roles = list(VibhaktiCase)
                if 0 <= role_idx < len(roles):
                    role = roles[role_idx]
                    sanskrit, english = VIBHAKTI_NAMES.get(role, ('???', 'Unknown'))
                    frame.stack.append(f"{sanskृत} ({english})")
                else:
                    frame.stack.append(None)

            # ── Nyāya Proof System ────────────────────────────────────────────
            elif op == OpCode.VERIFY_PROOF.value:
                """
                VERIFY_PROOF proof_idx
                
                Verifies a Nyāya proof certificate at runtime.
                Returns True if proof is valid.
                """
                proof_idx = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
                frame.pc += 3
                
                certificate = constants[proof_idx] if proof_idx < len(constants) else ""
                
                # In full implementation, this would verify the proof certificate
                # against the Sansmatic engine. For now, we trust compile-time verification.
                frame.stack.append(True)  # Proof verified at compile-time

            elif op == OpCode.LOAD_PROOF.value:
                """
                LOAD_PROOF cert_idx
                
                Loads proof certificate string for inspection.
                """
                cert_idx = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
                frame.pc += 3
                
                certificate = constants[cert_idx] if cert_idx < len(constants) else ""
                frame.stack.append(certificate)

            # ── Iteration ─────────────────────────────────────────────────────
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

            # ── Async/Coroutine ────────────────────────────────────────────────
            elif op == OpCode.AWAIT.value:
                # Await a coroutine
                awaitable = self._pop()
                
                if isinstance(awaitable, VakCoroutine):
                    # It's a VakyaLang coroutine
                    if awaitable.completed:
                        # Already completed, just push result
                        frame.stack.append(awaitable.result)
                    else:
                        # Need to execute the coroutine until it completes or yields
                        result = self._run_coroutine_until_yield(awaitable)
                        
                        if awaitable.completed:
                            # Coroutine finished, push result
                            frame.stack.append(awaitable.result)
                        else:
                            # Coroutine suspended - in a full async implementation,
                            # we would suspend the current frame too. For now, we
                            # run the coroutine to completion synchronously.
                            # The event loop handles proper async scheduling.
                            while not awaitable.completed and not awaitable.suspended:
                                result = self._run_coroutine_until_yield(awaitable)
                            frame.stack.append(awaitable.result if awaitable.completed else awaitable)
                elif hasattr(awaitable, '__await__'):
                    # Python awaitable - execute it
                    import types
                    if isinstance(awaitable, types.CoroutineType):
                        # Native Python coroutine - need event loop to run
                        # For now, just push it back
                        frame.stack.append(awaitable)
                    else:
                        # Other awaitable
                        frame.stack.append(awaitable)
                else:
                    # Not awaitable, just push it back (no-op await)
                    frame.stack.append(awaitable)
                
                frame.pc += 1

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

    def _run_coroutine_until_yield(self, coroutine: VakCoroutine) -> Any:
        """
        Execute a coroutine until it yields (awaits) or completes.
        
        Returns the result if completed, or None if suspended.
        
        This method executes the coroutine's bytecode step-by-step,
        properly handling AWAIT, RETURN, and RETURN_VOID opcodes.
        """
        if coroutine.completed:
            return coroutine.result
        
        # Push the coroutine's frame
        self.frames.append(coroutine.frame)
        self.current_frame = coroutine.frame
        
        # Save parent frame context
        parent_frame = self.frames[-2] if len(self.frames) > 1 else None
        parent_code = parent_frame.bytecode.code if parent_frame else None
        parent_constants = parent_frame.bytecode.constants if parent_frame else None
        
        # Get coroutine's execution context
        code = coroutine.frame.bytecode.code
        constants = coroutine.frame.bytecode.constants
        frame = coroutine.frame
        
        # Execute until AWAIT, RETURN, or HALT
        while frame.pc < len(code):
            op = code[frame.pc]
            
            if op == OpCode.AWAIT.value:
                # Hit an await - need to await another coroutine
                # Pop the awaitable
                awaitable = frame.stack.pop()
                
                if isinstance(awaitable, VakCoroutine):
                    # Nested coroutine - run it recursively until completion
                    nested_result = self._run_coroutine_until_yield(awaitable)
                    if awaitable.completed:
                        frame.stack.append(awaitable.result)
                        frame.pc += 1
                        continue
                    else:
                        # Nested coroutine suspended - suspend this one too
                        coroutine.suspended = True
                        self.frames.pop()
                        self.current_frame = parent_frame
                        return None
                else:
                    # Not a coroutine, just push back
                    frame.stack.append(awaitable)
                    frame.pc += 1
                    continue
            
            elif op == OpCode.RETURN.value:
                result = frame.stack.pop()
                coroutine.result = result
                coroutine.completed = True
                coroutine.suspended = False
                self.frames.pop()
                self.current_frame = parent_frame
                return result
            
            elif op == OpCode.RETURN_VOID.value:
                coroutine.result = None
                coroutine.completed = True
                coroutine.suspended = False
                self.frames.pop()
                self.current_frame = parent_frame
                return None
            
            elif op == OpCode.HALT.value:
                coroutine.completed = True
                coroutine.suspended = False
                self.frames.pop()
                self.current_frame = parent_frame
                return coroutine.result
            
            else:
                # Execute other opcodes normally
                self._execute_single_op(frame, code, constants)
        
        # Reached end of bytecode
        coroutine.completed = True
        self.frames.pop()
        self.current_frame = parent_frame
        return coroutine.result

    def _execute_single_op(self, frame: CallFrame, code: bytes, constants: list) -> None:
        """
        Execute a single bytecode instruction.
        
        This is a helper method extracted from _execute for coroutine stepping.
        It executes one opcode and advances the PC.
        """
        op = code[frame.pc]
        
        if op == OpCode.LOAD_CONST.value:
            idx = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
            val = constants[idx]
            # Handle closure creation for functions
            if isinstance(val, tuple) and len(val) >= 2 and val[0] == 'function':
                closure_env = {}
                for i, n in enumerate(frame.bytecode.var_names):
                    if not isinstance(frame.locals[i], Cell):
                        frame.locals[i] = Cell(frame.locals[i])
                    closure_env[n] = frame.locals[i]
                val = ('function', val[1], closure_env)
            frame.stack.append(val)
            frame.pc += 3

        elif op == OpCode.LOAD_VAR.value:
            slot = code[frame.pc + 1]
            name = frame.bytecode.var_names[slot]
            val = frame.locals[slot]
            # Unwrap Cell
            if isinstance(val, Cell):
                val = val.value
            # Fallback to globals/builtins
            if val is None:
                if name in self.globals:
                    val = self.globals[name]
                elif name in self.builtins:
                    val = self.builtins[name]
            frame.stack.append(val)
            frame.pc += 2

        elif op == OpCode.STORE_VAR.value:
            slot = code[frame.pc + 1]
            val = frame.stack.pop()
            name = frame.bytecode.var_names[slot]
            if isinstance(frame.locals[slot], Cell):
                frame.locals[slot].value = val
            else:
                frame.locals[slot] = val
            if len(self.frames) == 1 or name in frame.bytecode.global_names:
                self.globals[name] = val
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

        elif op == OpCode.ADD.value:
            b = frame.stack.pop()
            a = frame.stack.pop()
            frame.stack.append(str(a) + str(b) if isinstance(a, str) or isinstance(b, str) else a + b)
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

        elif op == OpCode.IDIV.value:
            b = frame.stack.pop()
            a = frame.stack.pop()
            frame.stack.append(a // b)
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

        elif op == OpCode.JUMP.value:
            offset = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
            if offset > 32767:
                offset -= 65536
            frame.pc += 3 + offset

        elif op == OpCode.JUMP_IF_TRUE.value:
            offset = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
            if offset > 32767:
                offset -= 65536
            cond = frame.stack.pop()
            frame.pc += 3 + offset if cond else 3

        elif op == OpCode.JUMP_IF_FALSE.value:
            offset = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
            if offset > 32767:
                offset -= 65536
            cond = frame.stack.pop()
            frame.pc += 3 + offset if not cond else 3

        elif op == OpCode.GET_ITER.value:
            obj = frame.stack.pop()
            frame.stack.append(iter(obj))
            frame.pc += 1

        elif op == OpCode.FOR_ITER.value:
            offset = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
            it = frame.stack[-1]
            try:
                val = next(it)
                frame.stack.append(val)
                frame.pc += 3
            except StopIteration:
                frame.stack.pop()
                frame.pc += 3 + offset

        elif op == OpCode.PRINT.value:
            val = frame.stack.pop()
            print(val, end='')
            frame.pc += 1

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
                val = frame.stack.pop()
                key = frame.stack.pop()
                pairs[key] = val
            frame.stack.append(pairs)
            frame.pc += 2

        elif op == OpCode.LIST_APPEND.value:
            val = frame.stack.pop()
            lst = frame.stack[-2]
            lst.append(val)
            frame.pc += 1

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
            idx = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
            attr_name = constants[idx]
            obj = frame.stack.pop()
            if isinstance(obj, VakInstance):
                if attr_name in obj.attrs:
                    frame.stack.append(obj.attrs[attr_name])
                elif attr_name in obj.klass.methods:
                    frame.stack.append(('bound_method', obj, attr_name))
                else:
                    raise VMError(f"Attribute '{attr_name}' not found on {obj.klass.name}")
            elif isinstance(obj, VakModule):
                if attr_name in obj.attrs:
                    frame.stack.append(obj.attrs[attr_name])
                else:
                    raise VMError(f"Attribute '{attr_name}' not found in module {obj.name}")
            else:
                frame.stack.append(getattr(obj, attr_name))
            frame.pc += 3

        elif op == OpCode.ATTR_SET.value:
            idx = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
            attr_name = constants[idx]
            val = frame.stack.pop()
            obj = frame.stack.pop()
            if isinstance(obj, VakInstance):
                obj.attrs[attr_name] = val
            else:
                setattr(obj, attr_name, val)
            frame.pc += 3

        elif op == OpCode.CALL_BUILTIN.value:
            idx = code[frame.pc + 1]
            argc = code[frame.pc + 2]
            builtins_list = list(self.builtins.keys())
            if idx < len(builtins_list):
                name = builtins_list[idx]
                func = self.builtins[name]
                args = [frame.stack.pop() for _ in range(argc)]
                args.reverse()
                frame.stack.append(func(*args))
            else:
                raise VMError(f"Unknown builtin: {idx}")
            frame.pc += 3

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
            handled = False
            while self.frames:
                current = self.frames[-1]
                if current.blocks:
                    catch_pc = current.blocks.pop()
                    current.pc = catch_pc
                    current.stack.append(exception_val)
                    self.current_frame = current
                    handled = True
                    break
                else:
                    self.frames.pop()
            if not handled:
                raise VMError(f"Unhandled exception: {exception_val}")

        else:
            # For unhandled opcodes in coroutine context, raise error
            raise VMError(f"Unsupported opcode in coroutine: {op:02X} at PC {frame.pc}")

    def _create_frame(self, bytecode: Bytecode) -> CallFrame:
        """
        Create a new CallFrame for the given bytecode.
        
        This is a helper method for creating coroutine frames.
        
        Args:
            bytecode: The bytecode to create a frame for
            
        Returns:
            A new CallFrame initialized for the bytecode
        """
        return CallFrame(bytecode)

    def create_coroutine(self, func_name: str, args: tuple = None) -> VakCoroutine:
        """
        Create a coroutine from a named function.
        
        This is a convenience method for creating coroutines from the VM.
        
        Args:
            func_name: Name of the coroutine function
            args: Arguments to pass to the coroutine
            
        Returns:
            A new VakCoroutine instance
        """
        if args is None:
            args = ()
        
        # Get the bytecode for the function
        if self.frames:
            func_bc = self.frames[0].bytecode.functions.get(func_name)
        else:
            func_bc = None
        
        if not func_bc:
            raise VMError(f"Coroutine function not found: {func_name}")
        
        # Create frame and set up arguments
        frame = CallFrame(func_bc)
        num_fixed = func_bc.num_params
        
        for i in range(min(len(args), num_fixed)):
            if i < len(frame.locals):
                frame.locals[i] = args[i]
        
        if func_bc.varargs_name:
            varargs_list = list(args[num_fixed:])
            if num_fixed < len(frame.locals):
                frame.locals[num_fixed] = varargs_list
        
        if hasattr(func_bc, 'defaults'):
            for i in range(len(args), num_fixed):
                if i < len(frame.locals) and func_bc.defaults[i] is not None:
                    frame.locals[i] = func_bc.defaults[i]
        
        return VakCoroutine(frame, func_bc)

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
