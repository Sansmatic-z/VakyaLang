# चित्रकला — Drawing Primitives
# Algorithms implemented from scratch (no external libraries)
# © 2026 Raj Mitra

"""
चित्रकला Drawing Primitives — Geometric drawing algorithms.

Implements:
- Bresenham's Line Algorithm (ब्रेसेनहैम रेखा)
- Midpoint Circle Algorithm (मध्यबिन्दु वृत्त)
- Rectangle/Polygon filling
- Point plotting

All algorithms implemented from scratch using pure Python.
References:
- Bresenham, J.E. (1965). "Algorithm for computer control of digital plotter"
- Ancient Indian geometric principles from Shulba Sutras
"""

from typing import Tuple, List, Optional
from .pixel_engine import ChitraCanvas, ChitraColor
from .colors import get_color


def draw_point(canvas: ChitraCanvas, x: int, y: int, color):
    """
    Draw a single pixel (बिन्दु).
    
    Args:
        canvas: Canvas to draw on
        x: X coordinate
        y: Y coordinate
        color: Color (name or ChitraColor)
    """
    if isinstance(color, str):
        color = get_color(color)
    canvas.set_pixel(x, y, color)


def draw_line(canvas: ChitraCanvas, x0: int, y0: int, x1: int, y1: int, color):
    """
    Draw a line using Bresenham's algorithm (रेखा).
    
    This is the classic Bresenham line algorithm, implemented from scratch.
    Works for all octants (all directions and slopes).
    
    Args:
        canvas: Canvas to draw on
        x0, y0: Start point
        x1, y1: End point
        color: Color (name or ChitraColor)
        
    Reference:
        Bresenham, J.E. (1965). "Algorithm for computer control of digital plotter"
    """
    if isinstance(color, str):
        color = get_color(color)
    
    # Bresenham's Line Algorithm
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


def draw_circle(canvas: ChitraCanvas, cx: int, cy: int, radius: int, color, fill: bool = False):
    """
    Draw a circle using midpoint algorithm (वृत्त).
    
    Uses the midpoint circle algorithm for efficient circle drawing.
    Can draw outline or filled circle.
    
    Args:
        canvas: Canvas to draw on
        cx, cy: Center point
        radius: Circle radius
        color: Color (name or ChitraColor)
        fill: If True, fill the circle; if False, draw outline only
        
    Reference:
        Midpoint circle algorithm (derived from Bresenham's work)
    """
    if isinstance(color, str):
        color = get_color(color)
    
    if fill:
        # Fill the circle by drawing horizontal lines
        for y in range(-radius, radius + 1):
            for x in range(-radius, radius + 1):
                if x*x + y*y <= radius*radius:
                    canvas.set_pixel(cx + x, cy + y, color)
    else:
        # Midpoint Circle Algorithm (outline)
        x = radius
        y = 0
        err = 0
        
        while x >= y:
            # Plot all 8 octants
            canvas.set_pixel(cx + x, cy + y, color)
            canvas.set_pixel(cx + y, cy + x, color)
            canvas.set_pixel(cx - y, cy + x, color)
            canvas.set_pixel(cx - x, cy + y, color)
            canvas.set_pixel(cx - x, cy - y, color)
            canvas.set_pixel(cx - y, cy - y, color)
            canvas.set_pixel(cx + y, cy - x, color)
            canvas.set_pixel(cx + x, cy - y, color)
            
            y += 1
            err += 1 + 2 * y
            if 2 * (err - x) + 1 > 0:
                x -= 1
                err += 1 - 2 * x


def draw_rectangle(canvas: ChitraCanvas, x: int, y: int, w: int, h: int, color, fill: bool = False):
    """
    Draw a rectangle (आयत).
    
    Args:
        canvas: Canvas to draw on
        x, y: Top-left corner
        w: Width
        h: Height
        color: Color (name or ChitraColor)
        fill: If True, fill the rectangle; if False, draw outline only
    """
    if isinstance(color, str):
        color = get_color(color)
    
    if fill:
        canvas.fill_rectangle(x, y, w, h, color)
    else:
        # Draw outline
        draw_line(canvas, x, y, x + w, y, color)           # Top
        draw_line(canvas, x + w, y, x + w, y + h, color)   # Right
        draw_line(canvas, x + w, y + h, x, y + h, color)   # Bottom
        draw_line(canvas, x, y + h, x, y, color)           # Left


def draw_polygon(canvas: ChitraCanvas, points: List[Tuple[int, int]], color, fill: bool = False):
    """
    Draw a polygon (बहुभुज).
    
    Args:
        canvas: Canvas to draw on
        points: List of (x, y) vertices
        color: Color (name or ChitraColor)
        fill: If True, fill the polygon; if False, draw outline only
        
    Reference:
        Scanline polygon fill algorithm
    """
    if isinstance(color, str):
        color = get_color(color)
    
    if len(points) < 3:
        raise ValueError("Polygon needs at least 3 points")
    
    if fill:
        _fill_polygon_scanline(canvas, points, color)
    else:
        # Draw edges
        for i in range(len(points)):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % len(points)]
            draw_line(canvas, x0, y0, x1, y1, color)


