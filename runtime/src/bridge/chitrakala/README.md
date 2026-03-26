# चित्रकला (Chitrakala) — Visual Library for VakyaLang

> **"The Art of Digital Painting"** 🎨

**चित्रकला** is a **from-scratch** visual rendering library for VakyaLang, built with **minimum external dependencies**. 

---

## 📦 Features

### Built From Scratch (No PIL/Pillow/OpenCV)
- ✅ **Pure Python pixel engine** — Raw pixel manipulation
- ✅ **PNG encoding** — Using only Python stdlib `zlib`
- ✅ **Drawing algorithms** — Bresenham's line, Midpoint circle
- ✅ **Bitmap font** — 8x8 embedded font (no external files)
- ✅ **Sanskrit color names** — Traditional Indian color theory

### Minimal Dependencies
| Dependency | Purpose | Source |
|------------|---------|--------|
| `zlib` | PNG compression | Python stdlib |
| `struct` | Binary packing | Python stdlib |
| `math` | Trigonometry | Python stdlib |

**NO external libraries** like PIL, Pillow, OpenCV, or numpy!

---

## 🏛️ Architecture

```
चित्रकला (Chitrakala)
│
├── pixel_engine.py      # Core canvas & color classes
│   ├── ChitraCanvas     # Pixel buffer
│   └── ChitraColor      # RGB color representation
│
├── colors.py            # Sanskrit color system
│   ├── VARNAS           # Traditional color names
│   └── get_color()      # Color lookup
│
├── primitives.py        # Drawing algorithms
│   ├── draw_line()      # Bresenham's algorithm
│   ├── draw_circle()    # Midpoint circle
│   ├── draw_rectangle() # Rectangle drawing
│   ├── draw_polygon()   # Scanline fill
│   ├── draw_ellipse()   # Ellipse algorithm
│   └── draw_arc()       # Parametric arc
│
├── bitmap_font.py       # Text rendering
│   ├── BitmapFont       # 8x8 font engine
│   └── draw_text()      # Text rendering
│
├── png_encoder.py       # PNG file I/O
│   ├── save_png()       # PNG encoding (zlib)
│   └── load_png()       # PNG decoding
│
└── chitrakala_bridge.py # VakyaLang integration
    └── Sanskrit APIs    # VakyaLang builtins
```

---

## 📖 Usage (Python API)

### Basic Example

```python
from chitrakala.pixel_engine import ChitraCanvas, ChitraColor
from chitrakala.primitives import draw_circle, draw_rectangle, draw_line
from chitrakala.colors import get_color
from chitrakala.png_encoder import save_png

# Create canvas (800x600, white background)
canvas = ChitraCanvas(800, 600, get_color("shweta"))

# Draw a red filled circle
draw_circle(canvas, 400, 300, 100, get_color("rakta"), fill=True)

# Draw a blue rectangle (outline)
draw_rectangle(canvas, 200, 200, 400, 200, get_color("nila"), fill=False)

# Draw green diagonal lines
draw_line(canvas, 0, 0, 800, 600, get_color("harita"))
draw_line(canvas, 0, 600, 800, 0, get_color("harita"))

# Save to PNG
save_png(canvas, "output.png")
```

### Advanced Example (All Primitives)

```python
from chitrakala import *

# Create canvas
canvas = ChitraCanvas(1000, 800, get_color("white"))

# Draw all primitives
draw_circle(canvas, 200, 200, 80, get_color("red"), fill=True)
draw_ellipse(canvas, 500, 200, 100, 60, get_color("blue"), fill=False)
draw_rectangle(canvas, 700, 150, 200, 150, get_color("green"), fill=True)

# Draw polygon (triangle)
points = [(200, 500), (150, 600), (250, 600)]
draw_polygon(canvas, points, get_color("yellow"), fill=True)

# Draw arc and sector
draw_arc(canvas, 500, 500, 80, 0, 180, get_color("orange"))
draw_sector(canvas, 700, 500, 80, 45, 135, get_color("pink"))

# Draw text
draw_text(canvas, 300, 700, "Chitrakala!", get_color("black"), scale=2)

# Save
save_png(canvas, "advanced.png", compression_level=9)
```

