# वाक् भाषा - JIT कंपाइलर (Just-In-Time Compiler)
# Vak Language - JIT Compilation for Hot Code Paths
#
# ═══════════════════════════════════════════════════════════════════════════
# Signature: Visionary RM (Raj Mitra) ⚡
# "JIT Compilation for Performance Optimization" 🔥
# ═══════════════════════════════════════════════════════════════════════════
#
# Month 2-3 Advanced Features: JIT Compilation
# - Tracks hot functions (call count threshold)
# - Compiles to native Python bytecode
# - Caches compiled functions for reuse
# - Performance profiling integration
#
# © 2026 Raj Mitra (Visionary RM)

from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
import os
import time
import hashlib

from .bytecode import NO_DEFAULT
from .opcodes import OpCode, OPCODE_NAMES


_JIT_UNBOUND = object()

_OPERAND_16BIT = {
    OpCode.LOAD_CONST.value,
    OpCode.CALL_BUILTIN.value,
    OpCode.JUMP.value,
    OpCode.JUMP_IF_TRUE.value,
    OpCode.JUMP_IF_FALSE.value,
}

_OPERAND_8BIT = {
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
}

_SUPPORTED_OPCODES = {
    OpCode.LOAD_CONST.value,
    OpCode.LOAD_VAR.value,
    OpCode.STORE_VAR.value,
    OpCode.POP.value,
    OpCode.DUP.value,
    OpCode.SWAP.value,
    OpCode.ADD.value,
    OpCode.SUB.value,
    OpCode.MUL.value,
    OpCode.DIV.value,
    OpCode.MOD.value,
    OpCode.POW.value,
    OpCode.NEG.value,
    OpCode.IDIV.value,
    OpCode.BAND.value,
    OpCode.BOR.value,
    OpCode.BXOR.value,
    OpCode.BNOT.value,
    OpCode.LSHIFT.value,
    OpCode.RSHIFT.value,
    OpCode.EQ.value,
    OpCode.NEQ.value,
    OpCode.LT.value,
    OpCode.GT.value,
    OpCode.LTE.value,
    OpCode.GTE.value,
    OpCode.CONTAINS.value,
    OpCode.AND.value,
    OpCode.OR.value,
    OpCode.NOT.value,
    OpCode.JUMP.value,
    OpCode.JUMP_IF_TRUE.value,
    OpCode.JUMP_IF_FALSE.value,
    OpCode.BUILD_LIST.value,
    OpCode.BUILD_DICT.value,
    OpCode.BUILD_SET.value,
    OpCode.BUILD_TUPLE.value,
    OpCode.UNPACK_SEQUENCE.value,
    OpCode.RETURN.value,
    OpCode.RETURN_VOID.value,
    OpCode.HALT.value,
}


class JITCompilationRejected(RuntimeError):
    """Raised when a function is outside the safe experimental JIT subset."""


@dataclass(frozen=True)
class DecodedInstruction:
    offset: int
    opcode_value: int
    opcode_name: str
    operand: Optional[int]
    size: int

    @property
    def next_offset(self) -> int:
        return self.offset + self.size

    @property
    def jump_target(self) -> Optional[int]:
        if self.opcode_value not in {
            OpCode.JUMP.value,
            OpCode.JUMP_IF_TRUE.value,
            OpCode.JUMP_IF_FALSE.value,
        }:
            return None
        offset = int(self.operand or 0)
        if offset > 32767:
            offset -= 65536
        return self.next_offset + offset


@dataclass
class FunctionStats:
    """Statistics for a function."""
    name: str
    call_count: int = 0
    total_time: float = 0.0
    compiled: bool = False
    compiled_time: Optional[float] = None
    
    @property
    def avg_time(self) -> float:
        """Average execution time."""
        if self.call_count == 0:
            return 0.0
        return self.total_time / self.call_count
    
    @property
    def is_hot(self) -> bool:
        """Check if function is hot under the default threshold heuristic."""
        return self.call_count >= JITCompiler.DEFAULT_THRESHOLD


