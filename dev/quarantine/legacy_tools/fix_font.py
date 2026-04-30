with open("runtime/src/vm.py", "r") as f:
    content = f.read()

content = content.replace(
    'def _chitra_text_impl(canv, x, y, text, font="krishna", size=1, c="black"):',
    '''def _chitra_text_impl(canv, x, y, text, font=None, size=1, c="black"):
            from chitrakala.bitmap_font import FONT_KRISHNA
            if font is None or font == "krishna": font = FONT_KRISHNA'''
)
content = content.replace(
    'draw_text(canv, int(x), int(y), str(text), get_color(c) if isinstance(c, str) else c, str(font), int(size))',
    'draw_text(canv, int(x), int(y), str(text), get_color(c) if isinstance(c, str) else c, font, int(size))'
)

with open("runtime/src/vm.py", "w") as f:
    f.write(content)
