# संस्कृत-कोडकः - अनुवादकः
# *Visionary RM (Raj Mitra)* ⚡
# *"संस्कृतम् अमरम् भवतु"* 🔥

"""
Sanskrit-English Translator
संस्कृत-English अनुवादकः
"""

import re
from typing import Dict, List, Optional


class SanskritTranslator:
    """Sanskrit-English Translation Engine"""
    
    MATH_DICTIONARY = {
        'शून्यम्': 'zero', 'एकम्': 'one', 'द्वे': 'two', 'त्रीणि': 'three', 'चत्वारि': 'four',
        'पञ्च': 'five', 'षट्': 'six', 'सप्त': 'seven', 'अष्टौ': 'eight', 'नव': 'nine', 'दश': 'ten',
        'प्लस': 'plus', 'योगः': 'plus', 'ऋण': 'minus', 'व्यवकलनम्': 'subtraction',
        'गुणनम्': 'multiply', 'गुण': 'times', 'भागहार': 'divide', 'विभाजनम्': 'division',
        'घात': 'power', 'शक्तिः': 'exponent', 'मूलम्': 'root', 'वर्गमूलम्': 'square root',
        'समीकरणम्': 'equation', 'चलः': 'variable', 'समाधत्स्व': 'solve', 'मानम्': 'value',
        'समानम्': 'equals', 'तुल्यम्': 'equal', '=': '=',
        'बलम्': 'force', 'द्रव्यमानम्': 'mass', 'त्वरणम्': 'acceleration', 'वेगः': 'velocity',
        'गणय': 'calculate', 'पश्य': 'show', 'दर्शय': 'show', 'अन्वेषय': 'search', 'परिवर्तय': 'convert',
    }
    
    SANSKRIT_DICTIONARY = {v: k for k, v in MATH_DICTIONARY.items()}
    
    def __init__(self):
        pass
    
    def is_sanskrit(self, text: str) -> bool:
        """Check if text contains Sanskrit (Devanagari) characters"""
        sanskrit_pattern = re.compile(r'[\u0900-\u097F]')
        return bool(sanskrit_pattern.search(text))
    
    def sanskrit_to_english(self, text: str) -> str:
        """Translate Sanskrit text to English"""
        result = text
        for sanskrit, english in self.MATH_DICTIONARY.items():
            result = result.replace(sanskrit, english)
        return result.strip()
    
    def sanskrit_to_english_math(self, expression: str) -> str:
        """Translate Sanskrit mathematical expression to English"""
        result = self._convert_sanskrit_digits_to_arabic(expression)
        
        # Word number mapping (including potential variants)
        word_numbers = {
            'शून्यम्': '0', 'एकम्': '1', 'द्वे': '2', 'त्रीणि': '3', 'चत्वारि': '4',
            'पञ्च': '5', 'षट्': '6', 'सप्त': '7', 'अष्टौ': '8', 'नव': '9', 'दश': '10',
        }
        
        # Operator mapping
        operator_map = {
            'प्लस': '+', 'योगः': '+', 'ऋण': '-', 'व्यवकलन्': '-', 'व्यवकलनम्': '-',
            'गुणनम्': '*', 'गुण': '*', 'भागहार': '/', 'विभाजनम्': '/',
            'घात': '**', 'शक्तिः': '**', 'समानम्': '=', '×': '*', '÷': '/',
        }

        # Replace word numbers first (to avoid overlapping with longer words)
        for word, num in word_numbers.items():
            result = result.replace(word, num)
            
        for sanskrit_op, english_op in operator_map.items():
            result = result.replace(sanskrit_op, english_op)
            
        return result.strip()
    
    def _convert_sanskrit_digits_to_arabic(self, number: str) -> str:
        """Convert Sanskrit digits to Arabic"""
        DIGITS_REVERSE = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}
        result = ""
        for char in str(number):
            if char in DIGITS_REVERSE:
                result += DIGITS_REVERSE[char]
            else:
                result += char
        return result
    
    def english_to_sanskrit(self, text: str) -> str:
        """Translate English text to Sanskrit"""
        result = text
        for english, sanskrit in self.SANSKRIT_DICTIONARY.items():
            pattern = r'\b' + re.escape(english) + r'\b'
            result = re.sub(pattern, sanskrit, result, flags=re.IGNORECASE)
        return result.strip()
    
    def translate(self, text: str, to_language: str = 'english') -> str:
        """Auto-detect and translate"""
        if to_language.lower() == 'sanskrit':
            return self.english_to_sanskrit(text)
        else:
            return self.sanskrit_to_english(text)