@dataclass
class CompiledFunction:
    """A compiled function with native Python code."""
    name: str
    python_code: str
    compiled_obj: Any  # Compiled Python code object
    compiled_callable: Callable[..., Any]
    constants: List[Any]
    var_names: List[str]
    param_names: List[str]
    defaults: List[Any]
    num_params: int
    varargs_name: Optional[str]
    compile_time: float
    
    def _bind_locals(self, *args, **kwargs) -> list[Any]:
        locals_list = [_JIT_UNBOUND] * len(self.var_names)
        param_names = list(self.param_names or self.var_names[: self.num_params])
        if len(param_names) < self.num_params:
            param_names.extend(
                self.var_names[len(param_names) : self.num_params]
            )
        else:
            param_names = param_names[: self.num_params]

        if len(args) > self.num_params and not self.varargs_name:
            raise TypeError(
                f"{self.name} expected at most {self.num_params} args, got {len(args)}"
            )

        slot_map = {
            name: self.var_names.index(name)
            for name in param_names
            if name in self.var_names
        }
        defaults = list(self.defaults or [])
        if len(defaults) < self.num_params:
            defaults = [NO_DEFAULT] * (self.num_params - len(defaults)) + defaults
        else:
            defaults = defaults[: self.num_params]

        remaining_kwargs = dict(kwargs)

        for local_index, name in enumerate(param_names):
            slot = slot_map.get(name, local_index)
            if local_index < len(args):
                locals_list[slot] = args[local_index]
                remaining_kwargs.pop(name, None)
                continue
            if name in remaining_kwargs:
                locals_list[slot] = remaining_kwargs.pop(name)
                continue
            default = defaults[local_index] if local_index < len(defaults) else NO_DEFAULT
            if default is not NO_DEFAULT:
                locals_list[slot] = default
                continue
            raise TypeError(f"Missing required argument: {name}")

        if remaining_kwargs:
            unexpected = ", ".join(sorted(remaining_kwargs))
            raise TypeError(f"Unexpected keyword arguments for {self.name}: {unexpected}")

        if self.varargs_name:
            if self.varargs_name not in self.var_names:
                raise TypeError(f"Invalid varargs slot for {self.name}")
            varargs_slot = self.var_names.index(self.varargs_name)
            locals_list[varargs_slot] = list(args[self.num_params :])

        return locals_list

    def execute(self, globals_dict: Dict[str, Any], *args, **kwargs) -> Any:
        """Execute the compiled function."""
        locals_list = self._bind_locals(*args, **kwargs)
        return self.compiled_callable(self.constants, locals_list, globals_dict, _JIT_UNBOUND)


