import sys
import os
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

vm = vm_mod.VakVM()
c = compiler_mod.Compiler()

vm_builtins = list(vm.builtins.keys())
c_builtins = [
            'पाठ_कर', 'str', 'परास', 'range', 'दीर्घता', 'len', 'प्रकार', 'type',
            'संख्या', 'int', 'दशमलव', 'float', 'मुद्रय', 'print',
            'पठन', 'लेखन', 'अस्तित्व', 'मिटाओ', 'सूची_निर्देशिका', 'बनाओ_निर्देशिका',
            'परिवेश_प्राप्त', 'परिवेश_सेट', 'प्रणाली_कमांड', 'मंच', 'कार्य_निर्देशिका',
            'संयोग', 'विभाजन', 'छाँटो', 'उच्च', 'निम्न', 'पूर्णांक_कर',
            'क्रमबद्ध', 'योग', 'अधिकतम', 'न्यूनतम', 'कुंजियाँ', 'मान', 'वर्गमूल',
            '_math_cos', '_math_sin', '_math_tan', '_math_sqrt', '_math_abs',
            '_math_floor', '_math_ceil', '_math_round', '_math_degrees', '_math_radians',
            'जाल_लाओ', 'जाल_भेजो', 'जाल_डाउनलोड', 'जाल_पुट', 'समय', 'निद्रा', 'धागा_शुरू',
            'सेट_टाइमआउट', 'सेट_इंटरवल', 'क्लियर_टाइमआउट', 'async_sleep',
            'रेगेक्स_खोज', 'रेगेक्स_बदलो', 'जेसन_लिखो', 'जेसन_पढ़ो',
            'परिभाषय', 'दावा', 'नियम', 'मूल्यांकन', 'सिद्ध_है',
            'आत्म_मूल्य', 'भाव_पढ़ो', 'अवस्था_पढ़ो', 'सभी_भाव', 'सभी_अवस्था', 'आत्म_इतिहास', 'आत्म_है', 'आत्म_भाव', 'आत्म_अवस्था', 'आत्म_मूल',
            '_chitra_canvas', '_chitra_fill', '_chitra_point', '_chitra_line', '_chitra_circle',
            '_chitra_rect', '_chitra_polygon', '_chitra_text', '_chitra_save', '_chitra_load',
            '_chitra_color', '_chitra_colors', '_chitra_width', '_chitra_height',
            '_chitra_pixel_get', '_chitra_pixel_set', '_chitra_clear', '_chitra_text_centered',
            '_chitra_gradient', '_chitra_rotate', '_chitra_mandala', '_chitra_kaleidoscope',
            'पायथन_आयात', 'पायथन_चलाओ', 'पायथन_मूल्यांकन', 'अक्षर_मान'
        ]

print('Length VM:', len(vm_builtins))
print('Length Compiler:', len(c_builtins))

for i in range(max(len(vm_builtins), len(c_builtins))):
    v = vm_builtins[i] if i < len(vm_builtins) else None
    c = c_builtins[i] if i < len(c_builtins) else None
    if v != c:
        print(f'Mismatch at {i}: VM={v}, Compiler={c}')
