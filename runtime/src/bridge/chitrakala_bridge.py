# चित्रकला — VakyaLang Bridge
# Integrates Chitrakala library with VakyaLang VM
# © 2026 Raj Mitra

"""
चित्रकला VakyaLang Bridge — Registers image functions as VakyaLang builtins.

This module connects the pure Python rendering engine to VakyaLang,
providing Sanskrit-named functions for VakyaLang programmers.

Usage in VakyaLang:
    आयात चित्रकला
    
    कैनवास = चित्रकला.कैनवास_निर्माण(800, 600)
    चित्रकला.वृत्त(कैनवास, 400, 300, 100, "रक्त")
    चित्रकला.सहेजो(कैनवास, "output.png")
"""

import sys
import os

# Add parent directory to path for imports
bridge_dir = os.path.dirname(os.path.abspath(__file__))
chitrakala_dir = os.path.dirname(bridge_dir)
if chitrakala_dir not in sys.path:
    sys.path.insert(0, chitrakala_dir)

from chitrakala.pixel_engine import ChitraCanvas, ChitraColor
from chitrakala.primitives import (
    draw_line, draw_circle, draw_rectangle, draw_polygon, 
    draw_point, draw_ellipse, draw_arc, draw_sector
)
from chitrakala.colors import get_color, list_colors, VARNAS
from chitrakala.png_encoder import save_png, load_png
from chitrakala.bitmap_font import draw_text, draw_text_centered, BitmapFont


