with open("runtime/src/vm.py", "r") as f:
    content = f.read()

content = content.replace(
    '''def _chitra_canvas_impl(w, h, c="white"):
            return ChitraCanvas(int(w), int(h), c)''',
    '''def _chitra_canvas_impl(w, h, c="white"):
            return ChitraCanvas(int(w), int(h), get_color(c) if isinstance(c, str) else c)'''
)

with open("runtime/src/vm.py", "w") as f:
    f.write(content)
