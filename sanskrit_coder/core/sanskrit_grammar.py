# संस्कृत-कोडकः - संस्कृत व्याकरण तन्त्रम्
# Sanskrit Coder - Sanskrit Grammar Engine

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class Vibhakti(Enum):
    """Eight Sanskrit cases."""
    PRATHAMA = 1   # Nominative
    DVITIYA = 2    # Accusative
    TRITIYA = 3    # Instrumental
    CHATURTHI = 4  # Dative
    PANCHAMI = 5   # Ablative
    SHASHHTHI = 6  # Genitive
    SAPTAMI = 7    # Locative
    SAMBODHANA = 8 # Vocative

@dataclass
class Subanta:
    """Nominal stem with inflection."""
    pratipadika: str  # Stem
    linga: str        # Gender (पुं, स्त्री, नपुं)
    vibhakti: Vibhakti
    vacana: int       # Number (1, 2, 3 = singular, dual, plural)
    
    def __str__(self):
        return f"{self.pratipadika} ({self.linga}, {self.vibhakti.name}, {self.vacana})"

class Dhatu:
    """Verbal root."""
    def __init__(self, dhatu: str, artha: str, gana: str):
        self.dhatu = dhatu      # Root (e.g., "गम्")
        self.artha = artha      # Meaning (e.g., "to go")
        self.gana = gana        # Conjugation class (e.g., "भ्वादि")
        
    def __str__(self):
        return f"√{self.dhatu} ({self.artha})"

class Lakara:
    """Tense/mood system."""
    NAMES = {
        'LAT': 'Present',
        'LIT': 'Perfect',
        'LUT': 'Periphrastic Future',
        'LRT': 'Simple Future',
        'LET': 'Vedic Subjunctive',
        'LOT': 'Imperative',
        'LAN': 'Imperfect',
        'VIDHILIN': 'Optative',
        'ASHIRLIN': 'Benedictive',
        'LUN': 'Aorist',
        'LRN': 'Conditional',
    }

