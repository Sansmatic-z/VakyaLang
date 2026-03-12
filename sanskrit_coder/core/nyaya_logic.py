# Sanskrit Coder — Copyright (c) 2026 Raj Mitra. All Rights Reserved.
# Part of VakyaLang project (https://github.com/Sansmatic-z/VakyaLang)
# Licensed under GNU AGPL v3.0 — see root LICENSE_AGPL and NOTICE.
# Any use or modification must preserve this header and include NOTICE.

from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum

class Pramana(Enum):
    """Valid sources of knowledge in Nyāya."""
    PRATYAKSHA = "प्रत्यक्ष"  # Perception
    ANUMANA = "अनुमान"      # Inference
    UPAMANA = "उपमान"       # Comparison
    SHABDA = "शब्द"          # Verbal testimony
    ARTHAPATTI = "अर्थापत्ति"  # Postulation
    ANUPALABDHI = "अनुपलब्धि" # Non-perception

@dataclass
class Padartha:
    """Category of reality (Nyāya ontology)."""
    name: str
    sanskrit_name: str
    category: str  # द्रव्य, गुण, कर्म, सामान्य, विशेष, समवाय
    
    def __str__(self):
        return f"{self.sanskrit_name} ({self.name})"

@dataclass
class Vyapti:
    """Invariable concomitance (universal relation)."""
    hetu: str      # Reason/middle term (e.g., "smoke")
    sadhya: str    # Proved/major term (e.g., "fire")
    paksha: str    # Subject/minor term (e.g., "mountain")
    
    def validate(self) -> bool:
        """Check if vyāpti holds (simplified)."""
        # In real implementation, this would check a knowledge base
        known_relations = {
            ('धूम', 'वह्नि'): True,  # Smoke implies fire
            ('मृत्तिका', 'घट'): True,  # Clay implies pot
            ('प्राण', 'जीव'): True,  # Breath implies life
        }
        return known_relations.get((self.hetu, self.sadhya), False)