def register_chitrakala_bridge(globals_env):
    """Register all Chitrakala functions into VakyaLang global scope."""
    
    from ..interpreter import BuiltinFunction
    
    # ── Canvas Creation ─────────────────────────────────────────────────────
    
    def _कैनवास_निर्माण(args, kwargs):
        """कैनवास_निर्माण(विस्तार, ऊंचाई, पृष्ठभूमि_रंग='श्वेत') → Canvas"""
        if len(args) < 2:
            raise ValueError("कैनवास_निर्माण: विस्तार और ऊंचाई चाहिए")
        width = int(args[0])
        height = int(args[1])
        bg_color = args[2] if len(args) > 2 else 'श्वेत'
        if isinstance(bg_color, str):
            bg_color = get_color(bg_color)
        return ChitraCanvas(width, height, bg_color)
    
    def _कैनवास_शोधन(args, kwargs):
        """कैनवास_शोधन(कैनवास, रंग) — Fill canvas with color"""
        if len(args) < 2:
            raise ValueError("कैनवास_शोधन: कैनवास और रंग चाहिए")
        canvas = args[0]
        color = get_color(args[1]) if isinstance(args[1], str) else args[1]
        canvas.fill(color)
        return None
    
    # ── Drawing Primitives ──────────────────────────────────────────────────
    
    def _बिन्दु(args, kwargs):
        """बिन्दु(कैनवास, x, y, रंग) — Draw a point"""
        if len(args) < 4:
            raise ValueError("बिन्दु: कैनवास, x, y, रंग चाहिए")
        draw_point(args[0], int(args[1]), int(args[2]), args[3])
        return None
    
    def _रेखा(args, kwargs):
        """रेखा(कैनवास, x0, y0, x1, y1, रंग) — Draw a line"""
        if len(args) < 6:
            raise ValueError("रेखा: कैनवास, x0, y0, x1, y1, रंग चाहिए")
        draw_line(args[0], int(args[1]), int(args[2]), int(args[3]), int(args[4]), args[5])
        return None
    
    def _वृत्त(args, kwargs):
        """वृत्त(कैनवास, केंद्र_x, केंद्र_y, त्रिज्या, रंग, भरण=असत्य) — Draw a circle"""
        if len(args) < 5:
            raise ValueError("वृत्त: कैनवास, केंद्र_x, केंद्र_y, त्रिज्या, रंग चाहिए")
        fill = bool(args[5]) if len(args) > 5 else False
        draw_circle(args[0], int(args[1]), int(args[2]), int(args[3]), args[4], fill)
        return None
    
    def _दीर्घवृत्त(args, kwargs):
        """दीर्घवृत्त(कैनवास, केंद्र_x, केंद्र_y, x_त्रिज्या, y_त्रिज्या, रंग, भरण=असत्य)"""
        if len(args) < 6:
            raise ValueError("दीर्घवृत्त: कैनवास, केंद्र_x, केंद्र_y, x_त्रिज्या, y_त्रिज्या, रंग चाहिए")
        fill = bool(args[6]) if len(args) > 6 else False
        draw_ellipse(args[0], int(args[1]), int(args[2]), int(args[3]), int(args[4]), args[5], fill)
        return None
    
    def _आयत(args, kwargs):
        """आयत(कैनवास, x, y, विस्तार, ऊंचाई, रंग, भरण=असत्य) — Draw a rectangle"""
        if len(args) < 6:
            raise ValueError("आयत: कैनवास, x, y, विस्तार, ऊंचाई, रंग चाहिए")
        fill = bool(args[6]) if len(args) > 6 else False
        draw_rectangle(args[0], int(args[1]), int(args[2]), int(args[3]), int(args[4]), args[5], fill)
        return None
    
    def _बहुभुज(args, kwargs):
        """बहुभुज(कैनवास, बिन्दु_सूची, रंग, भरण=असत्य) — Draw a polygon"""
        if len(args) < 3:
            raise ValueError("बहुभुज: कैनवास, बिन्दु_सूची, रंग चाहिए")
        points = args[1]
        if isinstance(points, (list, tuple)):
            points = [(int(p[0]), int(p[1])) for p in points]
        fill = bool(args[3]) if len(args) > 3 else False
        draw_polygon(args[0], points, args[2], fill)
        return None
    
    def _चाप(args, kwargs):
        """चाप(कैनवास, केंद्र_x, केंद्र_y, त्रिज्या, आरम्भ_कोण, अन्त_कोण, रंग)"""
        if len(args) < 7:
            raise ValueError("चाप: कैनवास, केंद्र_x, केंद्र_y, त्रिज्या, आरम्भ_कोण, अन्त_कोण, रंग चाहिए")
        draw_arc(args[0], int(args[1]), int(args[2]), int(args[3]), 
                 float(args[4]), float(args[5]), args[6])
        return None
    
    def _त्रिज्यखण्ड(args, kwargs):
        """त्रिज्यखण्ड(कैनवास, केंद्र_x, केंद्र_y, त्रिज्या, आरम्भ_कोण, अन्त_कोण, रंग) — Draw a sector"""
        if len(args) < 7:
            raise ValueError("त्रिज्यखण्ड: कैनवास, केंद्र_x, केंद्र_y, त्रिज्या, आरम्भ_कोण, अन्त_कोण, रंग चाहिए")
        draw_sector(args[0], int(args[1]), int(args[2]), int(args[3]),
                    float(args[4]), float(args[5]), args[6])
        return None
    
    # ── Text Rendering ──────────────────────────────────────────────────────
    
    def _पाठ(args, kwargs):
        """पाठ(कैनवास, x, y, पाठ, रंग, स्केल=1) — Draw text"""
        if len(args) < 4:
            raise ValueError("पाठ: कैनवास, x, y, पाठ, रंग चाहिए")
        scale = int(args[4]) if len(args) > 4 else 1
        draw_text(args[0], int(args[1]), int(args[2]), str(args[3]), args[4] if len(args) > 4 else 'krishna', scale=scale)
        return None
    
    def _मध्य_पाठ(args, kwargs):
        """मध्य_पाठ(कैनवास, y, पाठ, रंग, स्केल=1) — Draw centered text"""
        if len(args) < 3:
            raise ValueError("मध्य_पाठ: कैनवास, y, पाठ, रंग चाहिए")
        scale = int(args[4]) if len(args) > 4 else 1
        draw_text_centered(args[0], int(args[1]), str(args[2]), args[3], scale=scale)
        return None
    
    # ── File I/O ────────────────────────────────────────────────────────────
    
    def _सहेजो(args, kwargs):
        """सहेजो(कैनवास, पथ, संपीड़न=6) — Save canvas as PNG"""
        if len(args) < 2:
            raise ValueError("सहेजो: कैनवास और पथ चाहिए")
        compression = int(args[2]) if len(args) > 2 else 6
        save_png(args[0], str(args[1]), compression)
        return None
    
    def _लोड(args, kwargs):
        """लोड(पथ) → Canvas — Load PNG file"""
        if not args:
            raise ValueError("लोड: पथ चाहिए")
        return load_png(str(args[0]))
    
    # ── Color Utilities ─────────────────────────────────────────────────────
    
    def _रंग(args, kwargs):
        """रंग(नाम) → Color — Get color by name"""
        if not args:
            raise ValueError("रंग: नाम चाहिए")
        return get_color(str(args[0]))
    
    def _रंग_सूची(args, kwargs):
        """रंग_सूची() → list — List all available colors"""
        return list_colors()
    
    def _वर्ण(args, kwargs):
        """वर्ण() → dict — Get all Sanskrit color names"""
        return VARNAS
    
    # ── Canvas Properties ───────────────────────────────────────────────────
    
    def _विस्तार(args, kwargs):
        """विस्तार(कैनवास) → int — Get canvas width"""
        if not args:
            raise ValueError("विस्तार: कैनवास चाहिए")
        return args[0].width
    
    def _ऊंचाई(args, kwargs):
        """ऊंचाई(कैनवास) → int — Get canvas height"""
        if not args:
            raise ValueError("ऊंचाई: कैनवास चाहिए")
        return args[0].height
    
    def _पिक्सेल(args, kwargs):
        """पिक्सेल(कैनवास, x, y) → Color — Get pixel color"""
        if len(args) < 3:
            raise ValueError("पिक्सेल: कैनवास, x, y चाहिए")
        return args[0].get_pixel(int(args[1]), int(args[2]))
    
    def _पिक्सेल_सेट(args, kwargs):
        """पिक्सेल_सेट(कैनवास, x, y, रंग) — Set pixel color"""
        if len(args) < 4:
            raise ValueError("पिक्सेल_सेट: कैनवास, x, y, रंग चाहिए")
        args[0].set_pixel(int(args[1]), int(args[2]), args[3])
        return None
    
    # ── Registration ────────────────────────────────────────────────────────
    
    chitrakala_builtins = {
        # Canvas creation
        "कैनवास_निर्माण": _कैनवास_निर्माण,
        "कैनवास_शोधन": _कैनवास_शोधन,
        
        # Drawing primitives
        "बिन्दु": _बिन्दु,
        "रेखा": _रेखा,
        "वृत्त": _वृत्त,
        "दीर्घवृत्त": _दीर्घवृत्त,
        "आयत": _आयत,
        "बहुभुज": _बहुभुज,
        "चाप": _चाप,
        "त्रिज्यखण्ड": _त्रिज्यखण्ड,
        
        # Text rendering
        "पाठ": _पाठ,
        "मध्य_पाठ": _मध्य_पाठ,
        
        # File I/O
        "सहेजो": _सहेजो,
        "लोड": _लोड,
        
        # Color utilities
        "रंग": _रंग,
        "रंग_सूची": _रंग_सूची,
        "वर्ण": _वर्ण,
        
        # Canvas properties
        "विस्तार": _विस्तार,
        "ऊंचाई": _ऊंचाई,
        "पिक्सेल": _पिक्सेल,
        "पिक्सेल_सेट": _पिक्सेल_सेट,
    }
    
    for name, fn in chitrakala_builtins.items():
        globals_env.define(name, BuiltinFunction(name, fn))


