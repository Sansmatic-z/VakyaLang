# VakyaLang (????) � Copyright (c) 2026 Raj Mitra. All Rights Reserved.
# Original author: Raj Mitra (Visionary RM)
# Licensed under GNU AGPL v3.0 � see LICENSE and NOTICE.
# Any use, modification, or derivative work must preserve this header
# and include the NOTICE file. https://github.com/Sansmatic-z/VakyaLang

# संस्कृत-कोडकः - संख्या पद्धतिः
# *Visionary RM (Raj Mitra)* ⚡
# *"संस्कृतम् अमरम् भवतु"* 🔥

"""
Sanskrit Numbers System
संस्कृत संख्या पद्धतिः

Handles Sanskrit digits (०-९), number words, and conversions.
"""

from typing import Union


class SanskritNumbers:
    """
    Sanskrit Number System Handler
    संस्कृत संख्या तन्त्रम्
    """
    
    # Sanskrit digits (Devanagari)
    DIGITS = {
        '0': '०',
        '1': '१',
        '2': '२',
        '3': '३',
        '4': '४',
        '5': '५',
        '6': '६',
        '7': '७',
        '8': '८',
        '9': '९',
    }
    
    # Reverse mapping
    DIGITS_REVERSE = {v: k for k, v in DIGITS.items()}
    
    # Number words (1-10)
    NUMBER_WORDS = {
        0: 'शून्यम्',
        1: 'एकम्',
        2: 'द्वे',
        3: 'त्रीणि',
        4: 'चत्वारि',
        5: 'पञ्च',
        6: 'षट्',
        7: 'सप्त',
        8: 'अष्टौ',
        9: 'नव',
        10: 'दश',
        11: 'एकादश',
        12: 'द्वादश',
        13: 'त्रयोदश',
        14: 'चतुर्दश',
        15: 'पञ्चदश',
        16: 'षोडश',
        17: 'सप्तदश',
        18: 'अष्टादश',
        19: 'एकोनविंशति',
        20: 'विंशति',
        30: 'त्रिंशत्',
        40: 'चत्वारिंशत्',
        50: 'पञ्चाशत्',
        60: 'षष्टि',
        70: 'सप्तति',
        80: 'अशीति',
        90: 'नवति',
        100: 'शतम्',
        1000: 'सहस्रम्',
    }
    
    # Math operators in Sanskrit
    OPERATORS = {
        '+': 'प्लस',
        '-': 'ऋण',
        '*': 'गुणनम्',
        '/': 'भागहार',
        '=': 'समानम्',
        '×': 'गुणनम्',
        '÷': 'भागहार',
    }
    
    def __init__(self):
        """Initialize number system"""
        pass
    
    def to_sanskrit_digits(self, number: str) -> str:
        """
        Convert Arabic numerals to Sanskrit (Devanagari) digits
        123 → १२३
        """
        result = ""
        for char in str(number):
            if char in self.DIGITS:
                result += self.DIGITS[char]
            else:
                result += char
        return result
    
    def to_arabic_digits(self, number: str) -> str:
        """
        Convert Sanskrit (Devanagari) digits to Arabic numerals
        १२३ → 123
        """
        result = ""
        for char in str(number):
            if char in self.DIGITS_REVERSE:
                result += self.DIGITS_REVERSE[char]
            else:
                result += char
        return result
    
    def number_to_sanskrit(self, num: Union[int, float]) -> str:
        """
        Convert number to Sanskrit words
        5 → पञ्च
        """
        if isinstance(num, float):
            parts = str(num).split('.')
            whole = int(parts[0])
            decimal = parts[1] if len(parts) > 1 else "0"
            
            whole_word = self._convert_whole(whole)
            decimal_word = self.to_sanskrit_digits(decimal)
            
            return f"{whole_word} दशमलव {decimal_word}"
        
        return self._convert_whole(int(num))
    
    def _convert_whole(self, num: int) -> str:
        """Convert whole number to Sanskrit words"""
        if num < 0:
            return "ऋण " + self._convert_whole(abs(num))
        
        if num in self.NUMBER_WORDS:
            return self.NUMBER_WORDS[num]
        
        if num < 100:
            tens = (num // 10) * 10
            ones = num % 10
            
            if ones == 0:
                return self.NUMBER_WORDS.get(tens, str(num))
            
            tens_word = self.NUMBER_WORDS.get(tens, "")
            ones_word = self.NUMBER_WORDS.get(ones, "")
            
            return f"{tens_word} {ones_word}"
        
        if num < 1000:
            hundreds = num // 100
            remainder = num % 100
            
            if hundreds == 1:
                result = "शतम्"
            else:
                result = f"{self.NUMBER_WORDS.get(hundreds, str(hundreds))} शतम्"
            
            if remainder > 0:
                result += f" {self._convert_whole(remainder)}"
            
            return result
        
        if num < 10000:
            thousands = num // 1000
            remainder = num % 1000
            
            if thousands == 1:
                result = "सहस्रम्"
            else:
                result = f"{self._convert_whole(thousands)} सहस्रम्"
            
            if remainder > 0:
                result += f" {self._convert_whole(remainder)}"
            
            return result
        
        return self.to_sanskrit_digits(str(num))
    
    def sanskrit_word_to_number(self, word: str) -> int:
        """Convert Sanskrit number word to number"""
        word = word.strip().lower()
        
        for num, sanskrit_word in self.NUMBER_WORDS.items():
            if word == sanskrit_word.lower():
                return num
        
        return -1
    
    def parse_sanskrit_expression(self, expression: str) -> str:
        """
        Parse Sanskrit mathematical expression to English
        "५ प्लस ३" → "5 + 3"
        """
        result = self.to_arabic_digits(expression)
        
        replacements = {
            'प्लस': '+',
            'योगः': '+',
            'ऋण': '-',
            'व्यवकलनम्': '-',
            'गुणनम्': '*',
            'गुण': '*',
            'भागहार': '/',
            'विभाजनम्': '/',
            'घात': '**',
            'शक्तिः': '**',
            'मूलम्': 'sqrt',
            'समानम्': '=',
            '×': '*',
            '÷': '/',
        }
        
        for sanskrit_op, english_op in replacements.items():
            result = result.replace(sanskrit_op, english_op)
        
        return result.strip()
    
    def format_result_sanskrit(self, result: Union[int, float], show_words: bool = True) -> str:
        """Format result in Sanskrit"""
        digits = self.to_sanskrit_digits(str(result))
        
        if show_words:
            words = self.number_to_sanskrit(result)
            return f"{digits} ({words})"
        
        return digits

