# चित्रकला — Chitrakala: Visual Library for VakyaLang
# © 2026 Raj Mitra — Built from Scratch (Minimum Dependencies)
# 
# "चित्रकला" = Art of Painting/Drawing in Sanskrit
#
# This module provides pure Python image creation and manipulation
# with Sanskrit-named APIs for VakyaLang integration.

from .pixel_engine import ChitraCanvas, ChitraColor
from .primitives import draw_line, draw_circle, draw_rectangle, draw_polygon, draw_point
from .colors import VARNAS, get_color, list_colors
from .png_encoder import save_png, load_png
from .bitmap_font import draw_text, BitmapFont

__all__ = [
    'ChitraCanvas',
    'ChitraColor', 
    'draw_line',
    'draw_circle',
    'draw_rectangle',
    'draw_polygon',
    'draw_point',
    'draw_text',
    'BitmapFont',
    'VARNAS',
    'get_color',
    'list_colors',
    'save_png',
    'load_png',
]

# Version
__version__ = "1.0.0"
__author__ = "Visionary RM (Raj Mitra)"