# Convenience function to get module info
def get_module_info():
    """Return Chitrakala module information."""
    return {
        "name": "चित्रकला (Chitrakala)",
        "version": "1.0.0",
        "description": "Visual library for VakyaLang — Art of Digital Painting",
        "author": "Visionary RM (Raj Mitra)",
        "features": [
            "Pure Python rendering (from scratch)",
            "Sanskrit-named APIs",
            "PNG encoding/decoding",
            "Drawing primitives (line, circle, rectangle, polygon)",
            "Text rendering (bitmap font)",
            "Traditional Sanskrit color names",
            "Minimal dependencies (only zlib from stdlib)",
        ],
        "usage_example": """
आयात चित्रकला

# Create canvas (800x600, white background)
कैनवास = चित्रकला.कैनवास_निर्माण(800, 600)

# Draw shapes
चित्रकला.वृत्त(कैनवास, 400, 300, 100, "रक्त")
चित्रकला.आयत(कैनवास, 200, 200, 400, 200, "नील", असत्य)
चित्रकला.रेखा(कैनवास, 0, 0, 800, 600, "हरित")

# Draw text
चित्रकला.मध्य_पाठ(कैनवास, 300, "नमस्ते विश्व!", "krishna", स्केल=2)

# Save to file
चित्रकला.सहेजो(कैनवास, "output.png")
"""
    }