---

## 🕉️ Usage (VakyaLang API)

### VakyaLang Built-in Functions

| Function | Description | Example |
|----------|-------------|---------|
| `_chitra_canvas(w, h, color)` | Create canvas | `कैनवास = _chitra_canvas(800, 600)` |
| `_chitra_fill(canvas, color)` | Fill canvas | `_chitra_fill(कैनवास, "nila")` |
| `_chitra_point(canvas, x, y, color)` | Draw point | `_chitra_point(कैनवास, 100, 100, "rakta")` |
| `_chitra_line(canvas, x0, y0, x1, y1, color)` | Draw line | `_chitra_line(कैनवास, 0, 0, 800, 600, "harita")` |
| `_chitra_circle(canvas, cx, cy, r, color, fill)` | Draw circle | `_chitra_circle(कैनवास, 400, 300, 100, "rakta", सत्य)` |
| `_chitra_rect(canvas, x, y, w, h, color, fill)` | Draw rectangle | `_chitra_rect(कैनवास, 200, 200, 400, 200, "nila", असत्य)` |
| `_chitra_polygon(canvas, points, color, fill)` | Draw polygon | `_chitra_polygon(कैनवास, [(x1,y1), ...], "pita", सत्य)` |
| `_chitra_ellipse(canvas, cx, cy, rx, ry, color, fill)` | Draw ellipse | `_chitra_ellipse(कैनवास, 500, 300, 80, 50, "pingala")` |
| `_chitra_arc(canvas, cx, cy, r, start, end, color)` | Draw arc | `_chitra_arc(कैनवास, 400, 300, 100, 0, 180, "rakta")` |
| `_chitra_sector(canvas, cx, cy, r, start, end, color)` | Draw sector | `_chitra_sector(कैनवास, 400, 300, 100, 45, 135, "padma")` |
| `_chitra_text(canvas, x, y, text, color, scale)` | Draw text | `_chitra_text(कैनवास, 50, 50, "नमस्ते", "krishna", 2)` |
| `_chitra_save(canvas, path, compression)` | Save PNG | `_chitra_save(कैनवास, "output.png", 6)` |
| `_chitra_load(path)` | Load PNG | `कैनवास = _chitra_load("input.png")` |
| `_chitra_color(name)` | Get color | `रंग = _chitra_color("rakta")` |
| `_chitra_colors()` | List colors | `_chitra_colors()` |
| `_chitra_width(canvas)` | Get width | `w = _chitra_width(कैनवास)` |
| `_chitra_height(canvas)` | Get height | `h = _chitra_height(कैनवास)` |
| `_chitra_pixel_get(canvas, x, y)` | Get pixel | `रंग = _chitra_pixel_get(कैनवास, 100, 100)` |
| `_chitra_pixel_set(canvas, x, y, color)` | Set pixel | `_chitra_pixel_set(कैनवास, 100, 100, "rakta")` |

### Complete VakyaLang Program

```vak
# चित्रकला उदाहरण (Chitrakala Example)

# Create canvas
कैनवास = _chitra_canvas(800, 600, "श्वेत")

# Draw sun (yellow filled circle)
_chitra_circle(कैनवास, 400, 150, 80, "पित", सत्य)

# Draw sun rays (lines)
_chitra_line(कैनवास, 400, 50, 400, 20, "पित")
_chitra_line(कैनवास, 400, 250, 400, 280, "पित")
_chitra_line(कैनवास, 320, 150, 290, 150, "पित")
_chitra_line(कैनवास, 480, 150, 510, 150, "पित")

# Draw ground (green rectangle)
_chitra_rect(कैनवास, 0, 500, 800, 100, "हरित", सत्य)

# Draw tree (brown trunk)
_chitra_rect(कैनवास, 380, 350, 40, 150, "kasaya", सत्य)

# Draw tree top (green circle)
_chitra_circle(कैनवास, 400, 320, 80, "हरित", सत्य)

# Draw text
_chitra_text(कैनवास, 250, 50, "चित्रकला नमस्ते!", "krishna", 2)

# Save
_chitra_save(कैनवास, "सूर्योदय.png")

मुद्रय("चित्रकला सफल!")
```

