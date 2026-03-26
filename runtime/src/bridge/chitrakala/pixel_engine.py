# चित्रकला — Pixel Engine
# Pure Python Pixel Manipulation (From Scratch)
# © 2026 Raj Mitra

"""
चित्रकला Pixel Engine — Raw pixel manipulation for VakyaLang.

This module provides:
- ChitraColor: Color representation with Sanskrit names
- ChitraCanvas: Raw pixel buffer for image data

NO external dependencies except Python stdlib.
"""

from typing import Tuple, List, Optional
from dataclasses import dataclass


@dataclass
class ChitraColor:
    """
    Represents an RGB color.
    
    Attributes:
        r: Red component (0-255)
        g: Green component (0-255)
        b: Blue component (0-255)
        a: Alpha component (0-255, 255=opaque)
    """
    r: int
    g: int
    b: int
    a: int = 255
    
    def __post_init__(self):
        """Validate color values."""
        for val in [self.r, self.g, self.b, self.a]:
            if not (0 <= val <= 255):
                raise ValueError(f"Color value must be 0-255, got {val}")
    
    def to_tuple(self) -> Tuple[int, int, int]:
        """Return as (R, G, B) tuple."""
        return (self.r, self.g, self.b)
    
    def to_tuple_rgba(self) -> Tuple[int, int, int, int]:
        """Return as (R, G, B, A) tuple."""
        return (self.r, self.g, self.b, self.a)
    
    def __eq__(self, other):
        if isinstance(other, ChitraColor):
            return (self.r, self.g, self.b, self.a) == (other.r, other.g, other.b, other.a)
        return False
    
    def __repr__(self):
        return f"ChitraColor({self.r}, {self.g}, {self.b}, {self.a})"
    
    @classmethod
    def from_hex(cls, hex_color: str) -> 'ChitraColor':
        """Create color from hex string (#RRGGBB or #RRGGBBAA)."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return cls(r, g, b)
        elif len(hex_color) == 8:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            a = int(hex_color[6:8], 16)
            return cls(r, g, b, a)
        raise ValueError(f"Invalid hex color: {hex_color}")
    
    @classmethod
    def from_gray(cls, value: int) -> 'ChitraColor':
        """Create grayscale color."""
        return cls(value, value, value)
    
    # Predefined colors (Sanskrit names)
    @classmethod
    def shweta(cls) -> 'ChitraColor':
        """White (श्वेत)."""
        return cls(255, 255, 255)
    
    @classmethod
    def krishna(cls) -> 'ChitraColor':
        """Black (कृष्ण)."""
        return cls(0, 0, 0)
    
    @classmethod
    def rakta(cls) -> 'ChitraColor':
        """Red (रक्त)."""
        return cls(255, 0, 0)
    
    @classmethod
    def harita(cls) -> 'ChitraColor':
        """Green (हरित)."""
        return cls(0, 255, 0)
    
    @classmethod
    def nila(cls) -> 'ChitraColor':
        """Blue (नील)."""
        return cls(0, 0, 255)
    
    @classmethod
    def pita(cls) -> 'ChitraColor':
        """Yellow (पीत)."""
        return cls(255, 255, 0)
    
    @classmethod
    def pingala(cls) -> 'ChitraColor':
        """Orange/Brown (पिङ्गल)."""
        return cls(255, 128, 0)
    
    @classmethod
    def dhoomra(cls) -> 'ChitraColor':
        """Gray (धूम्र)."""
        return cls(128, 128, 128)


class ChitraCanvas:
    """
    Raw pixel buffer for image data.
    
    This is the core canvas class that stores pixel data.
    All drawing operations work on this canvas.
    
    Attributes:
        width: Canvas width in pixels
        height: Canvas height in pixels
        pixels: Flat list of ChitraColor objects (row-major order)
    """
    
    def __init__(self, width: int, height: int, background: Optional[ChitraColor] = None):
        """
        Create a new canvas.
        
        Args:
            width: Width in pixels
            height: Height in pixels
            background: Background color (default: white)
        """
        if width <= 0 or height <= 0:
            raise ValueError(f"Canvas dimensions must be positive, got {width}x{height}")
        
        self.width = width
        self.height = height
        self.background = background or ChitraColor.shweta()
        
        # Initialize pixel buffer (row-major order)
        self.pixels = [self.background] * (width * height)
    
    def _index(self, x: int, y: int) -> int:
        """Convert (x, y) to flat buffer index."""
        if not (0 <= x < self.width) or not (0 <= y < self.height):
            raise IndexError(f"Pixel ({x}, {y}) out of bounds [{self.width}x{self.height}]")
        return y * self.width + x
    
    def get_pixel(self, x: int, y: int) -> ChitraColor:
        """Get pixel color at (x, y)."""
        idx = self._index(x, y)
        return self.pixels[idx]
    
    def set_pixel(self, x: int, y: int, color: ChitraColor):
        """Set pixel color at (x, y)."""
        if not (0 <= x < self.width) or not (0 <= y < self.height):
            return  # Clip out-of-bounds pixels silently
        idx = self._index(x, y)
        self.pixels[idx] = color
    
    def fill(self, color: ChitraColor):
        """Fill entire canvas with a color."""
        self.pixels = [color] * (self.width * self.height)
    
    def fill_rectangle(self, x: int, y: int, w: int, h: int, color: ChitraColor):
        """Fill a rectangular region with a color."""
        for cy in range(y, y + h):
            for cx in range(x, x + w):
                if 0 <= cx < self.width and 0 <= cy < self.height:
                    self.set_pixel(cx, cy, color)
    
    def get_row(self, y: int) -> List[ChitraColor]:
        """Get a row of pixels."""
        start = y * self.width
        return self.pixels[start:start + self.width]
    
    def set_row(self, y: int, row: List[ChitraColor]):
        """Set a row of pixels."""
        if len(row) != self.width:
            raise ValueError(f"Row length must be {self.width}, got {len(row)}")
        start = y * self.width
        self.pixels[start:start + self.width] = row
    
    def get_pixel_data(self) -> List[Tuple[int, int, int]]:
        """Get raw RGB pixel data as list of tuples."""
        return [c.to_tuple() for c in self.pixels]
    
    def get_pixel_data_rgba(self) -> List[Tuple[int, int, int, int]]:
        """Get raw RGBA pixel data as list of tuples."""
        return [c.to_tuple_rgba() for c in self.pixels]
    
    def __repr__(self):
        return f"ChitraCanvas({self.width}x{self.height})"
    
    def copy(self) -> 'ChitraCanvas':
        """Create a deep copy of this canvas."""
        new_canvas = ChitraCanvas(self.width, self.height, self.background)
        new_canvas.pixels = self.pixels.copy()
        return new_canvas
