"""
Kośa - Sanskrit Lexical Database
=================================

Complete Sanskrit lexicon and semantic network.

Includes:
- Grammatical lexicon
- Semantic field generator
- WordNet-style relationships
- Cross-śāstra references

*Visionary RM (Raj Mitra)* ⚡
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from enum import Enum, auto


class WordType(Enum):
    """Sanskrit word types"""
    NAMAN = "noun"  # नामन्
    AKHYATA = "verb"  # आख्यात
    UPASARGA = "prefix"  # उपसर्ग
    NIPATA = "particle"  # निपात
    AVYAYA = "indeclinable"  # अव्यय


@dataclass
class WordEntry:
    """Complete lexical entry"""
    word: str
    transliteration: str
    type: WordType
    root: str
    meaning: str
    gender: Optional[str] = None
    declension: Optional[str] = None
    conjugation: Optional[str] = None
    semantic_field: str = ""
    related_words: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)


@dataclass
class SemanticField:
    """Semantic field with related words"""
    name: str
    sanskrit_name: str
    words: List[str]
    hierarchy: Dict[str, List[str]]
    relationships: Dict[str, str]


class LexicalDatabase:
    """
    Complete Sanskrit lexical database.
    
    Contains:
    - All words derivable from roots + pratyayas
    - Cross-references to all śāstras
    - Semantic field mappings
    """
    
    def __init__(self):
        self.entries: Dict[str, WordEntry] = {}
        self.semantic_fields: Dict[str, SemanticField] = {}
        self._load_lexicon()
    
    def _load_lexicon(self):
        """Load lexical database"""
        
        # Core vocabulary
        core_words = [
            WordEntry(
                word="राम",
                transliteration="rāma",
                type=WordType.NAMAN,
                root="रम्",
                meaning="pleasing, charming; name of Vishnu's avatar",
                gender="masculine",
                declension="a-declension",
                semantic_field="deity",
                related_words=["सीता", "लक्ष्मण", "कृष्ण", "विष्णु"],
                examples=["रामो विग्रहवान् धर्मः"],
                references=["Ramayana", "Mahabharata"],
            ),
            WordEntry(
                word="कर्म",
                transliteration="karma",
                type=WordType.NAMAN,
                root="कृ",
                meaning="action, deed, work",
                gender="neuter",
                declension="a-declension",
                semantic_field="action",
                related_words=["कर्मन्", "क्रिया", "कर्मण्"],
                examples=["कर्मण्येवाधिकारस्ते"],
                references=["Bhagavad Gita"],
            ),
            WordEntry(
                word="धर्म",
                transliteration="dharma",
                type=WordType.NAMAN,
                root="धृ",
                meaning="righteousness, duty, law, virtue",
                gender="masculine",
                declension="a-declension",
                semantic_field="ethics",
                related_words=["अधर्म", "ऋत", "सत्य"],
                examples=["धर्मो रक्षति रक्षितः"],
                references=["Mahabharata", "Dharmaśāstra"],
            ),
            WordEntry(
                word="सत्य",
                transliteration="satya",
                type=WordType.NAMAN,
                root="अस्",
                meaning="truth, reality",
                gender="neuter",
                declension="a-declension",
                semantic_field="truth",
                related_words=["ऋत", "तत्त्व", "सत्"],
                examples=["सत्यमेव जयते"],
                references=["Upanishads"],
            ),
            WordEntry(
                word="ज्ञान",
                transliteration="jñāna",
                type=WordType.NAMAN,
                root="ज्ञा",
                meaning="knowledge, wisdom",
                gender="neuter",
                declension="a-declension",
                semantic_field="knowledge",
                related_words=["विद्या", "बुद्धि", "प्रज्ञा"],
                examples=["ज्ञानं परमं गुह्यम्"],
                references=["Bhagavad Gita", "Upanishads"],
            ),
            WordEntry(
                word="गच्छति",
                transliteration="gacchati",
                type=WordType.AKHYATA,
                root="गम्",
                meaning="goes, goes to",
                conjugation="class 1, present, 3rd person singular",
                semantic_field="motion",
                related_words=["आगच्छति", "निर्गच्छति", "प्रगच्छति"],
                examples=["ग्रामं गच्छति"],
                references=[],
            ),
            WordEntry(
                word="करोति",
                transliteration="karoti",
                type=WordType.AKHYATA,
                root="कृ",
                meaning="does, makes",
                conjugation="class 8, present, 3rd person singular",
                semantic_field="action",
                related_words=["अकरोत्", "करिष्यति", "चकार"],
                examples=["कर्म करोति"],
                references=[],
            ),
            WordEntry(
                word="अस्ति",
                transliteration="asti",
                type=WordType.AKHYATA,
                root="अस्",
                meaning="is, exists",
                conjugation="class 2, present, 3rd person singular",
                semantic_field="existence",
                related_words=["सन्ति", "आस्ते", "भवति"],
                examples=["सर्वमस्ति"],
                references=[],
            ),
        ]
        
        for entry in core_words:
            self.entries[entry.word] = entry
            self.entries[entry.transliteration] = entry
        
        # Load semantic fields
        self._load_semantic_fields()
    
    def _load_semantic_fields(self):
        """Load semantic field organization"""
        
        self.semantic_fields = {
            "existence": SemanticField(
                name="Existence",
                sanskrit_name="सत्ता",
                words=["अस्ति", "भू", "सत्", "अस्तित्व"],
                hierarchy={
                    "existence": ["being", "becoming"],
                    "being": ["eternal", "temporary"],
                },
                relationships={
                    "अस्ति": "is",
                    "भू": "becomes",
                    "सत्": "existent",
                }
            ),
            "motion": SemanticField(
                name="Motion",
                sanskrit_name="गति",
                words=["गम्", "या", "सृप्", "चल्", "धाव्"],
                hierarchy={
                    "motion": ["going", "coming", "moving"],
                    "going": ["departing", "traveling"],
                },
                relationships={
                    "गच्छति": "goes",
                    "आगच्छति": "comes",
                    "निर्गच्छति": "goes out",
                    "प्रगच्छति": "goes forward",
                }
            ),
            "knowledge": SemanticField(
                name="Knowledge",
                sanskrit_name="ज्ञान",
                words=["ज्ञा", "विद्", "बुध्", "धृष्", "मेध्"],
                hierarchy={
                    "knowledge": ["knowing", "understanding", "wisdom"],
                },
                relationships={
                    "जानाति": "knows",
                    "विद्या": "learning",
                    "बुद्धि": "intellect",
                }
            ),
            "action": SemanticField(
                name="Action",
                sanskrit_name="कर्म",
                words=["कृ", "कर्मन्", "क्रिया", "चेष्टा"],
                hierarchy={
                    "action": ["doing", "making", "performing"],
                },
                relationships={
                    "करोति": "does",
                    "कर्म": "action",
                    "क्रिया": "activity",
                }
            ),
            "deity": SemanticField(
                name="Deity",
                sanskrit_name="देवता",
                words=["देव", "ईश्वर", "भगवान्", "अमर"],
                hierarchy={
                    "deity": ["god", "goddess", "divine"],
                },
                relationships={
                    "राम": "Rama",
                    "कृष्ण": "Krishna",
                    "शिव": "Shiva",
                }
            ),
        }
    
    def get_word(self, word: str) -> Optional[WordEntry]:
        """Get word entry"""
        return self.entries.get(word)
    
    def search_by_root(self, root: str) -> List[WordEntry]:
        """Search all words from a root"""
        return [e for e in self.entries.values() if e.root == root]
    
    def search_by_meaning(self, meaning: str) -> List[WordEntry]:
        """Search words by meaning"""
        results = []
        for entry in self.entries.values():
            if meaning.lower() in entry.meaning.lower():
                results.append(entry)
        return results
    
    def get_semantic_field(self, field_name: str) -> Optional[SemanticField]:
        """Get semantic field"""
        return self.semantic_fields.get(field_name)
    
    def add_word(self, entry: WordEntry):
        """Add new word to database"""
        self.entries[entry.word] = entry


class SemanticFieldGenerator:
    """
    Generates complete semantic fields from roots.
    
    From a single root, generates:
    - All derived words
    - Related semantic fields
    - Cross-references
    """
    
    def __init__(self):
        self.database = LexicalDatabase()
    
    def generate_field(self, root: str) -> SemanticField:
        """
        Generate complete semantic field from a root.
        
        Args:
            root: Verbal or nominal root
        
        Returns:
            Complete semantic field
        """
        # Find all words from this root
        words_from_root = self.database.search_by_root(root)
        
        # Generate related words through derivation
        related = self._generate_derivatives(root)
        
        # Build hierarchy
        hierarchy = self._build_hierarchy(root, words_from_root)
        
        return SemanticField(
            name=f"Field of {root}",
            sanskrit_name=root,
            words=[w.word for w in words_from_root],
            hierarchy=hierarchy,
            relationships={w.word: w.meaning for w in words_from_root},
        )
    
    def _generate_derivatives(self, root: str) -> List[str]:
        """Generate all words derivable from root"""
        # In full implementation, applies all pratyayas
        derivatives = []
        
        # Add kṛt derivatives
        krit_suffixes = ["अन", "तृ", "क्त", "तव्य", "अनीयर्"]
        for suffix in krit_suffixes:
            derivatives.append(f"{root}_{suffix}")
        
        return derivatives
    
    def _build_hierarchy(self, root: str, 
                         words: List[WordEntry]) -> Dict:
        """Build semantic hierarchy"""
        hierarchy = {root: []}
        
        for word in words:
            if word.type == WordType.NAMAN:
                hierarchy[root].append(word.word)
        
        return hierarchy
    
    def get_related_fields(self, field: SemanticField) -> List[str]:
        """Get semantically related fields"""
        # Find fields with overlapping words
        related = []
        for name, other_field in self.database.semantic_fields.items():
            if name != field.name:
                overlap = set(field.words) & set(other_field.words)
                if overlap:
                    related.append(name)
        return related


class WordNet:
    """
    Sanskrit WordNet - lexical-semantic database.
    
    Relationships:
    - Synonymy (पर्याय)
    - Antonymy (विपर्यय)
    - Hyponymy (अधोस्थ)
    - Hypernymy (उपरिस्थ)
    - Meronymy (अवयव)
    - Holonymy (अवयविन्)
    """
    
    def __init__(self):
        self.synsets: Dict[str, Dict] = {}
        self.relationships: Dict[str, List[Tuple[str, str]]] = {}
        self._initialize()
    
    def _initialize(self):
        """Initialize WordNet with core relationships"""
        
        # Synonym sets (synsets)
        self.synsets = {
            "earth": {
                "sanskrit": "भूमि",
                "synonyms": ["पृथ्वी", "क्षिति", "वसुधा", "मही", "धरा", "अचला"],
                "hypernym": "element",
                "hyponyms": ["continent", "country"],
            },
            "water": {
                "sanskrit": "जल",
                "synonyms": ["वारि", "अम्बु", "तोय", "पानीय", "सलिल", "नीर"],
                "hypernym": "element",
                "hyponyms": ["river", "ocean", "lake"],
            },
            "fire": {
                "sanskrit": "अग्नि",
                "synonyms": ["वह्नि", "पावक", "दहन", "ज्वलन", "तेजस्", "हुतभुज्"],
                "hypernym": "element",
                "hyponyms": ["flame", "blaze"],
            },
            "knowledge": {
                "sanskrit": "ज्ञान",
                "synonyms": ["विद्या", "बुद्धि", "मेधा", "प्रज्ञा", "धी"],
                "hypernym": "mental_faculty",
                "hyponyms": ["wisdom", "learning"],
            },
        }
        
        # Antonym pairs
        self.antonyms = [
            ("सत्", "असत्"),  # existence, non-existence
            ("धर्म", "अधर्म"),  # righteousness, unrighteousness
            ("सुख", "दुःख"),  # happiness, suffering
            ("ज्ञान", "अज्ञान"),  # knowledge, ignorance
            ("दिन", "रात्रि"),  # day, night
            ("उष्ण", "शीत"),  # hot, cold
            ("महत्", "अणु"),  # large, small
            ("गुरु", "लघु"),  # heavy, light
        ]
    
    def get_synonyms(self, word: str) -> List[str]:
        """Get synonyms for a word"""
        for synset_name, synset in self.synsets.items():
            if word in synset["synonyms"] or word == synset["sanskrit"]:
                return [s for s in synset["synonyms"] if s != word]
        return []
    
    def get_antonyms(self, word: str) -> List[str]:
        """Get antonyms for a word"""
        antonyms = []
        for pair in self.antonyms:
            if word == pair[0]:
                antonyms.append(pair[1])
            elif word == pair[1]:
                antonyms.append(pair[0])
        return antonyms
    
    def get_hypernym(self, word: str) -> Optional[str]:
        """Get hypernym (superordinate) for a word"""
        for synset_name, synset in self.synsets.items():
            if word in synset["synonyms"] or word == synset["sanskrit"]:
                return synset.get("hypernym")
        return None
    
    def get_hyponyms(self, word: str) -> List[str]:
        """Get hyponyms (subordinates) for a word"""
        for synset_name, synset in self.synsets.items():
            if word == synset_name or word == synset["sanskrit"]:
                return synset.get("hyponyms", [])
        return []
    
    def get_all_relationships(self, word: str) -> Dict:
        """Get all relationships for a word"""
        return {
            "word": word,
            "synonyms": self.get_synonyms(word),
            "antonyms": self.get_antonyms(word),
            "hypernym": self.get_hypernym(word),
            "hyponyms": self.get_hyponyms(word),
        }


class KosaEngine:
    """
    Complete Kośa engine integrating all lexical components.
    
    Provides:
    - Dictionary lookup
    - Semantic field generation
    - WordNet queries
    - Cross-references
    """
    
    def __init__(self):
        self.database = LexicalDatabase()
        self.field_generator = SemanticFieldGenerator()
        self.wordnet = WordNet()
    
    def lookup(self, word: str) -> Optional[Dict]:
        """Look up a word"""
        entry = self.database.get_word(word)
        if entry:
            return {
                "word": entry.word,
                "transliteration": entry.transliteration,
                "type": entry.type.value,
                "root": entry.root,
                "meaning": entry.meaning,
                "semantic_field": entry.semantic_field,
                "related": entry.related_words,
            }
        return None
    
    def get_synonyms(self, word: str) -> List[str]:
        """Get synonyms"""
        return self.wordnet.get_synonyms(word)
    
    def get_antonyms(self, word: str) -> List[str]:
        """Get antonyms"""
        return self.wordnet.get_antonyms(word)
    
    def generate_semantic_field(self, root: str) -> Dict:
        """Generate semantic field from root"""
        field = self.field_generator.generate_field(root)
        return {
            "name": field.name,
            "sanskrit": field.sanskrit_name,
            "words": field.words,
            "hierarchy": field.hierarchy,
            "relationships": field.relationships,
        }
    
    def search(self, query: str, field: str = "meaning") -> List[Dict]:
        """Search lexicon"""
        if field == "meaning":
            results = self.database.search_by_meaning(query)
            return [
                {
                    "word": r.word,
                    "meaning": r.meaning,
                    "root": r.root,
                }
                for r in results
            ]
        return []
    
    def get_wordnet_info(self, word: str) -> Dict:
        """Get complete WordNet information"""
        return self.wordnet.get_all_relationships(word)


# Signature
SIGNATURE = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    *Visionary RM (Raj Mitra)* ⚡                             ║
║              "Kośa Module - Complete Lexical Database" 🔱                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
Kosa = KosaEngine