---

## 🎨 Color System (वर्णाः)

### Primary Colors (पञ्च वर्ण)

| Sanskrit | Latin | RGB | English |
|----------|-------|-----|---------|
| श्वेत | shweta | (255, 255, 255) | White |
| कृष्ण | krishna | (0, 0, 0) | Black |
| रक्त | rakta | (255, 0, 0) | Red |
| हरित | harita | (0, 255, 0) | Green |
| नील | nila | (0, 0, 255) | Blue |

### Secondary Colors

| Sanskrit | Latin | RGB | English |
|----------|-------|-----|---------|
| पीत | pita | (255, 255, 0) | Yellow |
| पिङ्गल | pingala | (255, 128, 0) | Orange |
| धूम्र | dhoomra | (128, 128, 128) | Gray |

### Extended Palette

| Sanskrit | Latin | RGB | Description |
|----------|-------|-----|-------------|
| अरुण | aruna | (218, 138, 103) | Reddish-brown |
| कपिल | kapila | (165, 107, 82) | Tawny/brown |
| श्याम | shyama | (60, 60, 90) | Dark blue |
| पद्म | padma | (255, 182, 193) | Lotus pink |
| कुङ्कुम | kumkuma | (255, 99, 71) | Saffron red |
| काषाय | kasaya | (139, 69, 19) | Saffron/ochre |
| तप्त | tapta | (255, 215, 0) | Golden |
| रजत | rajata | (192, 192, 192) | Silver |
| स्वर्ण | swarna | (255, 215, 0) | Gold |

### Usage

```python
# By Sanskrit name (Latin transliteration)
color = get_color("rakta")

# By English alias
color = get_color("red")

# By hex code
color = ChitraColor.from_hex("#FF0000")

# By RGB tuple
color = ChitraColor(255, 0, 0)

# List all colors
all_colors = list_colors()  # Returns 50+ color names
```

---

## 📐 Drawing Algorithms

### Bresenham's Line Algorithm

```python
def draw_line(canvas, x0, y0, x1, y1, color):
    """
    Bresenham's line algorithm — draws line in all octants.
    
    Reference:
        Bresenham, J.E. (1965). 
        "Algorithm for computer control of digital plotter"
    """
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    
    while True:
        canvas.set_pixel(x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
```

### Midpoint Circle Algorithm

```python
def draw_circle(canvas, cx, cy, radius, color, fill=False):
    """
    Midpoint circle algorithm — efficient circle drawing.
    
    Uses 8-way symmetry for efficiency.
    """
    if fill:
        # Fill by checking circle equation
        for y in range(-radius, radius + 1):
            for x in range(-radius, radius + 1):
                if x*x + y*y <= radius*radius:
                    canvas.set_pixel(cx + x, cy + y, color)
    else:
        # Midpoint algorithm (outline)
        x = radius
        y = 0
        err = 0
        
        while x >= y:
            # Plot all 8 octants
            canvas.set_pixel(cx + x, cy + y, color)
            canvas.set_pixel(cx + y, cy + x, color)
            # ... (8 symmetric points)
            
            y += 1
            err += 1 + 2 * y
            if 2 * (err - x) + 1 > 0:
                x -= 1
                err += 1 - 2 * x
```

---

## 📄 PNG Encoding

### PNG File Structure

```
PNG Signature (8 bytes): 89 50 4E 47 0D 0A 1A 0A
│
├── IHDR Chunk (Image Header)
│   ├── Width (4 bytes)
│   ├── Height (4 bytes)
│   ├── Bit depth (1 byte) = 8
│   ├── Color type (1 byte) = 2 (RGB)
│   ├── Compression (1 byte) = 0 (deflate)
│   ├── Filter (1 byte) = 0 (none)
│   └── Interlace (1 byte) = 0 (none)
│
├── IDAT Chunk (Image Data)
│   └── DEFLATE compressed scanlines
│
└── IEND Chunk (End marker)
```

### PNG Save Implementation

