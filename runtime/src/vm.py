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
from .event_loop import EventLoop, SUSPEND
from .audit import emit_audit_event
from .errors import VMError

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
    vibhakti_signature: Any = None
    readonly_param_names: set[str] = None
    readonly_object_ids: set[int] = None
    
    def __post_init__(self):
        if self.locals is None:
            self.locals = [UNSET] * len(self.bytecode.var_names)
        if self.stack is None:
            self.stack = []
        if self.blocks is None:
            self.blocks = []
        if self.readonly_param_names is None:
            self.readonly_param_names = set()
        if self.readonly_object_ids is None:
            self.readonly_object_ids = set()

class Cell:
    """A container for shared mutable variables (upvalues)."""
    def __init__(self, value=None):
        self.value = value
    def __repr__(self):
        return f"Cell({self.value})"


UNSET = object()

class VakClass:
    """Represents a custom VakyaLang class."""
    def __init__(self, name: str, methods: dict, method_envs: dict | None = None):
        self.name = name
        self.methods = methods
        self.method_envs = method_envs or {}
        
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


def _rewrite_node_to_source(node: Any) -> str:
    from .ast_nodes import (
        BinaryExpr,
        BoolLiteral,
        CallExpr,
        DictLiteral,
        IdentifierExpr,
        IndexExpr,
        ListLiteral,
        MemberExpr,
        NullLiteral,
        NumberLiteral,
        SetLiteral,
        SliceExpr,
        StringLiteral,
        TupleLiteral,
        UnaryExpr,
    )

    if isinstance(node, NumberLiteral):
        return str(node.value)
    if isinstance(node, StringLiteral):
        return repr(node.value)
    if isinstance(node, BoolLiteral):
        return "सत्य" if node.value else "असत्य"
    if isinstance(node, NullLiteral):
        return "शून्य"
    if isinstance(node, IdentifierExpr):
        return node.name
    if isinstance(node, UnaryExpr):
        return f"{node.op}{_rewrite_node_to_source(node.operand)}"
    if isinstance(node, BinaryExpr):
        return f"({_rewrite_node_to_source(node.left)} {node.op} {_rewrite_node_to_source(node.right)})"
    if isinstance(node, CallExpr):
        args = [_rewrite_node_to_source(arg) for arg in node.args]
        args.extend(
            f"{key}={_rewrite_node_to_source(value)}"
            for key, value in node.kwargs.items()
        )
        return f"{_rewrite_node_to_source(node.callee)}({', '.join(args)})"
    if isinstance(node, MemberExpr):
        return f"{_rewrite_node_to_source(node.obj)}.{node.attr}"
    if isinstance(node, IndexExpr):
        return f"{_rewrite_node_to_source(node.obj)}[{_rewrite_node_to_source(node.index)}]"
    if isinstance(node, SliceExpr):
        parts = [
            _rewrite_node_to_source(part) if part is not None else ""
            for part in (node.start, node.stop, node.step)
        ]
        while parts and parts[-1] == "":
            parts.pop()
        return f"{_rewrite_node_to_source(node.obj)}[{':'.join(parts)}]"
    if isinstance(node, ListLiteral):
        return "[" + ", ".join(_rewrite_node_to_source(element) for element in node.elements) + "]"
    if isinstance(node, TupleLiteral):
        suffix = "," if len(node.elements) == 1 else ""
        return "(" + ", ".join(_rewrite_node_to_source(element) for element in node.elements) + suffix + ")"
    if isinstance(node, SetLiteral):
        return "{" + ", ".join(_rewrite_node_to_source(element) for element in node.elements) + "}"
    if isinstance(node, DictLiteral):
        return "{" + ", ".join(
            f"{_rewrite_node_to_source(key)}: {_rewrite_node_to_source(value)}"
            for key, value in node.pairs
        ) + "}"
    return repr(node)


class VakTerm:
    """Symbolic rewrite term used by runtime परिणाम dispatch."""
    def __init__(self, node: Any):
        self.node = node

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return _rewrite_node_to_source(self.node)


