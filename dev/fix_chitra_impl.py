with open("runtime/src/vm.py", "r") as f:
    content = f.read()

impl_code = """
        def _chitra_canvas_impl(w, h, c="श्वेत"):
            return ChitraCanvas(int(w), int(h), c)
        def _chitra_fill_impl(canv, c):
            canv.fill(get_color(c) if isinstance(c, str) else c)
        def _chitra_point_impl(canv, x, y, c):
            draw_point(canv, int(x), int(y), get_color(c) if isinstance(c, str) else c)
        def _chitra_line_impl(canv, x1, y1, x2, y2, c):
            draw_line(canv, int(x1), int(y1), int(x2), int(y2), get_color(c) if isinstance(c, str) else c)
        def _chitra_circle_impl(canv, x, y, r, c, fill=False):
            draw_circle(canv, int(x), int(y), int(r), get_color(c) if isinstance(c, str) else c, bool(fill))
        def _chitra_rect_impl(canv, x, y, w, h, c, fill=False):
            draw_rectangle(canv, int(x), int(y), int(w), int(h), get_color(c) if isinstance(c, str) else c, bool(fill))
        def _chitra_polygon_impl(canv, pts, c, fill=False):
            draw_polygon(canv, [(int(p[0]), int(p[1])) for p in pts], get_color(c) if isinstance(c, str) else c, bool(fill))
        def _chitra_text_impl(canv, x, y, text, font="krishna", size=1, c="कृष्ण"):
            draw_text(canv, int(x), int(y), str(text), get_color(c) if isinstance(c, str) else c, str(font), int(size))
        def _chitra_save_impl(canv, path):
            save_png(canv, str(path))
        def _chitra_load_impl(path):
            return load_png(str(path))
        def _chitra_color_impl(c):
            return get_color(str(c))
        def _chitra_colors_impl():
            return list_colors()
        def _chitra_width_impl(canv):
            return canv.width
        def _chitra_height_impl(canv):
            return canv.height
        def _chitra_pixel_get_impl(canv, x, y):
            return canv.get_pixel(int(x), int(y))
        def _chitra_pixel_set_impl(canv, x, y, c):
            canv.set_pixel(int(x), int(y), get_color(c) if isinstance(c, str) else c)

"""

content = content.replace("        return {", impl_code + "        return {")

with open("runtime/src/vm.py", "w") as f:
    f.write(content)
print("Injected impl functions")
