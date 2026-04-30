import re
with open("runtime/src/vm.py", "r") as f:
    content = f.read()

# Fix the import
content = content.replace(
    "from chitrakala.primitives import draw_point, draw_line, draw_circle, draw_rectangle, draw_polygon, draw_text",
    "from chitrakala.primitives import draw_point, draw_line, draw_circle, draw_rectangle, draw_polygon\n            from chitrakala.bitmap_font import draw_text"
)

with open("runtime/src/vm.py", "w") as f:
    f.write(content)
