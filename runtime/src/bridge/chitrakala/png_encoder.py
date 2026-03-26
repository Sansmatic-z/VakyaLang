# चित्रकला — PNG Encoder (From Scratch)
# Minimal dependencies: Only Python stdlib zlib
# © 2026 Raj Mitra

"""
चित्रकला PNG Encoder — PNG file encoding/decoding from scratch.

This module implements the PNG file format specification:
- PNG signature detection
- Chunk-based structure (IHDR, IDAT, IEND)
- DEFLATE compression via zlib (stdlib)
- CRC-32 checksums
- Filter methods for compression optimization

References:
- PNG Specification (ISO/IEC 15948:2003)
- https://www.w3.org/TR/PNG/
- zlib library (Python stdlib)

Only dependency: zlib (Python standard library)
"""

import zlib
import struct
from typing import List, Tuple, Optional
from .pixel_engine import ChitraCanvas, ChitraColor


# PNG Signature (8 bytes)
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'


def _crc32(data: bytes) -> int:
    """Calculate CRC-32 checksum for a chunk."""
    return zlib.crc32(data) & 0xffffffff


def _create_chunk(chunk_type: bytes, data: bytes) -> bytes:
    """
    Create a PNG chunk.
    
    Chunk structure:
    - Length (4 bytes): Length of data field
    - Type (4 bytes): Chunk type code
    - Data (n bytes): Chunk data
    - CRC (4 bytes): CRC-32 of type + data
    """
    length = struct.pack('>I', len(data))
    crc = struct.pack('>I', _crc32(chunk_type + data))
    return length + chunk_type + data + crc


def _apply_filter(filter_type: int, scanline: List[int], prev_scanline: List[int]) -> List[int]:
    """
    Apply PNG filter method to a scanline.
    
    Filter methods (PNG Spec):
    0: None
    1: Sub (left)
    2: Up (above)
    3: Average (left + above) / 2
    4: Paeth (predictive)
    
    Reference: PNG Specification Section 9
    """
    if filter_type == 0:
        return scanline
    elif filter_type == 1:  # Sub
        result = []
        for i in range(len(scanline)):
            left = scanline[i - 1] if i >= 1 else 0
            result.append((scanline[i] - left) & 0xFF)
        return result
    elif filter_type == 2:  # Up
        result = []
        for i in range(len(scanline)):
            up = prev_scanline[i] if prev_scanline else 0
            result.append((scanline[i] - up) & 0xFF)
        return result
    elif filter_type == 3:  # Average
        result = []
        for i in range(len(scanline)):
            left = scanline[i - 1] if i >= 1 else 0
            up = prev_scanline[i] if prev_scanline else 0
            result.append((scanline[i] - (left + up) // 2) & 0xFF)
        return result
    elif filter_type == 4:  # Paeth
        result = []
        for i in range(len(scanline)):
            left = scanline[i - 1] if i >= 1 else 0
            up = prev_scanline[i] if prev_scanline else 0
            up_left = prev_scanline[i - 1] if (prev_scanline and i >= 1) else 0
            
            paeth = _paeth_predictor(left, up, up_left)
            result.append((scanline[i] - paeth) & 0xFF)
        return result
    else:
        return scanline


def _paeth_predictor(a: int, b: int, c: int) -> int:
    """
    Paeth predictor function for PNG filter method 4.
    
    Reference: PNG Specification Section 9
    """
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    
    if pa <= pb and pa <= pc:
        return a
    elif pb <= pc:
        return b
    else:
        return c


def save_png(canvas: ChitraCanvas, filepath: str, compression_level: int = 6):
    """
    Save canvas as PNG file.
    
    Args:
        canvas: ChitraCanvas to save
        filepath: Output file path
        compression_level: zlib compression level (0-9)
        
    PNG Structure:
    - Signature (8 bytes)
    - IHDR chunk (image header)
    - IDAT chunks (image data, compressed)
    - IEND chunk (end marker)
    """
    width = canvas.width
    height = canvas.height
    pixels = canvas.get_pixel_data()  # List of (R, G, B) tuples
    
    # Build IHDR chunk data
    # Width (4), Height (4), Bit depth (1), Color type (1), 
    # Compression (1), Filter (1), Interlace (1)
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr_chunk = _create_chunk(b'IHDR', ihdr_data)
    
    # Build image data (with filter bytes)
    raw_data = []
    prev_scanline = []
    
    for y in range(height):
        # Add filter byte (0 = no filter)
        filter_type = 0
        raw_data.append(filter_type)
        
        # Get scanline pixels
        scanline = []
        for x in range(width):
            idx = y * width + x
            r, g, b = pixels[idx]
            scanline.extend([r, g, b])
        
        # Apply filter
        filtered = _apply_filter(filter_type, scanline, prev_scanline)
        raw_data.extend(filtered)
        prev_scanline = scanline
    
    # Compress with zlib
    compressed = zlib.compress(bytes(raw_data), compression_level)
    idat_chunk = _create_chunk(b'IDAT', compressed)
    
    # Create IEND chunk
    iend_chunk = _create_chunk(b'IEND', b'')
    
    # Write PNG file
    with open(filepath, 'wb') as f:
        f.write(PNG_SIGNATURE)
        f.write(ihdr_chunk)
        f.write(idat_chunk)
        f.write(iend_chunk)


def load_png(filepath: str) -> ChitraCanvas:
    """
    Load PNG file into ChitraCanvas.
    
    Args:
        filepath: Path to PNG file
        
    Returns:
        ChitraCanvas with loaded image data
    """
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # Verify PNG signature
    if data[:8] != PNG_SIGNATURE:
        raise ValueError("Not a valid PNG file")
    
    # Parse chunks
    pos = 8
    width = height = 0
    image_data = b''
    
    while pos < len(data):
        length = struct.unpack('>I', data[pos:pos+4])[0]
        chunk_type = data[pos+4:pos+8]
        chunk_data = data[pos+8:pos+8+length]
        # crc = data[pos+8+length:pos+12+length]
        
        if chunk_type == b'IHDR':
            width, height = struct.unpack('>II', chunk_data[:8])
        elif chunk_type == b'IDAT':
            image_data += chunk_data
        elif chunk_type == b'IEND':
            break
        
        pos += 12 + length
    
    # Decompress image data
    decompressed = zlib.decompress(image_data)
    
    # Parse scanlines
    canvas = ChitraCanvas(width, height)
    pos = 0
    
    for y in range(height):
        filter_type = decompressed[pos]
        pos += 1
        
        scanline = []
        for x in range(width):
            r = decompressed[pos]
            g = decompressed[pos + 1]
            b = decompressed[pos + 2]
            pos += 3
            scanline.append(ChitraColor(r, g, b))
        
        # Apply reverse filter
        # (simplified - assumes filter type 0)
        for x, color in enumerate(scanline):
            canvas.set_pixel(x, y, color)
    
    return canvas
