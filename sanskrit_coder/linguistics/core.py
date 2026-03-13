# -*- coding: utf-8 -*-
"""
Core Sanskrit Logic - THE HEART
===============================

Integrated phoneme engine, Shiva Sutras, and normalization logic.
Replaces the old placeholder with the functional True Engine logic.

*Visionary RM (Raj Mitra)* ⚡
"The DNA of Sanskrit" 🔱
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Set, List, Optional, Dict, Any

# ============================================================================
# PHONETIC BASE (Varna Properties)
# ============================================================================

class Sthana(Enum):
    URAS = auto(); KANTHA = auto(); SHIRAS = auto(); JIHVAMULA = auto()
    DANTA = auto(); NASIKA = auto(); OSTHA = auto(); TALU = auto()

class AbhyantaraPrayatna(Enum):
    SPRISTA = auto(); ISAT_SPRISTA = auto(); VIVRTA = auto()
    ISAT_VIVRTA = auto(); SAMVRTA = auto()

@dataclass(frozen=True)
class Varna:
    symbol: str
    sthana: Set[Sthana]
    abhyantara: AbhyantaraPrayatna
    is_vowel: bool

# ============================================================================
# SHIVA SUTRAS & PRATYAHARAS
# ============================================================================

SHIVA_SUTRAS = [
    "अ इ उ ण्", "ऋ ऌ क्", "ए ओ ङ्", "ऐ औ च्", "ह य व र ट्", "ल ण्",
    "ञ म ङ ण न म्", "झ भ ञ्", "घ ढ ध ष्", "ज ब ग ड द श्",
    "ख फ छ ठ थ च ट त व्", "क प य्", "श ष स र्", "ह ल्"
]

class ShivaSutraEngine:
    def __init__(self):
        self.sound_positions: List[str] = []
        self.it_markers: Set[str] = set()
        for sutra in SHIVA_SUTRAS:
            parts = sutra.split()
            it_marker = parts[-1]
            self.it_markers.add(it_marker)
            for s in parts[:-1]: self.sound_positions.append(s)
            self.sound_positions.append(it_marker)

    def get_savarnas(self, sound: str) -> Set[str]:
        mapping = {'अ': {'अ', 'आ'}, 'इ': {'इ', 'ई'}, 'उ': {'उ', 'ऊ'}, 'ऋ': {'ऋ', 'ॠ'}, 'ऌ': {'ऌ'}}
        return mapping.get(sound, {sound})

    def generate_pratyahara(self, code: str, include_savarnas: bool = True) -> List[str]:
        start = ""
        end_it = ""
        for i in range(1, len(code)):
            p_start = code[:i]
            p_it = code[i:]
            check_it = p_it if p_it.endswith('्') or p_it in self.it_markers else p_it + '्'
            if check_it in self.it_markers:
                start, end_it = p_start, check_it
                break
        if not start: raise ValueError(f"Invalid Pratyahara: {code}")
        result = []
        started = False
        for s in self.sound_positions:
            if not started and s == start: started = True
            if started:
                if s == end_it: break
                if s not in self.it_markers:
                    if include_savarnas: result.extend(list(self.get_savarnas(s)))
                    else: result.append(s)
        return result

# ============================================================================
# PHONEME ENGINE
# ============================================================================

MATRA_TO_VOWEL = {'ा': 'आ', 'ि': 'इ', 'ी': 'ई', 'ु': 'उ', 'ू': 'ऊ', 'ृ': 'ऋ', 'ॄ': 'ॠ', 'े': 'ए', 'ो': 'ओ', 'ै': 'ऐ', 'ौ': 'औ'}
VOWEL_TO_MATRA = {v: k for k, v in MATRA_TO_VOWEL.items()}

@dataclass
class Phoneme:
    symbol: str
    is_vowel: bool

class SanskritWord:
    def __init__(self, phonemes: List[Phoneme]):
        self.phonemes = phonemes

    @classmethod
    def from_devanagari(cls, text: str):
        res = []; i = 0; vowels = "अआइईउऊऋॠऌएओऐऔ"
        while i < len(text):
            char = text[i]
            if char in vowels: res.append(Phoneme(char, True)); i += 1
            elif i + 1 < len(text) and text[i+1] == '्': res.append(Phoneme(char, False)); i += 2
            elif i + 1 < len(text) and text[i+1] in MATRA_TO_VOWEL:
                res.append(Phoneme(char, False)); res.append(Phoneme(MATRA_TO_VOWEL[text[i+1]], True)); i += 2
            else: res.append(Phoneme(char, False)); res.append(Phoneme('अ', True)); i += 1
        return cls(res)

    def to_devanagari(self) -> str:
        res = ""
        for i, p in enumerate(self.phonemes):
            if p.is_vowel:
                if i > 0 and not self.phonemes[i-1].is_vowel:
                    if p.symbol != 'अ': res += VOWEL_TO_MATRA.get(p.symbol, p.symbol)
                else: res += p.symbol
            else:
                res += p.symbol
                if i + 1 < len(self.phonemes) and not self.phonemes[i+1].is_vowel: res += '्'
                elif i + 1 == len(self.phonemes): res += '्'
        return res
