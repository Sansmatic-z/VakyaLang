# आत्मलिपि — चेतना मेटाडेटा स्तर
# AtmaLipi — Consciousness Metadata Layer
# Original concept: Raj Mitra (AtmaLipi repo)
# Integrated into VakyaLang unified ecosystem: Mar 2026
#
# "If language shaped the mind — can we design a language that shapes it better?"
#
# AtmaLipi adds two metadata layers to any value or expression:
#   {भाव}     — Emotional state tags  (CALM, JOY, FOCUS, GRIEF, WONDER...)
#   [अवस्था]  — Cognitive state tags  (SELF_AWARE, LEARNING, QUESTIONING...)
#
# Example:
#   ātmaḥ {CALM} [SELF_AWARE] → "I am aware of myself, peacefully."
#   In वाक्: चर x = आत्म_मूल्य("शांत है", भाव="शान्त", अवस्था="स्वयं_बोध")

from typing import Any, Optional, List


# ── Symbol Dictionaries ────────────────────────────────────────────────────────

# Emotional states (भाव) — Sanskrit names with English equivalents
BHAV = {
    # Positive
    "आनन्द":      "JOY",
    "शान्त":      "CALM",
    "उत्साह":     "ENTHUSIASM",
    "कृतज्ञता":   "GRATITUDE",
    "प्रेम":      "LOVE",
    "जिज्ञासा":   "CURIOSITY",
    "विस्मय":     "WONDER",
    "शक्ति":      "STRENGTH",
    # Neutral
    "तटस्थ":      "NEUTRAL",
    "केन्द्रित":   "FOCUSED",
    "सजग":        "ALERT",
    # Challenging
    "दुःख":       "GRIEF",
    "भय":         "FEAR",
    "क्रोध":      "ANGER",
    "भ्रम":       "CONFUSION",
    "थकान":       "FATIGUE",
}

# Cognitive states (अवस्था) — Sanskrit names
AVASTHA = {
    "स्वयं_बोध":  "SELF_AWARE",
    "सीख_रहा":    "LEARNING",
    "प्रश्न":      "QUESTIONING",
    "चिंतन":      "REFLECTING",
    "निर्णय":     "DECIDING",
    "सृजन":       "CREATING",
    "विश्लेषण":   "ANALYSING",
    "ध्यान":      "MEDITATING",
    "स्मृति":     "REMEMBERING",
    "कल्पना":     "IMAGINING",
}

# Reverse lookups
BHAV_REVERSE    = {v: k for k, v in BHAV.items()}
AVASTHA_REVERSE = {v: k for k, v in AVASTHA.items()}


# ── AtmaValue — A value with consciousness metadata ───────────────────────────

class AtmaValue:
    """
    A वाक् value carrying AtmaLipi consciousness metadata.

    Every AtmaValue has:
      - value:   the actual data
      - bhav:    emotional state tag (भाव)
      - avastha: cognitive state tag (अवस्था)
      - note:    optional human-readable annotation
    """

    def __init__(self, value: Any,
                 bhav: Optional[str] = None,
                 avastha: Optional[str] = None,
                 note: Optional[str] = None):
        self.value   = value
        self.bhav    = bhav      # Sanskrit emotional tag
        self.avastha = avastha   # Sanskrit cognitive tag
        self.note    = note

    def __str__(self):
        parts = [str(self.value)]
        if self.bhav:
            parts.append(f"{{{self.bhav}}}")
        if self.avastha:
            parts.append(f"[{self.avastha}]")
        if self.note:
            parts.append(f'→ "{self.note}"')
        return " ".join(parts)

    def __repr__(self):
        return f"AtmaValue({self.__str__()})"

    def to_dict(self):
        return {
            "मूल्य":   self.value,
            "भाव":     self.bhav,
            "अवस्था":  self.avastha,
            "टिप्पणी": self.note,
        }


# ── AtmaLipi Engine ───────────────────────────────────────────────────────────

class AtmaLipiEngine:
    """
    Processes AtmaLipi symbol annotations.
    Can wrap any value with consciousness metadata.
    Can analyse emotional/cognitive content of text.
    """

    def __init__(self):
        self.history: List[AtmaValue] = []

    def wrap(self, value: Any,
             bhav: Optional[str] = None,
             avastha: Optional[str] = None,
             note: Optional[str] = None) -> AtmaValue:
        """Wrap a value with AtmaLipi metadata."""
        av = AtmaValue(value, bhav, avastha, note)
        self.history.append(av)
        return av

    def read_bhav(self, tag: str) -> str:
        """Translate Sanskrit emotional tag to English or vice versa."""
        if tag in BHAV:
            return f"{tag} ({BHAV[tag]})"
        if tag.upper() in BHAV_REVERSE:
            return f"{BHAV_REVERSE[tag.upper()]} ({tag.upper()})"
        return f"अज्ञात भाव: {tag}"

    def read_avastha(self, tag: str) -> str:
        """Translate Sanskrit cognitive tag to English or vice versa."""
        if tag in AVASTHA:
            return f"{tag} ({AVASTHA[tag]})"
        if tag.upper() in AVASTHA_REVERSE:
            return f"{AVASTHA_REVERSE[tag.upper()]} ({tag.upper()})"
        return f"अज्ञात अवस्था: {tag}"

    def all_bhav(self) -> dict:
        return dict(BHAV)

    def all_avastha(self) -> dict:
        return dict(AVASTHA)

    def get_history(self) -> List[dict]:
        return [av.to_dict() for av in self.history]
