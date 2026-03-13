# -*- coding: utf-8 -*-
"""
Vyākaraṇa - Pāṇinian Grammar Engine
====================================

Integrated Functional Sutra Engine.
Handles the Prakriya (derivation) using actual sutra objects.

*Visionary RM (Raj Mitra)* ⚡
"The Generative DNA" 🔱
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import json
import os

from .core import SanskritWord, Phoneme, ShivaSutraEngine

# ============================================================================
# SUTRA ENGINE
# ============================================================================

class RuleType(Enum):
    SAMJNA = auto(); PARIBHASHA = auto(); VIDHI = auto(); ADHIKARA = auto()

@dataclass
class PrakriyaState:
    phonemes: List[Phoneme]
    metadata: Dict[str, Any] = field(default_factory=dict)
    applied_rules: List[str] = field(default_factory=list)
    def to_str(self): return SanskritWord(self.phonemes).to_devanagari()

class Sutra:
    def __init__(self, number: str, sanskrit: str, rtype: RuleType):
        self.number = number; self.sanskrit = sanskrit; self.rtype = rtype
    def match(self, state: PrakriyaState) -> bool: return False
    def apply(self, state: PrakriyaState) -> PrakriyaState:
        state.applied_rules.append(f"{self.number} ({self.sanskrit})")
        return state

class IkoYanaci(Sutra):
    def __init__(self, shiva: ShivaSutraEngine):
        super().__init__("1.1.3", "इको यणचि", RuleType.VIDHI)
        self.ik = set(shiva.generate_pratyahara("इक्"))
        self.ac = set(shiva.generate_pratyahara("अच्"))
        self.mapping = {'इ': 'य', 'ई': 'य', 'उ': 'व', 'ऊ': 'व', 'ऋ': 'र', 'ॠ': 'र', 'ऌ': 'ल'}
    def match(self, state: PrakriyaState) -> bool:
        for i in range(len(state.phonemes) - 1):
            if state.phonemes[i].symbol in self.ik and state.phonemes[i+1].symbol in self.ac:
                state.metadata['match_idx'] = i; return True
        return False
    def apply(self, state: PrakriyaState) -> PrakriyaState:
        idx = state.metadata.pop('match_idx')
        new_symbol = self.mapping[state.phonemes[idx].symbol]
        state.phonemes[idx] = Phoneme(new_symbol, False)
        return super().apply(state)

class AkahSavarnaDirghah(Sutra):
    """6.1.101 अकः सवर्णे दीर्घः - Savarna Dirgha Sandhi"""
    def __init__(self, shiva: ShivaSutraEngine):
        super().__init__("6.1.101", "अकः सवर्णे दीर्घः", RuleType.VIDHI)
        self.ak = set(shiva.generate_pratyahara("अक्"))
        self.shiva = shiva
        self.dirgha_map = {'अ': 'आ', 'आ': 'आ', 'इ': 'ई', 'ई': 'ई', 'उ': 'ऊ', 'ऊ': 'ऊ', 'ऋ': 'ॠ', 'ॠ': 'ॠ'}
    
    def match(self, state: PrakriyaState) -> bool:
        for i in range(len(state.phonemes) - 1):
            p1 = state.phonemes[i].symbol
            p2 = state.phonemes[i+1].symbol
            if p1 in self.ak:
                savarnas = self.shiva.get_savarnas(p1)
                if p2 in savarnas:
                    state.metadata['match_idx'] = i; return True
        return False
        
    def apply(self, state: PrakriyaState) -> PrakriyaState:
        idx = state.metadata.pop('match_idx')
        p1 = state.phonemes[idx].symbol
        new_symbol = self.dirgha_map.get(p1, p1)
        state.phonemes[idx] = Phoneme(new_symbol, True)
        state.phonemes.pop(idx + 1) # Merge them
        return super().apply(state)

class AadGunah(Sutra):
    """6.1.87 आद् गुणः - Guna Sandhi"""
    def __init__(self, shiva: ShivaSutraEngine):
        super().__init__("6.1.87", "आद् गुणः", RuleType.VIDHI)
        self.a_savarna = self.shiva.get_savarnas("अ") if hasattr(self, 'shiva') else {'अ', 'आ'}
        self.ic = set(shiva.generate_pratyahara("इक्")) # broadly equivalent to relevant vowels here
        
    def match(self, state: PrakriyaState) -> bool:
        for i in range(len(state.phonemes) - 1):
            if state.phonemes[i].symbol in self.a_savarna:
                if state.phonemes[i+1].symbol in {'इ', 'ई', 'उ', 'ऊ', 'ऋ', 'ॠ', 'ऌ'}:
                    state.metadata['match_idx'] = i; return True
        return False
        
    def apply(self, state: PrakriyaState) -> PrakriyaState:
        idx = state.metadata.pop('match_idx')
        p2 = state.phonemes[idx+1].symbol
        mapping = {'इ': 'ए', 'ई': 'ए', 'उ': 'ओ', 'ऊ': 'ओ'}
        if p2 in mapping:
            state.phonemes[idx] = Phoneme(mapping[p2], True)
            state.phonemes.pop(idx + 1)
        elif p2 in {'ऋ', 'ॠ'}:
            state.phonemes[idx] = Phoneme('अ', True)
            state.phonemes[idx+1] = Phoneme('र', False) # Ar
        return super().apply(state)

class VriddhirEci(Sutra):
    """6.1.88 वृद्धिरेचि - Vriddhi Sandhi"""
    def __init__(self, shiva: ShivaSutraEngine):
        super().__init__("6.1.88", "वृद्धिरेचि", RuleType.VIDHI)
        self.a_savarna = {'अ', 'आ'}
        self.ec = set(shiva.generate_pratyahara("एच्")) # e, o, ai, au
        
    def match(self, state: PrakriyaState) -> bool:
        for i in range(len(state.phonemes) - 1):
            if state.phonemes[i].symbol in self.a_savarna and state.phonemes[i+1].symbol in self.ec:
                state.metadata['match_idx'] = i; return True
        return False
        
    def apply(self, state: PrakriyaState) -> PrakriyaState:
        idx = state.metadata.pop('match_idx')
        p2 = state.phonemes[idx+1].symbol
        mapping = {'ए': 'ऐ', 'ऐ': 'ऐ', 'ओ': 'औ', 'औ': 'औ'}
        state.phonemes[idx] = Phoneme(mapping[p2], True)
        state.phonemes.pop(idx + 1)
        return super().apply(state)

class SthohScunaScuh(Sutra):
    """8.4.40 स्तोः श्चुना श्चुः - Scutva Sandhi (Dental + Palatal -> Palatal)"""
    def __init__(self):
        super().__init__("8.4.40", "स्तोः श्चुना श्चुः", RuleType.VIDHI)
        # s or tu (t, th, d, dh, n) + S or cu (c, ch, j, jh, n~) -> S or cu
        self.stu = {'स', 'त', 'थ', 'द', 'ध', 'न'}
        self.scu = {'श', 'च', 'छ', 'ज', 'झ', 'ञ'}
        self.mapping = {'स': 'श', 'त': 'च', 'थ': 'छ', 'द': 'ज', 'ध': 'झ', 'न': 'ञ'}
        
    def match(self, state: PrakriyaState) -> bool:
        for i in range(len(state.phonemes) - 1):
            p1 = state.phonemes[i].symbol
            p2 = state.phonemes[i+1].symbol
            # Applies in both directions (either p1 or p2 can be the palatal trigger)
            if (p1 in self.stu and p2 in self.scu) or (p1 in self.scu and p2 in self.stu):
                state.metadata['match_idx'] = i if p1 in self.stu else i + 1
                return True
        return False
        
    def apply(self, state: PrakriyaState) -> PrakriyaState:
        idx = state.metadata.pop('match_idx')
        old_symbol = state.phonemes[idx].symbol
        state.phonemes[idx] = Phoneme(self.mapping[old_symbol], False)
        return super().apply(state)

class JhalanJasoNte(Sutra):
    """8.2.39 झलां जशोऽन्ते - Jastva Sandhi (Hard consonant to soft consonant at word end/before soft)"""
    # 8.4.53 is झलां जश् झशि (jhal -> jaS before jhaS). We combine the logic for demonstration.
    def __init__(self, shiva: ShivaSutraEngine):
        super().__init__("8.4.53", "झलां जश् झशि", RuleType.VIDHI)
        self.jhal = set(shiva.generate_pratyahara("झल्")) # All non-nasal consonants
        self.jhash = set(shiva.generate_pratyahara("झश्")) # Voiced consonants
        self.jas = set(shiva.generate_pratyahara("जश्")) # j, b, g, d, D
        # Mapping to the 3rd consonant of the same varga
        self.mapping = {
            'क': 'ग', 'ख': 'ग', 'ग': 'ग', 'घ': 'ग',
            'च': 'ज', 'छ': 'ज', 'ज': 'ज', 'झ': 'ज',
            'ट': 'ड', 'ठ': 'ड', 'ड': 'ड', 'ढ': 'ड',
            'त': 'द', 'थ': 'द', 'द': 'द', 'ध': 'द',
            'प': 'ब', 'फ': 'ब', 'ब': 'ब', 'भ': 'ब',
            'श': 'ड', 'ष': 'ड', 'स': 'द', 'ह': 'ग' # Simplification
        }
        
    def match(self, state: PrakriyaState) -> bool:
        for i in range(len(state.phonemes) - 1):
            if state.phonemes[i].symbol in self.jhal and state.phonemes[i+1].symbol in self.jhash:
                state.metadata['match_idx'] = i; return True
        return False
        
    def apply(self, state: PrakriyaState) -> PrakriyaState:
        idx = state.metadata.pop('match_idx')
        old_symbol = state.phonemes[idx].symbol
        new_symbol = self.mapping.get(old_symbol, old_symbol)
        state.phonemes[idx] = Phoneme(new_symbol, False)
        return super().apply(state)

class AshtadhyayiEngine:
    def __init__(self, data_path: Optional[str] = None):
        self.shiva = ShivaSutraEngine()
        self.sutras: List[Sutra] = [
            IkoYanaci(self.shiva),
            AkahSavarnaDirghah(self.shiva),
            AadGunah(self.shiva),
            VriddhirEci(self.shiva),
            SthohScunaScuh(),
            JhalanJasoNte(self.shiva)
        ]
        if data_path: self._load_bulk_sutras(data_path)
        self.sutras.sort(key=lambda s: [int(x) for x in s.number.split('.')])

    def _load_bulk_sutras(self, path: str):
        if not os.path.exists(path): return
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for sid, info in data['sutras'].items():
                self.sutras.append(Sutra(info['Sutra_id'], info['Sutra_text'].strip(' |'), RuleType.VIDHI))

    def derive(self, phonemes: List[Phoneme]) -> PrakriyaState:
        state = PrakriyaState(phonemes)
        for _ in range(50):
            matches = [s for s in self.sutras if type(s) is not Sutra and s.match(state)]
            if not matches: break
            # 1.4.2 Priority: Later rule wins
            state = matches[-1].apply(state)
        return state

# ============================================================================
# DHATUPATHA & CONJUGATION
# ============================================================================

class Dhatupatha:
    def __init__(self, path: str):
        with open(path, 'r', encoding='utf-8') as f: self.dhatus = json.load(f)
    def get_root(self, root_str: str):
        for gana in self.dhatus.values():
            for d in gana:
                if d['root'] == root_str: return d
        return None

class ConjugationEngine:
    def __init__(self, data_dir: str):
        self.dhatupatha = Dhatupatha(os.path.join(data_dir, "dhatupatha/dhatupatha.json"))
        self.ashtadhyayi = AshtadhyayiEngine(os.path.join(data_dir, "sutras/ashtadhyayi.json"))

    def conjugate(self, root_str: str, lakara: str = "lat") -> str:
        dhatu = self.dhatupatha.get_root(root_str)
        if not dhatu: return f"{root_str} (unknown)"
        w1 = SanskritWord.from_devanagari(root_str)
        if dhatu['gana'] == 1: w1.phonemes.append(Phoneme('अ', True))
        w2 = SanskritWord.from_devanagari("ति")
        prakriya = self.ashtadhyayi.derive(w1.phonemes + w2.phonemes)
        return prakriya.to_str()
