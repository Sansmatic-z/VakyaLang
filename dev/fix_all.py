import sys
import os

# 1. Restore py_bridge.py from a git checkout or just fix it directly
with open("runtime/stdlib/py_bridge.py", "r") as f:
    content = f.read()

# I will find the class WrappedCallable and carefully replace its body
# It's easier to just do a clean regex replacement
import re

content = re.sub(
    r'class WrappedCallable:.*?def convert_to_python',
    r'''class WrappedCallable:
    """Wrapper for Python callable objects"""
    
    def __init__(self, func, module_name: str):
        self._func = func
        self._module_name = module_name
        self.__name__ = getattr(func, '__name__', 'unknown')

    def __getattr__(self, name: str):
        if name in ['_func', '_module_name', '__name__', '__class__']:
            raise AttributeError()
        try:
            attr = getattr(self._func, name)
            if callable(attr):
                return WrappedCallable(attr, self._module_name)
            if not isinstance(attr, (int, float, str, bool, type(None), list, dict)):
                return PythonObjectWrapper(attr, self._module_name)
            return attr
        except AttributeError:
            raise Exception(f"Attribute '{name}' not found")
    
    def __call__(self, *args, **kwargs):
        """Call the wrapped function with type conversion"""
        try:
            py_args = convert_to_python(args)
            py_kwargs = convert_to_python(kwargs)
            result = self._func(*py_args, **py_kwargs)
            return convert_to_vak(result)
        except Exception as e:
            raise Exception(f"Error in {self._module_name}.{self.__name__}: {e}")
    
    def __repr__(self) -> str:
        return f"PythonFunction({self._module_name}.{self.__name__})"

def convert_to_python''',
    content, flags=re.DOTALL
)

# Fix the duplicate __getattr__ in PythonObjectWrapper
content = re.sub(r'    def __getattr__\(self, name: str\) -> Any:\n        if name in \[\'_func\'.*?raise PythonBridgeError\(f"Attribute.*?\n\n    def __repr__', '    def __repr__', content, flags=re.DOTALL)

with open("runtime/stdlib/py_bridge.py", "w") as f:
    f.write(content)

# 2. Fix vm.py Chitrakala imports
with open("runtime/src/vm.py", "r") as f:
    vm_content = f.read()

# We can just put the chitrakala imports at the global level of vm.py, wrapping them in try/except
chitra_imports = """
try:
    import sys, os
    vm_dir = os.path.dirname(os.path.abspath(__file__))
    bridge_dir = os.path.join(vm_dir, 'bridge')
    if bridge_dir not in sys.path:
        sys.path.insert(0, bridge_dir)
    from chitrakala.pixel_engine import ChitraCanvas, ChitraColor
    from chitrakala.colors import get_color, list_colors
    from chitrakala.png_encoder import save_png, load_png
    from chitrakala.primitives import draw_point, draw_line, draw_circle, draw_rectangle, draw_polygon, draw_text
except ImportError:
    pass
"""

# Insert at the top
vm_content = vm_content.replace('from .opcodes import OpCode, OPCODE_NAMES', 'from .opcodes import OpCode, OPCODE_NAMES\n' + chitra_imports)

# Remove the inline _get_chitra_modules definition and usage
vm_content = re.sub(r'        def _get_chitra_modules_old\(\):.*?\n        try:\n', '        try:\n', vm_content, flags=re.DOTALL)

with open("runtime/src/vm.py", "w") as f:
    f.write(vm_content)
print("Fixes applied.")