def _fill_polygon_scanline(canvas: ChitraCanvas, points: List[Tuple[int, int]], color: ChitraColor):
    """
    Fill polygon using scanline algorithm.
    
    Reference: Traditional scanline polygon rasterization.
    """
    if not points:
        return
    
    # Find bounding box
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    
    # Scanline fill
    for y in range(min_y, max_y + 1):
        # Find intersections with polygon edges
        intersections = []
        for i in range(len(points)):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % len(points)]
            
            # Check if edge crosses this scanline
            if min(y0, y1) <= y < max(y0, y1):
                # Calculate intersection x coordinate
                x = x0 + (y - y0) * (x1 - x0) // (y1 - y0) if y1 != y0 else x0
                intersections.append(x)
        
        # Sort intersections and fill between pairs
        intersections.sort()
        for i in range(0, len(intersections) - 1, 2):
            if i + 1 < len(intersections):
                for x in range(intersections[i], intersections[i + 1] + 1):
                    canvas.set_pixel(x, y, color)


def draw_ellipse(canvas: ChitraCanvas, cx: int, cy: int, rx: int, ry: int, color, fill: bool = False):
    """
    Draw an ellipse (दीर्घवृत्त).
    
    Args:
        canvas: Canvas to draw on
        cx, cy: Center point
        rx: X radius (semi-major axis)
        ry: Y radius (semi-minor axis)
        color: Color (name or ChitraColor)
        fill: If True, fill the ellipse; if False, draw outline only
    """
    if isinstance(color, str):
        color = get_color(color)
    
    if fill:
        # Fill by checking ellipse equation
        for y in range(-ry, ry + 1):
            for x in range(-rx, rx + 1):
                if (x*x)/(rx*rx) + (y*y)/(ry*ry) <= 1:
                    canvas.set_pixel(cx + x, cy + y, color)
    else:
        # Midpoint ellipse algorithm (simplified)
        x = 0
        y = ry
        rx_sq = rx * rx
        ry_sq = ry * ry
        two_rx_sq = 2 * rx_sq
        two_ry_sq = 2 * ry_sq
        
        # Region 1
        p1 = ry_sq - rx_sq * ry + 0.25 * rx_sq
        dx = two_ry_sq * x
        dy = two_rx_sq * y
        
        while dx < dy:
            canvas.set_pixel(cx + x, cy + y, color)
            canvas.set_pixel(cx - x, cy + y, color)
            canvas.set_pixel(cx + x, cy - y, color)
            canvas.set_pixel(cx - x, cy - y, color)
            
            if p1 < 0:
                x += 1
                dx += two_ry_sq
                p1 += dx + ry_sq
            else:
                x += 1
                y -= 1
                dx += two_ry_sq
                dy -= two_rx_sq
                p1 += dx - dy + ry_sq
        
        # Region 2
        p2 = ry_sq * (x + 0.5) ** 2 + rx_sq * (y - 1) ** 2 - rx_sq * ry_sq
        while y >= 0:
            canvas.set_pixel(cx + x, cy + y, color)
            canvas.set_pixel(cx - x, cy + y, color)
            canvas.set_pixel(cx + x, cy - y, color)
            canvas.set_pixel(cx - x, cy - y, color)
            
            if p2 > 0:
                y -= 1
                dy -= two_rx_sq
                p2 += rx_sq - dy
            else:
                y -= 1
                x += 1
                dy -= two_rx_sq
                dx += two_ry_sq
                p2 += dx - dy + rx_sq


def draw_arc(canvas: ChitraCanvas, cx: int, cy: int, radius: int, 
             start_angle: float, end_angle: float, color):
    """
    Draw an arc (चाप).
    
    Args:
        canvas: Canvas to draw on
        cx, cy: Center point
        radius: Arc radius
        start_angle: Start angle in degrees (0 = right, counter-clockwise)
        end_angle: End angle in degrees
        color: Color (name or ChitraColor)
    """
    if isinstance(color, str):
        color = get_color(color)
    
    import math
    start_rad = math.radians(start_angle)
    end_rad = math.radians(end_angle)
    
    # Draw arc using parametric equation
    steps = int(abs(end_angle - start_angle)) + 1
    for i in range(steps):
        t = start_rad + (end_rad - start_rad) * i / steps
        x = cx + int(radius * math.cos(t))
        y = cy + int(radius * math.sin(t))
        canvas.set_pixel(x, y, color)


def draw_sector(canvas: ChitraCanvas, cx: int, cy: int, radius: int,
                start_angle: float, end_angle: float, color):
    """
    Draw a filled sector/pie slice (त्रिज्यखण्ड).
    
    Args:
        canvas: Canvas to draw on
        cx, cy: Center point
        radius: Sector radius
        start_angle: Start angle in degrees
        end_angle: End angle in degrees
        color: Color (name or ChitraColor)
    """
    if isinstance(color, str):
        color = get_color(color)
    
    import math
    
    # Fill sector by scanning angles
    start_rad = math.radians(start_angle)
    end_rad = math.radians(end_angle)
    
    for r in range(radius + 1):
        for i in range(int(abs(end_angle - start_angle)) + 1):
            t = start_rad + (end_rad - start_rad) * i / max(1, int(abs(end_angle - start_angle)))
            x = cx + int(r * math.cos(t))
            y = cy + int(r * math.sin(t))
            canvas.set_pixel(x, y, color)