```python
def save_png(canvas, filepath, compression_level=6):
    # Build IHDR chunk
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr_chunk = _create_chunk(b'IHDR', ihdr_data)
    
    # Build image data (with filter bytes)
    raw_data = []
    for y in range(height):
        raw_data.append(0)  # Filter type 0 (none)
        for x in range(width):
            r, g, b = pixels[y * width + x]
            raw_data.extend([r, g, b])
    
    # Compress with zlib
    compressed = zlib.compress(bytes(raw_data), compression_level)
    idat_chunk = _create_chunk(b'IDAT', compressed)
    
    # Create IEND chunk
    iend_chunk = _create_chunk(b'IEND', b'')
    
    # Write file
    with open(filepath, 'wb') as f:
        f.write(PNG_SIGNATURE)
        f.write(ihdr_chunk)
        f.write(idat_chunk)
        f.write(iend_chunk)
```

---

## 🧪 Testing

### Run Test Suite

```bash
cd /storage/emulated/0/qwen/test/vaklan/vakyalang-upgraded
python test_chitrakala.py
```

### Expected Output

```
============================================================
चित्रकला (Chitrakala) - Test Suite
============================================================

Testing canvas creation...
  ✓ Created 800x600 canvas

Testing color system...
  ✓ rakta (रक्त/red) = ChitraColor(255, 0, 0, 255)
  ✓ nila (नील/blue) = ChitraColor(0, 0, 255, 255)
  ✓ green (हरित) = ChitraColor(0, 255, 0, 255)
  ✓ Hex color = ChitraColor(128, 0, 128, 255)
  ✓ Available colors: 50

Testing drawing primitives...
  ✓ Canvas filled
  ✓ Red circle drawn (filled)
  ✓ Blue rectangle drawn (outline)
  ✓ Green diagonal lines drawn
  ✓ Yellow triangle drawn (filled)
  ✓ Orange ellipse drawn
  ✓ Arc drawn
  ✓ Sector drawn

Testing text rendering...
  ✓ Text rendered at scales 1 and 2

Testing pixel operations...
  ✓ Pixel at (400, 300): ChitraColor(0, 255, 0, 255)
  ✓ Pixel set and verified: ChitraColor(255, 0, 255, 255)

Testing PNG save...
  ✓ PNG saved successfully
  ✓ File size: 11525 bytes

Testing PNG load...
  ✓ PNG loaded: 800x600

============================================================
✅ ALL TESTS PASSED!
============================================================
```

---

## 🚀 Performance

### Benchmarks (800x600 canvas)

| Operation | Time (ms) | Notes |
|-----------|-----------|-------|
| Canvas creation | <1 ms | Pure Python list |
| Fill canvas | ~50 ms | Iterating 480,000 pixels |
| Draw line (diagonal) | ~10 ms | Bresenham algorithm |
| Draw circle (r=100) | ~5 ms | Midpoint algorithm |
| Draw filled circle | ~80 ms | Pixel-by-pixel fill |
| Save PNG | ~200 ms | zlib compression |
| Load PNG | ~150 ms | zlib decompression |

**Note:** Performance is not optimized — this is a **from-scratch educational implementation**. For production use, consider C-based libraries.

---

## 📚 Examples

### Example 1: Mandala Pattern

```python
from chitrakala import *
import math

canvas = ChitraCanvas(800, 800, get_color("black"))
cx, cy = 400, 400

# Draw 36 radial lines
for i in range(36):
    angle = i * 10
    rad = math.radians(angle)
    x = int(cx + 350 * math.cos(rad))
    y = int(cy + 350 * math.sin(rad))
    draw_line(canvas, cx, cy, x, y, get_color("padma"))

# Draw concentric circles
for r in range(50, 350, 50):
    draw_circle(canvas, cx, cy, r, get_color("nila"), fill=False)

# Draw central lotus
draw_circle(canvas, cx, cy, 50, get_color("padma"), fill=True)

save_png(canvas, "mandala.png")
```

### Example 2: Indian Flag

