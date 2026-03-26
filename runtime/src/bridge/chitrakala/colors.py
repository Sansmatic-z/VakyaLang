# चित्रकला — Sanskrit Color System
# © 2026 Raj Mitra

"""
चित्रकला Color System — Sanskrit Color Names for VakyaLang.

This module provides traditional Sanskrit color names (वर्णाः)
mapped to RGB values, following traditional Indian color theory.

Reference: Ancient Indian color theory from Shilpa Shastras.
"""

from typing import Dict, Tuple, Optional
from .pixel_engine import ChitraColor


# Traditional Sanskrit Color Names (वर्णाः)
VARNAS: Dict[str, Tuple[int, int, int]] = {
    # Primary colors (पञ्च वर्ण)
    "श्वेत": (255, 255, 255),      # White
    "krishna": (0, 0, 0),          # Black (कृष्ण)
    "rakta": (255, 0, 0),          # Red (रक्त)
    "harita": (0, 255, 0),         # Green (हरित)
    "nila": (0, 0, 255),           # Blue (नील)
    
    # Secondary colors
    "pita": (255, 255, 0),         # Yellow (पीत)
    "pingala": (255, 128, 0),      # Orange/Brown (पिङ्गल)
    "dhoomra": (128, 128, 128),    # Gray (धूम्र)
    
    # Extended palette (traditional)
    "aruna": (218, 138, 103),      # Reddish-brown (अरुण)
    "kapila": (165, 107, 82),      # Tawny/brown (कपिल)
    "shyama": (60, 60, 90),        # Dark blue/black (श्याम)
    "padma": (255, 182, 193),      # Lotus pink (पद्म)
    "kumkuma": (255, 99, 71),      # Saffron red (कुङ्कुम)
    "kasaya": (139, 69, 19),       # Saffron/ochre (काषाय)
    "hari": (0, 128, 0),           # Dark green (हरि)
    "indragopa": (220, 20, 60),    # Crimson (इन्द्रगोप)
    "jamuna": (65, 105, 225),      # Royal blue (जमुन)
    "tapta": (255, 215, 0),        # Golden (तप्त)
    "rajata": (192, 192, 192),     # Silver (रजत)
    "swarna": (255, 215, 0),       # Gold (स्वर्ण)
    "mrinala": (255, 250, 240),    # Lotus fiber white (मृणाल)
    "manjishtha": (227, 38, 54),   # Madder red (मञ्जिष्ठ)
    "nilotpala": (60, 80, 120),    # Blue lotus (नीलोत्पल)
    "palasha": (255, 127, 80),     # Flame of forest (पलाश)
    "parpata": (255, 239, 213),    # Pale yellow (पर्पट)
    
    # Modern additions (Sanskritized)
    "neela": (0, 0, 139),          # Dark blue (नील)
    "rakta_pita": (255, 128, 0),   # Orange (रक्तपीत)
    "shweta_nila": (173, 216, 230),# Light blue (श्वेतनील)
    "harita_nila": (0, 128, 128),  # Teal (हरितनील)
}


# English aliases for convenience
ENGLISH_ALIASES: Dict[str, str] = {
    "white": "श्वेत",
    "shweta": "श्वेत",
    "black": "krishna",
    "red": "rakta",
    "rakta": "rakta",
    "green": "harita",
    "harita": "harita",
    "blue": "nila",
    "nila": "nila",
    "yellow": "pita",
    "pita": "pita",
    "orange": "pingala",
    "pingala": "pingala",
    "gray": "dhoomra",
    "grey": "dhoomra",
    "dhoomra": "dhoomra",
    "pink": "padma",
    "brown": "kapila",
    "purple": "shyama",
    "gold": "swarna",
    "silver": "rajata",
}


def get_color(name: str) -> ChitraColor:
    """
    Get a color by name (Sanskrit or English).
    
    Args:
        name: Color name in Sanskrit (Devanagari or Latin) or English
        
    Returns:
        ChitraColor object
        
    Raises:
        ValueError: If color name not found
    """
    # Try direct lookup first
    if name in VARNAS:
        r, g, b = VARNAS[name]
        return ChitraColor(r, g, b)
    
    # Try English alias
    if name.lower() in ENGLISH_ALIASES:
        sanskrit_name = ENGLISH_ALIASES[name.lower()]
        return get_color(sanskrit_name)
    
    # Try to parse hex color
    if name.startswith('#'):
        return ChitraColor.from_hex(name)
    
    # Try to parse RGB tuple
    if isinstance(name, (tuple, list)) and len(name) == 3:
        return ChitraColor(name[0], name[1], name[2])
    
    raise ValueError(f"Unknown color: {name}. Use list_colors() to see available colors.")


def list_colors() -> list:
    """Return list of all available color names."""
    return list(VARNAS.keys()) + list(ENGLISH_ALIASES.keys())


def color_palette(palette_name: str = "pancha_varna") -> list:
    """
    Get a predefined color palette.
    
    Args:
        palette_name: Name of palette
            - "pancha_varna": Five primary colors
            - "warm": Warm colors
            - "cool": Cool colors
            - "earth": Earth tones
            - "all": All colors
            
    Returns:
        List of (name, ChitraColor) tuples
    """
    palettes = {
        "pancha_varna": ["श्वेत", "krishna", "rakta", "harita", "nila"],
        "warm": ["rakta", "pita", "pingala", "kumkuma", "kasaya", "tapta"],
        "cool": ["nila", "harita", "shyama", "nilotpala", "jamuna"],
        "earth": ["kapila", "kasaya", "dhoomra", "aruna", "parpata"],
        "all": list(VARNAS.keys()),
    }
    
    if palette_name not in palettes:
        raise ValueError(f"Unknown palette: {palette_name}")
    
    result = []
    for name in palettes[palette_name]:
        result.append((name, get_color(name)))
    return result
