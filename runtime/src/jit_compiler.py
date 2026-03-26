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
import time
import hashlib


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
        """Check if function is hot (should be compiled)."""
        return self.call_count >= JITCompiler.DEFAULT_THRESHOLD


@dataclass
class CompiledFunction:
    """A compiled function with native Python code."""
    name: str
    python_code: str
    compiled_obj: Any  # Compiled Python code object
    constants: List[Any]
    compile_time: float
    
    def execute(self, globals_dict: Dict[str, Any], *args) -> Any:
        """Execute the compiled function."""
        # Create execution namespace
        namespace = {
            '__builtins__': __builtins__,
            'stack': [],
            'constants': self.constants,
            'globals': globals_dict,
        }
        
        # Execute compiled code
        exec(self.compiled_obj, namespace)
        
        # Return result from stack
        return namespace['stack'][-1] if namespace['stack'] else None


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
    
    def __init__(self, threshold: int = None):
        """
        Initialize JIT compiler.
        
        Args:
            threshold: Call count threshold for compilation
        """
        self.call_threshold = threshold or self.DEFAULT_THRESHOLD
        self.function_stats: Dict[str, FunctionStats] = {}
        self.compiled_functions: Dict[str, CompiledFunction] = {}
        self.enabled = True
        self.verbose = False
    
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
            # Translate bytecode to Python
            python_code = self._bytecode_to_python(bytecode, func_name)
            
            # Compile Python code
            compiled_obj = compile(python_code, f'<jit:{func_name}>', 'exec')
            
            compile_time = time.time() - start_time
            
            # Create compiled function
            compiled_func = CompiledFunction(
                name=func_name,
                python_code=python_code,
                compiled_obj=compiled_obj,
                constants=constants,
                compile_time=compile_time
            )
            
            self.compiled_functions[func_name] = compiled_func
            
            # Update stats
            if func_name in self.function_stats:
                self.function_stats[func_name].compiled = True
                self.function_stats[func_name].compiled_time = compile_time
            
            if self.verbose:
                print(f"✓ Compiled '{func_name}' in {compile_time*1000:.2f}ms")
            
            return compiled_func
            
        except Exception as e:
            if self.verbose:
                print(f"✗ Compilation failed for '{func_name}': {e}")
            return None
    
    def _bytecode_to_python(self, bytecode: Any, func_name: str) -> str:
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
            "def jit_function():",
            "    stack = []",
            "    constants = globals()['constants']",
            "    _globals = globals()['globals']",
        ]
        
        # Get instructions from bytecode
        instructions = self._extract_instructions(bytecode)
        
        for offset, (op, operand) in enumerate(instructions):
            try:
                python_line = self._translate_instruction(op, operand, offset)
                if python_line:
                    lines.append(f"    {python_line}")
            except Exception as e:
                lines.append(f"    # Error translating offset {offset}: {e}")
        
        lines.append("    return stack[-1] if stack else None")
        
        return "\n".join(lines)
    
    def _extract_instructions(self, bytecode: Any) -> List[Tuple[Any, Any]]:
        """Extract instructions from bytecode object."""
        instructions = []
        
        # Try to get code array
        if hasattr(bytecode, 'code'):
            code = bytecode.code
        elif hasattr(bytecode, 'instructions'):
            code = bytecode.instructions
        else:
            # Assume it's already a list
            code = bytecode if isinstance(bytecode, list) else []
        
        # Parse instructions
        i = 0
        while i < len(code):
            op = code[i]
            operand = None
            
            # Check if opcode has operand
            if hasattr(op, 'value'):
                op_value = op.value
            else:
                op_value = op
            
            # Opcodes with 16-bit operands (assume > 100 is operand opcode)
            if op_value > 100 and i + 1 < len(code):
                operand = code[i + 1]
                i += 2
            else:
                i += 1
            
            instructions.append((op, operand))
        
        return instructions
    
    def _translate_instruction(self, op: Any, operand: Any, offset: int) -> str:
        """
        Translate single instruction to Python.
        
        Args:
            op: Opcode
            operand: Operand (if any)
            offset: Instruction offset
        
        Returns:
            Python code line
        """
        from .opcodes import OpCode
        
        # Get opcode value
        if hasattr(op, 'value'):
            op_value = op.value
            op_name = op.name
        else:
            op_value = op
            op_name = str(op)
        
        # Translate based on opcode
        if op_name == 'LOAD_CONST' or op_value == 1:
            return f"stack.append(constants[{operand}])"
        
        elif op_name == 'LOAD_VAR' or op_value == 2:
            var_name = operand if isinstance(operand, str) else f"var_{operand}"
            return f"stack.append(_globals.get('{var_name}', None))"
        
        elif op_name == 'STORE_VAR' or op_value == 3:
            var_name = operand if isinstance(operand, str) else f"var_{operand}"
            return f"_globals['{var_name}'] = stack.pop()"
        
        elif op_name == 'ADD' or op_value == 10:
            return "stack.append(stack.pop() + stack.pop())"
        
        elif op_name == 'SUB' or op_value == 11:
            return "b, a = stack.pop(), stack.pop(); stack.append(a - b)"
        
        elif op_name == 'MUL' or op_value == 12:
            return "stack.append(stack.pop() * stack.pop())"
        
        elif op_name == 'DIV' or op_value == 13:
            return "b, a = stack.pop(), stack.pop(); stack.append(a / b if b != 0 else 0)"
        
        elif op_name == 'PRINT' or op_value == 50:
            return "print(stack.pop())"
        
        elif op_name == 'RETURN' or op_value == 100:
            return "return stack.pop() if stack else None"
        
        elif op_name == 'RETURN_VOID' or op_value == 101:
            return "return None"
        
        elif op_name == 'HALT' or op_value == 255:
            return "return stack[-1] if stack else None"
        
        else:
            return f"# Unhandled opcode: {op_name} ({op_value})"
    
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
                    'hot': stats.is_hot,
                }
            return None
        
        # Return all stats
        return {
            name: {
                'calls': stats.call_count,
                'avg_time': stats.avg_time,
                'compiled': stats.compiled,
                'hot': stats.is_hot,
            }
            for name, stats in self.function_stats.items()
        }
    
    def get_compiled_functions(self) -> List[str]:
        """Get list of compiled function names."""
        return list(self.compiled_functions.keys())
    
    def clear_cache(self):
        """Clear compilation cache."""
        self.compiled_functions.clear()
    
    def reset_stats(self):
        """Reset all statistics."""
        self.function_stats.clear()
    
    def enable(self):
        """Enable JIT compilation."""
        self.enabled = True
    
    def disable(self):
        """Disable JIT compilation."""
        self.enabled = False


# Export public API
__all__ = [
    'JITCompiler',
    'FunctionStats',
    'CompiledFunction',
]
