import os
with open("runtime/src/vm.py", "r") as f:
    content = f.read()

import_block = """
        def _get_chitra_modules():
            pass

        import sys
        vm_dir = os.path.dirname(os.path.abspath(__file__))
        bridge_dir = os.path.join(vm_dir, 'bridge')
        if bridge_dir not in sys.path:
            sys.path.insert(0, bridge_dir)
        try:
            from chitrakala.pixel_engine import ChitraCanvas, ChitraColor
            from chitrakala.colors import get_color, list_colors
            from chitrakala.png_encoder import save_png, load_png
            from chitrakala.primitives import draw_point, draw_line, draw_circle, draw_rectangle, draw_polygon, draw_text
        except ImportError:
            pass
"""

content = content.replace(
    '        def _get_chitra_modules():',
    import_block + '\n        def _get_chitra_modules_old():'
)

# And replace `ChitraCanvas, ChitraColor, *_ = _get_chitra_modules()` with nothing
content = content.replace('ChitraCanvas, ChitraColor, *_ = _get_chitra_modules()', 'pass')

with open("runtime/src/vm.py", "w") as f:
    f.write(content)
