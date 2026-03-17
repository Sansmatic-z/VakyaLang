# वाक् भाषा - आभासी यंत्र (Virtual Machine)
# Vak Language - Bytecode Execution Engine

from .opcodes import OpCode
from .compiler import CodeObject
from ..environment import Environment
from ..errors import VakRuntimeError, VakTypeError, VakNameError
from ..interpreter import VakNull, VAK_NULL, VakFunction, VakClass, VakInstance, BuiltinFunction

class VakVM:
    """
    Executes compiled Vak Bytecode.
    """
    def __init__(self, globals_env=None):
        self.globals = globals_env or Environment(name="global")
        self.stack = []
        self.ip = 0 # Instruction Pointer

    def run(self, code: CodeObject):
        self.ip = 0
        instructions = code.instructions
        constants = code.constants
        globals_env = self.globals
        stack = self.stack
        stack_pop = stack.pop
        stack_append = stack.append
        
        while self.ip < len(instructions):
            op, operand = instructions[self.ip]
            self.ip += 1

            if op == OpCode.LOAD_CONST:
                stack_append(constants[operand])

            elif op == OpCode.LOAD_VAR:
                stack_append(globals_env.get(operand))

            elif op == OpCode.STORE_VAR:
                val = stack[-1]
                globals_env.assign(operand, val)

            elif op == OpCode.DEFINE_VAR:
                val = stack_pop()
                globals_env.define(operand, val)

            elif op == OpCode.POP:
                stack_pop()

            elif op == OpCode.ADD:
                b = stack_pop()
                a = stack_pop()
                stack_append(a + b)

            elif op == OpCode.SUB:
                b = stack_pop()
                a = stack_pop()
                stack_append(a - b)

            elif op == OpCode.MUL:
                b = stack_pop()
                a = stack_pop()
                stack_append(a * b)

            elif op == OpCode.DIV:
                b = stack_pop()
                a = stack_pop()
                stack_append(a / b)

            elif op == OpCode.IDIV:
                b = stack_pop()
                a = stack_pop()
                stack_append(a // b)

            elif op == OpCode.MOD:
                b = stack_pop()
                a = stack_pop()
                stack_append(a % b)

            elif op == OpCode.POW:
                b = stack_pop()
                a = stack_pop()
                stack_append(a ** b)

            elif op == OpCode.NEG:
                stack_append(-stack_pop())

            elif op == OpCode.NOT:
                stack_append(not self._truthy(stack_pop()))

            elif op == OpCode.EQ:
                b = stack_pop()
                a = stack_pop()
                stack_append(a == b)

            elif op == OpCode.NEQ:
                b = stack_pop()
                a = stack_pop()
                stack_append(a != b)

            elif op == OpCode.LT:
                b = stack_pop()
                a = stack_pop()
                stack_append(a < b)

            elif op == OpCode.GT:
                b = stack_pop()
                a = stack_pop()
                stack_append(a > b)

            elif op == OpCode.LTE:
                b = stack_pop()
                a = stack_pop()
                stack_append(a <= b)

            elif op == OpCode.GTE:
                b = stack_pop()
                a = stack_pop()
                stack_append(a >= b)

            elif op == OpCode.IN:
                b = stack_pop()
                a = stack_pop()
                stack_append(a in b)

            elif op == OpCode.PRINT:
                vals = []
                for _ in range(operand):
                    vals.insert(0, str(stack_pop()))
                print(' '.join(vals))

            elif op == OpCode.JUMP:
                self.ip = operand

            elif op == OpCode.JUMP_IF_FALSE:
                if not self._truthy(stack[-1]):
                    self.ip = operand

            elif op == OpCode.LOOP:
                self.ip = operand

            elif op == OpCode.CALL:
                args = []
                for _ in range(operand):
                    args.insert(0, stack_pop())
                callee = stack_pop()
                if isinstance(callee, BuiltinFunction):
                    stack_append(callee.fn(args, {}))
                else:
                    raise VakRuntimeError("VM call supports built-ins only in this phase")

            elif op == OpCode.HALT:
                break

    def _truthy(self, val):
        if val is None or val is False: return False
        if isinstance(val, VakNull): return False
        return bool(val)