class Pancavayava:
    """
    Five-membered syllogism (पञ्चावयव).
    
    The classical Nyāya syllogism structure:
    1. प्रतिज्ञा (Proposition)
    2. हेतु (Reason)
    3. उदाहरण (Example)
    4. उपनय (Application)
    5. निगमन (Conclusion)
    """
    
    def __init__(self):
        self.pratijna: str = ""      # Proposition: "The mountain has fire"
        self.hetu: str = ""          # Reason: "Because it has smoke"
        self.udaharana: str = ""     # Example: "Where there's smoke, there's fire, like a kitchen"
        self.upanaya: str = ""       # Application: "This mountain has smoke"
        self.nigamana: str = ""      # Conclusion: "Therefore, this mountain has fire"
        
    def construct(self, paksha: str, sadhya: str, hetu: str, drishtanta: str) -> str:
        """
        Construct a five-membered syllogism.
        
        Args:
            paksha: Subject (e.g., "पर्वत" - mountain)
            sadhya: Predicate (e.g., "वह्निमान्" - possessor of fire)
            hetu: Reason (e.g., "धूमवत्त्वात्" - because of having smoke)
            drishtanta: Example (e.g., "महानस" - kitchen)
        """
        self.pratijna = f"{paksha} {sadhya} अस्ति"
        self.hetu = f"{hetu} कारणात्"
        self.udaharana = f"यः {hetu.split('वत्त्वात्')[0] if 'वत्त्वात्' in hetu else hetu}वान् सः {sadhya} अस्ति, यथा {drishtanta}"
        self.upanaya = f"अयं {paksha} तथा"
        self.nigamana = f"तस्मात् {paksha} {sadhya} अस्ति"
        
        return self.render()
    
    def render(self) -> str:
        """Render the full syllogism in Sanskrit."""
        return f"""
प्रतिज्ञा (Proposition):
  {self.pratijna}

हेतु (Reason):
  {self.hetu}

उदाहरण (Example):
  {self.udaharana}

उपनय (Application):
  {self.upanaya}

निगमन (Conclusion):
  {self.nigamana}
""".strip()
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the syllogism against Nyāya rules."""
        errors = []
        
        # Check for five avayavas
        if not all([self.pratijna, self.hetu, self.udaharana, self.upanaya, self.nigamana]):
            errors.append("अपूर्णं पञ्चावयवम् (Incomplete syllogism)")
        
        # Check for pakṣadoṣa (fallacies)
        # Simplified checks - real implementation would be more thorough
        
        # 1. सिद्धसाधन (proving what is already proved)
        # 2. असिद्ध (unproved middle)
        # 3. विरुद्ध (contradictory)
        # 4. सत्प्रतिपक्ष (counter-balanced)
        # 5. बाधित (counter-facted)
        # 6. चल (erratic)
        # 7. करणाटिक (too narrow)
        # 8. दीर्घटिक (too broad)
        
        return len(errors) == 0, errors

class Hetvabhasa:
    """
    Fallacies of reason (हेत्वाभास).
    
    The 5 main types of fallacious reasons in Nyāya.
    """
    
    FALLACIES = {
        'सव्यभिचार': {
            'name': 'Savyabhicāra (The Erratic)',
            'desc': 'The reason is too broad, present in both similar and dissimilar cases',
            'example': 'Sound is eternal because it is knowable (knowability is present in both eternal and non-eternal things)'
        },
        'विरुद्ध': {
            'name': 'Viruddha (The Contradictory)',
            'desc': 'The reason contradicts the conclusion',
            'example': 'Sound is eternal because it is produced (produced things are non-eternal)'
        },
        'सत्प्रतिपक्ष': {
            'name': 'Satpratipakṣa (The Counter-balanced)',
            'desc': 'There is an equally strong reason for the opposite conclusion',
            'example': 'Sound is eternal because it is audible, but also non-eternal because it is produced'
        },
        'असिद्ध': {
            'name': 'Asiddha (The Unproved)',
            'desc': 'The reason itself needs proof',
            'example': 'Shadow is a substance because it has motion (whether shadow has motion is disputed)'
        },
        'बाधित': {
            'name': 'Bādhita (The Counter-facted)',
            'desc': 'The reason is contradicted by direct perception or other pramāṇa',
            'example': 'Fire is cold because it is a substance (contradicted by touch)'
        }
    }
    
    def analyze(self, hetu: str, paksha: str, sadhya: str) -> Dict:
        """
        Analyze a reason for fallacies.
        
        Returns analysis of which fallacies (if any) are present.
        """
        results = {}
        
        # Check for each fallacy type
        # This is a simplified implementation
        
        # Check Viruddha (contradictory)
        contradictory_pairs = [
            ('नित्य', 'अनित्य'),  # eternal / non-eternal
            ('सत्', 'असत्'),      # existent / non-existent
            ('सुख', 'दुःख'),      # pleasure / pain
        ]
        
        for pair in contradictory_pairs:
            if pair[0] in sadhya and pair[1] in hetu:
                results['विरुद्ध'] = self.FALLACIES['विरुद्ध']
            if pair[1] in sadhya and pair[0] in hetu:
                results['विरुद्ध'] = self.FALLACIES['विरुद्ध']
        
        return results

class NyayaInference:
    """
    Nyāya inference engine for logical reasoning.
    """
    
    def __init__(self):
        self.knowledge_base: List[Dict] = []
        self.pancavayava = Pancavayava()
        self.hetvabhasa = Hetvabhasa()
        
    def add_fact(self, subject: str, predicate: str, certainty: float = 1.0):
        """Add a fact to the knowledge base."""
        self.knowledge_base.append({
            'subject': subject,
            'predicate': predicate,
            'certainty': certainty
        })
        
    def infer(self, observation: str, known_relation: str) -> List[Dict]:
        """
        Perform anumāna (inference) from observation.
        
        Classical example:
        - Observation: "The mountain has smoke" (observation)
        - Known relation: "Where there's smoke, there's fire" (vyāpti)
        - Inference: "The mountain has fire"
        """
        inferences = []
        
        # Parse the observation
        # Format: "X has Y" or "X is Y"
        
        # Check knowledge base for relations
        for fact in self.knowledge_base:
            if known_relation in fact['predicate']:
                inferences.append({
                    'conclusion': f"{observation.split()[0]} has {fact['predicate'].split()[-1]}",
                    'confidence': fact['certainty'],
                    'method': 'anumana'
                })
        
        return inferences
    
    def compare(self, subject: str, standard: str, shared_quality: str) -> str:
        """
        Upamāna (comparison/analogy).
        
        Example: 
        - Subject: "gavaya" (forest ox)
        - Standard: "cow"
        - Shared quality: "having horns, etc."
        - Conclusion: "gavaya is similar to cow"
        """
        return f"""
