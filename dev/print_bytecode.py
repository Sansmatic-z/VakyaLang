import sys, os
import importlib.util

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

load_module('runtime.src.tokens', 'runtime/src/tokens.py')
load_module('runtime.src.opcodes', 'runtime/src/opcodes.py')
load_module('runtime.src.ast_nodes', 'runtime/src/ast_nodes.py')
load_module('runtime.src.errors', 'runtime/src/errors.py')
load_module('runtime.src.lexer', 'runtime/src/lexer.py')
load_module('runtime.src.parser', 'runtime/src/parser.py')
load_module('runtime.src.bytecode', 'runtime/src/bytecode.py')
load_module('runtime.src.jit_compiler', 'runtime/src/jit_compiler.py')
load_module('runtime.src.vibhakti', 'runtime/src/vibhakti.py')
load_module('sansmatic.src.engine', 'sansmatic/src/engine.py')
load_module('atmalipi.src.engine', 'atmalipi/src/engine.py')

vm_mod = load_module('runtime.src.vm', 'runtime/src/vm.py')
compiler_mod = load_module('runtime.src.compiler', 'runtime/src/compiler.py')

Lexer = sys.modules['runtime.src.lexer'].Lexer
Parser = sys.modules['runtime.src.parser'].Parser
Compiler = compiler_mod.Compiler
OpCode = sys.modules['runtime.src.opcodes'].OpCode
OPCODE_NAMES = sys.modules['runtime.src.opcodes'].OPCODE_NAMES

with open('repro_test_json.vak', 'r') as f:
    source = f.read()

l = Lexer(source)
p = Parser(l.tokenize())
c = Compiler()
c._eliminate_dead_code = lambda: None
bc = c.compile(p.parse())

def print_bc(b, name):
    print(f'=== {name} ===')
    i = 0
    code = b.code
    while i < len(code):
        op = code[i]
        oname = OPCODE_NAMES.get(op, f'UNKNOWN({op})')
        
        # Opcodes with 16-bit operands (3 bytes total)
        op16 = (
            OpCode.LOAD_CONST.value, OpCode.JUMP.value, OpCode.JUMP_IF_TRUE.value,
            OpCode.JUMP_IF_FALSE.value, OpCode.IMPORT_NAME.value, OpCode.ATTR_GET.value,
            OpCode.ATTR_SET.value, OpCode.FOR_ITER.value, OpCode.VERIFY_PROOF.value,
            OpCode.LOAD_PROOF.value, OpCode.SETUP_EXCEPT.value, OpCode.CALL_BUILTIN.value
        )
        # Opcodes with 8-bit operands (2 bytes total)
        op8 = (
            OpCode.LOAD_VAR.value, OpCode.STORE_VAR.value, OpCode.CALL.value,
            OpCode.BUILD_LIST.value, OpCode.BUILD_DICT.value,
            OpCode.BUILD_SET.value, OpCode.BUILD_STRING.value, OpCode.UNPACK_SEQUENCE.value,
            OpCode.LOAD_VIBHAKTI.value, OpCode.CALL_METHOD.value
        )
        
        size = 1
        if op in op16: size = 3
        elif op in op8: size = 2
        elif op == OpCode.CHECK_VIBHAKTI.value: size = 4
        
        operands = []
        if size == 2 and i + 1 < len(code): operands = [code[i+1]]
        elif size == 3 and i + 2 < len(code): operands = [(code[i+1] << 8) | code[i+2]]
        elif size == 4 and i + 3 < len(code): operands = [(code[i+1] << 8) | code[i+2], code[i+3]]
        
        print(f'{i:04d}: {oname:15} {operands}')
        i += size

print_bc(bc, 'module')