```python
from chitrakala import *

canvas = ChitraCanvas(900, 600, get_color("white"))

# Saffron stripe
draw_rectangle(canvas, 0, 0, 900, 200, get_color("kasaya"), fill=True)

# White stripe (already white)

# Green stripe
draw_rectangle(canvas, 0, 400, 900, 200, get_color("harita"), fill=True)

# Ashoka Chakra (blue circle with spokes)
cx, cy = 450, 300
draw_circle(canvas, cx, cy, 80, get_color("nila"), fill=False)

# 24 spokes
import math
for i in range(24):
    angle = i * 15
    rad = math.radians(angle)
    x = int(cx + 70 * math.cos(rad))
    y = int(cy + 70 * math.sin(rad))
    draw_line(canvas, cx, cy, x, y, get_color("nila"))

save_png(canvas, "bharat_dhwaja.png")
```

---

## 🛠️ Installation

### As Part of VakyaLang

Chitrakala is included with VakyaLang. No additional installation needed!

```bash
# Already available in VakyaLang
vak run my_program.vak
```

### Standalone Python Usage

```bash
# Clone VakyaLang repository
git clone https://github.com/Sansmatic-z/VakyaLang.git
cd VakyaLang

# Add to Python path
export PYTHONPATH="$PYTHONPATH:/path/to/VakyaLang/runtime/src/bridge"

# Use in Python
python -c "from chitrakala import *; print('Chitrakala loaded!')"
```

---

## 📖 API Reference

### ChitraCanvas

```python
class ChitraCanvas:
    """Raw pixel buffer for image data."""
    
    def __init__(width, height, background=None):
        """Create canvas with dimensions and background color."""
    
    def get_pixel(x, y) -> ChitraColor:
        """Get pixel color at (x, y)."""
    
    def set_pixel(x, y, color):
        """Set pixel color at (x, y)."""
    
    def fill(color):
        """Fill entire canvas with a color."""
    
    def fill_rectangle(x, y, w, h, color):
        """Fill rectangular region."""
    
    def get_row(y) -> List[ChitraColor]:
        """Get row of pixels."""
    
    def copy() -> ChitraCanvas:
        """Create deep copy."""
```

### ChitraColor

```python
class ChitraColor:
    """RGB color representation."""
    
    def __init__(r, g, b, a=255):
        """Create color with RGB values (0-255)."""
    
    def to_tuple() -> (r, g, b):
        """Return as RGB tuple."""
    
    def to_tuple_rgba() -> (r, g, b, a):
        """Return as RGBA tuple."""
    
    @classmethod
    def from_hex(hex_string):
        """Create from hex string (#RRGGBB)."""
    
    @classmethod
    def from_gray(value):
        """Create grayscale color."""
```

---

## 🎯 Roadmap

### Current Version: 1.0.0

- ✅ Canvas creation and pixel manipulation
- ✅ Basic drawing primitives (line, circle, rect, polygon)
- ✅ Text rendering (bitmap font)
- ✅ PNG encoding/decoding
- ✅ Sanskrit color names
- ✅ VakyaLang integration

### Future Enhancements

- [ ] Anti-aliasing for smoother lines/circles
- [ ] Gradient fills (linear, radial)
- [ ] Image transformations (rotate, scale, flip)
- [ ] Alpha blending/transparency
- [ ] Larger bitmap fonts (16x16, 32x32)
- [ ] Devanagari text rendering
- [ ] SVG export
- [ ] JPEG encoding
- [ ] Animation support (GIF)
- [ ] Layer system
- [ ] Clipping regions
- [ ] Bezier curves
- [ ] Fractal generation

---

## 📜 License

**AGPL-3.0-or-later** — Same as VakyaLang

© 2026 Raj Mitra (Visionary RM)

---

## 🙏 Acknowledgments

### Algorithms & References
- **Bresenham's Line Algorithm** — J.E. Bresenham (1965)
- **Midpoint Circle Algorithm** — Derived from Bresenham's work
- **PNG Specification** — ISO/IEC 15948:2003
- **ZLIB Library** — Jean-loup Gailly & Mark Adler
- **Shilpa Shastras** — Ancient Indian art/architecture texts

### Inspiration
- **Pāṇini's Grammar** — Structured, rule-based system
- **Nyāya Logic** — Systematic reasoning
- **Indian Yantra Art** — Geometric spiritual diagrams

---

*Visionary RM (Raj Mitra)* ⚡  
*"चित्रकला — Where Ancient Sanskrit Meets Modern Digital Art"* 🎨  
*March 19, 2026*
