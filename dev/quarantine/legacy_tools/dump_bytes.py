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

with open('repro_critical.vak', 'r') as f:
    source = f.read()

l = Lexer(source)
p = Parser(l.tokenize())
c = Compiler()
c._eliminate_dead_code = lambda: None
bc = c.compile(p.parse())

print("CODE BYTES:", bc.code)