उपमानम् (Comparison):
{subject} तथा {standard} योः {shared_quality} साम्यम् अस्ति।
तस्मात् {subject} {standard} इव।
"""
    
    def classify_pramana(self, statement: str) -> Pramana:
        """
        Classify how a statement is known (which pramāṇa applies).
        """
        # Simple heuristic classification
        if any(word in statement for word in ['पश्य', 'दृश्यते', 'seen']):
            return Pramana.PRATYAKSHA
        elif any(word in statement for word in ['तस्मात्', 'अतः', 'therefore']):
            return Pramana.ANUMANA
        elif any(word in statement for word in ['यथा', 'like', 'as']):
            return Pramana.UPAMANA
        elif any(word in statement for word in ['शास्त्र', 'आप्त', 'scripture']):
            return Pramana.SHABDA
        else:
            return Pramana.ANUMANA  # Default to inference
    
    def debate_format(self, thesis: str, antithesis: str) -> str:
        """
        Format a debate (vāda) between two positions.
        
        Nyāya debate structure:
        1. प्रतिज्ञा (Thesis)
        2. प्रतिज्ञाहानि (Objection)
        3. उत्तर (Reply)
        4. संगति (Conclusion)
        """
        return f"""
वादः (Debate)

पक्षः (Proponent):
  प्रतिज्ञा: {thesis}

प्रतिपक्षः (Opponent):
  प्रतिज्ञाहानि: {antithesis}

पक्षस्य उत्तरम् (Reply):
  {self._generate_reply(thesis, antithesis)}

निर्णयः (Conclusion):
  {self._evaluate_debate(thesis, antithesis)}
"""
    
    def _generate_reply(self, thesis: str, antithesis: str) -> str:
        """Generate a reply to an objection."""
        # Simplified - real implementation would analyze the content
        return f"{thesis} इति वचनं {antithesis} इति दोषेण न दूष्यते।"
    
    def _evaluate_debate(self, thesis: str, antithesis: str) -> str:
        """Evaluate which position is stronger."""
        # Placeholder for actual evaluation logic
        return "पक्षः प्रबलतरः (Thesis is stronger)" if len(thesis) > len(antithesis) else "प्रतिपक्षः प्रबलतरः (Antithesis is stronger)"

class Tarka:
    """
    तर्क - Hypothetical reasoning/reductio ad absurdum.
    """
    
    def __init__(self):
        self.hypotheses: List[str] = []
        
    def assume(self, hypothesis: str):
        """Assume a hypothesis for testing."""
        self.hypotheses.append(hypothesis)
        
    def derive_contradiction(self, assumption: str, known_facts: List[str]) -> Optional[str]:
        """
        Show that assumption leads to contradiction (tarka).
        
        If assuming X leads to contradiction with known facts,
        then X must be false.
        """
        # Check for contradictions
        contradictions = []
        
        for fact in known_facts:
            # Simple string matching for contradiction
            # Real implementation would use logical analysis
            negated_fact = self._negate(fact)
            if negated_fact in assumption or negated_fact in self.hypotheses:
                contradictions.append(fact)
        
        if contradictions:
            return f"""
तर्कः (Reductio):
यदि {assumption} स्यात्,
तर्हि {', '.join(contradictions)} इति सत्यं न स्यात्।
किन्तु {', '.join(contradictions)} इति सत्यम्।
तस्मात् {assumption} असत्यम्।
"""
        return None
    
    def _negate(self, statement: str) -> str:
        """Create negation of a statement."""
        negations = {
            'सत्': 'असत्', 'असत्': 'सत्',
            'नित्य': 'अनित्य', 'अनित्य': 'नित्य',
            'सुख': 'दुःख', 'दुःख': 'सुख',
        }
        for pos, neg in negations.items():
            if pos in statement:
                return statement.replace(pos, neg)
            if neg in statement:
                return statement.replace(neg, pos)
        return f"न {statement}"


