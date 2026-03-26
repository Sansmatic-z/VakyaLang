# चित्रकला — प्रभाव (Chitrakala Effects)
# Chitrakala Advanced Graphics Effects
#
# ═══════════════════════════════════════════════════════════════════════════
# Signature: Visionary RM (Raj Mitra) ⚡
# "Advanced Graphics Effects for VakyaLang" 🔥
# ═══════════════════════════════════════════════════════════════════════════
#
# Month 2-3 Advanced Features: Advanced Chitrakala Effects
# - Gradient fills (linear, radial)
# - Rotation transformations
# - Mandala pattern generation
# - Advanced visual effects
#
# © 2026 Raj Mitra (Visionary RM)

import math
from typing import List, Tuple, Optional
from .pixel_engine import ChitraCanvas, ChitraColor
from .colors import get_color


class ChitraEffects:
    """
    Advanced Chitrakala effects.
    
    Provides:
    - Gradient fills (linear, radial)
    - Rotation transformations
    - Mandala patterns
    - Mirror effects
    - Fractal patterns
    
    Usage:
        canvas = ChitraCanvas(800, 600)
        ChitraEffects.gradient_fill(canvas, 0, 0, 800, 600, 
                                     ChitraColor(255, 0, 0),
                                     ChitraColor(0, 0, 255))
    """
    
    @staticmethod
    def gradient_fill(canvas: ChitraCanvas, 
                     x1: int, y1: int, x2: int, y2: int,
                     color1: ChitraColor, color2: ChitraColor):
        """
        Draw gradient rectangle.
        
        Args:
            canvas: Canvas to draw on
            x1, y1: Top-left corner
            x2, y2: Bottom-right corner
            color1: Start color
            color2: End color
        
        Usage:
            ChitraEffects.gradient_fill(canvas, 0, 0, 800, 600,
                                        ChitraColor(255, 0, 0),  # Red
                                        ChitraColor(0, 0, 255))  # Blue
        """
        # Ensure colors are ChitraColor objects
        if isinstance(color1, str):
            color1 = get_color(color1)
        if isinstance(color2, str):
            color2 = get_color(color2)
        
        height = y2 - y1
        if height <= 0:
            height = 1
        
        for y in range(y1, y2):
            # Calculate interpolation factor
            t = (y - y1) / height
            t = max(0, min(1, t))  # Clamp to [0, 1]
            
            # Interpolate RGB components
            r = int(color1.r * (1 - t) + color2.r * t)
            g = int(color1.g * (1 - t) + color2.g * t)
            b = int(color1.b * (1 - t) + color2.b * t)
            
            # Draw horizontal line
            gradient_color = ChitraColor(r, g, b)
            ChitraEffects.draw_horizontal_line(canvas, x1, y, x2, gradient_color)
    
    @staticmethod
    def radial_gradient(canvas: ChitraCanvas,
                       center_x: int, center_y: int,
                       radius: int,
                       inner_color: ChitraColor,
                       outer_color: ChitraColor):
        """
        Draw radial gradient circle.
        
        Args:
            canvas: Canvas to draw on
            center_x, center_y: Center of gradient
            radius: Radius of gradient
            inner_color: Color at center
            outer_color: Color at edge
        """
        if isinstance(inner_color, str):
            inner_color = get_color(inner_color)
        if isinstance(outer_color, str):
            outer_color = get_color(outer_color)
        
        for y in range(center_y - radius, center_y + radius + 1):
            for x in range(center_x - radius, center_x + radius + 1):
                # Calculate distance from center
                dx = x - center_x
                dy = y - center_y
                dist = math.sqrt(dx * dx + dy * dy)
                
                if dist <= radius:
                    # Calculate interpolation factor
                    t = dist / radius
                    
                    # Interpolate RGB components
                    r = int(inner_color.r * (1 - t) + outer_color.r * t)
                    g = int(inner_color.g * (1 - t) + outer_color.g * t)
                    b = int(inner_color.b * (1 - t) + outer_color.b * t)
                    
                    canvas.set_pixel(x, y, ChitraColor(r, g, b))
    
    @staticmethod
    def rotate(canvas: ChitraCanvas, 
               angle: float, 
               center_x: int, center_y: int) -> ChitraCanvas:
        """
        Rotate canvas around center point.
        
        Args:
            canvas: Canvas to rotate
            angle: Rotation angle in degrees
            center_x, center_y: Center of rotation
        
        Returns:
            New rotated canvas
        
        Usage:
            rotated = ChitraEffects.rotate(canvas, 45, 400, 300)
        """
        # Create rotated copy
        rotated = ChitraCanvas(canvas.width, canvas.height)
        
        # Convert angle to radians
        angle_rad = math.radians(angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        # Rotate each pixel
        for y in range(canvas.height):
            for x in range(canvas.width):
                # Calculate rotated coordinates
                dx = x - center_x
                dy = y - center_y
                
                # Apply rotation matrix
                rx = int(dx * cos_a - dy * sin_a + center_x)
                ry = int(dx * sin_a + dy * cos_a + center_y)
                
                # Check bounds and copy pixel
                if 0 <= rx < canvas.width and 0 <= ry < canvas.height:
                    color = canvas.get_pixel(x, y)
                    rotated.set_pixel(rx, ry, color)
        
        return rotated
    
    @staticmethod
    def mandala_pattern(canvas: ChitraCanvas,
                       center_x: int, center_y: int,
                       radius: int,
                       petals: int,
                       colors: List[ChitraColor]):
        """
        Generate complex mandala pattern.
        
        Args:
            canvas: Canvas to draw on
            center_x, center_y: Center of mandala
            radius: Outer radius
            petals: Number of petals
            colors: List of colors to use
        
        Usage:
            colors = [ChitraColor(255, 0, 0), ChitraColor(0, 255, 0), ChitraColor(0, 0, 255)]
            ChitraEffects.mandala_pattern(canvas, 400, 300, 200, 12, colors)
        """
        # Convert string colors to ChitraColor
        colors = [get_color(c) if isinstance(c, str) else c for c in colors]
        
        if not colors:
            colors = [ChitraColor(255, 255, 255)]
        
        angle_step = 360 / petals
        
        for i in range(petals):
            angle = i * angle_step
            color = colors[i % len(colors)]
            
            # Draw petal
            start_x = int(center_x + math.cos(math.radians(angle)) * radius * 0.3)
            start_y = int(center_y + math.sin(math.radians(angle)) * radius * 0.3)
            end_x = int(center_x + math.cos(math.radians(angle)) * radius)
            end_y = int(center_y + math.sin(math.radians(angle)) * radius)
            
            # Draw line from center to edge
            ChitraEffects.draw_line(canvas, start_x, start_y, end_x, end_y, color)
            
            # Draw concentric circles
            for r in range(radius // 4, radius, radius // 4):
                circle_x = center_x + math.cos(math.radians(angle)) * r
                circle_y = center_y + math.sin(math.radians(angle)) * r
                ChitraEffects.draw_circle(canvas, int(circle_x), int(circle_y), 
                                         radius // 8, color)
    
    @staticmethod
    def mirror_horizontal(canvas: ChitraCanvas) -> ChitraCanvas:
        """
        Create horizontal mirror effect.
        
        Args:
            canvas: Canvas to mirror
        
        Returns:
            New mirrored canvas
        """
        mirrored = ChitraCanvas(canvas.width, canvas.height)
        
        for y in range(canvas.height):
            for x in range(canvas.width):
                color = canvas.get_pixel(x, y)
                mirrored.set_pixel(canvas.width - 1 - x, y, color)
        
        return mirrored
    
    @staticmethod
    def mirror_vertical(canvas: ChitraCanvas) -> ChitraCanvas:
        """
        Create vertical mirror effect.
        
        Args:
            canvas: Canvas to mirror
        
        Returns:
            New mirrored canvas
        """
        mirrored = ChitraCanvas(canvas.width, canvas.height)
        
        for y in range(canvas.height):
            for x in range(canvas.width):
                color = canvas.get_pixel(x, y)
                mirrored.set_pixel(x, canvas.height - 1 - y, color)
        
        return mirrored
    
    @staticmethod
    def kaleidoscope(canvas: ChitraCanvas, segments: int = 8) -> ChitraCanvas:
        """
        Create kaleidoscope effect.
        
        Args:
            canvas: Canvas to process
            segments: Number of segments (must be even)
        
        Returns:
            New kaleidoscope canvas
        """
        if segments % 2 != 0:
            segments = 8
        
        result = ChitraCanvas(canvas.width, canvas.height)
        center_x = canvas.width // 2
        center_y = canvas.height // 2
        
        # Copy one segment and mirror it
        segment_angle = 360 / segments
        
        for y in range(canvas.height):
            for x in range(canvas.width):
                # Get color from source
                color = canvas.get_pixel(x, y)
                
                # Set in all mirrored positions
                for i in range(segments):
                    angle = i * segment_angle
                    angle_rad = math.radians(angle)
                    cos_a = math.cos(angle_rad)
                    sin_a = math.sin(angle_rad)
                    
                    dx = x - center_x
                    dy = y - center_y
                    
                    rx = int(dx * cos_a - dy * sin_a) + center_x
                    ry = int(dx * sin_a + dy * cos_a) + center_y
                    
                    if 0 <= rx < canvas.width and 0 <= ry < canvas.height:
                        result.set_pixel(rx, ry, color)
        
        return result
    
    @staticmethod
    def draw_horizontal_line(canvas: ChitraCanvas, 
                            x1: int, y: int, x2: int, 
                            color: ChitraColor):
        """Draw a horizontal line."""
        if isinstance(color, str):
            color = get_color(color)
        
        for x in range(x1, x2 + 1):
            if 0 <= x < canvas.width and 0 <= y < canvas.height:
                canvas.set_pixel(x, y, color)
    
    @staticmethod
    def draw_line(canvas: ChitraCanvas,
                 x1: int, y1: int, x2: int, y2: int,
                 color: ChitraColor):
        """Draw a line using Bresenham's algorithm."""
        if isinstance(color, str):
            color = get_color(color)
        
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        while True:
            if 0 <= x1 < canvas.width and 0 <= y1 < canvas.height:
                canvas.set_pixel(x1, y1, color)
            
            if x1 == x2 and y1 == y2:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy
    
    @staticmethod
    def draw_circle(canvas: ChitraCanvas,
                   center_x: int, center_y: int,
                   radius: int,
                   color: ChitraColor):
        """Draw a circle using midpoint algorithm."""
        if isinstance(color, str):
            color = get_color(color)
        
        x = 0
        y = radius
        d = 3 - 2 * radius
        
        while y >= x:
            # Draw eight octants
            points = [
                (center_x + x, center_y + y),
                (center_x - x, center_y + y),
                (center_x + x, center_y - y),
                (center_x - x, center_y - y),
                (center_x + y, center_y + x),
                (center_x - y, center_y + x),
                (center_x + y, center_y - x),
                (center_x - y, center_y - x),
            ]
            
            for px, py in points:
                if 0 <= px < canvas.width and 0 <= py < canvas.height:
                    canvas.set_pixel(px, py, color)
            
            x += 1
            if d > 0:
                y -= 1
                d = d + 4 * (x - y) + 10
            else:
                d = d + 4 * x + 6
    
    @staticmethod
    def sierpinski_triangle(canvas: ChitraCanvas,
                           x1: int, y1: int,
                           x2: int, y2: int,
                           x3: int, y3: int,
                           depth: int,
                           color: ChitraColor):
        """
        Draw Sierpinski triangle fractal.
        
        Args:
            canvas: Canvas to draw on
            x1, y1: First vertex
            x2, y2: Second vertex
            x3, y3: Third vertex
            depth: Recursion depth
            color: Color to draw
        """
        if isinstance(color, str):
            color = get_color(color)
        
        if depth == 0:
            # Draw filled triangle
            ChitraEffects.fill_triangle(canvas, x1, y1, x2, y2, x3, y3, color)
        else:
            # Midpoints
            mx1 = (x1 + x2) // 2
            my1 = (y1 + y2) // 2
            mx2 = (x2 + x3) // 2
            my2 = (y2 + y3) // 2
            mx3 = (x1 + x3) // 2
            my3 = (y1 + y3) // 2
            
            # Recurse on three smaller triangles
            ChitraEffects.sierpinski_triangle(canvas, x1, y1, mx1, my1, mx3, my3, 
                                             depth - 1, color)
            ChitraEffects.sierpinski_triangle(canvas, mx1, my1, x2, y2, mx2, my2, 
                                             depth - 1, color)
            ChitraEffects.sierpinski_triangle(canvas, mx3, my3, mx2, my2, x3, y3, 
                                             depth - 1, color)
    
    @staticmethod
    def fill_triangle(canvas: ChitraCanvas,
                     x1: int, y1: int,
                     x2: int, y2: int,
                     x3: int, y3: int,
                     color: ChitraColor):
        """Fill a triangle using scanline algorithm."""
        if isinstance(color, str):
            color = get_color(color)
        
        # Sort vertices by y-coordinate
        points = sorted([(x1, y1), (x2, y2), (x3, y3)], key=lambda p: p[1])
        (x1, y1), (x2, y2), (x3, y3) = points
        
        # Fill triangle
        for y in range(y1, y3 + 1):
            if y < y2:
                # Upper part
                if y2 - y1 == 0:
                    continue
                t = (y - y1) / (y2 - y1)
                lx = int(x1 + t * (x2 - x1))
                rx = int(x1 + t * (x3 - x1))
            else:
                # Lower part
                if y3 - y2 == 0:
                    continue
                t = (y - y2) / (y3 - y2)
                lx = int(x2 + t * (x3 - x2))
                rx = int(x1 + ((y - y1) / (y3 - y1)) * (x3 - x1))
            
            for x in range(min(lx, rx), max(lx, rx) + 1):
                if 0 <= x < canvas.width and 0 <= y < canvas.height:
                    canvas.set_pixel(x, y, color)


# Export public API
__all__ = [
    'ChitraEffects',
]
