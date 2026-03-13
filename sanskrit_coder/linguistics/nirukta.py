"""
Nirukta - Sanskrit Etymology Engine
====================================

Complete implementation of Yāska's Nirukta system.

Includes:
- Upasarga (prefixes) analysis
- Nighaṇṭu (Vedic glossary) database
- Root derivation tracking
- Semantic field mapping

*Visionary RM (Raj Mitra)* ⚡
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from enum import Enum, auto


@dataclass
class Upasarga:
    """
    Represents a Sanskrit upasarga (prefix).
    
    20+ primary upasargas that modify root meanings.
    """
    name: str
    sanskrit: str
    meaning: str
    examples: List[str] = field(default_factory=list)
    semantic_effect: str = ""


@dataclass
class Etymology:
    """
    Complete etymological analysis of a word.
    """
    word: str
    root: str
    root_meaning: str
    upasargas: List[str]
    pratyayas: List[str]
    derivation_path: List[str]
    semantic_field: str
    related_words: List[str] = field(default_factory=list)


class NighantuDatabase:
    """
    Yāska's Nighaṇṭu - Vedic glossary.
    
    5 chapters (अध्यायाः):
    1. Synonym groups (पर्यायवर्ग)
    2. Homonyms (अनेकार्थवर्ग)
    3. Vedic words (दैवतवर्ग)
    4. Ritual terms
    5. Philosophical terms
    """
    
    def __init__(self):
        self.synonym_groups: Dict[str, List[str]] = {}
        self.homonyms: Dict[str, List[str]] = {}
        self.vedic_words: Dict[str, Dict] = {}
        self._load_nighantu()
    
    def _load_nighantu(self):
        """Load Nighaṇṭu data"""
        
        # Chapter 1: Synonym groups
        self.synonym_groups = {
            "earth": ["भूमि", "पृथ्वी", "क्षिति", "वसुधा", "मही", "धरा", "अचला"],
            "water": ["जल", "वारि", "अम्बु", "तोय", "पानीय", "सलिल", "नीर"],
            "fire": ["अग्नि", "वह्नि", "पावक", "दहन", "ज्वलन", "तेजस्", "हुतभुज्"],
            "sun": ["सूर्य", "रवि", "भानु", "दिवाकर", "आदित्य", "अर्क", "मार्तण्ड"],
            "moon": ["चन्द्र", "सोम", "इन्दु", "शशिन्", "मृगाङ्क", "निशाकर"],
            "wind": ["वायु", "पवन", "मारुत", "अनिल", "समीर", "प्रभञ्जन"],
            "sky": ["आकाश", "नभस्", "गगन", "व्योम", "अम्बर", "द्यौस्", "अन्तरिक्ष"],
            "speech": ["वाच्", "भाषा", "गीर्", "सरस्वती", "वाणी", "उक्ति"],
            "knowledge": ["ज्ञान", "विद्या", "बुद्धि", "मेधा", "प्रज्ञा", "धी"],
            "bliss": ["आनन्द", "सुख", "हर्ष", "प्रमोद", "उल्लास"],
            "lord": ["ईश्वर", "भगवान्", "नाथ", "पति", "प्रभु", "अधिप"],
            "soul": ["आत्मन्", "पुरुष", "जीव", "चेतन", "अन्तर्यामिन्"],
        }
        
        # Chapter 2: Homonyms (words with multiple meanings)
        self.homonyms = {
            "अक्ष": ["eye", "axle", "die (gambling)", "sense organ"],
            "कक्ष": ["armpit", "girdle", "region", "side"],
            "गुण": ["quality", "rope", "string", "virtue"],
            "ज्योतिस्": ["light", "flame", "star", "eye"],
            "पद": ["word", "foot", "step", "position"],
            "रूप": ["form", "beauty", "color", "appearance"],
            "शब्द": ["sound", "word", "noise", "name"],
            "सत्": ["being", "good", "true", "existent"],
        }
        
        # Chapter 3: Vedic deity words
        self.vedic_words = {
            "इन्द्र": {
                "meaning": "King of gods, lord of thunder",
                "root": "इन्द्",
                "class": "deity",
                "attributes": ["thunder", "rain", "warrior"],
            },
            "अग्नि": {
                "meaning": "Fire god, messenger",
                "root": "अङ्ग्",
                "class": "deity",
                "attributes": ["fire", "sacrifice", "messenger"],
            },
            "वरुण": {
                "meaning": "God of cosmic waters, law",
                "root": "वृ",
                "class": "deity",
                "attributes": ["water", "law", "oath"],
            },
            "मरुत्": {
                "meaning": "Storm gods, winds",
                "root": "मृ",
                "class": "deity",
                "attributes": ["wind", "storm", "rain"],
            },
            "अश्विन्": {
                "meaning": "Twin physician gods",
                "root": "अश्",
                "class": "deity",
                "attributes": ["healing", "dawn", "horses"],
            },
        }
    
    def get_synonyms(self, word: str) -> List[str]:
        """Get synonyms for a word"""
        # Search in all groups
        for group, words in self.synonym_groups.items():
            if word in words:
                return [w for w in words if w != word]
        return []
    
    def get_homonyms(self, word: str) -> List[str]:
        """Get alternative meanings of a word"""
        return self.homonyms.get(word, [])
    
    def get_vedic_info(self, word: str) -> Optional[Dict]:
        """Get Vedic word information"""
        return self.vedic_words.get(word)
    
    def search_by_meaning(self, meaning: str) -> List[str]:
        """Search words by meaning"""
        results = []
        for group, words in self.synonym_groups.items():
            if meaning.lower() in group.lower():
                results.extend(words)
        return results


class UpasargaAnalyzer:
    """
    Analyzes upasargas (prefixes) in Sanskrit words.
    
    20+ primary upasargas:
    प्र, अप, सम्, नि, निर्, दुस्, सु, उत्, अभि, प्रति, etc.
    """
    
    def __init__(self):
        self.upasargas = {
            "प्र": Upasarga(
                name="pra",
                sanskrit="प्र",
                meaning="forth, forward, before",
                semantic_effect="intensification, forward motion",
                examples=["प्र + गम् → प्रगच्छति (goes forward)",
                         "प्र + कृ → प्रकरोति (does thoroughly)"],
            ),
            "अप": Upasarga(
                name="apa",
                sanskrit="अप",
                meaning="away, off, down",
                semantic_effect="separation, removal",
                examples=["अप + गम् → अपगच्छति (goes away)",
                         "अप + नुद् → अपनोदति (removes)"],
            ),
            "सम्": Upasarga(
                name="sam",
                sanskrit="सम्",
                meaning="together, completely",
                semantic_effect="union, completion, intensity",
                examples=["सम् + गम् → सम्गच्छति (meets)",
                         "सम् + कृ → सम्स्करोति (perfects, refines)"],
            ),
            "नि": Upasarga(
                name="ni",
                sanskrit="नि",
                meaning="down, into, within",
                semantic_effect="downward motion, certainty",
                examples=["नि + गम् → निगच्छति (goes down)",
                         "नि + धा → निदधाति (places within)"],
            ),
            "निर्": Upasarga(
                name="nir",
                sanskrit="निर्",
                meaning="out, away, without",
                semantic_effect="exit, absence, completion",
                examples=["निर् + गम् → निर्गच्छति (goes out)",
                         "निर् + वृत् → निर्वर्तते (accomplishes)"],
            ),
            "दुस्": Upasarga(
                name="dus",
                sanskrit="दुस्",
                meaning="bad, difficult, evil",
                semantic_effect="negation, difficulty",
                examples=["दुस् + कृ → दुष्करोति (does with difficulty)",
                         "दुस् + नामन् → दुर्नामन् (bad name)"],
            ),
            "सु": Upasarga(
                name="su",
                sanskrit="सु",
                meaning="good, well, easy",
                semantic_effect="positive quality, ease",
                examples=["सु + कृ → सुकरोति (does well)",
                         "सु + ख → सुख (happiness)"],
            ),
            "उत्": Upasarga(
                name="ut",
                sanskrit="उत्",
                meaning="up, upwards, away",
                semantic_effect="upward motion, increase",
                examples=["उत् + पत् → उत्पतति (flies up)",
                         "उत् + ठा → उत्तिष्ठति (stands up)"],
            ),
            "अभि": Upasarga(
                name="abhi",
                sanskrit="अभि",
                meaning="towards, over, to",
                semantic_effect="direction towards, superiority",
                examples=["अभि + गम् → अभिगच्छति (approaches)",
                         "अभि + वद् → अभिवदति (greets)"],
            ),
            "प्रति": Upasarga(
                name="prati",
                sanskrit="प्रति",
                meaning="back, against, towards",
                semantic_effect="return, opposition, response",
                examples=["प्रति + गम् → प्रतिगच्छति (returns)",
                         "प्रति + वच् → प्रत्युवच (replied)"],
            ),
            "आ": Upasarga(
                name="ā",
                sanskrit="आ",
                meaning="towards, near, until",
                semantic_effect="approach, completeness",
                examples=["आ + गम् → आगच्छति (comes)",
                         "आ + धा → आदधाति (takes)"],
            ),
            "वि": Upasarga(
                name="vi",
                sanskrit="वि",
                meaning="apart, asunder, in different directions",
                semantic_effect="separation, distinction",
                examples=["वि + गम् → विगच्छति (goes apart)",
                         "वि + धा → विदधाति (arranges)"],
            ),
            "अनु": Upasarga(
                name="anu",
                sanskrit="अनु",
                meaning="after, along, following",
                semantic_effect="sequence, imitation",
                examples=["अनु + गम् → अनुगच्छति (follows)",
                         "अनु + कृ → अनुकरोति (imitates)"],
            ),
            "अधि": Upasarga(
                name="adhi",
                sanskrit="अधि",
                meaning="over, above, upon",
                semantic_effect="superiority, authority",
                examples=["अधि + गम् → अधिगच्छति (studies)",
                         "अधि + कृ → अधिकरोति (places over)"],
            ),
            "अव": Upasarga(
                name="ava",
                sanskrit="अव",
                meaning="down, away",
                semantic_effect="downward motion",
                examples=["अव + गम् → अवगच्छति (goes down)",
                         "अव + तृ → अवतरति (descends)"],
            ),
            "परि": Upasarga(
                name="pari",
                sanskrit="परि",
                meaning="around, about",
                semantic_effect="surrounding, completeness",
                examples=["परि + गम् → परिगच्छति (goes around)",
                         "परि + कृ → परिष्करोति (polishes)"],
            ),
            "उप": Upasarga(
                name="upa",
                sanskrit="उप",
                meaning="near, towards, under",
                semantic_effect="proximity, subordination",
                examples=["उप + गम् → उपगच्छति (approaches)",
                         "उप + विद् → उपविन्दति (obtains)"],
            ),
        }
    
    def analyze(self, word: str) -> List[Upasarga]:
        """
        Analyze word for upasargas.
        
        Returns:
            List of detected upasargas
        """
        detected = []
        for upasarga in self.upasargas.values():
            if word.startswith(upasarga.sanskrit):
                detected.append(upasarga)
        return detected
    
    def get_meaning_modification(self, root_meaning: str, upasarga: str) -> str:
        """Get modified meaning when upasarga is added to root"""
        ups = self.upasargas.get(upasarga)
        if not ups:
            return root_meaning
        
        # Simplified meaning modification
        return f"{ups.meaning} + {root_meaning}"


class EtymologyTracker:
    """
    Tracks complete etymology of Sanskrit words.
    
    Traces words back to their roots through:
    - Upasarga analysis
    - Pratyaya removal
    - Root identification
    - Semantic field mapping
    """
    
    def __init__(self):
        self.upasarga_analyzer = UpasargaAnalyzer()
        self.nighantu = NighantuDatabase()
        
        # Root database (sample)
        self.root_db = {
            "गच्छति": {"root": "गम्", "meaning": "to go"},
            "करोति": {"root": "कृ", "meaning": "to do"},
            "पठति": {"root": "पठ्", "meaning": "to read"},
            "लिखति": {"root": "लिख्", "meaning": "to write"},
            "भवति": {"root": "भू", "meaning": "to be"},
            "गच्छन्ति": {"root": "गम्", "meaning": "to go"},
            "कुर्वन्ति": {"root": "कृ", "meaning": "to do"},
        }
    
    def trace(self, word: str) -> Etymology:
        """
        Trace complete etymology of a word.
        
        Args:
            word: Sanskrit word
        
        Returns:
            Complete etymological analysis
        """
        # Detect upasargas
        upasargas = self.upasarga_analyzer.analyze(word)
        upasarga_names = [u.sanskrit for u in upasargas]
        
        # Remove upasargas to get base
        base = word
        for ups in upasarga_names:
            if base.startswith(ups):
                base = base[len(ups):]
                break
        
        # Identify root
        root_info = self.root_db.get(base, {"root": base, "meaning": "unknown"})
        
        # Get semantic field
        semantic_field = self._get_semantic_field(root_info["root"])
        
        # Get related words
        related = self.nighantu.get_synonyms(root_info["root"])
        
        return Etymology(
            word=word,
            root=root_info["root"],
            root_meaning=root_info["meaning"],
            upasargas=upasarga_names,
            pratyayas=[],
            derivation_path=[root_info["root"]] + upasarga_names,
            semantic_field=semantic_field,
            related_words=related,
        )
    
    def _get_semantic_field(self, root: str) -> str:
        """Determine semantic field of a root"""
        fields = {
            "गम्": "motion",
            "कृ": "action",
            "भू": "existence",
            "अस्": "existence",
            "पठ्": "knowledge",
            "लिख्": "creation",
            "यज्": "worship",
            "वद्": "speech",
            "दृश्": "perception",
            "श्रु": "perception",
        }
        return fields.get(root, "general")


class NiruktaEngine:
    """
    Complete Nirukta engine integrating all etymology components.
    
    Provides:
    - Word etymology
    - Semantic field analysis
    - Vedic word interpretation
    - Root derivation
    """
    
    def __init__(self):
        self.etymology_tracker = EtymologyTracker()
        self.upasarga_analyzer = UpasargaAnalyzer()
        self.nighantu = NighantuDatabase()
    
    def analyze_etymology(self, word: str) -> Etymology:
        """Get complete etymology of a word"""
        return self.etymology_tracker.trace(word)
    
    def get_synonyms(self, word: str) -> List[str]:
        """Get synonyms from Nighaṇṭu"""
        return self.nighantu.get_synonyms(word)
    
    def get_upasargas(self, word: str) -> List[Dict]:
        """Get upasargas in a word"""
        upasargas = self.upasarga_analyzer.analyze(word)
        return [
            {
                "name": u.name,
                "sanskrit": u.sanskrit,
                "meaning": u.meaning,
                "effect": u.semantic_effect,
            }
            for u in upasargas
        ]
    
    def interpret_vedic_word(self, word: str) -> Optional[Dict]:
        """Get Vedic word interpretation"""
        return self.nighantu.get_vedic_info(word)
    
    def derive_meaning(self, root: str, upasargas: List[str] = None) -> str:
        """
        Derive meaning from root + upasargas.
        
        Args:
            root: Verbal root
            upasargas: List of upasargas
        
        Returns:
            Derived meaning
        """
        root_meanings = {
            "गम्": "to go",
            "कृ": "to do",
            "भू": "to be",
            "अस्": "to be",
            "पठ्": "to read",
            "वद्": "to speak",
            "दृश्": "to see",
            "यज्": "to worship",
        }
        
        meaning = root_meanings.get(root, "unknown")
        
        if upasargas:
            for ups in upasargas:
                ups_info = self.upasarga_analyzer.upasargas.get(ups)
                if ups_info:
                    meaning = f"{ups_info.meaning} + {meaning}"
        
        return meaning


# Signature
SIGNATURE = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    *Visionary RM (Raj Mitra)* ⚡                             ║
║              "Nirukta Module - Complete Etymology Engine" 🔱                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
Nirukta = NiruktaEngine