class VakParinama:
    """Callable fixed-point rewrite object for runtime परिणाम execution."""
    def __init__(self, vm: "VakVM", name: str, rules_spec: list[dict[str, Any]], scope: str | None = None):
        self.vm = vm
        self.name = name
        self.rules_spec = rules_spec
        self.scope = scope
        self._rules = None

    def __repr__(self):
        scope = f", scope={self.scope}" if self.scope else ""
        return f"<पारिणाम:{self.name}{scope}>"

    def _decoded_rules(self):
        if self._rules is None:
            from .ast_nodes import RewriteRule
            from .rewrite_engine import decode_rewrite_node

            self._rules = [
                RewriteRule(
                    pattern=decode_rewrite_node(rule.get('pattern')),
                    replacement=decode_rewrite_node(rule.get('replacement')),
                    line=rule.get('line', 0),
                )
                for rule in self.rules_spec
            ]
        return self._rules

    def __call__(self, term: Any, **kwargs: Any) -> Any:
        from .rewrite_engine import rewrite_fixed_point

        requested_scope = kwargs.get('अधिकार', kwargs.get('scope'))
        extra_kwargs = {key: value for key, value in kwargs.items() if key not in ('अधिकार', 'scope')}
        if extra_kwargs:
            names = ", ".join(sorted(extra_kwargs))
            raise VMError(f"पारिणाम '{self.name}' does not accept keyword arguments: {names}")
        if self.scope is not None and requested_scope != self.scope:
            raise VMError(f"पारिणाम '{self.name}' is not visible in scope '{requested_scope}'")

        term_node = self.vm._coerce_runtime_term(term)
        rewritten = rewrite_fixed_point(term_node, self._decoded_rules())
        return self.vm._term_node_to_runtime_value(rewritten)


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
        self.suppress_output = False
        self.module_cache: Dict[str, VakModule] = {}
        
        # JIT Compiler (Month 2-3 Advanced Feature)
        self.jit = JITCompiler() if enable_jit else None
        self.jit_enabled = enable_jit

    def _write_text(self, text: str) -> None:
        """Write VM output without crashing on non-UTF8 consoles."""
        if self.suppress_output:
            return

        import sys

        try:
            sys.stdout.write(text)
        except UnicodeEncodeError:
            encoding = sys.stdout.encoding or 'utf-8'
            safe_text = text.encode(encoding, errors='backslashreplace').decode(
                encoding, errors='replace'
            )
            sys.stdout.write(safe_text)
        sys.stdout.flush()

    def _stringify_value(self, value: Any) -> str:
        if isinstance(value, VakInstance):
            for method_name in ('__str__', '__repr__'):
                if method_name in value.klass.methods:
                    try:
                        result = self._invoke_vak_method(value, method_name)
                        return str(result)
                    except Exception:
                        pass
        return str(value)

    def _print_value(self, value: Any, end: str = '') -> None:
        self._write_text(f"{self._stringify_value(value)}{end}")

    def _handle_runtime_exception(self, exception_val: Any) -> bool:
        """Unwind frames to the nearest active catch block."""
        while self.frames:
            current = self.frames[-1]
            if current.blocks:
                catch_pc = current.blocks.pop()
                current.pc = catch_pc
                current.stack.append(exception_val)
                self.current_frame = current
                return True
            self.frames.pop()

        self.current_frame = self.frames[-1] if self.frames else None
        return False

    def _get_constructor_name(self, klass: VakClass) -> str | None:
        if 'प्रारम्भ' in klass.methods:
            return 'प्रारम्भ'
        if '__init__' in klass.methods:
            return '__init__'
        return None

    def _get_method_closure_env(
        self,
        klass: VakClass,
        method_name: str,
    ) -> Dict[str, Any] | None:
        method_envs = getattr(klass, "method_envs", None) or {}
        closure_env = method_envs.get(method_name)
        return closure_env if isinstance(closure_env, dict) else None

    def _lookup_imported_module_attr(self, frame: CallFrame | None, name: str) -> Any:
        def candidates(values):
            for value in reversed(list(values)):
                if isinstance(value, Cell):
                    value = value.value
                if isinstance(value, VakModule) and name in value.attrs:
                    return value.attrs[name]
            return None

        if frame is not None:
            val = candidates(frame.locals)
            if val is not None:
                return val

            if getattr(frame, 'closure_env', None):
                val = candidates(frame.closure_env.values())
                if val is not None:
                    return val

        return None

    def _invoke_vak_method(self, obj: VakInstance, method_name: str, *args: Any) -> Any:
        method_bc = obj.klass.methods[method_name]
        nested_vm = VakVM(enable_jit=False)
        nested_vm.globals = self.globals
        nested_vm.builtins = self.builtins
        nested_vm.suppress_output = self.suppress_output
        nested_vm.module_cache = self.module_cache

        frame = CallFrame(method_bc)
        if len(frame.locals) > 0:
            frame.locals[0] = obj
        for i, arg in enumerate(args, start=1):
            if i < len(frame.locals):
                frame.locals[i] = arg
        closure_env = self._get_method_closure_env(obj.klass, method_name)
        if closure_env is not None:
            self._hydrate_closure_locals(frame, closure_env)

        nested_vm.frames = [frame]
        nested_vm.current_frame = frame
        return nested_vm._execute()

    def _normalize_kwargs(self, kwargs: Any) -> dict[str, Any]:
        if kwargs is None:
            return {}
        if not isinstance(kwargs, dict):
            raise VMError(f"Expected keyword arguments dict, got {type(kwargs).__name__}")
        return kwargs

    def _unwrap_cell(self, value: Any) -> Any:
        if isinstance(value, Cell):
            value = value.value
        return None if value is UNSET else value

    def _lookup_term_name_value(self, name: str, frame: CallFrame | None) -> tuple[bool, Any]:
        if frame is not None and name in getattr(frame.bytecode, "var_names", []):
            slot = frame.bytecode.var_names.index(name)
            try:
                return True, self._load_named_value(frame, slot)
            except VMError:
                local_names = set(getattr(frame.bytecode, "local_names", set()) or set())
                if name in local_names and name not in getattr(frame.bytecode, "global_names", set()):
                    return False, None

        if frame is not None and getattr(frame, "closure_env", None) and name in frame.closure_env:
            return True, self._unwrap_cell(frame.closure_env[name])

        if name in self.globals:
            return True, self.globals[name]

        imported = self._lookup_imported_module_attr(frame, name)
        if imported is not None:
            return True, imported

        return False, None

    def _coerce_runtime_term(self, value: Any) -> Any:
        if isinstance(value, VakTerm):
            return value.node
        return self._runtime_value_to_term_node(value)

    def _runtime_value_to_term_node(self, value: Any) -> Any:
        from .ast_nodes import (
            BoolLiteral,
            DictLiteral,
            ListLiteral,
            NullLiteral,
            NumberLiteral,
            SetLiteral,
            StringLiteral,
            TupleLiteral,
        )

        if isinstance(value, VakTerm):
            return value.node
        if type(value) in (int, float):
            return NumberLiteral(value=value, line=0)
        if isinstance(value, str):
            return StringLiteral(value=value, line=0)
        if type(value) is bool:
            return BoolLiteral(value=value, line=0)
        if value is None:
            return NullLiteral(line=0)
        if isinstance(value, list):
            return ListLiteral(elements=[self._runtime_value_to_term_node(item) for item in value], line=0)
        if isinstance(value, tuple):
            return TupleLiteral(elements=[self._runtime_value_to_term_node(item) for item in value], line=0)
        if isinstance(value, set):
            return SetLiteral(elements=[self._runtime_value_to_term_node(item) for item in value], line=0)
        if isinstance(value, dict):
            return DictLiteral(
                pairs=[
                    (self._runtime_value_to_term_node(key), self._runtime_value_to_term_node(item))
                    for key, item in value.items()
                ],
                line=0,
            )
        raise VMError(f"पारिणाम term conversion unsupported for {type(value).__name__}")

    def _term_node_to_runtime_value(self, node: Any) -> Any:
        from .ast_nodes import (
            BoolLiteral,
            CallExpr,
            DictLiteral,
            IdentifierExpr,
            ListLiteral,
            NullLiteral,
            NumberLiteral,
            SetLiteral,
            StringLiteral,
            TupleLiteral,
        )

        if isinstance(node, NumberLiteral):
            return node.value
        if isinstance(node, StringLiteral):
            return node.value
        if isinstance(node, BoolLiteral):
            return node.value
        if isinstance(node, NullLiteral):
            return None
        if isinstance(node, ListLiteral):
            return [self._term_node_to_runtime_value(element) for element in node.elements]
        if isinstance(node, TupleLiteral):
            return tuple(self._term_node_to_runtime_value(element) for element in node.elements)
        if isinstance(node, SetLiteral):
            return set(self._term_node_to_runtime_value(element) for element in node.elements)
        if isinstance(node, DictLiteral):
            converted: dict[Any, Any] = {}
            for key_node, value_node in node.pairs:
                key = self._term_node_to_runtime_value(key_node)
                if isinstance(key, VakTerm):
                    return VakTerm(node)
                converted[key] = self._term_node_to_runtime_value(value_node)
            return converted
        if isinstance(node, CallExpr) and isinstance(node.callee, IdentifierExpr):
            pure_wrappers = {
                'संख्या', 'int', 'दशमलव', 'float', 'bool',
                'list', 'dict', 'set', 'tuple',
                'पाठ_कर', 'str', 'सिद्ध', 'असिद्ध',
            }
            if node.callee.name in pure_wrappers:
                args = [self._term_node_to_runtime_value(arg) for arg in node.args]
                kwargs = {
                    key: self._term_node_to_runtime_value(value)
                    for key, value in node.kwargs.items()
                }
                if any(isinstance(arg, VakTerm) for arg in args) or any(
                    isinstance(value, VakTerm) for value in kwargs.values()
                ):
                    return VakTerm(node)
                func = self.builtins.get(node.callee.name)
                if func is None and node.callee.name == 'tuple':
                    func = tuple
                if callable(func):
                    return func(*args, **kwargs)
        return VakTerm(node)

    def _build_term_from_spec(
        self,
        spec: Any,
        *,
        frame: CallFrame | None = None,
        resolve_identifiers: bool = True,
    ) -> Any:
        from .ast_nodes import (
            BinaryExpr,
            BoolLiteral,
            CallExpr,
            DictLiteral,
            IdentifierExpr,
            IndexExpr,
            ListLiteral,
            MemberExpr,
            NullLiteral,
            NumberLiteral,
            SetLiteral,
            SliceExpr,
            StringLiteral,
            TupleLiteral,
            UnaryExpr,
        )

        if spec is None:
            return None

        kind = spec.get('kind')
        line = spec.get('line', 0)

        if kind == 'number':
            return NumberLiteral(value=spec.get('value'), line=line)
        if kind == 'string':
            return StringLiteral(value=spec.get('value', ''), line=line)
        if kind == 'bool':
            return BoolLiteral(value=bool(spec.get('value')), line=line)
        if kind == 'null':
            return NullLiteral(line=line)
        if kind == 'identifier':
            name = spec.get('name', '')
            if resolve_identifiers:
                found, value = self._lookup_term_name_value(name, frame or self.current_frame)
                if found:
                    return self._coerce_runtime_term(value)
            return IdentifierExpr(name=name, line=line)
        if kind == 'binary':
            return BinaryExpr(
                op=spec.get('op', ''),
                left=self._build_term_from_spec(spec.get('left'), frame=frame, resolve_identifiers=resolve_identifiers),
                right=self._build_term_from_spec(spec.get('right'), frame=frame, resolve_identifiers=resolve_identifiers),
                line=line,
            )
        if kind == 'unary':
            return UnaryExpr(
                op=spec.get('op', ''),
                operand=self._build_term_from_spec(spec.get('operand'), frame=frame, resolve_identifiers=resolve_identifiers),
                line=line,
            )
        if kind == 'call':
            return CallExpr(
                callee=self._build_term_from_spec(spec.get('callee'), frame=frame, resolve_identifiers=False),
                args=[
                    self._build_term_from_spec(arg, frame=frame, resolve_identifiers=resolve_identifiers)
                    for arg in spec.get('args', [])
                ],
                kwargs={
                    key: self._build_term_from_spec(value, frame=frame, resolve_identifiers=resolve_identifiers)
                    for key, value in spec.get('kwargs', {}).items()
                },
                line=line,
            )
        if kind == 'member':
            return MemberExpr(
                obj=self._build_term_from_spec(spec.get('obj'), frame=frame, resolve_identifiers=resolve_identifiers),
                attr=spec.get('attr', ''),
                line=line,
            )
        if kind == 'index':
            return IndexExpr(
                obj=self._build_term_from_spec(spec.get('obj'), frame=frame, resolve_identifiers=resolve_identifiers),
                index=self._build_term_from_spec(spec.get('index'), frame=frame, resolve_identifiers=resolve_identifiers),
                line=line,
            )
        if kind == 'slice':
            return SliceExpr(
                obj=self._build_term_from_spec(spec.get('obj'), frame=frame, resolve_identifiers=resolve_identifiers),
                start=self._build_term_from_spec(spec.get('start'), frame=frame, resolve_identifiers=resolve_identifiers),
                stop=self._build_term_from_spec(spec.get('stop'), frame=frame, resolve_identifiers=resolve_identifiers),
                step=self._build_term_from_spec(spec.get('step'), frame=frame, resolve_identifiers=resolve_identifiers),
                line=line,
            )
        if kind == 'list':
            return ListLiteral(
                elements=[
                    self._build_term_from_spec(element, frame=frame, resolve_identifiers=resolve_identifiers)
                    for element in spec.get('elements', [])
                ],
                line=line,
            )
        if kind == 'tuple':
            return TupleLiteral(
                elements=[
                    self._build_term_from_spec(element, frame=frame, resolve_identifiers=resolve_identifiers)
                    for element in spec.get('elements', [])
                ],
                line=line,
            )
        if kind == 'set':
            return SetLiteral(
                elements=[
                    self._build_term_from_spec(element, frame=frame, resolve_identifiers=resolve_identifiers)
                    for element in spec.get('elements', [])
                ],
                line=line,
            )
        if kind == 'dict':
            return DictLiteral(
                pairs=[
                    (
                        self._build_term_from_spec(pair.get('key'), frame=frame, resolve_identifiers=resolve_identifiers),
                        self._build_term_from_spec(pair.get('value'), frame=frame, resolve_identifiers=resolve_identifiers),
                    )
                    for pair in spec.get('pairs', [])
                ],
                line=line,
            )
        raise VMError(f"Unsupported term spec kind: {kind}")

    def _is_module_frame(self, frame: CallFrame) -> bool:
        return getattr(getattr(frame, "bytecode", None), "name", None) == "<module>"

    def _capture_closure_env(self, frame: CallFrame, func_bc: Any) -> dict[str, Any]:
        closure_env: dict[str, Any] = {}
        required_names = set(getattr(func_bc, "closure_names", set()) or set())
        required_names.update(getattr(func_bc, "nonlocal_names", set()) or set())

        if not required_names:
            return closure_env

        current_scope = {
            name: index
            for index, name in enumerate(getattr(frame.bytecode, "var_names", []) or [])
        }

        for name in required_names:
            if name in current_scope:
                slot = current_scope[name]
                if slot < len(frame.locals):
                    value = frame.locals[slot]
                    if not isinstance(value, Cell):
                        value = Cell(value)
                        frame.locals[slot] = value
                    closure_env[name] = value
                    continue

            if getattr(frame, "closure_env", None) and name in frame.closure_env:
                value = frame.closure_env[name]
                if not isinstance(value, Cell):
                    value = Cell(value)
                    frame.closure_env[name] = value
                closure_env[name] = value

        return closure_env

    def _hydrate_closure_locals(self, frame: CallFrame, closure_env: Dict[str, Any] | None) -> None:
        if not closure_env:
            return

        frame.closure_env = closure_env
        closure_names = set(getattr(frame.bytecode, "closure_names", set()) or set())
        closure_names.update(getattr(frame.bytecode, "nonlocal_names", set()) or set())

        if not closure_names:
            return

        for index, name in enumerate(getattr(frame.bytecode, "var_names", []) or []):
            if name not in closure_names or name not in closure_env:
                continue
            cell_value = closure_env[name]
            if not isinstance(cell_value, Cell):
                cell_value = Cell(cell_value)
                closure_env[name] = cell_value
            if index < len(frame.locals):
                frame.locals[index] = cell_value

    def _load_named_value(self, frame: CallFrame, slot: int) -> Any:
        if slot >= len(frame.locals):
            raise VMError(f"VM Error: Invalid local variable slot {slot}")

        name = frame.bytecode.var_names[slot]
        local_names = set(getattr(frame.bytecode, "local_names", set()) or set())
        closure_names = set(getattr(frame.bytecode, "closure_names", set()) or set())
        nonlocal_names = set(getattr(frame.bytecode, "nonlocal_names", set()) or set())
        is_global_name = self._is_module_frame(frame) or name in frame.bytecode.global_names

        if is_global_name and name in self.globals:
            return self.globals[name]

        local_value = frame.locals[slot]
        if isinstance(local_value, Cell):
            local_value = local_value.value
        if local_value is not UNSET:
            return local_value

        if getattr(frame, "closure_env", None):
            if name not in local_names and name in frame.closure_env:
                closure_value = frame.closure_env[name]
                if isinstance(closure_value, Cell):
                    closure_value = closure_value.value
                if closure_value is not UNSET:
                    return closure_value

            if name in closure_names or name in nonlocal_names:
                if name in frame.closure_env:
                    closure_value = frame.closure_env[name]
                    if isinstance(closure_value, Cell):
                        closure_value = closure_value.value
                    if closure_value is not UNSET:
                        return closure_value

            # Imported module environments are carried in closure_env and should
            # remain readable even when the function itself has no lexical capture.
            if "__bytecode__" in frame.closure_env and name in frame.closure_env:
                module_value = frame.closure_env[name]
                if isinstance(module_value, Cell):
                    module_value = module_value.value
                if module_value is not UNSET:
                    return module_value

        if name not in local_names or is_global_name:
            if name in self.globals:
                return self.globals[name]
            imported = self._lookup_imported_module_attr(frame, name)
            if imported is not None:
                return imported
            if name in self.builtins:
                return self.builtins[name]
            raise VMError(f"Name not found: {name}")

        raise VMError(f"Local variable '{name}' referenced before assignment")

    def _store_named_value(self, frame: CallFrame, slot: int, value: Any) -> None:
        if slot >= len(frame.locals):
            raise VMError(f"VM Error: Invalid local variable slot {slot}")

        name = frame.bytecode.var_names[slot]
        self._enforce_vibhakti_store(frame, name)

        if name in getattr(frame.bytecode, "nonlocal_names", set()):
            if not getattr(frame, "closure_env", None) or name not in frame.closure_env:
                raise VMError(f"Nonlocal binding not found: {name}")
            cell_value = frame.closure_env[name]
            if not isinstance(cell_value, Cell):
                cell_value = Cell(cell_value)
                frame.closure_env[name] = cell_value
            cell_value.value = value
            frame.locals[slot] = cell_value
            return

        if isinstance(frame.locals[slot], Cell):
            frame.locals[slot].value = value
        else:
            frame.locals[slot] = value

        if self._is_module_frame(frame) or name in frame.bytecode.global_names:
            self.globals[name] = value

    def _merge_pattern_bindings(
        self,
        left: dict[str, Any],
        right: dict[str, Any],
    ) -> dict[str, Any] | None:
        merged = dict(left)
        for key, value in right.items():
            if key in merged and merged[key] != value:
                return None
            merged[key] = value
        return merged

    def _match_pattern_spec(self, value: Any, spec: Any) -> dict[str, Any] | None:
        if not isinstance(spec, tuple) or not spec:
            return None

        kind = spec[0]
        if kind == 'wildcard':
            return {}

        if kind == 'bind':
            return {spec[1]: value}

        if kind == 'literal':
            return {} if value == spec[1] else None

        if kind == 'sequence':
            _, sequence_kind, element_specs, rest_name = spec
            if sequence_kind == 'list':
                if not isinstance(value, list):
                    return None
            elif sequence_kind == 'tuple':
                if not isinstance(value, tuple):
                    return None
            else:
                return None

            if rest_name is None and len(value) != len(element_specs):
                return None
            if rest_name is not None and len(value) < len(element_specs):
                return None

            bindings: dict[str, Any] = {}
            for index, element_spec in enumerate(element_specs):
                matched = self._match_pattern_spec(value[index], element_spec)
                if matched is None:
                    return None
                bindings = self._merge_pattern_bindings(bindings, matched)
                if bindings is None:
                    return None

            if rest_name is not None:
                remainder = value[len(element_specs):]
                bindings[rest_name] = list(remainder) if sequence_kind == 'list' else tuple(remainder)
            elif len(value) != len(element_specs):
                return None
            return bindings

        if kind == 'call':
            _, callee_name, arg_specs = spec
            args = None
            if isinstance(value, tuple) and len(value) >= 1 and value[0] == callee_name:
                args = list(value[1:])
            elif isinstance(value, list) and len(value) >= 1 and value[0] == callee_name:
                args = list(value[1:])
            elif isinstance(value, VakInstance) and value.klass.name == callee_name:
                attrs = list(value.attrs.values())
                if len(attrs) == len(arg_specs):
                    args = attrs

            if args is None or len(args) != len(arg_specs):
                return None

            bindings: dict[str, Any] = {}
            for arg_value, arg_spec in zip(args, arg_specs):
                matched = self._match_pattern_spec(arg_value, arg_spec)
                if matched is None:
                    return None
                bindings = self._merge_pattern_bindings(bindings, matched)
                if bindings is None:
                    return None
            return bindings

        return None

    def _value_matches_type(self, value: Any, expected_type: str | None) -> bool:
        if not expected_type or expected_type == 'कोई_भी':
            return True
        from .types import (
            ADT_REGISTRY,
            ADTType,
            ANY,
            BOOL,
            FLOAT,
            INT,
            NULL,
            STR,
            DictType,
            InstanceType,
            ListType,
            ResultType,
            SetType,
            TupleType,
            TypeVarType,
            UnionType,
            VariantValueType,
            parse_type_hint,
        )

        def matches(value_obj: Any, vak_type: Any) -> bool:
            if vak_type == ANY or isinstance(vak_type, TypeVarType):
                return True
            if vak_type == NULL:
                return value_obj is None
            if vak_type == BOOL:
                return type(value_obj) is bool
            if vak_type == INT:
                return type(value_obj) is int
            if vak_type == FLOAT:
                return type(value_obj) in (int, float)
            if vak_type == STR:
                return isinstance(value_obj, str)
            if isinstance(vak_type, ListType):
                return isinstance(value_obj, list) and all(matches(item, vak_type.element_type) for item in value_obj)
            if isinstance(vak_type, SetType):
                return isinstance(value_obj, set) and all(matches(item, vak_type.element_type) for item in value_obj)
            if isinstance(vak_type, TupleType):
                return (
                    isinstance(value_obj, tuple)
                    and len(value_obj) == len(vak_type.element_types)
                    and all(matches(item, item_type) for item, item_type in zip(value_obj, vak_type.element_types))
                )
            if isinstance(vak_type, DictType):
                return (
                    isinstance(value_obj, dict)
                    and all(matches(key, vak_type.key_type) for key in value_obj.keys())
                    and all(matches(item, vak_type.value_type) for item in value_obj.values())
                )
            if isinstance(vak_type, ResultType):
                return (
                    isinstance(value_obj, tuple)
                    and len(value_obj) == 2
                    and value_obj[0] in ("सिद्ध", "असिद्ध")
                    and (
                        matches(value_obj[1], vak_type.ok_type)
                        if value_obj[0] == "सिद्ध"
                        else matches(value_obj[1], vak_type.err_type)
                    )
                )
            if isinstance(vak_type, VariantValueType):
                return (
                    isinstance(value_obj, tuple)
                    and len(value_obj) == len(vak_type.field_types) + 1
                    and value_obj[0] == vak_type.variant_name
                    and all(matches(item, item_type) for item, item_type in zip(value_obj[1:], vak_type.field_types))
                )
            if isinstance(vak_type, ADTType):
                return (
                    isinstance(value_obj, tuple)
                    and len(value_obj) >= 1
                    and vak_type.name in ADT_REGISTRY
                    and value_obj[0] in set(ADT_REGISTRY[vak_type.name].get("variants", ()))
                )
            if isinstance(vak_type, UnionType):
                return any(matches(value_obj, option) for option in vak_type.options)
            if isinstance(vak_type, InstanceType):
                return isinstance(value_obj, VakInstance) and value_obj.klass.name == vak_type.name
            actual_type = self.builtins['प्रकार'](value_obj)
            return str(vak_type) == actual_type

        return matches(value, parse_type_hint(expected_type))

    def _configure_vibhakti_frame(self, frame: CallFrame, func_bc: Any) -> None:
        from .vibhakti import VibhaktiCase

        signature = getattr(func_bc, 'vibhakti_signature', None)
        frame.vibhakti_signature = signature
        frame.readonly_param_names.clear()
        frame.readonly_object_ids.clear()

        if not signature:
            return

        for param in signature.params:
            if param.name not in frame.bytecode.var_names:
                continue
            slot = frame.bytecode.var_names.index(param.name)
            value = self._unwrap_cell(frame.locals[slot])

            if param.vibhakti == VibhaktiCase.KARTA and value is None:
                raise VMError(f"विभक्ति त्रुटि: कर्ता '{param.name}' शून्य नहीं हो सकता")

            if not self._value_matches_type(value, param.type_hint):
                actual_type = self.builtins['प्रकार'](value)
                raise VMError(
                    f"विभक्ति प्रकार त्रुटि: {param.name} के लिए '{param.type_hint}' अपेक्षित था, लेकिन '{actual_type}' मिला"
                )

            if param.vibhakti == VibhaktiCase.KARANA:
                frame.readonly_param_names.add(param.name)
                if isinstance(value, (list, dict, VakInstance)):
                    frame.readonly_object_ids.add(id(value))

    def _enforce_vibhakti_store(self, frame: CallFrame, name: str) -> None:
        if name in frame.readonly_param_names:
            raise VMError(f"विभक्ति त्रुटि: करण '{name}' को पुनर्नियोजित नहीं किया जा सकता")

    def _enforce_vibhakti_object_mutation(self, frame: CallFrame, obj: Any) -> None:
        if id(obj) in frame.readonly_object_ids:
            raise VMError("विभक्ति त्रुटि: करण मान को परिवर्तित नहीं किया जा सकता")

    def _enforce_vibhakti_return(self, frame: CallFrame, result: Any) -> Any:
        signature = getattr(frame, 'vibhakti_signature', None)
        if signature and getattr(signature, 'return_vibhakti', None) is not None and result is None:
            raise VMError("विभक्ति त्रुटि: return value required by function signature")
        return result

    def _is_internal_binding_name(self, name: str) -> bool:
        return name.startswith("__imported_module_") or (
            name.startswith("<") and name.endswith(">")
        )

    def _resolve_function_bytecode(
        self,
        func_name: str,
        func: Any = None,
        frame: CallFrame | None = None,
    ) -> Any:
        search_spaces = []

        if frame is not None and getattr(frame, "bytecode", None):
            search_spaces.append(frame.bytecode)

        if self.frames:
            root_bytecode = self.frames[0].bytecode
            if root_bytecode not in search_spaces:
                search_spaces.append(root_bytecode)

        for bytecode in search_spaces:
            func_bc = getattr(bytecode, "functions", {}).get(func_name)
            if func_bc:
                return func_bc

        if isinstance(func, tuple) and len(func) >= 3:
            closure_env = func[2]
            if isinstance(closure_env, dict):
                module_bytecode = closure_env.get("__bytecode__")
                if hasattr(module_bytecode, "functions"):
                    return module_bytecode.functions.get(func_name)

        return None

    def _bind_call_arguments(
        self,
        new_frame: CallFrame,
        func_bc: Any,
        args: list[Any],
        kwargs: dict[str, Any] | None = None,
        self_obj: Any = None,
    ) -> None:
        kwargs = kwargs or {}

        self_offset = 1 if self_obj is not None else 0
        if self_obj is not None and len(new_frame.locals) > 0:
            new_frame.locals[0] = self_obj

        user_param_count = max(func_bc.num_params - self_offset, 0)
        param_names = list(getattr(func_bc, 'param_names', []) or [])
        if len(param_names) >= func_bc.num_params:
            user_param_names = param_names[self_offset:func_bc.num_params]
        else:
            user_param_names = list(new_frame.bytecode.var_names[self_offset:func_bc.num_params])

        assigned = set()

        for index, arg in enumerate(args[:user_param_count]):
            local_index = self_offset + index
            if local_index < len(new_frame.locals):
                new_frame.locals[local_index] = arg
            assigned.add(index)

        for kw_name, kw_value in kwargs.items():
            if kw_name not in user_param_names:
                raise VMError(f"Unexpected keyword argument: {kw_name}")
            param_index = user_param_names.index(kw_name)
            if param_index in assigned:
                raise VMError(f"Multiple values for argument: {kw_name}")
            local_index = self_offset + param_index
            if local_index < len(new_frame.locals):
                new_frame.locals[local_index] = kw_value
            assigned.add(param_index)

        defaults = list(getattr(func_bc, 'defaults', []) or [])
        if len(defaults) < func_bc.num_params:
            defaults = [None] * (func_bc.num_params - len(defaults)) + defaults
        elif len(defaults) > func_bc.num_params:
            defaults = defaults[:func_bc.num_params]

        for param_index in range(user_param_count):
            if param_index in assigned:
                continue
            local_index = self_offset + param_index
            if local_index < len(defaults) and defaults[local_index] is not None:
                if local_index < len(new_frame.locals):
                    new_frame.locals[local_index] = defaults[local_index]

        if func_bc.varargs_name:
            varargs_slot = func_bc.num_params
            if varargs_slot < len(new_frame.locals):
                new_frame.locals[varargs_slot] = list(args[user_param_count:])

        self._configure_vibhakti_frame(new_frame, func_bc)

    def _module_name_candidates(self, module_name: str) -> list[str]:
        aliases = {
            'गणित': 'ganit',
            'गणित_विस्तारित': 'ganit_vistarit',
            'भाषा_प्रसादन': 'bhasha_prasadan',
            'तर्क_शास्त्र': 'tarka_shastra',
            'संग्रह': 'sangrah',
            'संग्रह_विस्तारित': 'sangrah_vistarit',
            'डेटा_संग्रह': 'data_sangrah',
            'कंटेनर_संग्रह': 'container_sangrah',
            'मैट्रिक्स_गणित': 'matrix_ganit',
            'संभावना': 'sambhavana',
            'उपयोगिता': 'upayogita',
            'रेखा_गणित': 'rekha_ganit',
            'धागा': 'dhaaga',
            'फाइल': 'file',
            'कूटलेख': 'kootlekh',
            'नियमित': 'niyamit',
            'मूल': 'mool',
            'यादृच्छ': 'yadricha',
            'यादृच्छा': 'yadricha',
            'पायथन_ब्रिज': 'py_bridge',
            'उन्नत_सांख्यिकी': 'unnata_sankhyiki',
        }
        candidates = [module_name]
        alias = aliases.get(module_name)
        if alias and alias not in candidates:
            candidates.append(alias)
        return candidates

    def _module_search_dirs(self, frame: CallFrame | None) -> list[str]:
        import os

        search_dirs: list[str] = []

        def add_dir(path: str | None) -> None:
            if not path:
                return
            abs_path = os.path.abspath(path)
            if abs_path not in search_dirs:
                search_dirs.append(abs_path)

        bytecodes = []
        if frame is not None and getattr(frame, "bytecode", None):
            bytecodes.append(frame.bytecode)
        for active_frame in reversed(self.frames):
            if getattr(active_frame, "bytecode", None):
                bytecodes.append(active_frame.bytecode)

        for bytecode in bytecodes:
            source_path = getattr(bytecode, "source_path", None)
            if source_path:
                add_dir(os.path.dirname(source_path))

        vm_dir = os.path.dirname(os.path.abspath(__file__))
        runtime_root = os.path.abspath(os.path.join(vm_dir, '..'))
        project_root = os.path.abspath(os.path.join(vm_dir, '..', '..'))

        add_dir(os.getcwd())
        add_dir(os.path.join(os.getcwd(), 'वाक्_ग्रंथालय'))
        add_dir(runtime_root)
        add_dir(os.path.join(runtime_root, 'stdlib'))
        add_dir(project_root)
        add_dir(os.path.join(project_root, 'वाक्_ग्रंथालय'))

        return search_dirs

    def _resolve_module_path(self, module_name: str, frame: CallFrame | None) -> tuple[str, str]:
        import os

        for candidate_name in self._module_name_candidates(module_name):
            relative_names = [candidate_name]
            package_name = candidate_name.replace('.', os.sep)
            if package_name not in relative_names:
                relative_names.append(package_name)

            for search_dir in self._module_search_dirs(frame):
                for relative_name in relative_names:
                    file_path = os.path.abspath(os.path.join(search_dir, f"{relative_name}.vak"))
                    if os.path.exists(file_path):
                        return candidate_name, file_path

                    init_path = os.path.abspath(
                        os.path.join(search_dir, relative_name, "__init__.vak")
                    )
                    if os.path.exists(init_path):
                        return candidate_name, init_path

        raise VMError(f"Module not found: {module_name}")
        
    def _init_builtins(self) -> Dict[str, Callable]:
        """Initialize builtin functions."""
        import builtins as py_builtins
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

        def _normalize_path(path):
            try:
                return os.path.abspath(os.fspath(path))
            except TypeError:
                return os.path.abspath(str(path))

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
            from chitrakala.bitmap_font import draw_text, draw_text_centered
            from chitrakala.effects import ChitraEffects
            _chitra_available = True
        except ImportError:
            ChitraCanvas = None
            ChitraColor = None
            get_color = None
            list_colors = None
            save_png = None
            load_png = None
            draw_point = None
            draw_line = None
            draw_circle = None
            draw_rectangle = None
            draw_polygon = None
            draw_text = None
            draw_text_centered = None
            ChitraEffects = None
            _chitra_available = False

        def _read_file(path):
            resolved = _normalize_path(path)
            emit_audit_event("vak.file.read", resolved)
            with open(resolved, 'r', encoding='utf-8') as f:
                return f.read()
                
        def _write_file(path, content, mode='w'):
            resolved = _normalize_path(path)
            emit_audit_event("vak.file.write", resolved, mode)
            with open(resolved, mode, encoding='utf-8') as f:
                f.write(self._stringify_value(content))
            return None

        def _open_file(path, mode='r'):
            resolved = _normalize_path(path)
            emit_audit_event("vak.file.open", resolved, mode)
            if 'b' in mode:
                return open(resolved, mode)
            return open(resolved, mode, encoding='utf-8')

        def _require_chitra_support():
            if not _chitra_available:
                raise VMError("चित्रकला समर्थन उपलब्ध नहीं है")

        def _resolve_chitra_color(value):
            _require_chitra_support()
            return get_color(value) if isinstance(value, str) else value

        def _resolve_chitra_palette(values):
            if isinstance(values, (list, tuple)):
                return [_resolve_chitra_color(value) for value in values]
            return [_resolve_chitra_color(values)]

        def _make_dir(path):
            resolved = _normalize_path(path)
            emit_audit_event("vak.file.mkdir", resolved)
            os.makedirs(resolved, exist_ok=True)
            return None

        def _remove_path(path):
            resolved = _normalize_path(path)
            if os.path.exists(resolved):
                emit_audit_event("vak.file.remove", resolved)
                os.remove(resolved)
            return None

        def _list_dir(path='.'):
            resolved = _normalize_path(path)
            emit_audit_event("vak.file.listdir", resolved)
            return os.listdir(resolved)

        def _get_env(name, default=None):
            emit_audit_event("vak.env.get", str(name))
            return os.getenv(name, default)

        def _set_env(name, value):
            emit_audit_event("vak.env.set", str(name))
            os.putenv(str(name), str(value))
            return None

        def _system_command(command):
            emit_audit_event("vak.system.command", str(command))
            return os.system(command)
            
        def _http_get(url, headers_dict=None):
            import urllib.request
            headers = headers_dict if headers_dict else {'User-Agent': 'VakyaLang/3.0'}
            try:
                emit_audit_event("vak.http.request", "GET", str(url))
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=30) as response:
                    return response.read().decode('utf-8')
            except Exception as e:
                return f"HTTP Error: {e}"

        def _http_post(url, data, headers_dict=None):
            import urllib.request
            headers = headers_dict if headers_dict else {'User-Agent': 'VakyaLang/3.0'}
            try:
                emit_audit_event("vak.http.request", "POST", str(url))
                req = urllib.request.Request(url, data=str(data).encode('utf-8'), headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=30) as response:
                    return response.read().decode('utf-8')
            except Exception as e:
                return f"HTTP Error: {e}"

        def _http_put(url, data, headers_dict=None):
            import urllib.request
            headers = headers_dict if headers_dict else {'User-Agent': 'VakyaLang/3.0'}
            try:
                emit_audit_event("vak.http.request", "PUT", str(url))
                req = urllib.request.Request(url, data=str(data).encode('utf-8'), headers=headers, method='PUT')
                with urllib.request.urlopen(req, timeout=30) as response:
                    return response.read().decode('utf-8')
            except Exception as e:
                return f"HTTP Error: {e}"

        def _http_delete(url, headers_dict=None):
            import urllib.request
            headers = headers_dict if headers_dict else {'User-Agent': 'VakyaLang/3.0'}
            try:
                emit_audit_event("vak.http.request", "DELETE", str(url))
                req = urllib.request.Request(url, headers=headers, method='DELETE')
                with urllib.request.urlopen(req, timeout=30) as response:
                    return response.read().decode('utf-8')
            except Exception as e:
                return f"HTTP Error: {e}"

        def _http_download(url, path, headers_dict=None):
            import urllib.request

            headers = headers_dict if headers_dict else {'User-Agent': 'VakyaLang/3.0'}
            resolved = _normalize_path(path)
            os.makedirs(os.path.dirname(resolved) or '.', exist_ok=True)

            try:
                emit_audit_event("vak.http.download", str(url), resolved)
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=30) as response:
                    with open(resolved, 'wb') as target:
                        target.write(response.read())
                return resolved
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

        def _vak_str(obj):
            return self._stringify_value(obj)

        def _invoke_callable(func, *args, **kwargs):
            if isinstance(func, tuple) and func[0] == 'function':
                func_bc = self._resolve_function_bytecode(
                    func[1],
                    func,
                    self.current_frame if self.frames else None,
                )
                if not func_bc:
                    raise VMError(f"Function not found: {func[1]}")

                new_frame = CallFrame(func_bc)
                self._bind_call_arguments(new_frame, func_bc, list(args), kwargs)
                if len(func) >= 3:
                    self._hydrate_closure_locals(new_frame, func[2])
                return self._execute_single_frame(new_frame)

            if isinstance(func, tuple) and func[0] == 'bound_method':
                obj, method_name = func[1], func[2]
                if isinstance(obj, VakInstance) and method_name in obj.klass.methods:
                    func_bc = obj.klass.methods[method_name]
                    new_frame = CallFrame(func_bc)
                    self._bind_call_arguments(new_frame, func_bc, list(args), kwargs, self_obj=obj)
                    closure_env = self._get_method_closure_env(obj.klass, method_name)
                    if closure_env is not None:
                        self._hydrate_closure_locals(new_frame, closure_env)
                    return self._execute_single_frame(new_frame)
                raise VMError(f"Cannot call bound method {method_name}")

            if callable(func):
                return func(*args, **kwargs)

            raise VMError(f"Object not callable: {type(func).__name__}")

        def _vak_isinstance(obj, cls):
            if isinstance(cls, VakClass):
                return isinstance(obj, VakInstance) and obj.klass.name == cls.name
            if isinstance(cls, str):
                return _vak_type(obj) == cls or type(obj).__name__ == cls
            try:
                return isinstance(obj, cls)
            except TypeError:
                return False

        def _vak_hasattr(obj, attr_name):
            attr_name = str(attr_name)
            if isinstance(obj, VakInstance):
                return attr_name in obj.attrs or attr_name in obj.klass.methods
            if isinstance(obj, VakModule):
                return attr_name in obj.attrs
            return hasattr(obj, attr_name)

        def _vak_match_exception(exception, handler_name):
            if handler_name in (None, "", "_"):
                return True
            handler_text = str(handler_name).strip()
            if not handler_text:
                return True
            candidate = getattr(py_builtins, handler_text, None)
            if isinstance(candidate, type) and issubclass(candidate, BaseException):
                return isinstance(exception, candidate)
            if handler_text.endswith(("Error", "Exception")):
                return any(cls.__name__ == handler_text for cls in type(exception).__mro__)
            return True

        def _vak_map(func, iterable):
            return [_invoke_callable(func, item) for item in iterable]

        def _vak_filter(func, iterable):
            return [item for item in iterable if _invoke_callable(func, item)]

        def _vak_enumerate(iterable, start=0):
            return list(enumerate(iterable, int(start)))

        def _vak_zip(*iterables):
            return list(zip(*iterables))

        def _get_time(): return time.time()
        def _sleep(seconds): time.sleep(float(seconds))
        
        def _vak_print(*args):
            self._write_text(' '.join(self._stringify_value(arg) for arg in args) + '\n')
            return None

        def _vak_result_ok(value=None):
            return ('सिद्ध', value)

        def _vak_result_err(error=None):
            return ('असिद्ध', error)

        def _vak_result_is_ok(value):
            return isinstance(value, tuple) and len(value) == 2 and value[0] == 'सिद्ध'

        def _vak_result_is_err(value):
            return isinstance(value, tuple) and len(value) == 2 and value[0] == 'असिद्ध'

        def _vak_result_unwrap(value):
            if _vak_result_is_ok(value):
                return value[1]
            raise VMError(f"फल unwrap असफल: {value}")

        def _vak_result_error(value):
            if _vak_result_is_err(value):
                return value[1]
            raise VMError(f"फल error access असफल: {value}")

        def _vak_match_pattern(value, pattern_spec):
            return self._match_pattern_spec(value, pattern_spec)

        def _vak_term(value=None):
            return VakTerm(self._coerce_runtime_term(value))

        def _build_term(spec):
            return VakTerm(self._build_term_from_spec(spec, frame=self.current_frame))

        def _make_parinama(name, rules_spec, scope=None):
            normalized_scope = None if scope is None else str(scope)
            return VakParinama(self, str(name), list(rules_spec or []), normalized_scope)

        # Timer functions wired to EventLoop (Fixed: async/await support)
        def _set_timeout(callback, delay_ms):
            """Set timeout - execute callback after delay (in milliseconds)."""
            loop = EventLoop.current()
            delay_sec = float(delay_ms) / 1000.0
            timer = loop.set_timeout(delay_sec, callback)
            return timer

        def _set_interval(callback, interval_ms):
            """Set interval - execute callback repeatedly at interval (in milliseconds)."""
            loop = EventLoop.current()
            interval_sec = float(interval_ms) / 1000.0
            timer = loop.set_interval(interval_sec, callback)
            return timer

        def _clear_timeout(timer):
            """Clear/cancel a timeout or interval timer."""
            loop = EventLoop.current()
            loop.clear_timeout(timer)
            return None

        def _async_sleep(seconds):
            """Async sleep - non-blocking sleep for coroutines."""
            loop = EventLoop.current()
            return loop.sleep(float(seconds))

        def _atma_wrap(val, bhav=None, avastha=None, note=None):
            # If the user passes 4 arguments, AtmaValue expects them, although AtmaValue might only take 3.
            # Let's check atmalipi/src/engine.py
            return AtmaValue(val, bhav, avastha)

        def _re_match(pattern, string):
            import re
            return bool(re.match(pattern, string))

        def _re_replace(pattern, repl, string):
            import re
            return re.sub(pattern, repl, string)

        def _json_encode(obj):
            import json
            return json.dumps(obj, ensure_ascii=False)

        def _json_decode(string):
            import json
            return json.loads(string)

        def _start_thread(func, args_list=None):
            import threading
            if args_list is None: args_list = []
            emit_audit_event("vak.thread.start", getattr(func, "__name__", repr(func)))
            
            def thread_main():
                try:
                    if isinstance(func, tuple) and func[0] == 'function':
                        # To run VakyaLang function in a thread, we need a new VM state
                        new_vm = VakVM()
                        new_vm.globals = self.globals
                        new_vm.builtins = self.builtins
                        new_vm.module_cache = self.module_cache
                        
                        func_name = func[1]
                        # Look for bytecode in the current module's functions
                        func_bc = self.frames[0].bytecode.functions.get(func_name)
                        if not func_bc:
                            # Try other modules
                            for f in self.frames:
                                if func_name in f.bytecode.functions:
                                    func_bc = f.bytecode.functions[func_name]
                                    break
                        
                        if func_bc:
                            # Manually setup the first frame
                            from .vm import CallFrame
                            new_frame = CallFrame(func_bc)
                            for i, val in enumerate(args_list):
                                if i < len(new_frame.locals):
                                    new_frame.locals[i] = val
                            new_vm.frames = [new_frame]
                            new_vm.current_frame = new_frame
                            new_vm._execute()
                    elif callable(func):
                        func(*args_list)
                except Exception as e:
                    print(f"Thread Error: {e}")

            t = threading.Thread(target=thread_main)
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

        # Chitrakala implementations - using *args for flexibility
        def _chitra_canvas_impl(*args):
            _require_chitra_support()
            w, h = int(args[0]), int(args[1])
            c = args[2] if len(args) > 2 else "white"
            return ChitraCanvas(w, h, _resolve_chitra_color(c))
        def _chitra_fill_impl(*args):
            _require_chitra_support()
            canv, c = args[0], args[1]
            canv.fill(_resolve_chitra_color(c))
        def _chitra_point_impl(*args):
            _require_chitra_support()
            canv, x, y = args[0], int(args[1]), int(args[2])
            c = args[3] if len(args) > 3 else "black"
            draw_point(canv, x, y, _resolve_chitra_color(c))
        def _chitra_line_impl(*args):
            _require_chitra_support()
            canv, x0, y0, x1, y1 = args[0], int(args[1]), int(args[2]), int(args[3]), int(args[4])
            c = args[5] if len(args) > 5 else "black"
            draw_line(canv, x0, y0, x1, y1, _resolve_chitra_color(c))
        def _chitra_circle_impl(*args):
            _require_chitra_support()
            canv, x, y, r = args[0], int(args[1]), int(args[2]), int(args[3])
            c = args[4] if len(args) > 4 else "black"
            fill = bool(args[5]) if len(args) > 5 else False
            draw_circle(canv, x, y, r, _resolve_chitra_color(c), fill)
        def _chitra_rect_impl(*args):
            _require_chitra_support()
            canv, x, y, w, h = args[0], int(args[1]), int(args[2]), int(args[3]), int(args[4])
            c = args[5] if len(args) > 5 else "black"
            fill = bool(args[6]) if len(args) > 6 else False
            draw_rectangle(canv, x, y, w, h, _resolve_chitra_color(c), fill)
        def _chitra_polygon_impl(*args):
            _require_chitra_support()
            canv, pts, c = args[0], args[1], args[2] if len(args) > 2 else "black"
            fill = bool(args[3]) if len(args) > 3 else False
            draw_polygon(canv, [(int(p[0]), int(p[1])) for p in pts], _resolve_chitra_color(c), fill)
        def _chitra_text_impl(*args):
            _require_chitra_support()
            canv, x, y, text = args[0], int(args[1]), int(args[2]), str(args[3])
            font_arg = args[4] if len(args) > 4 else None
            size = int(args[5]) if len(args) > 5 else 1
            c = args[6] if len(args) > 6 else "black"
            # Handle font argument - if it's a string, pass None (use default font)
            font = None if isinstance(font_arg, str) else font_arg
            draw_text(canv, x, y, text, _resolve_chitra_color(c), font, size)
            return canv
        def _chitra_text_centered_impl(*args):
            _require_chitra_support()
            canv, y, text = args[0], int(args[1]), str(args[2])
            color = args[3] if len(args) > 3 else "black"
            scale = int(args[4]) if len(args) > 4 else 1
            draw_text_centered(canv, y, text, _resolve_chitra_color(color), scale=scale)
            return canv
        def _chitra_save_impl(*args):
            _require_chitra_support()
            canv, path = args[0], str(args[1])
            save_png(canv, path)
        def _chitra_load_impl(*args):
            _require_chitra_support()
            path = str(args[0])
            return load_png(path)
        def _chitra_color_impl(*args):
            _require_chitra_support()
            return get_color(str(args[0]))
        def _chitra_colors_impl():
            _require_chitra_support()
            return list_colors()
        def _chitra_width_impl(*args):
            return args[0].width
        def _chitra_height_impl(*args):
            return args[0].height
        def _chitra_pixel_get_impl(*args):
            _require_chitra_support()
            canv, x, y = args[0], int(args[1]), int(args[2])
            return canv.get_pixel(x, y)
        def _chitra_pixel_set_impl(*args):
            _require_chitra_support()
            canv, x, y, c = args[0], int(args[1]), int(args[2]), args[3]
            canv.set_pixel(x, y, _resolve_chitra_color(c))
            return canv
        def _chitra_clear_impl(*args):
            _require_chitra_support()
            canv, c = args[0], args[1] if len(args) > 1 else "white"
            canv.fill(_resolve_chitra_color(c))
            return canv
        def _chitra_gradient_impl(*args):
            _require_chitra_support()
            # Horizontal gradient
            canv, c1, c2 = args[0], args[1], args[2]
            c1 = _resolve_chitra_color(c1)
            c2 = _resolve_chitra_color(c2)
            for x in range(canv.width):
                ratio = x / max(1, canv.width - 1)
                r = int(c1.r * (1 - ratio) + c2.r * ratio)
                g = int(c1.g * (1 - ratio) + c2.g * ratio)
                b = int(c1.b * (1 - ratio) + c2.b * ratio)
                for y in range(canv.height):
                    canv.set_pixel(x, y, ChitraColor(r, g, b))
            return canv
        def _chitra_rotate_impl(*args):
            _require_chitra_support()
            canv = args[0]
            angle = float(args[1]) if len(args) > 1 else 0.0
            center_x = int(args[2]) if len(args) > 2 else canv.width // 2
            center_y = int(args[3]) if len(args) > 3 else canv.height // 2
            return ChitraEffects.rotate(canv, angle, center_x, center_y)
        def _chitra_mandala_impl(*args):
            _require_chitra_support()
            canv = args[0]
            center_x = int(args[1]) if len(args) > 1 else canv.width // 2
            center_y = int(args[2]) if len(args) > 2 else canv.height // 2
            radius = int(args[3]) if len(args) > 3 else min(canv.width, canv.height) // 3
            petals = max(1, int(args[4])) if len(args) > 4 else 12
            palette = args[5] if len(args) > 5 else ["red", "green", "blue", "yellow"]
            ChitraEffects.mandala_pattern(
                canv,
                center_x,
                center_y,
                radius,
                petals,
                _resolve_chitra_palette(palette),
            )
            return canv
        def _chitra_kaleidoscope_impl(*args):
            _require_chitra_support()
            canv = args[0]
            segments = max(2, int(args[1])) if len(args) > 1 else 8
            return ChitraEffects.kaleidoscope(canv, segments)

        return {
            'None': None,
            'True': True,
            'False': False,
            'पाठ_कर': _vak_str,
            'str': str,
            'परास': range,
            'range': range,
            'दीर्घता': len,
            'len': len,
            'प्रकार': _vak_type,
            'type': type,
            'संख्या': int,
            'int': int,
            'दशमलव': float,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'set': set,
            'callable': lambda obj: isinstance(obj, tuple) and obj[0] in ('function', 'bound_method') or callable(obj),
            'enumerate': _vak_enumerate,
            'zip': _vak_zip,
            'map': _vak_map,
            'filter': _vak_filter,
            'isinstance': _vak_isinstance,
            'hasattr': _vak_hasattr,
            'all': all,
            'any': any,
            'chr': chr,
            'ord': ord,
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'sum': sum,
            'sorted': sorted,
            'मुद्रय': _vak_print,
            'print': _vak_print,
            'सिद्ध': _vak_result_ok,
            'असिद्ध': _vak_result_err,
            'फल_सफल_है': _vak_result_is_ok,
            'फल_विफल_है': _vak_result_is_err,
            'फल_खोलो': _vak_result_unwrap,
            'फल_त्रुटि': _vak_result_error,
            'पद': _vak_term,
            'term': _vak_term,
            '__build_term__': _build_term,
            '__make_parinama__': _make_parinama,
            '__match_exception__': _vak_match_exception,
            '__match_pattern__': _vak_match_pattern,
            'पठन': _read_file,
            'लेखन': _write_file,
            'खोलो': _open_file,
            'अस्तित्व': os.path.exists,
            'मिटाओ': _remove_path,
            'सूची_निर्देशिका': _list_dir,
            'बनाओ_निर्देशिका': _make_dir,
            'परिवेश_प्राप्त': _get_env,
            'परिवेश_सेट': _set_env,
            'प्रणाली_कमांड': _system_command,
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
            'परम': _math_abs,              # Fixed: Added परम (absolute value) for ganit module
            '_math_cos': _math_cos,
            '_math_sin': _math_sin,
            '_math_tan': _math_tan,
            '_math_sqrt': _math_sqrt,
            '_math_abs': _math_abs,
            '_math_floor': _math_floor,
            '_math_ceil': _math_ceil,
            '_math_round': _math_round,
            '_math_degrees': _math_degrees,
            '_math_radians': _math_radians,
            'जाल_लाओ': _http_get,
            'जाल_भेजो': _http_post,
            'जाल_पुट': _http_put,          # Fixed: Added HTTP PUT support
            'जाल_हटाओ': _http_delete,      # Fixed: Added HTTP DELETE support
            'जाल_डाउनलोड': _http_download,
            'समय': _get_time,
            'निद्रा': _sleep,
            'धागा_शुरू': _start_thread,
            'सेट_टाइमआउट': _set_timeout,     # Fixed: Wired to EventLoop
            'सेट_इंटरवल': _set_interval,     # Fixed: Wired to EventLoop
            'क्लियर_टाइमआउट': _clear_timeout, # Fixed: Wired to EventLoop
            'async_sleep': _async_sleep,      # Fixed: Wired to EventLoop
            'रेगेक्स_खोज': _re_match,
            'रेगेक्स_बदलो': _re_replace,
            'जेसन_लिखो': _json_encode,
            'जेसन_पढ़ो': _json_decode,
            'परिभाषय': lambda *args: _sansmatic.define(str(args[0]), args[1]),
            'दावा': lambda *args: _sansmatic.assert_fact(str(args[0]), str(args[1]), str(args[2]), str(args[3]) if len(args)>3 else None),
            'नियम': lambda *args: _sansmatic.rule((str(args[0]), str(args[1]), str(args[2])), (str(args[3]), str(args[4]), str(args[5]))),
            'मूल्यांकन': lambda *args: _sansmatic.evaluate(str(args[0]), str(args[1]), str(args[2])),
            'सिद्ध_है': lambda *args: _sansmatic.is_provable(str(args[0]), str(args[1]), str(args[2])),
            'प्रमाण_लॉग': lambda *args: _sansmatic.get_log(),
            'प्रमाण_रीसेट': lambda *args: _sansmatic.reset(),
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
            '_chitra_clear': lambda *args: _chitra_clear_impl(*args),
            '_chitra_text_centered': lambda *args: _chitra_text_centered_impl(*args),
            '_chitra_gradient': lambda *args: _chitra_gradient_impl(*args),
            '_chitra_rotate': lambda *args: _chitra_rotate_impl(*args),
            '_chitra_mandala': lambda *args: _chitra_mandala_impl(*args),
            '_chitra_kaleidoscope': lambda *args: _chitra_kaleidoscope_impl(*args),
            'पायथन_आयात': पायथन_आयात,
            'पायथन_चलाओ': पायथन_चलाओ,
            'पायथन_मूल्यांकन': पायथन_मूल्यांकन,
            'अक्षर_मान': ord,
            'अक्षर_कर': chr,
        }


    def run(self, bytecode: Bytecode) -> Any:
        """Execute bytecode and return result."""
        frame = CallFrame(bytecode)
        self.frames = [frame]
        self.current_frame = frame
        
        while True:
            try:
                return self._execute()
            except Exception as e:
                if self._handle_runtime_exception(e):
                    continue
                if isinstance(e, VMError):
                    raise
                trace = self._format_stack_trace()
                raise VMError(f"Internal VM Crash: {e}\n{trace}") from e


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
            # op_name = OPCODE_NAMES.get(op, f"UNKNOWN({op})")
            # print(f"TRACE: pc={frame.pc:04d} op={op_name:15} stack={frame.stack}")
            # -------------------
            
            if op == OpCode.HALT.value:
                break
                
            elif op == OpCode.LOAD_CONST.value:
                # 16-bit operand
                idx = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
                val = constants[idx]
                if isinstance(val, tuple) and len(val) >= 2 and val[0] in ('function', 'coroutine'):
                    func_name = val[1]
                    is_coroutine = val[0] == 'coroutine'  # Async function marker
                    func_bc = frame.bytecode.functions.get(func_name)
                    closure_env = self._capture_closure_env(frame, func_bc) if func_bc else {}

                    # Include is_async flag in the tuple for CALL handler
                    is_async = is_coroutine or getattr(func_bc, 'is_async', False)
                    val = ('function', func_name, closure_env, is_async)
                frame.stack.append(val)
                frame.pc += 3
                
            elif op == OpCode.LOAD_VAR.value:
                slot = code[frame.pc + 1]
                frame.stack.append(self._load_named_value(frame, slot))
                frame.pc += 2
                
            elif op == OpCode.STORE_VAR.value:
                slot = code[frame.pc + 1]
                val = self._pop()
                self._store_named_value(frame, slot, val)
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

            elif op == OpCode.CONTAINS.value:
                b = self._pop()
                a = self._pop()
                frame.stack.append(a in b)
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
            elif op in (OpCode.CALL.value, OpCode.CALL_KW.value):
                argc = code[frame.pc + 1]
                kwargs = self._normalize_kwargs(self._pop()) if op == OpCode.CALL_KW.value else {}
                args = [self._pop() for _ in range(argc)]
                args.reverse()
                func = self._pop()
                instruction_size = 2

                if isinstance(func, tuple) and func[0] == 'function':
                    func_name = func[1]
                    # Check 4th element for is_async flag (or lookup from bytecode)
                    is_async = func[3] if len(func) > 3 else False

                    if self.jit_enabled and self.jit:
                        self.jit.track_call(func_name)
                        if func_name in self.jit.compiled_functions:
                            compiled_func = self.jit.compiled_functions[func_name]
                            try:
                                result = compiled_func.execute(self.globals, *args, **kwargs)
                                self._push(result)
                                frame.pc += instruction_size
                                continue
                            except Exception as e:
                                trace = self._format_stack_trace()
                                raise VMError(f"Internal VM Crash: {e}\n{trace}")

                    func_bc = self._resolve_function_bytecode(func_name, func, frame)
                    if func_bc and not is_async:
                        is_async = getattr(func_bc, 'is_async', False)
                    
                    if func_bc:
                        # Also check bytecode is_async if not in tuple
                        if not is_async:
                            is_async = getattr(func_bc, 'is_async', False)
                        
                        # Check if this is an async function - if so, create coroutine wrapper
                        if is_async:
                            # Create coroutine but don't execute - return it to caller
                            new_frame = CallFrame(func_bc)
                            self._bind_call_arguments(new_frame, func_bc, args, kwargs)
                            if len(func) >= 3:
                                self._hydrate_closure_locals(new_frame, func[2])

                            # Create and return coroutine
                            coroutine = VakCoroutine(new_frame, func_bc)
                            self._push(coroutine)
                            frame.pc += instruction_size
                            continue
                        else:
                            # Regular synchronous function - execute normally
                            new_frame = CallFrame(func_bc)
                            self._bind_call_arguments(new_frame, func_bc, args, kwargs)
                            if len(func) >= 3:
                                self._hydrate_closure_locals(new_frame, func[2])
                            frame.pc += instruction_size
                            self.frames.append(new_frame)
                            self.current_frame = new_frame
                            frame = new_frame
                            code = frame.bytecode.code
                            constants = frame.bytecode.constants
                            frame.pc = 0
                            continue
                    else: raise VMError(f"Function not found: {func_name}")

                elif isinstance(func, VakClass):
                    instance = VakInstance(func)
                    constructor_name = self._get_constructor_name(func)
                    if constructor_name:
                        func_bc = func.methods[constructor_name]
                        new_frame = CallFrame(func_bc, is_constructor=True)
                        self._bind_call_arguments(new_frame, func_bc, args, kwargs, self_obj=instance)
                        closure_env = self._get_method_closure_env(func, constructor_name)
                        if closure_env is not None:
                            self._hydrate_closure_locals(new_frame, closure_env)
                        frame.pc += instruction_size
                        self.frames.append(new_frame)
                        self.current_frame = new_frame
                        frame = new_frame
                        code = frame.bytecode.code
                        constants = frame.bytecode.constants
                        frame.pc = 0
                        continue
                    else:
                        self._push(instance)
                        frame.pc += instruction_size
                        continue

                elif isinstance(func, tuple) and func[0] == 'bound_method':
                    obj, method_name = func[1], func[2]
                    if isinstance(obj, VakInstance):
                        func_bc = obj.klass.methods.get(method_name)
                        if func_bc:
                            new_frame = CallFrame(func_bc)
                            self._bind_call_arguments(new_frame, func_bc, args, kwargs, self_obj=obj)
                            closure_env = self._get_method_closure_env(obj.klass, method_name)
                            if closure_env is not None:
                                self._hydrate_closure_locals(new_frame, closure_env)
                            frame.pc += instruction_size
                            self.frames.append(new_frame)
                            self.current_frame = new_frame
                            frame = new_frame
                            code = frame.bytecode.code
                            constants = frame.bytecode.constants
                            frame.pc = 0
                            continue
                    raise VMError(f"Cannot call bound method {method_name}")

                elif callable(func):
                    try:
                        result = func(*args, **kwargs)
                        self._push(result)
                        frame.pc += instruction_size
                        continue
                    except Exception as e: raise VMError(f"Error calling builtin: {e}")
                else: raise VMError(f"Object not callable: {type(func).__name__}")
            elif op == OpCode.RETURN.value:
                result = self._pop()
                is_ctor = frame.is_constructor
                if is_ctor:
                    result = frame.locals[0] # Return the instance instead
                result = self._enforce_vibhakti_return(frame, result)
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
                result = self._enforce_vibhakti_return(frame, result)
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
                method_envs = {}
                class_namespace = {}

                if hasattr(frame, 'locals'):
                    for i, name in enumerate(frame.bytecode.var_names):
                        if i < len(frame.locals) and frame.locals[i] is not UNSET:
                            class_namespace[name] = frame.locals[i]

                for name, value in self.globals.items():
                    class_namespace.setdefault(name, value)
                
                # Copy methods from parent if inheritance is used
                if parent_class and isinstance(parent_class, VakClass):
                    methods.update(parent_class.methods)
                    method_envs.update(getattr(parent_class, 'method_envs', {}))
                    
                if class_bc:
                    for m_name, m_bc in class_bc.functions.items():
                        methods[m_name] = m_bc
                        method_envs[m_name] = class_namespace
                
                vak_class = VakClass(class_name, methods, method_envs)
                class_namespace[class_name] = vak_class
                frame.stack.append(vak_class)
                frame.pc += 1

            elif op in (OpCode.CALL_METHOD.value, OpCode.CALL_METHOD_KW.value):
                # Format: CALL_METHOD argc
                argc = code[frame.pc + 1]
                kwargs = self._normalize_kwargs(self._pop()) if op == OpCode.CALL_METHOD_KW.value else {}
                args = [self._pop() for _ in range(argc)]
                args.reverse()
                method_name = self._pop()
                obj = self._pop()
                instruction_size = 2
                
                if isinstance(obj, VakInstance):
                    if method_name in obj.klass.methods:
                        func_bc = obj.klass.methods[method_name]
                        new_frame = CallFrame(func_bc)
                        self._bind_call_arguments(new_frame, func_bc, args, kwargs, self_obj=obj)
                        closure_env = self._get_method_closure_env(obj.klass, method_name)
                        if closure_env is not None:
                            self._hydrate_closure_locals(new_frame, closure_env)
                        frame.pc += instruction_size
                        self.frames.append(new_frame)
                        self.current_frame = new_frame
                        frame = new_frame
                        code = frame.bytecode.code
                        constants = frame.bytecode.constants
                        frame.pc = 0
                        continue
                    elif method_name == '__enter__':
                        frame.stack.append(obj)
                        frame.pc += instruction_size
                        continue
                    else:
                        raise VMError(f"Method '{method_name}' not found on {obj.klass.name}")
                elif isinstance(obj, VakModule):
                    if method_name in obj.attrs:
                        func = obj.attrs[method_name]

                        if isinstance(func, tuple) and func[0] == 'function':
                            func_name = func[1]
                            func_bc = self._resolve_function_bytecode(func_name, func, frame)
                            if func_bc:
                                new_frame = CallFrame(func_bc)
                                self._bind_call_arguments(new_frame, func_bc, args, kwargs)
                                if len(func) >= 3:
                                    self._hydrate_closure_locals(new_frame, func[2])
                                            
                                frame.pc += instruction_size
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
                            frame.pc += instruction_size
                            
                            constructor_name = self._get_constructor_name(func)
                            if constructor_name:
                                func_bc = func.methods[constructor_name]
                                new_frame = CallFrame(func_bc, is_constructor=True)
                                self._bind_call_arguments(new_frame, func_bc, args, kwargs, self_obj=instance)
                                closure_env = self._get_method_closure_env(func, constructor_name)
                                if closure_env is not None:
                                    self._hydrate_closure_locals(new_frame, closure_env)
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
                        elif callable(func):
                            result = func(*args, **kwargs)
                            frame.stack.append(result)
                            frame.pc += instruction_size
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
                        result = func(*args, **kwargs)
                        frame.stack.append(result)
                        frame.pc += instruction_size
                    elif method_name == '__enter__':
                        frame.stack.append(obj)
                        frame.pc += instruction_size
                    else:
                        raise VMError(f"Object {type(obj).__name__} has no method {method_name}")

            # ── Data Structures ─────────────────────────────────────────────────
            elif op == OpCode.BUILD_LIST.value:
                count = code[frame.pc + 1]
                elements = [self._pop() for _ in range(count)]
                elements.reverse()
                frame.stack.append(elements)
                frame.pc += 2

            elif op == OpCode.BUILD_TUPLE.value:
                count = code[frame.pc + 1]
                elements = [self._pop() for _ in range(count)]
                elements.reverse()
                frame.stack.append(tuple(elements))
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
                self._enforce_vibhakti_object_mutation(frame, obj)
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
                self._enforce_vibhakti_object_mutation(frame, obj)
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
                if self._handle_runtime_exception(exception_val):
                    frame = self.current_frame
                    code = frame.bytecode.code
                    constants = frame.bytecode.constants
                    continue
                else:
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

                import os
                from runtime.src.lexer import Lexer
                from runtime.src.parser import Parser
                from runtime.src.compiler import Compiler

                resolved_module_name, target_path = self._resolve_module_path(module_name, frame)
                emit_audit_event(
                    "vak.import.module",
                    str(module_name),
                    resolved_module_name,
                    target_path,
                )
                cache_key = os.path.normcase(os.path.abspath(target_path))
                cached_module = self.module_cache.get(cache_key)
                if cached_module is not None:
                    frame.stack.append(cached_module)
                    frame.pc += 3
                    continue
                
                # Compile and execute the module in isolation
                with open(target_path, 'r', encoding='utf-8') as f:
                    source = f.read()

                lexer = Lexer(source)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                ast = parser.parse()
                compiler = Compiler()
                module_bytecode = compiler.compile(ast)
                module_bytecode.source_path = target_path
                defined_function_names = set(module_bytecode.functions.keys())

                # CRITICAL FIX: Pre-populate module_env with function stubs BEFORE running
                # This allows module functions to call each other during execution.
                # Without this, when विचरण calls माध्य internally, माध्य returns None.
                module_env = {}

                # Store module bytecode in module_env for runtime function lookup
                # This is essential for module function cross-references when called from outside
                module_env['__bytecode__'] = module_bytecode

                # Pre-create function tuples for source-defined top-level callables.
                for fn_name in defined_function_names:
                    fn_bc = module_bytecode.functions[fn_name]
                    is_async = getattr(fn_bc, 'is_async', False)
                    # Create a self-referential environment - will be fully populated after exec
                    module_env[fn_name] = ('function', fn_name, module_env, is_async)

                mod_obj = VakModule(module_name, {})
                self.module_cache[cache_key] = mod_obj

                # Run the module to populate its frame
                # Functions will now capture module_env in their closure, enabling cross-calls
                module_vm = VakVM()
                module_vm.suppress_output = True
                module_vm.module_cache = self.module_cache
                # Run without halting the main VM
                try:
                    module_vm.run(module_bytecode)
                except Exception as e:
                    self.module_cache.pop(cache_key, None)
                    trace = self._format_stack_trace()
                    raise VMError(f"Error executing module '{module_name}': {e}\n{trace}")

                # Extract the top-level globals that were defined
                exported_attrs = {}
                exportable_names = {
                    name for name in module_bytecode.var_names
                    if not self._is_internal_binding_name(name)
                }

                # Check shared globals - merge with pre-populated module_env
                for name, value in module_vm.globals.items():
                    if self._is_internal_binding_name(name):
                        continue
                    exported_attrs[name] = self._unwrap_cell(value)
                module_env.update(module_vm.globals)

                # Check local slots
                module_frame = module_vm.frames[0] if module_vm.frames else module_vm.current_frame
                if module_frame and hasattr(module_frame, 'locals'):
                    for i, name in enumerate(module_bytecode.var_names):
                        if i < len(module_frame.locals) and module_frame.locals[i] is not UNSET:
                            raw_value = module_frame.locals[i]
                            module_env[name] = raw_value
                            if not self._is_internal_binding_name(name):
                                exported_attrs[name] = self._unwrap_cell(raw_value)

                # CRITICAL FIX: Update function tuples in module_frame.locals to include __bytecode__
                # This ensures that when module functions call each other internally, they can find bytecode
                if module_frame and hasattr(module_frame, 'locals'):
                    for i, name in enumerate(module_bytecode.var_names):
                        if i < len(module_frame.locals):
                            val = module_frame.locals[i]
                            if isinstance(val, Cell):
                                val = val.value
                            if isinstance(val, tuple) and len(val) >= 3 and val[0] == 'function':
                                func_name = val[1]
                                if func_name not in defined_function_names:
                                    continue
                                closure_env = val[2]
                                if isinstance(closure_env, dict):
                                    closure_env['__bytecode__'] = module_bytecode

                # Update module_env with actual function tuples from executed module
                # The pre-created tuples already have correct structure, just ensure is_async is correct
                for fn_name in defined_function_names:
                    fn_bc = module_bytecode.functions[fn_name]
                    if fn_name not in exportable_names:
                        continue
                    is_async = getattr(fn_bc, 'is_async', False)
                    existing = self._unwrap_cell(module_env.get(fn_name))
                    if existing is not None and not (
                        isinstance(existing, tuple) and len(existing) >= 1 and existing[0] == 'function'
                    ):
                        continue
                    module_env[fn_name] = ('function', fn_name, module_env, is_async)

                # Add module functions to exported attributes
                for fn_name in defined_function_names:
                    fn_bc = module_bytecode.functions[fn_name]
                    if fn_name not in exportable_names:
                        continue
                    existing = self._unwrap_cell(exported_attrs.get(fn_name))
                    if existing is not None and not (
                        isinstance(existing, tuple) and len(existing) >= 1 and existing[0] == 'function'
                    ):
                        continue
                    is_async = getattr(fn_bc, 'is_async', False)
                    func_tuple = ('function', fn_name, module_env, is_async)
                    exported_attrs[fn_name] = func_tuple

                mod_obj.name = resolved_module_name
                mod_obj.attrs.clear()
                mod_obj.attrs.update(exported_attrs)
                frame.stack.append(mod_obj)
                frame.pc += 3

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
                Raises if the embedded certificate is invalid or tampered.
                """
                proof_idx = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
                frame.pc += 3
                
                certificate = constants[proof_idx] if proof_idx < len(constants) else ""
                from .nyaya_verifier import NyayaProofVerifier

                valid = NyayaProofVerifier.verify_certificate_payload(certificate)
                if not valid:
                    raise VMError("Invalid or tampered proof certificate")
                frame.stack.append(True)

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
                self._print_value(val)
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

    def _execute_single_frame(self, frame: CallFrame) -> Any:
        """
        Execute a single frame until it completes or suspends.
        
        This is used by the event loop to run coroutines.
        Unlike _execute(), this handles SUSPEND when hitting AWAIT.
        
        Args:
            frame: CallFrame to execute
            
        Returns:
            Result value if completed, SUSPEND if suspended
        """
        code = frame.bytecode.code
        constants = frame.bytecode.constants
        
        while frame.pc < len(code):
            op = code[frame.pc]
            
            if op == OpCode.HALT.value:
                # Frame completed without return
                if frame.stack:
                    return frame.stack[-1]
                return None
                
            elif op == OpCode.RETURN.value:
                result = self._enforce_vibhakti_return(frame, frame.stack.pop())
                return result
                
            elif op == OpCode.RETURN_VOID.value:
                return self._enforce_vibhakti_return(frame, None)
                
            elif op == OpCode.AWAIT.value:
                # Hit await - suspend execution
                return SUSPEND
            
            # ── Load/Store ──────────────────────────────────────────────────────
            elif op == OpCode.LOAD_CONST.value:
                idx = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
                val = constants[idx]
                frame.stack.append(val)
                frame.pc += 3
                
            elif op == OpCode.LOAD_VAR.value:
                slot = code[frame.pc + 1]
                frame.stack.append(self._load_named_value(frame, slot))
                frame.pc += 2
                
            elif op == OpCode.STORE_VAR.value:
                slot = code[frame.pc + 1]
                val = frame.stack.pop()
                self._store_named_value(frame, slot, val)
                frame.pc += 2
                
            elif op == OpCode.POP.value:
                frame.stack.pop()
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
            
            # ── Comparison ──────────────────────────────────────────────────────
            elif op == OpCode.EQ.value:
                b = frame.stack.pop()
                a = frame.stack.pop()
                frame.stack.append(a == b)
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
            
            # ── Control Flow ────────────────────────────────────────────────────
            elif op == OpCode.JUMP.value:
                offset = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
                if offset > 32767:
                    offset -= 65536
                frame.pc += 3 + offset
                
            elif op == OpCode.JUMP_IF_FALSE.value:
                offset = (code[frame.pc + 1] << 8) | code[frame.pc + 2]
                if offset > 32767:
                    offset -= 65536
                cond = frame.stack.pop()
                if not cond:
                    frame.pc += 3 + offset
                else:
                    frame.pc += 3
            
            # ── Functions ───────────────────────────────────────────────────────
            elif op in (OpCode.CALL.value, OpCode.CALL_KW.value):
                argc = code[frame.pc + 1]
                kwargs = frame.stack.pop() if op == OpCode.CALL_KW.value else {}
                args = [frame.stack.pop() for _ in range(argc)]
                args.reverse()
                func = frame.stack.pop()
                
                if callable(func):
                    result = func(*args, **kwargs)
                    frame.stack.append(result)
                else:
                    frame.stack.append(None)  # Can't call this
                frame.pc += 2
                
            # ── I/O ──────────────────────────────────────────────────────────────
            elif op == OpCode.PRINT.value:
                val = frame.stack.pop()
                self._print_value(val)
                frame.pc += 1
            
            else:
                # Unknown opcode - skip
                frame.pc += 1
                
        # End of bytecode without explicit return
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
                result = self._enforce_vibhakti_return(frame, frame.stack.pop())
                coroutine.result = result
                coroutine.completed = True
                coroutine.suspended = False
                self.frames.pop()
                self.current_frame = parent_frame
                return result
            
            elif op == OpCode.RETURN_VOID.value:
                coroutine.result = self._enforce_vibhakti_return(frame, None)
                coroutine.completed = True
                coroutine.suspended = False
                self.frames.pop()
                self.current_frame = parent_frame
                return coroutine.result
            
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
                func_bc = frame.bytecode.functions.get(val[1])
                closure_env = self._capture_closure_env(frame, func_bc) if func_bc else {}
                val = ('function', val[1], closure_env)
            frame.stack.append(val)
            frame.pc += 3

        elif op == OpCode.LOAD_VAR.value:
            slot = code[frame.pc + 1]
            frame.stack.append(self._load_named_value(frame, slot))
            frame.pc += 2

        elif op == OpCode.STORE_VAR.value:
            slot = code[frame.pc + 1]
            val = frame.stack.pop()
            self._store_named_value(frame, slot, val)
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

        elif op == OpCode.CONTAINS.value:
            b = frame.stack.pop()
            a = frame.stack.pop()
            frame.stack.append(a in b)
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
            self._print_value(val)
            frame.pc += 1

        elif op == OpCode.BUILD_LIST.value:
            count = code[frame.pc + 1]
            elements = [frame.stack.pop() for _ in range(count)]
            elements.reverse()
            frame.stack.append(elements)
            frame.pc += 2

        elif op == OpCode.BUILD_TUPLE.value:
            count = code[frame.pc + 1]
            elements = [frame.stack.pop() for _ in range(count)]
            elements.reverse()
            frame.stack.append(tuple(elements))
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
            self._enforce_vibhakti_object_mutation(frame, obj)
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
            self._enforce_vibhakti_object_mutation(frame, obj)
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
            if not self._handle_runtime_exception(exception_val):
                raise VMError(f"Unhandled exception: {exception_val}")
            frame = self.current_frame

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
