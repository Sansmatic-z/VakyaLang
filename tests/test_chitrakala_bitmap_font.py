import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from runtime.src.bridge.chitrakala.bitmap_font import BitmapFont, draw_text, draw_text_centered
from runtime.src.bridge.chitrakala.colors import get_color
from runtime.src.bridge.chitrakala.pixel_engine import ChitraCanvas, ChitraColor


class ChitrakalaBitmapFontTests(unittest.TestCase):
    def _colored_pixels(self, canvas: ChitraCanvas, color: ChitraColor):
        pixels = []
        for y in range(canvas.height):
            for x in range(canvas.width):
                if canvas.get_pixel(x, y) == color:
                    pixels.append((x, y))
        return pixels

    def test_measure_text_ignores_devanagari_attaching_mark_width(self):
        font = BitmapFont()

        self.assertEqual(font.measure_text("का"), (8, 8))
        self.assertEqual(font.measure_text("कि"), (8, 8))
        self.assertEqual(font.measure_text("वाक्"), (16, 8))

    def test_draw_text_renders_devanagari_glyphs_with_attaching_marks(self):
        canvas = ChitraCanvas(64, 24, ChitraColor.krishna())
        color = get_color("padma")

        draw_text(canvas, 4, 4, "वाक्", color)
        pixels = self._colored_pixels(canvas, color)

        self.assertTrue(pixels, "expected Devanagari glyph pixels to be drawn")
        max_x = max(x for x, _ in pixels)
        min_y = min(y for _, y in pixels)
        max_y = max(y for _, y in pixels)
        self.assertLess(max_x, 20, "attaching marks should not expand width like full glyphs")
        self.assertEqual(min_y, 4)
        self.assertGreaterEqual(max_y, 9)

    def test_draw_text_centered_renders_showcase_sanskrit_title(self):
        canvas = ChitraCanvas(320, 120, ChitraColor.krishna())
        color = get_color("padma")

        draw_text_centered(canvas, 40, "वाक् चित्रकला प्रदर्शन", color, scale=2)
        pixels = self._colored_pixels(canvas, color)

        self.assertTrue(pixels, "expected centered Sanskrit title to produce visible pixels")
        min_x = min(x for x, _ in pixels)
        max_x = max(x for x, _ in pixels)
        min_y = min(y for _, y in pixels)
        max_y = max(y for _, y in pixels)
        self.assertGreater(min_x, 0)
        self.assertLess(max_x, canvas.width - 1)
        self.assertGreaterEqual(min_y, 38)
        self.assertLessEqual(max_y, 58)


if __name__ == "__main__":
    unittest.main()
