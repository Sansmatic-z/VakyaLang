#!/usr/bin/env python3
# चित्रकला — परीक्षण कार्यक्रम (Test Program)
# Tests the Chitrakala visual library
# © 2026 Raj Mitra

"""
This script tests the Chitrakala library independently of VakyaLang VM.
Run this first to verify the rendering engine works correctly.
"""

import sys
import os

# Add runtime/src/bridge to path
bridge_dir = os.path.join(os.path.dirname(__file__), 'runtime', 'src', 'bridge')
if bridge_dir not in sys.path:
    sys.path.insert(0, bridge_dir)

from chitrakala.pixel_engine import ChitraCanvas, ChitraColor
from chitrakala.primitives import (
    draw_line, draw_circle, draw_rectangle, draw_polygon, 
    draw_point, draw_ellipse, draw_arc, draw_sector
)
from chitrakala.colors import get_color, list_colors, VARNAS
from chitrakala.png_encoder import save_png, load_png
from chitrakala.bitmap_font import draw_text, BitmapFont


def test_canvas_creation():
    """Test canvas creation."""
    print("Testing canvas creation...")
    canvas = ChitraCanvas(800, 600)
    assert canvas.width == 800
    assert canvas.height == 600
    print(f"  ✓ Created {canvas.width}x{canvas.height} canvas")
    return canvas


def test_colors():
    """Test color system."""
    print("Testing color system...")
    
    # Test Sanskrit colors (Latin transliteration)
    rakta = get_color("rakta")
    assert rakta.r == 255 and rakta.g == 0 and rakta.b == 0
    print(f"  ✓ rakta (रक्त/red) = {rakta}")
    
    nila = get_color("nila")
    assert nila.r == 0 and nila.g == 0 and nila.b == 255
    print(f"  ✓ nila (नील/blue) = {nila}")
    
    # Test English aliases
    green = get_color("green")
    print(f"  ✓ green (हरित) = {green}")
    
    # Test hex colors
    purple = ChitraColor.from_hex("#800080")
    print(f"  ✓ Hex color = {purple}")
    
    # List all colors
    colors = list_colors()
    print(f"  ✓ Available colors: {len(colors)}")
    return True


def test_drawing_primitives(canvas):
    """Test drawing primitives."""
    print("Testing drawing primitives...")
    
    # Fill with white
    canvas.fill(get_color("shweta"))
    print("  ✓ Canvas filled")
    
    # Draw red circle
    draw_circle(canvas, 400, 300, 100, get_color("rakta"), fill=True)
    print("  ✓ Red circle drawn (filled)")
    
    # Draw blue rectangle
    draw_rectangle(canvas, 200, 200, 400, 200, get_color("nila"), fill=False)
    print("  ✓ Blue rectangle drawn (outline)")
    
    # Draw green lines
    draw_line(canvas, 0, 0, 800, 600, get_color("harita"))
    draw_line(canvas, 0, 600, 800, 0, get_color("harita"))
    print("  ✓ Green diagonal lines drawn")
    
    # Draw yellow triangle
    points = [(400, 50), (350, 150), (450, 150)]
    draw_polygon(canvas, points, get_color("pita"), fill=True)
    print("  ✓ Yellow triangle drawn (filled)")
    
    # Draw ellipse
    draw_ellipse(canvas, 600, 450, 80, 50, get_color("pingala"), fill=False)
    print("  ✓ Orange ellipse drawn")
    
    # Draw arc
    draw_arc(canvas, 200, 450, 60, 0, 180, get_color("shyama"))
    print("  ✓ Arc drawn")
    
    # Draw sector
    draw_sector(canvas, 650, 150, 70, 45, 135, get_color("padma"))
    print("  ✓ Sector drawn")
    
    return True


def test_text_rendering(canvas):
    """Test text rendering."""
    print("Testing text rendering...")
    
    # Draw text at different scales
    draw_text(canvas, 50, 30, "Chitrakala!", get_color("krishna"), scale=1)
    draw_text(canvas, 50, 50, "Namaste!", get_color("rakta"), scale=2)
    print("  ✓ Text rendered at scales 1 and 2")
    
    return True


def test_save_png(canvas, filepath="test_output.png"):
    """Test PNG saving."""
    print(f"Testing PNG save to {filepath}...")
    save_png(canvas, filepath)
    print(f"  ✓ PNG saved successfully")
    
    # Verify file exists
    assert os.path.exists(filepath)
    file_size = os.path.getsize(filepath)
    print(f"  ✓ File size: {file_size} bytes")
    
    return filepath


def test_load_png(filepath):
    """Test PNG loading."""
    print(f"Testing PNG load from {filepath}...")
    loaded_canvas = load_png(filepath)
    print(f"  ✓ PNG loaded: {loaded_canvas.width}x{loaded_canvas.height}")
    return loaded_canvas


def test_pixel_operations(canvas):
    """Test pixel-level operations."""
    print("Testing pixel operations...")
    
    # Get pixel
    pixel = canvas.get_pixel(400, 300)
    print(f"  ✓ Pixel at (400, 300): {pixel}")
    
    # Set pixel
    canvas.set_pixel(100, 100, ChitraColor(255, 0, 255))
    pixel = canvas.get_pixel(100, 100)
    assert pixel.r == 255 and pixel.b == 255
    print(f"  ✓ Pixel set and verified: {pixel}")
    
    return True


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("चित्रकला (Chitrakala) - Test Suite")
    print("=" * 60)
    print()
    
    # Test 1: Canvas creation
    canvas = test_canvas_creation()
    print()
    
    # Test 2: Color system
    test_colors()
    print()
    
    # Test 3: Drawing primitives
    test_drawing_primitives(canvas)
    print()
    
    # Test 4: Text rendering
    test_text_rendering(canvas)
    print()
    
    # Test 5: Pixel operations
    test_pixel_operations(canvas)
    print()
    
    # Test 6: Save PNG
    filepath = test_save_png(canvas)
    print()
    
    # Test 7: Load PNG
    test_load_png(filepath)
    print()
    
    print("=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print()
    print(f"Output file: {os.path.abspath(filepath)}")
    print()
    print("चित्रकला is ready for VakyaLang integration!")
    print()
    print("*Visionary RM (Raj Mitra)* ⚡")
    print('"चित्रकला - Art of Digital Painting" 🎨')


if __name__ == "__main__":
    run_all_tests()
