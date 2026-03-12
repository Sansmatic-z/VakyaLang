# VakyaLang (????) � Copyright (c) 2026 Raj Mitra. All Rights Reserved.
# Original author: Raj Mitra (Visionary RM)
# Licensed under GNU AGPL v3.0 � see LICENSE and NOTICE.
# Any use, modification, or derivative work must preserve this header
# and include the NOTICE file. https://github.com/Sansmatic-z/VakyaLang

# संस्कृत-कोडकः - संस्कृत गणित इन्जिन्
# Sanskrit Coder - Native Sanskrit Mathematics Engine

import re
import math
from typing import Union, List, Dict, Tuple, Optional
from fractions import Fraction
from decimal import Decimal, getcontext

getcontext().prec = 50

class SanskritMathEngine:
    """
    Native Sanskrit mathematics engine supporting:
    - Sanskrit numeral arithmetic (०-९)
    - Bhūtasaṅkhyā (word-numeral) system
    - Vedic algorithms for multiplication/division
    - Sanskrit algebraic notation
    - Geometric calculations with Sanskrit terminology
    """
    
    def __init__(self):
        # Sanskrit digit mapping
        self.deva_digits = {
            '०': 0, '१': 1, '२': 2, '३': 3, '४': 4,
            '५': 5, '६': 6, '७': 7, '८': 8, '९': 9
        }
        self.digit_to_deva = {v: k for k, v in self.deva_digits.items()}
        
        # Bhūtasaṅkhyā system - word numerals from Sanskrit literature
        self.bhuta_sankhya = {
            'शून्यम्': 0, 'आकाश': 0, 'व्योम': 0, 'अंबर': 0, 'अनन्त': 0,
            'एक': 1, 'एकम्': 1, 'सूर्य': 1, 'आदित्य': 1, 'भानु': 1, 'रवि': 1,
            'द्वि': 2, 'द्वे': 2, 'नेत्र': 2, 'कर': 2, 'बाहु': 2, 'पक्ष': 2,
            'त्रि': 3, 'त्रीणि': 3, 'लोक': 3, 'अग्नि': 3, 'भुवन': 3,
            'चतुर्': 4, 'चत्वारि': 4, 'वेद': 4, 'युग': 4, 'समुद्र': 4,
            'पञ्च': 5, 'बाण': 5, 'इन्द्रिय': 5, 'पल्लव': 5,
            'षष्': 6, 'षट्': 6, 'अङ्ग': 6, 'ऋतु': 6, 'मस': 6,
            'सप्त': 7, 'मुनि': 7, 'धी': 7, 'समुद्र': 7,
            'अष्ट': 8, 'अष्टौ': 8, 'वसु': 8, 'नाग': 8, ' elephant': 8,
            'नव': 9, 'ग्रह': 9, 'रन्ध्र': 9, 'नन्दन': 9,
            'दश': 10, 'दिश्': 10, 'अवतार': 10,
            'एकादश': 11, 'द्वादश': 12, 'त्रयोदश': 13,
            'चतुर्दश': 14, 'पञ्चदश': 15, 'षोडश': 16,
            'सप्तदश': 17, 'अष्टादश': 18, 'एकोनविंशति': 19,
            'विंशति': 20, 'एकविंशति': 21, 'त्रिंशत्': 30,
            'चत्वारिंशत्': 40, 'पञ्चाशत्': 50, 'षष्टि': 60,
            'सप्तति': 70, 'अशीति': 80, 'नवति': 90,
            'शत': 100, 'सहस्र': 1000, 'अयुत': 10000,
            'लक्ष': 100000, 'प्रयुत': 1000000, 'कोटि': 10000000,
            'अर्बुद': 100000000, 'खर्व': 1000000000,
            'निखर्व': 10000000000, 'महापद्म': 100000000000,
        }
        
        # Sanskrit mathematical operations
        self.operations = {
            '+': '+', 'योगः': '+', 'सन्धिः': '+', 'सम्मेलनम्': '+',
            '-': '-', 'व्यवकलनम्': '-', 'अपसरणम्': '-', 'वियोगः': '-',
            '*': '*', 'गुणनम्': '*', 'हननम्': '*', 'वर्धनम्': '*',
            '/': '/', 'भागहारः': '/', 'विभाजनम्': '/', 'परिकलनम्': '/',
            '**': '**', 'वर्गः': '**2', 'घनः': '**3', 'घातः': '**',
            'मूलम्': 'sqrt', 'वर्गमूलम्': 'sqrt', 'घनमूलम्': 'cbrt',
            '%': '%', 'शेषः': '%', 'अवशेषः': '%',
            '(': '(', ')': ')'
        }
        
        # Algebraic variables in Sanskrit
        self.variables = {}
        
        # Formula database
        self.formulas = {
            'क्षेत्रफलम्': {
                'वर्ग': 'भुजा²',
                'आयत': 'दैर्घ्य × व्यास',
                'वृत्त': 'π × व्यासार्ध²',
                'त्रिभुज': '½ × आधार × उच्चता',
            },
            'परिमाणम्': {
                'वर्ग': '4 × भुजा',
                'आयत': '2 × (दैर्घ्य + व्यास)',
                'वृत्त': '2 × π × व्यासार्ध',
            },
            'आयतनम्': {
                'घन': 'भुजा³',
                'लम्बक': 'दैर्घ्य × व्यास × उच्चता',
                'गोल': '4/3 × π × व्यासार्ध³',
                'शङ्कु': '⅓ × π × व्यासार्ध² × उच्चता',
            }
        }
        
        # Physical constants in Sanskrit
        self.constants = {
            'पिः': math.pi,
            'π': math.pi,
            'ई': math.e,
            'e': math.e,
            'स्वर्णयोनिः': 1.618033988749895,  # Golden ratio
            'φ': 1.618033988749895,
            'प्रकाशवेगः': 299792458,  # Speed of light
            'c': 299792458,
            'गुरुत्वाकर्षणम्': 9.80665,  # g
            'g': 9.80665,
        }
        
    def parse_sanskrit_number(self, text: str) -> Union[int, float]:
        """
        Parse Sanskrit number in various formats:
        - Devanagari digits: १२३४
        - Word numerals: एक, द्वे, त्रीणि
        - Bhūtasaṅkhyā: सूर्य (1), नेत्र (2), etc.
        - Compound: द्वादश (12), त्रयोविंशति (23)
        """
        text = text.strip()
        
        # Try direct Devanagari digit parsing
        if all(c in self.deva_digits or c == '.' for c in text):
            return self._parse_deva_digits(text)
        
        # Try word numeral
        if text in self.bhuta_sankhya:
            return self.bhuta_sankhya[text]
        
        # Try compound numbers (simplified)
        compound = self._parse_compound_number(text)
        if compound is not None:
            return compound
            
        # Try mixed (e.g., "१२ दश" = 12 * 10 = 120)
        mixed = self._parse_mixed_number(text)
        if mixed is not None:
            return mixed
            
        raise ValueError(f"अज्ञात संख्या: {text}")
    
    def _parse_deva_digits(self, text: str) -> Union[int, float]:
        """Parse Devanagari digit string."""
        if '.' in text:
            parts = text.split('.')
            int_part = ''.join(str(self.deva_digits.get(c, c)) for c in parts[0])
            frac_part = ''.join(str(self.deva_digits.get(c, c)) for c in parts[1])
            return float(f"{int_part}.{frac_part}")
        else:
            result = ''.join(str(self.deva_digits.get(c, c)) for c in text)
            return int(result) if result else 0
    
    def _parse_compound_number(self, text: str) -> Optional[Union[int, float]]:
        """Parse compound Sanskrit numbers."""
        # Handle common compounds
        compounds = {
            'एकादश': 11, 'द्वादश': 12, 'त्रयोदश': 13, 'चतुर्दश': 14,
            'पञ्चदश': 15, 'षोडश': 16, 'सप्तदश': 17, 'अष्टादश': 18,
            'एकोनविंशति': 19, 'विंशति': 20, 'एकविंशति': 21,
            'द्वाविंशति': 22, 'त्रयोविंशति': 23, 'चतुर्विंशति': 24,
            'पञ्चविंशति': 25, 'षड्विंशति': 26, 'सप्तविंशति': 27,
            'अष्टाविंशति': 28, 'एकोनत्रिंशत्': 29, 'त्रिंशत्': 30,
        }
        return compounds.get(text)
    
    def _parse_mixed_number(self, text: str) -> Optional[Union[int, float]]:
        """Parse mixed notation like 'द्वे शत' (2 * 100)."""
        parts = text.split()
        if len(parts) == 2:
            try:
                first = self.parse_sanskrit_number(parts[0])
                second = self.parse_sanskrit_number(parts[1])
                return first * second
            except:
                pass
        return None
    
    def to_sanskrit_number(self, n: Union[int, float]) -> str:
        """Convert number to Sanskrit representation."""
        if isinstance(n, float) and n.is_integer():
            n = int(n)
            
        if isinstance(n, int):
            if n <= 20:
                return self._int_to_sanskrit_word(n)
            elif n < 100:
                return self._int_to_sanskrit_tens(n)
            elif n < 1000:
                return self._int_to_sanskrit_hundreds(n)
            else:
                return self._int_to_devanagari(n)
        else:
            # Float - use Devanagari
            return self._float_to_devanagari(n)
    
    def _int_to_sanskrit_word(self, n: int) -> str:
        """Convert small integer to Sanskrit word."""
        words = {
            0: 'शून्यम्', 1: 'एकम्', 2: 'द्वे', 3: 'त्रीणि', 4: 'चत्वारि',
            5: 'पञ्च', 6: 'षट्', 7: 'सप्त', 8: 'अष्टौ', 9: 'नव',
            10: 'दश', 11: 'एकादश', 12: 'द्वादश', 13: 'त्रयोदश',
            14: 'चतुर्दश', 15: 'पञ्चदश', 16: 'षोडश', 17: 'सप्तदश',
            18: 'अष्टादश', 19: 'एकोनविंशति', 20: 'विंशति',
        }
        return words.get(n, self._int_to_devanagari(n))
    
    def _int_to_sanskrit_tens(self, n: int) -> str:
        """Convert tens to Sanskrit."""
        tens = {
            20: 'विंशति', 30: 'त्रिंशत्', 40: 'चत्वारिंशत्',
            50: 'पञ्चाशत्', 60: 'षष्टि', 70: 'सप्तति',
            80: 'अशीति', 90: 'नवति',
        }
        if n in tens:
            return tens[n]
        
        # Compound: 21 = एकविंशति, 35 = पञ्चत्रिंशत्
        unit = n % 10
        ten = (n // 10) * 10
        
        if ten == 20:
            return self._int_to_sanskrit_word(unit) + 'विंशति'
        elif ten == 30:
            return self._int_to_sanskrit_word(unit) + 'त्रिंशत्'
        # ... etc
        
        return self._int_to_devanagari(n)
    
    def _int_to_sanskrit_hundreds(self, n: int) -> str:
        """Convert hundreds to Sanskrit."""
        if n == 100:
            return 'शतम्'
        elif n == 200:
            return 'द्विशतम्'
        elif n == 1000:
            return 'सहस्रम्'
        
        hundreds = n // 100
        remainder = n % 100
        
        result = self._int_to_sanskrit_word(hundreds) + 'शत'
        if remainder > 0:
            result += ' ' + self.to_sanskrit_number(remainder)
        return result
    
    def _int_to_devanagari(self, n: int) -> str:
        """Convert integer to Devanagari digits."""
        return ''.join(self.digit_to_deva.get(int(d), d) for d in str(n))
    
    def _float_to_devanagari(self, n: float) -> str:
        """Convert float to Devanagari digits."""
        if '.' in str(n):
            int_part, frac_part = str(n).split('.')
            return self._int_to_devanagari(int(int_part)) + '.' + ''.join(
                self.digit_to_deva.get(int(d), d) for d in frac_part
            )
        return self._int_to_devanagari(int(n))
    
    def calculate(self, expression: str) -> str:
        """
        Calculate mathematical expression in Sanskrit notation.
        
        Supports:
        - ५ + ३ (Devanagari arithmetic)
        - पञ्च योगः त्रीणि (word arithmetic)
        - वर्गः ५ (square of 5)
        - मूलम् १६ (square root of 16)
        """
        # Tokenize and parse
        tokens = self._tokenize_math(expression)
        
        # Convert to evaluable form
        evaluable = self._tokens_to_evaluable(tokens)
        
        # Evaluate safely
        try:
            result = self._safe_eval(evaluable)
            sanskrit_result = self.to_sanskrit_number(result)
            return f"{result} ({sanskrit_result})"
        except Exception as e:
            raise ValueError(f"गणना त्रुटिः {str(e)}")
    
    def _tokenize_math(self, expr: str) -> List[Tuple[str, Union[str, Decimal, int]]]:
        """Tokenize mathematical expression."""
        tokens = []
        i = 0
        expr = expr.strip()
        
        while i < len(expr):
            char = expr[i]
            
            # Skip whitespace
            if char.isspace():
                i += 1
                continue
            
            # Devanagari digit
            if char in self.deva_digits:
                num = ''
                while i < len(expr) and (expr[i] in self.deva_digits or expr[i] == '.'):
                    num += expr[i]
                    i += 1
                
                parsed_num = self._parse_deva_digits(num)
                if isinstance(parsed_num, float):
                    parsed_num = Decimal(str(parsed_num))
                tokens.append(('NUMBER', parsed_num))
                continue
            
            # ASCII digit
            if char.isdigit():
                num = ''
                while i < len(expr) and (expr[i].isdigit() or expr[i] == '.'):
                    num += expr[i]
                    i += 1
                tokens.append(('NUMBER', Decimal(num) if '.' in num else int(num)))
                continue
            
            # Word numeral or operation
            word = ''
            while i < len(expr) and not expr[i].isspace() and expr[i] not in '()':
                word += expr[i]
                i += 1
            
            if word:
                if word in self.bhuta_sankhya:
                    tokens.append(('NUMBER', self.bhuta_sankhya[word]))
                elif word in self.operations:
                    tokens.append(('OP', self.operations[word]))
                elif word in self.constants:
                    tokens.append(('NUMBER', self.constants[word]))
                else:
                    tokens.append(('UNKNOWN', word))
            else:
                i += 1
        
        return tokens
    
    def _tokens_to_evaluable(self, tokens: List[Tuple[str, Union[str, float]]]) -> str:
        """Convert tokens to Python-evaluable string."""
        parts = []
        for ttype, val in tokens:
            if ttype == 'NUMBER':
                parts.append(str(val))
            elif ttype == 'OP':
                if val == 'sqrt':
                    parts.append('math.sqrt')
                elif val == 'cbrt':
                    parts.append('(lambda x: x**(1/3))')
                else:
                    parts.append(val)
            elif ttype == 'UNKNOWN':
                # Try as variable
                if val in self.variables:
                    parts.append(str(self.variables[val]))
                else:
                    raise ValueError(f"अज्ञात पदम्: {val}")
        
        return ' '.join(parts)
    
    def _safe_eval(self, expr: str):
        """Safely evaluate mathematical expression."""
        allowed_names = {
            'math': math,
            'sqrt': math.sqrt,
            'pi': math.pi,
            'e': math.e,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log,
            'exp': math.exp,
            'abs': abs,
            'pow': pow,
        }
        
        # Replace Sanskrit fractions
        expr = expr.replace('⅓', '(1/3)').replace('½', '(1/2)').replace('¼', '(1/4)')
        expr = expr.replace('⅔', '(2/3)').replace('¾', '(3/4)')
        
        code = compile(expr, "<string>", "eval")
        for name in code.co_names:
            if name not in allowed_names:
                raise NameError(f"Use of {name} not allowed")
        
        return eval(code, {"__builtins__": {}}, allowed_names)
    
    def solve_equation(self, equation: str) -> str:
        """
        Solve algebraic equation in Sanskrit notation.
        
        Examples:
        - २x + ३ = ७
        - x² + ५x + ६ = ०
        """
        # Parse equation
        if '=' not in equation:
            raise ValueError("समीकरणे समाधान चिह्न (=) आवश्यकम्")
        
        left, right = equation.split('=', 1)
        
        # Convert to standard form ax + b = c or ax² + bx + c = 0
        left = self._sanskrit_to_algebraic(left.strip())
        right = self._sanskrit_to_algebraic(right.strip())
        
        # Move everything to left side
        standard_form = f"({left}) - ({right})"
        
        # Parse terms
        terms = self._parse_polynomial(standard_form)
        
        # Solve based on degree
        if len(terms) == 2:  # Linear: ax + b = 0
            return self._solve_linear(terms)
        elif len(terms) == 3:  # Quadratic: ax² + bx + c = 0
            return self._solve_quadratic(terms)
        else:
            return self._solve_numerical(standard_form)
    
    def _sanskrit_to_algebraic(self, expr: str) -> str:
        """Convert Sanskrit algebraic notation to Python."""
        # Replace Sanskrit numbers
        result = ''
        i = 0
        while i < len(expr):
            # Check for Devanagari digits
            if expr[i] in self.deva_digits:
                num = ''
                while i < len(expr) and expr[i] in self.deva_digits:
                    num += expr[i]
                    i += 1
                result += str(self._parse_deva_digits(num))
                continue
            
            # Check for word numerals
            word = ''
            while i < len(expr) and expr[i].isalpha():
                word += expr[i]
                i += 1
            
            if word:
                if word in self.bhuta_sankhya:
                    result += str(self.bhuta_sankhya[word])
                elif word in ['वर्गः', 'वर्ग']:
                    result += '**2'
                elif word in ['घनः', 'घन']:
                    result += '**3'
                elif word == 'मूलम्':
                    result += 'sqrt'
                else:
                    result += word
            else:
                if i < len(expr):
                    result += expr[i]
                i += 1
        
        # Handle implicit multiplication (2x -> 2*x)
        result = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', result)
        
        return result
    
    def _parse_polynomial(self, expr: str) -> Dict[int, Decimal]:
        """
        Parse polynomial into coefficient dictionary.
        Handles signs, numbers, and x, x**2 terms.
        Example: "2x**2 + 5x - 3" -> {2: Decimal('2.0'), 1: Decimal('5.0'), 0: Decimal('-3.0')}
        """
        terms = {0: Decimal('0.0'), 1: Decimal('0.0'), 2: Decimal('0.0')}
        expr = expr.replace(' ', '')
        
        # Tokenize by finding all terms (signed groups of digits and variables)
        # Pattern: [+-]? (number)? (x)? (**2)?
        pattern = r'([+-]?(?:\d*\.?\d+)?)(x)?(?:\*\*(\d))?'
        matches = re.finditer(pattern, expr)
        
        for m in matches:
            coeff_str, var, power_str = m.groups()
            if not coeff_str and not var: continue
            
            # Determine coefficient value
            if coeff_str == "+" or not coeff_str:
                coeff = Decimal('1.0')
            elif coeff_str == "-":
                coeff = Decimal('-1.0')
            else:
                coeff = Decimal(coeff_str)
                
            # Determine power
            if not var:
                power = 0
            elif not power_str:
                power = 1
            else:
                power = int(power_str)
                
            if power in terms:
                terms[power] += coeff
                
        return terms
    
    def _solve_linear(self, terms: Dict[int, Decimal]) -> str:
        """Solve linear equation ax + b = 0."""
        a = terms.get(1, Decimal('0.0'))
        b = terms.get(0, Decimal('0.0'))
        
        if a == 0:
            if b == 0:
                return "अनन्त हलानि (Infinite solutions)"
            else:
                return "कोऽपि हलं नास्ति (No solution)"
        
        x = -b / a
        return f"x = {self.to_sanskrit_number(float(x))}"
    
    def _solve_quadratic(self, terms: Dict[int, Decimal]) -> str:
        """Solve quadratic equation ax² + bx + c = 0 using Sanskrit method."""
        a = terms.get(2, Decimal('0.0'))
        b = terms.get(1, Decimal('0.0'))
        c = terms.get(0, Decimal('0.0'))
        
        if a == 0:
            return self._solve_linear(terms)
        
        # Calculate discriminant (विभेदकः)
        discriminant = b**2 - 4*a*c
        
        if discriminant < 0:
            return "वास्तविक हलं नास्ति (No real solutions)"
        elif discriminant == 0:
            x = -b / (2*a)
            return f"x = {self.to_sanskrit_number(float(x))} (एकं हलम्)"
        else:
            # For square root of decimal, we can convert back to float or use math.sqrt
            sqrt_d = Decimal(str(math.sqrt(float(discriminant))))
            x1 = (-b + sqrt_d) / (2*a)
            x2 = (-b - sqrt_d) / (2*a)
            return f"x₁ = {self.to_sanskrit_number(float(x1))}, x₂ = {self.to_sanskrit_number(float(x2))}"
    
    def _solve_numerical(self, expr: str) -> str:
        """Solve using numerical methods."""
        # Newton-Raphson method implementation
        # Placeholder for complex equations
        return "जटिल समीकरणम् - सांख्यिकी विधिः आवश्यकी"
    
    def vedic_multiply(self, a: Union[int, str], b: Union[int, str]) -> str:
        """
        Multiply using Vedic method (Urdhva-Tiryagbhyam - vertical and crosswise).
        
        This is the actual Vedic algorithm, not just standard multiplication.
        """
        # Convert to integers if Sanskrit
        if isinstance(a, str):
            a = self.parse_sanskrit_number(a)
        if isinstance(b, str):
            b = self.parse_sanskrit_number(b)
        
        a_int = int(a)
        b_int = int(b)
        
        # For 2-digit numbers, show the Vedic method
        if 10 <= a_int < 100 and 10 <= b_int < 100:
            return self._vedic_multiply_2digit(a_int, b_int)
        
        # General case
        result = a_int * b_int
        return f"{self.to_sanskrit_number(a_int)} × {self.to_sanskrit_number(b_int)} = {self.to_sanskrit_number(result)}"
    
    def _vedic_multiply_2digit(self, a: int, b: int) -> str:
        """Demonstrate Vedic multiplication for 2-digit numbers."""
        # a = 10*p + q, b = 10*r + s
        # Result = 100*(p*r) + 10*(p*s + q*r) + q*s
        
        p, q = a // 10, a % 10
        r, s = b // 10, b % 10
        
        vertical_left = p * r
        cross = p * s + q * r
        vertical_right = q * s
        
        # Handle carries
        carry = cross // 10
        vertical_left += carry
        cross = cross % 10
        
        result = vertical_left * 100 + cross * 10 + vertical_right
        
        explanation = f"""
वैदिक गुणनम् (Urdhva-Tiryagbhyam):
{a} × {b}

ऊर्ध्वतिर्यक् (Vertical & Crosswise):
  {p} | {q}
  {r} | {s}

दक्षिण ऊर्ध्व: {q} × {s} = {vertical_right}
तिर्यक्: ({p} × {s}) + ({q} × {r}) = {p*s} + {q*r} = {p*s + q*r}
वाम ऊर्ध्व: {p} × {r} = {vertical_left}

परिणाम: {result}
"""
        return explanation.strip()
    
    def calculate_area(self, shape: str, **params) -> str:
        """Calculate area using Sanskrit geometric formulas."""
        shape_map = {
            'वर्ग': 'square', 'समचतुरस्र': 'square',
            'आयत': 'rectangle', 'दीर्घचतुरस्र': 'rectangle',
            'वृत्त': 'circle', 'मण्डल': 'circle',
            'त्रिभुज': 'triangle', 'तribhuj': 'triangle',
        }
        
        shape_en = shape_map.get(shape, shape)
        
        if shape_en == 'square':
            side = params.get('भुजा', params.get('side', 0))
            if isinstance(side, str):
                side = self.parse_sanskrit_number(side)
            area = side ** 2
            return f"क्षेत्रफलम् = {self.to_sanskrit_number(area)} (वर्ग {self.to_sanskrit_number(side)})"
        
        elif shape_en == 'rectangle':
            length = params.get('दैर्घ्य', params.get('length', 0))
            width = params.get('व्यास', params.get('width', 0))
            if isinstance(length, str):
                length = self.parse_sanskrit_number(length)
            if isinstance(width, str):
                width = self.parse_sanskrit_number(width)
            area = length * width
            return f"क्षेत्रफलम् = {self.to_sanskrit_number(area)}"
        
        elif shape_en == 'circle':
            radius = params.get('व्यासार्ध', params.get('radius', 0))
            if isinstance(radius, str):
                radius = self.parse_sanskrit_number(radius)
            area = math.pi * radius ** 2
            return f"क्षेत्रफलम् = {area:.6f} (व्यासार्ध {self.to_sanskrit_number(radius)})"
        
        elif shape_en == 'triangle':
            base = params.get('आधार', params.get('base', 0))
            height = params.get('उच्चता', params.get('height', 0))
            if isinstance(base, str):
                base = self.parse_sanskrit_number(base)
            if isinstance(height, str):
                height = self.parse_sanskrit_number(height)
            area = 0.5 * base * height
            return f"क्षेत्रफलम् = {self.to_sanskrit_number(area)}"
        
        else:
            return f"अज्ञात आकृति: {shape}"
    
    def lookup_formula(self, query: str) -> str:
        """Lookup mathematical formula."""
        query = query.lower()
        
        for category, formulas in self.formulas.items():
            for name, formula in formulas.items():
                if query in name or query in formula:
                    return f"{category} ({name}): {formula}"
        
        # Check constants
        for name, value in self.constants.items():
            if query in name:
                return f"{name} = {value}"
        
        return f"सूत्रं न लब्धम्: {query}"