class SanskritGrammar:
    """
    Paninian grammar implementation for Sanskrit Coder.
    
    Provides:
    - Subanta (nominal) inflection
    - Tinanta (verbal) conjugation
    - Sandhi (euphonic combination)
    - Samasa (compound analysis)
    """
    
    def __init__(self):
        self.vibhakti_endings = self._init_vibhakti_endings()
        self.dhatus = self._init_dhatus()
        self.sandhi_rules = self._init_sandhi_rules()
        
    def _init_vibhakti_endings(self) -> Dict:
        """Initialize case endings."""
        # Simplified endings for a-stems (deva)
        return {
            'पुं': {
                1: {1: 'ः', 2: 'ौ', 3: 'ाः'},      # प्रथमा
                2: {1: 'म्', 2: 'ौ', 3: 'ान्'},     # द्वितीया
                3: {1: 'ेन', 2: 'ाभ्याम्', 3: 'ैः'}, # तृतीया
                4: {1: 'ाय', 2: 'ाभ्याम्', 3: 'ेभ्यः'}, # चतुर्थी
                5: {1: 'ात्', 2: 'ाभ्याम्', 3: 'ेभ्यः'}, # पञ्चमी
                6: {1: 'स्य', 2: 'योः', 3: 'ानाम्'},   # षष्ठी
                7: {1: 'े', 2: 'योः', 3: 'ेषु'},      # सप्तमी
                8: {1: '', 2: 'ौ', 3: 'ाः'},         # सम्बोधन
            },
            'स्त्री': {
                # Similar structure for feminine
            },
            'नपुं': {
                # Similar structure for neuter
            }
        }
    
    def _init_dhatus(self) -> Dict[str, Dhatu]:
        """Initialize verbal roots."""
        return {
            'गम्': Dhatu('गम्', 'to go', 'भ्वादि'),
            'हन्': Dhatu('हन्', 'to kill', 'अदादि'),
            'कृ': Dhatu('कृ', 'to do', 'स्वादि'),
            'भू': Dhatu('भू', 'to be', 'भ्वादि'),
            'अस्': Dhatu('अस्', 'to be', 'अदादि'),
            'इ': Dhatu('इ', 'to go', 'अदादि'),
            'दा': Dhatu('दा', 'to give', 'जुहोत्यादि'),
            'पा': Dhatu('पा', 'to drink', 'प्यादि'),
            'लिख्': Dhatu('लिख्', 'to write', 'रुधादि'),
            'पठ्': Dhatu('पठ्', 'to read', 'भ्वादि'),
            'गण्': Dhatu('गण्', 'to count', 'चुरादि'),
            'चल्': Dhatu('चल्', 'to move', 'भ्वादि'),
        }
    
    def _init_sandhi_rules(self) -> List[Dict]:
        """Initialize sandhi (euphonic combination) rules."""
        return [
            {'pattern': r'अs+अ', 'replacement': 'ा'},  # a + a = ā
            {'pattern': r'इs+इ', 'replacement': 'ी'},  # i + i = ī
            {'pattern': r'उs+उ', 'replacement': 'ू'},  # u + u = ū
            {'pattern': r'अs+इ', 'replacement': 'े'},  # a + i = e
            {'pattern': r'अs+उ', 'replacement': 'ो'},  # a + u = o
            {'pattern': r'स्s+', 'replacement': ''},   # visarga sandhi
        ]
    
    def decline(self, stem: str, gender: str, case: Vibhakti, number: int) -> str:
        """
        Decline a nominal stem.
        
        Args:
            stem: Prātipadika (e.g., "देव")
            gender: पुं, स्त्री, or नपुं
            case: Vibhakti enum
            number: 1, 2, or 3 (singular, dual, plural)
        """
        # Remove final 'a' if present for a-stems
        base = stem[:-1] if stem.endswith('अ') or stem.endswith('ा') else stem
        
        try:
            ending = self.vibhakti_endings[gender][case.value][number]
            return base + ending
        except KeyError:
            # Fallback for unimplemented forms
            return f"{stem} ({case.name}, {number})"
    
    def conjugate(self, dhatu: str, lakara: str, purusha: int, vacana: int) -> str:
        """
        Conjugate a verbal root.
        
        Args:
            dhatu: Verbal root
            lakara: Tense/mood (LAT, LAN, etc.)
            purusha: Person (1, 2, 3)
            vacana: Number (1, 2, 3)
        """
        if dhatu not in self.dhatus:
            return f"{dhatu} (unknown root)"
        
        # Simplified conjugation for present tense (LAT)
        if lakara == 'LAT':
            endings = {
                (1, 1): 'मि', (1, 2): 'वः', (1, 3): 'मः',  # 1st person
                (2, 1): 'सि', (2, 2): 'थः', (2, 3): 'थ',   # 2nd person
                (3, 1): 'ति', (3, 2): 'तः', (3, 3): 'न्ति', # 3rd person
            }
            
            # Get stem (simplified)
            if dhatu == 'गम्':
                stem = 'गच्छ'
            elif dhatu == 'हन्':
                stem = 'हन्ति' if (purusha, vacana) == (3, 1) else 'हन्'
            elif dhatu == 'कृ':
                stem = 'करो'
            elif dhatu == 'भू':
                stem = 'भव'
            else:
                stem = dhatu
            
            ending = endings.get((purusha, vacana), 'ति')
            return stem + ending
        
        return f"{dhatu} ({lakara})"
    
    def apply_sandhi(self, word1: str, word2: str) -> str:
        """
        Apply sandhi rules to combine two words.
        """
        # Simple sandhi implementation
        # Real implementation would be much more complex
        
        # Check for specific combinations
        if word1.endswith('अ') and word2.startswith('अ'):
            return word1[:-1] + 'ा' + word2[1:]
        elif word1.endswith('अ') and word2.startswith('इ'):
            return word1[:-1] + 'े' + word2[1:]
        elif word1.endswith('अ') and word2.startswith('उ'):
            return word1[:-1] + 'ो' + word2[1:]
        elif word1.endswith('ि') and word2.startswith('अ'):
            return word1[:-1] + '्य' + word2
        elif word1.endswith('ु') and word2.startswith('अ'):
            return word1[:-1] + '्व' + word2
        
        # Default: no sandhi
        return word1 + ' ' + word2
    
    def analyze_compound(self, compound: str) -> Dict:
        """
        Analyze a samāsa (compound word).
        
        Types:
        - द्वन्द्व (Dvandva) - copulative
        - तत्पुरुष (Tatpurusha) - determinative
        - बहुव्रीहि (Bahuvrihi) - possessive
        - अव्ययीभाव (Avyayibhava) - adverbial
        """
        # This is a complex analysis - simplified here
        
        # Check for dvandva (and relationship)
        if 'च' in compound or 'तथा' in compound:
            return {
                'type': 'द्वन्द्व (Dvandva)',
                'components': compound.replace('च', '+').replace('तथा', '+').split('+'),
                'meaning': 'and relationship'
            }
        
        # Check for tatpurusha (genitive relationship)
        # Pattern: X + Y where Y is modified by X
        
        # Check for bahuvrihi (possessive)
        # Pattern: X + Y where neither is main, but describes possessor
        
        return {
            'type': 'तत्पुरुष (Tatpurusha)',
            'components': [compound],  # Would be split in real implementation
            'meaning': 'determinative compound'
        }
    
    def parse_sentence(self, sentence: str) -> Dict:
        """
        Parse a Sanskrit sentence.
        
        Returns grammatical analysis of each word.
        """
        words = sentence.split()
        analysis = []
        
        for word in words:
            # Try to identify case/number/gender
            word_analysis = {
                'word': word,
                'possible_forms': []
            }
            
            # Check against known endings
            for gender in ['पुं', 'स्त्री', 'नपुं']:
                for case in Vibhakti:
                    for number in [1, 2, 3]:
                        # This is simplified - real implementation would check all stems
                        pass
            
            analysis.append(word_analysis)
        
        return {
            'sentence': sentence,
            'words': analysis,
            'structure': self._identify_structure(analysis)
        }
    
    def _identify_structure(self, analysis: List[Dict]) -> str:
        """Identify sentence structure."""
        # Simple heuristic
        if len(analysis) >= 2:
            return 'कर्तृ-कर्मन्-क्रिया (Subject-Object-Verb)'
        return 'अल्पवाक्य (Short sentence)'
    
    def generate_sentence(self, subject: str, verb: str, object: str = None) -> str:
        """
        Generate a grammatically correct Sanskrit sentence.
        """
        # Subject in nominative (prathama)
        subj = self.decline(subject, 'पुं', Vibhakti.PRATHAMA, 1)
        
        # Verb in 3rd person singular present
        verb_form = self.conjugate(verb, 'LAT', 3, 1)
        
        if object:
            # Object in accusative (dvitiya)
            obj = self.decline(object, 'पुं', Vibhakti.DVITIYA, 1)
            return f"{subj} {obj} {verb_form} ।"
        
        return f"{subj} {verb_form} ।"
