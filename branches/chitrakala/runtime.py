from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from runtime.src.errors import VMError


CHITRAKALA_BUILTIN_NAMES = (
    "_chitra_canvas",
    "_chitra_fill",
    "_chitra_point",
    "_chitra_line",
    "_chitra_circle",
    "_chitra_rect",
    "_chitra_polygon",
    "_chitra_text",
    "_chitra_save",
    "_chitra_load",
    "_chitra_color",
    "_chitra_colors",
    "_chitra_width",
    "_chitra_height",
    "_chitra_pixel_get",
    "_chitra_pixel_set",
    "_chitra_clear",
    "_chitra_text_centered",
    "_chitra_gradient",
    "_chitra_rotate",
    "_chitra_mandala",
    "_chitra_kaleidoscope",
)


@dataclass(frozen=True)
class ChitrakalaSupport:
    available: bool
    builtins: dict[str, Callable[..., Any]]


def build_chitrakala_builtins() -> ChitrakalaSupport:
    try:
        from runtime.src.bridge.chitrakala.pixel_engine import ChitraCanvas, ChitraColor
        from runtime.src.bridge.chitrakala.colors import get_color, list_colors
        from runtime.src.bridge.chitrakala.png_encoder import save_png, load_png
        from runtime.src.bridge.chitrakala.primitives import (
            draw_circle,
            draw_line,
            draw_point,
            draw_polygon,
            draw_rectangle,
        )
        from runtime.src.bridge.chitrakala.bitmap_font import draw_text, draw_text_centered
        from runtime.src.bridge.chitrakala.effects import ChitraEffects
        available = True
    except ImportError:
        ChitraCanvas = None
        ChitraColor = None
        get_color = None
        list_colors = None
        save_png = None
        load_png = None
        draw_point = None
        draw_line = None
        draw_circle = None
        draw_rectangle = None
        draw_polygon = None
        draw_text = None
        draw_text_centered = None
        ChitraEffects = None
        available = False

    def _require_chitra_support() -> None:
        if not available:
            raise VMError("चित्रकला समर्थन उपलब्ध नहीं है")

    def _resolve_chitra_color(value: Any) -> Any:
        _require_chitra_support()
        return get_color(value) if isinstance(value, str) else value

    def _resolve_chitra_palette(values: Any) -> list[Any]:
        if isinstance(values, (list, tuple)):
            return [_resolve_chitra_color(value) for value in values]
        return [_resolve_chitra_color(values)]

    def _chitra_canvas_impl(*args: Any) -> Any:
        _require_chitra_support()
        w, h = int(args[0]), int(args[1])
        c = args[2] if len(args) > 2 else "white"
        return ChitraCanvas(w, h, _resolve_chitra_color(c))

    def _chitra_fill_impl(*args: Any) -> None:
        _require_chitra_support()
        canv, c = args[0], args[1]
        canv.fill(_resolve_chitra_color(c))

    def _chitra_point_impl(*args: Any) -> None:
        _require_chitra_support()
        canv, x, y = args[0], int(args[1]), int(args[2])
        c = args[3] if len(args) > 3 else "black"
        draw_point(canv, x, y, _resolve_chitra_color(c))

    def _chitra_line_impl(*args: Any) -> None:
        _require_chitra_support()
        canv, x0, y0, x1, y1 = args[0], int(args[1]), int(args[2]), int(args[3]), int(args[4])
        c = args[5] if len(args) > 5 else "black"
        draw_line(canv, x0, y0, x1, y1, _resolve_chitra_color(c))

    def _chitra_circle_impl(*args: Any) -> None:
        _require_chitra_support()
        canv, x, y, r = args[0], int(args[1]), int(args[2]), int(args[3])
        c = args[4] if len(args) > 4 else "black"
        fill = bool(args[5]) if len(args) > 5 else False
        draw_circle(canv, x, y, r, _resolve_chitra_color(c), fill)

    def _chitra_rect_impl(*args: Any) -> None:
        _require_chitra_support()
        canv, x, y, w, h = args[0], int(args[1]), int(args[2]), int(args[3]), int(args[4])
        c = args[5] if len(args) > 5 else "black"
        fill = bool(args[6]) if len(args) > 6 else False
        draw_rectangle(canv, x, y, w, h, _resolve_chitra_color(c), fill)

    def _chitra_polygon_impl(*args: Any) -> None:
        _require_chitra_support()
        canv, pts = args[0], args[1]
        c = args[2] if len(args) > 2 else "black"
        fill = bool(args[3]) if len(args) > 3 else False
        draw_polygon(
            canv,
            [(int(point[0]), int(point[1])) for point in pts],
            _resolve_chitra_color(c),
            fill,
        )

    def _chitra_text_impl(*args: Any) -> Any:
        _require_chitra_support()
        canv, x, y, text = args[0], int(args[1]), int(args[2]), str(args[3])
        font_arg = args[4] if len(args) > 4 else None
        size = int(args[5]) if len(args) > 5 else 1
        c = args[6] if len(args) > 6 else "black"
        font = None if isinstance(font_arg, str) else font_arg
        draw_text(canv, x, y, text, _resolve_chitra_color(c), font, size)
        return canv

    def _chitra_text_centered_impl(*args: Any) -> Any:
        _require_chitra_support()
        canv, y, text = args[0], int(args[1]), str(args[2])
        color = args[3] if len(args) > 3 else "black"
        scale = int(args[4]) if len(args) > 4 else 1
        draw_text_centered(canv, y, text, _resolve_chitra_color(color), scale=scale)
        return canv

    def _chitra_save_impl(*args: Any) -> None:
        _require_chitra_support()
        canv, path = args[0], str(args[1])
        save_png(canv, path)

    def _chitra_load_impl(*args: Any) -> Any:
        _require_chitra_support()
        return load_png(str(args[0]))

    def _chitra_color_impl(*args: Any) -> Any:
        _require_chitra_support()
        return get_color(str(args[0]))

    def _chitra_colors_impl() -> Any:
        _require_chitra_support()
        return list_colors()

    def _chitra_width_impl(*args: Any) -> Any:
        return args[0].width

    def _chitra_height_impl(*args: Any) -> Any:
        return args[0].height

    def _chitra_pixel_get_impl(*args: Any) -> Any:
        _require_chitra_support()
        canv, x, y = args[0], int(args[1]), int(args[2])
        return canv.get_pixel(x, y)

    def _chitra_pixel_set_impl(*args: Any) -> Any:
        _require_chitra_support()
        canv, x, y, c = args[0], int(args[1]), int(args[2]), args[3]
        canv.set_pixel(x, y, _resolve_chitra_color(c))
        return canv

    def _chitra_clear_impl(*args: Any) -> Any:
        _require_chitra_support()
        canv, c = args[0], args[1] if len(args) > 1 else "white"
        canv.fill(_resolve_chitra_color(c))
        return canv

    def _chitra_gradient_impl(*args: Any) -> Any:
        _require_chitra_support()
        canv, c1, c2 = args[0], args[1], args[2]
        c1 = _resolve_chitra_color(c1)
        c2 = _resolve_chitra_color(c2)
        for x in range(canv.width):
            ratio = x / max(1, canv.width - 1)
            r = int(c1.r * (1 - ratio) + c2.r * ratio)
            g = int(c1.g * (1 - ratio) + c2.g * ratio)
            b = int(c1.b * (1 - ratio) + c2.b * ratio)
            for y in range(canv.height):
                canv.set_pixel(x, y, ChitraColor(r, g, b))
        return canv

    def _chitra_rotate_impl(*args: Any) -> Any:
        _require_chitra_support()
        canv = args[0]
        angle = float(args[1]) if len(args) > 1 else 0.0
        center_x = int(args[2]) if len(args) > 2 else canv.width // 2
        center_y = int(args[3]) if len(args) > 3 else canv.height // 2
        return ChitraEffects.rotate(canv, angle, center_x, center_y)

    def _chitra_mandala_impl(*args: Any) -> Any:
        _require_chitra_support()
        canv = args[0]
        center_x = int(args[1]) if len(args) > 1 else canv.width // 2
        center_y = int(args[2]) if len(args) > 2 else canv.height // 2
        radius = int(args[3]) if len(args) > 3 else min(canv.width, canv.height) // 3
        petals = max(1, int(args[4])) if len(args) > 4 else 12
        palette = args[5] if len(args) > 5 else ["red", "green", "blue", "yellow"]
        ChitraEffects.mandala_pattern(
            canv,
            center_x,
            center_y,
            radius,
            petals,
            _resolve_chitra_palette(palette),
        )
        return canv

    def _chitra_kaleidoscope_impl(*args: Any) -> Any:
        _require_chitra_support()
        canv = args[0]
        segments = max(2, int(args[1])) if len(args) > 1 else 8
        return ChitraEffects.kaleidoscope(canv, segments)

    return ChitrakalaSupport(
        available=available,
        builtins={
            "_chitra_canvas": _chitra_canvas_impl,
            "_chitra_fill": _chitra_fill_impl,
            "_chitra_point": _chitra_point_impl,
            "_chitra_line": _chitra_line_impl,
            "_chitra_circle": _chitra_circle_impl,
            "_chitra_rect": _chitra_rect_impl,
            "_chitra_polygon": _chitra_polygon_impl,
            "_chitra_text": _chitra_text_impl,
            "_chitra_save": _chitra_save_impl,
            "_chitra_load": _chitra_load_impl,
            "_chitra_color": _chitra_color_impl,
            "_chitra_colors": _chitra_colors_impl,
            "_chitra_width": _chitra_width_impl,
            "_chitra_height": _chitra_height_impl,
            "_chitra_pixel_get": _chitra_pixel_get_impl,
            "_chitra_pixel_set": _chitra_pixel_set_impl,
            "_chitra_clear": _chitra_clear_impl,
            "_chitra_text_centered": _chitra_text_centered_impl,
            "_chitra_gradient": _chitra_gradient_impl,
            "_chitra_rotate": _chitra_rotate_impl,
            "_chitra_mandala": _chitra_mandala_impl,
            "_chitra_kaleidoscope": _chitra_kaleidoscope_impl,
        },
    )