class JITCompiler:
    """
    Just-In-Time compiler for hot code paths.
    
    Uses Python's eval/exec for hot functions.
    
    Features:
    - Call counting and threshold detection
    - Bytecode to Python translation
    - Function caching
    - Performance statistics
    
    Usage:
        jit = JITCompiler()
        
        # Track function calls
        jit.track_call("my_function")
        
        # When function becomes hot, it's automatically compiled
        if jit.is_hot("my_function"):
            compiled = jit.compile_function(bytecode, globals)
    
    Architecture:
    1. Call Counter: Tracks how many times each function is called
    2. Hot Detector: Identifies functions that exceed threshold
    3. Translator: Converts Vak bytecode to Python code
    4. Compiler: Compiles Python code to bytecode
    5. Executor: Runs compiled code with optimized performance
    """
    
    DEFAULT_THRESHOLD = 100  # Compile after 100 calls
    EXPERIMENTAL_RUNTIME_ENV = "VAK_EXPERIMENTAL_JIT"
    
    def __init__(self, threshold: int = None, *, experimental_runtime: Optional[bool] = None):
        """
        Initialize JIT compiler.
        
        Args:
            threshold: Call count threshold for compilation
        """
        self.call_threshold = threshold or self.DEFAULT_THRESHOLD
        self.function_stats: Dict[str, FunctionStats] = {}
        self.compiled_functions: Dict[str, CompiledFunction] = {}
        self.rejected_functions: Dict[str, str] = {}
        self.benchmark_results: Dict[str, Dict[str, Any]] = {}
        self.enabled = True
        self.verbose = False
        if experimental_runtime is None:
            flag = os.getenv(self.EXPERIMENTAL_RUNTIME_ENV, "")
            experimental_runtime = flag.strip().lower() in {"1", "true", "yes", "on"}
        self.experimental_runtime = bool(experimental_runtime)
    
    def track_call(self, func_name: str, execution_time: float = 0.0):
        """
        Track function call count.
        
        Args:
            func_name: Function name
            execution_time: Time taken to execute (optional)
        
        Returns:
            True if function is now hot and should be compiled
        """
        if not self.enabled:
            return False
        
        if func_name not in self.function_stats:
            self.function_stats[func_name] = FunctionStats(name=func_name)
        
        stats = self.function_stats[func_name]
        stats.call_count += 1
        stats.total_time += execution_time
        
        # Check if function just became hot
        if stats.call_count >= self.call_threshold and not stats.compiled:
            if self.verbose:
                print(f"🔥 Function '{func_name}' is now HOT ({stats.call_count} calls)")
            return True
        
        return False
    
    def is_hot(self, func_name: str) -> bool:
        """Check if function is hot."""
        if func_name not in self.function_stats:
            return False
        return self.function_stats[func_name].call_count >= self.call_threshold

    @property
    def runtime_enabled(self) -> bool:
        """Whether compiled functions may execute in the VM."""
        return self.enabled and self.experimental_runtime

    def should_attempt_compile(self, func_name: str) -> bool:
        """Return True when a hot function should be compiled for runtime execution."""
        return (
            self.runtime_enabled
            and self.is_hot(func_name)
            and func_name not in self.compiled_functions
            and func_name not in self.rejected_functions
        )
    
    def compile_function(self, func_name: str, bytecode: Any, 
                        constants: List[Any]) -> Optional[CompiledFunction]:
        """
        Compile a hot function to native Python.
        
        Args:
            func_name: Function name
            bytecode: Vak bytecode object
            constants: List of constants
        
        Returns:
            CompiledFunction object or None if compilation failed
        """
        if not self.enabled:
            return None
        
        start_time = time.time()
        
        try:
            decoded = self._decode_instructions(bytecode)
            self._validate_supported_bytecode(func_name, bytecode, decoded)

            # Translate bytecode to Python
            python_code = self._bytecode_to_python(decoded, func_name, bytecode)
            
            # Compile Python code
            compiled_obj = compile(python_code, f'<jit:{func_name}>', 'exec')
            namespace: dict[str, Any] = {"__builtins__": __builtins__}
            exec(compiled_obj, namespace)
            compiled_callable = namespace["jit_function"]
            
            compile_time = time.time() - start_time
            
            # Create compiled function
            compiled_func = CompiledFunction(
                name=func_name,
                python_code=python_code,
                compiled_obj=compiled_obj,
                compiled_callable=compiled_callable,
                constants=constants,
                var_names=list(getattr(bytecode, "var_names", []) or []),
                param_names=list(getattr(bytecode, "param_names", []) or []),
                defaults=list(getattr(bytecode, "defaults", []) or []),
                num_params=int(getattr(bytecode, "num_params", 0) or 0),
                varargs_name=getattr(bytecode, "varargs_name", None),
                compile_time=compile_time
            )
            
            self.compiled_functions[func_name] = compiled_func
            self.rejected_functions.pop(func_name, None)
            
            # Update stats
            if func_name in self.function_stats:
                self.function_stats[func_name].compiled = True
                self.function_stats[func_name].compiled_time = compile_time
            
            if self.verbose:
                print(f"✓ Compiled '{func_name}' in {compile_time*1000:.2f}ms")
            
            return compiled_func
            
        except JITCompilationRejected as e:
            self.rejected_functions[func_name] = str(e)
            if self.verbose:
                print(f"⚠ JIT rejected '{func_name}': {e}")
            return None
        except Exception as e:
            self.rejected_functions[func_name] = f"compile failure: {e}"
            if self.verbose:
                print(f"✗ Compilation failed for '{func_name}': {e}")
            return None

    def reject_runtime_function(self, func_name: str, reason: str) -> None:
        """Demote a compiled function after a runtime mismatch or crash."""
        self.compiled_functions.pop(func_name, None)
        self.rejected_functions[func_name] = f"runtime fallback: {reason}"
        if func_name in self.function_stats:
            self.function_stats[func_name].compiled = False

    def _decode_instructions(self, bytecode: Any) -> List[DecodedInstruction]:
        """Decode bytecode using the real instruction schema."""
        if hasattr(bytecode, 'code'):
            code = list(bytecode.code)
        elif hasattr(bytecode, 'instructions'):
            code = list(bytecode.instructions)
        elif isinstance(bytecode, list):
            code = list(bytecode)
        else:
            raise JITCompilationRejected("unsupported bytecode container")

        instructions: List[DecodedInstruction] = []
        i = 0
        while i < len(code):
            op_value = code[i]
            op_name = OPCODE_NAMES.get(op_value, f"UNKNOWN({op_value:02X})")
            if op_value in _OPERAND_16BIT:
                if i + 2 >= len(code):
                    raise JITCompilationRejected(
                        f"truncated 16-bit operand for {op_name} at offset {i}"
                    )
                operand = (code[i + 1] << 8) | code[i + 2]
                size = 3
            elif op_value in _OPERAND_8BIT:
                if i + 1 >= len(code):
                    raise JITCompilationRejected(
                        f"truncated operand for {op_name} at offset {i}"
                    )
                operand = code[i + 1]
                size = 2
            else:
                operand = None
                size = 1
            instructions.append(
                DecodedInstruction(
                    offset=i,
                    opcode_value=op_value,
                    opcode_name=op_name,
                    operand=operand,
                    size=size,
                )
            )
            i += size
        return instructions

    def _validate_supported_bytecode(
        self,
        func_name: str,
        bytecode: Any,
        instructions: List[DecodedInstruction],
    ) -> None:
        """Reject functions outside the safe experimental subset."""
        if getattr(bytecode, "is_async", False):
            raise JITCompilationRejected("async functions are not supported")
        if getattr(bytecode, "closure_names", set()) or getattr(bytecode, "nonlocal_names", set()):
            raise JITCompilationRejected("closures/nonlocal bindings are not supported")
        if getattr(bytecode, "global_names", set()):
            raise JITCompilationRejected("global writes are not supported")
        if getattr(bytecode, "vibhakti_signature", None) is not None:
            raise JITCompilationRejected("vibhakti runtime contracts are not supported")
        if dict(getattr(bytecode, "type_hints", {}) or {}):
            raise JITCompilationRejected("runtime type-hint enforcement is not supported")

        for const in list(getattr(bytecode, "constants", []) or []):
            if isinstance(const, tuple) and const and const[0] in {"function", "coroutine"}:
                raise JITCompilationRejected("callable constants are not supported")

        valid_offsets = {instruction.offset for instruction in instructions}
        valid_terminal_offsets = valid_offsets | {len(getattr(bytecode, "code", []) or [])}

        for instruction in instructions:
            if instruction.opcode_value not in _SUPPORTED_OPCODES:
                raise JITCompilationRejected(
                    f"unsupported opcode {instruction.opcode_name} at offset {instruction.offset}"
                )
            target = instruction.jump_target
            if target is not None and target not in valid_terminal_offsets:
                raise JITCompilationRejected(
                    f"invalid jump target {target} from offset {instruction.offset}"
                )

        if not instructions:
            raise JITCompilationRejected(f"{func_name} has no instructions")

    def _bytecode_to_python(
        self,
        instructions: List[DecodedInstruction],
        func_name: str,
        bytecode: Any,
    ) -> str:
        """
        Translate Vak bytecode to Python code.
        
        Args:
            bytecode: Vak bytecode object
            func_name: Function name
        
        Returns:
            Python code string
        """
        lines = [
            f"# JIT-compiled function: {func_name}",
            f"# Generated at: {time.time()}",
            "def jit_function(constants, locals_, _globals, UNBOUND):",
            "    stack = []",
            "    pc = 0",
            "    while True:",
        ]

        for index, instruction in enumerate(instructions):
            head = "if" if index == 0 else "elif"
            lines.append(f"        {head} pc == {instruction.offset}:")
            translated = self._translate_instruction(instruction, bytecode)
            for item in translated:
                lines.append(f"            {item}")

        lines.append(
            f"        raise RuntimeError('Invalid JIT program counter for {func_name}: ' + str(pc))"
        )
        return "\n".join(lines)

    def _translate_instruction(self, instruction: DecodedInstruction, bytecode: Any) -> List[str]:
        """
        Translate single instruction to Python.
        """
        op_value = instruction.opcode_value
        operand = instruction.operand
        next_pc = instruction.next_offset

        if op_value == OpCode.LOAD_CONST.value:
            return [f"stack.append(constants[{operand}])", f"pc = {next_pc}", "continue"]

        if op_value == OpCode.LOAD_VAR.value:
            slot = int(operand or 0)
            name = (
                getattr(bytecode, "var_names", [])[slot]
                if slot < len(getattr(bytecode, "var_names", []) or [])
                else f"slot_{slot}"
            )
            return [
                f"value = locals_[{slot}]",
                "if value is UNBOUND:",
                f"    raise RuntimeError(\"Local variable '{name}' referenced before assignment\")",
                "stack.append(value)",
                f"pc = {next_pc}",
                "continue",
            ]

        if op_value == OpCode.STORE_VAR.value:
            slot = int(operand or 0)
            return [f"locals_[{slot}] = stack.pop()", f"pc = {next_pc}", "continue"]

        if op_value == OpCode.POP.value:
            return ["stack.pop()", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.DUP.value:
            return ["stack.append(stack[-1])", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.SWAP.value:
            return ["stack[-1], stack[-2] = stack[-2], stack[-1]", f"pc = {next_pc}", "continue"]

        if op_value == OpCode.ADD.value:
            return [
                "b = stack.pop()",
                "a = stack.pop()",
                "stack.append(str(a) + str(b) if isinstance(a, str) or isinstance(b, str) else a + b)",
                f"pc = {next_pc}",
                "continue",
            ]
        if op_value == OpCode.SUB.value:
            return ["b = stack.pop()", "a = stack.pop()", "stack.append(a - b)", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.MUL.value:
            return ["b = stack.pop()", "a = stack.pop()", "stack.append(a * b)", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.DIV.value:
            return ["b = stack.pop()", "a = stack.pop()", "stack.append(a / b)", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.MOD.value:
            return ["b = stack.pop()", "a = stack.pop()", "stack.append(a % b)", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.POW.value:
            return ["b = stack.pop()", "a = stack.pop()", "stack.append(a ** b)", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.NEG.value:
            return ["a = stack.pop()", "stack.append(-a)", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.IDIV.value:
            return ["b = stack.pop()", "a = stack.pop()", "stack.append(a // b)", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.BAND.value:
            return ["b = stack.pop()", "a = stack.pop()", "stack.append(a & b)", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.BOR.value:
            return ["b = stack.pop()", "a = stack.pop()", "stack.append(a | b)", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.BXOR.value:
            return ["b = stack.pop()", "a = stack.pop()", "stack.append(a ^ b)", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.BNOT.value:
            return ["a = stack.pop()", "stack.append(~a)", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.LSHIFT.value:
            return ["b = stack.pop()", "a = stack.pop()", "stack.append(a << b)", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.RSHIFT.value:
            return ["b = stack.pop()", "a = stack.pop()", "stack.append(a >> b)", f"pc = {next_pc}", "continue"]

        if op_value == OpCode.EQ.value:
            return ["b = stack.pop()", "a = stack.pop()", "stack.append(a == b)", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.NEQ.value:
            return ["b = stack.pop()", "a = stack.pop()", "stack.append(a != b)", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.LT.value:
            return ["b = stack.pop()", "a = stack.pop()", "stack.append(a < b)", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.GT.value:
            return ["b = stack.pop()", "a = stack.pop()", "stack.append(a > b)", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.LTE.value:
            return ["b = stack.pop()", "a = stack.pop()", "stack.append(a <= b)", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.GTE.value:
            return ["b = stack.pop()", "a = stack.pop()", "stack.append(a >= b)", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.CONTAINS.value:
            return ["b = stack.pop()", "a = stack.pop()", "stack.append(b in a)", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.AND.value:
            return ["b = stack.pop()", "a = stack.pop()", "stack.append(a and b)", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.OR.value:
            return ["b = stack.pop()", "a = stack.pop()", "stack.append(a or b)", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.NOT.value:
            return ["a = stack.pop()", "stack.append(not a)", f"pc = {next_pc}", "continue"]

        if op_value == OpCode.JUMP.value:
            return [f"pc = {instruction.jump_target}", "continue"]
        if op_value == OpCode.JUMP_IF_TRUE.value:
            return [
                "cond = stack.pop()",
                f"pc = {instruction.jump_target} if cond else {next_pc}",
                "continue",
            ]
        if op_value == OpCode.JUMP_IF_FALSE.value:
            return [
                "cond = stack.pop()",
                f"pc = {instruction.jump_target} if not cond else {next_pc}",
                "continue",
            ]

        if op_value == OpCode.BUILD_LIST.value:
            count = int(operand or 0)
            if count:
                return [
                    f"items = stack[-{count}:]",
                    f"del stack[-{count}:]",
                    "stack.append(list(items))",
                    f"pc = {next_pc}",
                    "continue",
                ]
            return ["stack.append([])", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.BUILD_TUPLE.value:
            count = int(operand or 0)
            if count:
                return [
                    f"items = stack[-{count}:]",
                    f"del stack[-{count}:]",
                    "stack.append(tuple(items))",
                    f"pc = {next_pc}",
                    "continue",
                ]
            return ["stack.append(())", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.BUILD_DICT.value:
            count = int(operand or 0)
            if count:
                return [
                    "pairs = {}",
                    f"for _ in range({count}):",
                    "    key = stack.pop()",
                    "    value = stack.pop()",
                    "    pairs[key] = value",
                    "stack.append(pairs)",
                    f"pc = {next_pc}",
                    "continue",
                ]
            return ["stack.append({})", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.BUILD_SET.value:
            count = int(operand or 0)
            if count:
                return [
                    "items = set()",
                    f"for _ in range({count}):",
                    "    items.add(stack.pop())",
                    "stack.append(items)",
                    f"pc = {next_pc}",
                    "continue",
                ]
            return ["stack.append(set())", f"pc = {next_pc}", "continue"]
        if op_value == OpCode.UNPACK_SEQUENCE.value:
            count = int(operand or 0)
            return [
                "seq = stack.pop()",
                "items = list(seq)",
                f"if len(items) != {count}:",
                f"    raise RuntimeError('UNPACK_SEQUENCE expected {count} values, got ' + str(len(items)))",
                "for item in reversed(items):",
                "    stack.append(item)",
                f"pc = {next_pc}",
                "continue",
            ]

        if op_value == OpCode.RETURN.value:
            return ["return stack.pop() if stack else None"]
        if op_value == OpCode.RETURN_VOID.value:
            return ["return None"]
        if op_value == OpCode.HALT.value:
            return ["return stack[-1] if stack else None"]

        raise JITCompilationRejected(
            f"unsupported opcode {instruction.opcode_name} at offset {instruction.offset}"
        )
    
    def get_stats(self, func_name: str = None) -> Dict[str, Any]:
        """
        Get compilation statistics.
        
        Args:
            func_name: Specific function name (or None for all)
        
        Returns:
            Statistics dictionary
        """
        if func_name:
            if func_name in self.function_stats:
                stats = self.function_stats[func_name]
                return {
                    'name': stats.name,
                    'calls': stats.call_count,
                    'avg_time': stats.avg_time,
                    'compiled': stats.compiled,
                    'hot': self.is_hot(func_name),
                    'rejection_reason': self.rejected_functions.get(func_name),
                    'benchmark': self.benchmark_results.get(func_name),
                }
            return None
        
        # Return all stats
        return {
            name: {
                'calls': stats.call_count,
                'avg_time': stats.avg_time,
                'compiled': stats.compiled,
                'hot': self.is_hot(name),
                'rejection_reason': self.rejected_functions.get(name),
                'benchmark': self.benchmark_results.get(name),
            }
            for name, stats in self.function_stats.items()
        }
    
    def get_compiled_functions(self) -> List[str]:
        """Get list of compiled function names."""
        return list(self.compiled_functions.keys())

    def _normalize_benchmark_case(self, case: Any) -> Tuple[Tuple[Any, ...], Dict[str, Any]]:
        if isinstance(case, dict) and ("args" in case or "kwargs" in case):
            args = tuple(case.get("args", ()))
            kwargs = dict(case.get("kwargs", {}))
            return args, kwargs
        if isinstance(case, tuple):
            return tuple(case), {}
        return (case,), {}

    def benchmark_function(
        self,
        func_name: str,
        bytecode: Any,
        constants: List[Any],
        call_cases: List[Any],
        *,
        globals_dict: Optional[Dict[str, Any]] = None,
        reference_callable: Optional[Callable[..., Any]] = None,
        iterations: int = 200,
        warmup: int = 5,
    ) -> Dict[str, Any]:
        compiled = self.compiled_functions.get(func_name)
        if compiled is None:
            compiled = self.compile_function(func_name, bytecode, constants)
        if compiled is None:
            return {
                "name": func_name,
                "compiled": False,
                "reason": self.rejected_functions.get(func_name, "not compiled"),
            }

        cases = [self._normalize_benchmark_case(case) for case in call_cases]
        runtime_globals = globals_dict or {}

        for _ in range(max(0, warmup)):
            for args, kwargs in cases:
                compiled.execute(runtime_globals, *args, **kwargs)

        expected_outputs = None
        parity_ok = None
        if reference_callable is not None:
            expected_outputs = [
                reference_callable(*args, **kwargs)
                for args, kwargs in cases
            ]
            actual_outputs = [
                compiled.execute(runtime_globals, *args, **kwargs)
                for args, kwargs in cases
            ]
            parity_ok = actual_outputs == expected_outputs

        compiled_start = time.perf_counter()
        for _ in range(max(1, iterations)):
            for args, kwargs in cases:
                compiled.execute(runtime_globals, *args, **kwargs)
        compiled_elapsed = time.perf_counter() - compiled_start

        baseline_elapsed = None
        if reference_callable is not None:
            baseline_start = time.perf_counter()
            for _ in range(max(1, iterations)):
                for args, kwargs in cases:
                    reference_callable(*args, **kwargs)
            baseline_elapsed = time.perf_counter() - baseline_start

        report = {
            "name": func_name,
            "compiled": True,
            "cases": len(cases),
            "iterations": max(1, iterations),
            "compiled_ms": compiled_elapsed * 1000.0,
            "compiled_per_call_us": (compiled_elapsed * 1_000_000.0) / (max(1, iterations) * max(1, len(cases))),
            "baseline_ms": None if baseline_elapsed is None else baseline_elapsed * 1000.0,
            "baseline_per_call_us": None if baseline_elapsed is None else (baseline_elapsed * 1_000_000.0) / (max(1, iterations) * max(1, len(cases))),
            "speedup": None if baseline_elapsed is None or compiled_elapsed == 0 else baseline_elapsed / compiled_elapsed,
            "parity_ok": parity_ok,
            "reference_available": reference_callable is not None,
        }
        self.benchmark_results[func_name] = report
        return report

    def status(self) -> Dict[str, Any]:
        """Return runtime gating and cache status for diagnostics."""
        hot_functions = sorted(
            name for name, stats in self.function_stats.items()
            if stats.call_count >= self.call_threshold
        )
        return {
            "enabled": self.enabled,
            "experimental_runtime": self.experimental_runtime,
            "runtime_enabled": self.runtime_enabled,
            "mode": "experimental_runtime" if self.runtime_enabled else "observe_only",
            "threshold": self.call_threshold,
            "tracked_functions": len(self.function_stats),
            "hot_functions": hot_functions,
            "compiled_functions": self.get_compiled_functions(),
            "rejected_functions": dict(self.rejected_functions),
            "benchmarked_functions": sorted(self.benchmark_results),
            "benchmark_results": dict(self.benchmark_results),
            "supported_subset": sorted(
                OpCode(value).name for value in _SUPPORTED_OPCODES if value in OpCode._value2member_map_
            ),
            "env_var": self.EXPERIMENTAL_RUNTIME_ENV,
        }
    
    def clear_cache(self):
        """Clear compilation cache."""
        self.compiled_functions.clear()
        self.rejected_functions.clear()
        self.benchmark_results.clear()
    
    def reset_stats(self):
        """Reset all statistics."""
        self.function_stats.clear()
    
    def enable(self, *, runtime: Optional[bool] = None):
        """Enable JIT compilation."""
        self.enabled = True
        if runtime is not None:
            self.experimental_runtime = bool(runtime)
    
    def disable(self, *, clear_cache: bool = False):
        """Disable JIT compilation."""
        self.enabled = False
        if clear_cache:
            self.clear_cache()


# Export public API
__all__ = [
    'JITCompiler',
    'FunctionStats',
    'CompiledFunction',
]
